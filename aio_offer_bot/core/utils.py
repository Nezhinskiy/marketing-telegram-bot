import asyncio
import io
import random
import re
import time
import traceback
from collections import UserDict
from collections.abc import Iterable as IterableABC
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Iterable, Union

from PIL import Image, ImageEnhance
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)

import config
from loggers import get_logger

logger = get_logger()


def restart_container(container_name: str) -> None:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    container = client.containers.get(container_name)
    container.restart()


def chunks(lst: list, n: int) -> Iterable[list]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def str_exception(exc: Exception, with_traceback=True) -> str:
    message = f"{type(exc)}: {str(exc)}."
    if with_traceback:
        traceback_str = ''.join(traceback.format_tb(exc.__traceback__))
        message = f"{message}\n{traceback_str}"
    return message


def get_map_from_list(
        list_: Iterable,
        extract_key_func: Callable,
        extract_elem_func: Callable = lambda elem: elem
) -> dict:
    """Конвертит список в мапу списков по ключу."""
    result = {}
    for elem in list_:
        key = extract_key_func(elem)
        result[key] = result.get(key, []) + [extract_elem_func(elem)]
    return result


def replace_all(text: str, to_replace: Iterable[str], replacement: str) -> str:
    pattern = '|'.join(to_replace)
    return re.sub(pattern, replacement, text)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def set_random_enhance(photo: io.BytesIO) -> bytes:
    img = Image.open(photo)
    # Меняем яркость изображения, т.к. миджорни палит одинаковые фотки
    # После чего присылает ссылку только на первую уникальную фотку
    enhancer = ImageEnhance.Brightness(img)
    im_output = enhancer.enhance(random.uniform(0.95, 1.05))
    new_img = io.BytesIO()
    im_output.save(new_img, format='JPEG')
    return new_img.getvalue()


def log_event_loop_info(
        loop: asyncio.AbstractEventLoop,
        logger: 'BaseLogger' = logger
) -> None:
    if loop is None:
        logger.error('Provided loop is None.')
        return
    logger.info(f'Event Loop ID: {id(loop)}')
    logger.info(f'Is loop running: {loop.is_running()}')
    logger.info(f'Is loop closed: {loop.is_closed()}')
    logger.info(f'Debug mode status: {loop.get_debug()}')
    current_task = asyncio.current_task(loop)
    if current_task:
        logger.info(f'Current task: {current_task}')
    else:
        logger.info('No current task is running.')
    all_tasks = asyncio.all_tasks(loop)
    if all_tasks:
        logger.info(f'Number of all tasks scheduled: {len(all_tasks)}')
        for task in all_tasks:
            logger.info(f'Task: {task}')
    else:
        logger.info('No tasks scheduled.')


class TwoWayMap(UserDict):
    """
    Двухсторонняя мапа.
    АТТЕНШИОН: Двойной размер!!!
    АТТЕНШИОН: К значениям такие же требования как к ключам!!!
    """

    def __init__(self, dict=None, /, **kwargs):
        super().__init__(dict, **kwargs)
        self._reversed = {value: key for key, value in self.items()}

    def get(
            self,
            key: Any,
            default: Any = None,
            reverse: bool = False
    ) -> Any:
        if not reverse:
            return super().get(key, default)
        return self._reversed.get(key, default)


def time_track(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            logger.info(f'>>>time_track function {func.__name__} '
                        f'completed in {end_time - start_time} seconds')
            return result
        except Exception as exc:
            logger.error(f'>>>time_track Unexpected error in function '
                         f'{func.__name__}: {exc}')
            raise
    return wrapper


def log_stack_for_retry(retry_state: 'RetryState') -> None:
    if retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        current_stack = traceback.extract_stack()
        relevant_stack = current_stack[-49:-39]
        formatted_stack_trace = traceback.format_list(relevant_stack)
        logger.traceback_for_retry(
            'error' if retry_state.attempt_number > 1 else 'info',
            f'Attempt: {retry_state.attempt_number}; '
            f'Exception: {type(exception).__name__}; '
            f'Stack trace abbreviated: {formatted_stack_trace}'
        )


def divide_text_smartly(
        text: str,
        max_length: int,
        separators: Iterable[str] = None
) -> Iterable[str]:
    if len(text) <= max_length:
        return [text]

    if separators is None:
        separators = ['\n\n', '\n', '.', '!', '?', ',', ' ']

    result = []
    current_index = 0

    while current_index < len(text):
        # Ограничиваем текущую часть максимальной длиной
        end_index = min(current_index + max_length, len(text))
        if end_index == len(text):
            result.append(text[current_index:end_index].strip())
            break

        found_separator = False
        for separator in separators:
            separator_index = text.rfind(separator, current_index,
                                         end_index + 1)
            if separator_index != -1:
                # Нашли подходящий разделитель, добавляем часть до разделителя
                # (включительно)
                result.append(text[current_index:separator_index + len(
                    separator)].strip())
                current_index = separator_index + len(separator)
                found_separator = True
                break

        if not found_separator:
            # Если подходящий разделитель не найден, делим в последнем пробеле
            fallback_space = text.rfind(' ', current_index, end_index)
            if fallback_space != -1:
                result.append(text[current_index:fallback_space].strip())
                current_index = fallback_space + 1
            else:
                # Разделяем по max_length.
                result.append(text[current_index:end_index].strip())
                current_index = end_index

    return result


@retry(retry=retry_if_exception_type(asyncio.TimeoutError),
       stop=stop_after_attempt(config.MAX_RETRIES_DB_REQUESTS),
       wait=wait_fixed(config.RETRY_DELAY_DB_REQUESTS),
       reraise=True,
       before_sleep=log_stack_for_retry)
async def add_to_db_with_session_begin_and_retry(
        session: 'QueryAsyncSession',
        objects: Union[object, Iterable[object]]
) -> None:
    async with session.begin():
        if isinstance(objects, IterableABC):
            session.add_all(objects)
        else:
            session.add(objects)


class StrEnum(str, Enum):
    def __str__(self):
        return self.value

    @classmethod
    def has_value(cls, value):
        try:
            cls(value)
        except ValueError:
            return False
        return True
