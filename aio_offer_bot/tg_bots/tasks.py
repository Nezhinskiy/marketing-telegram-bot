import traceback
from typing import Union

from celery.app.control import Inspect
from celery.signals import worker_ready
from tg_logger import BaseLogger

import config
from core.redis import restart_redis_remote
from core.utils import log_event_loop_info, restart_container, str_exception
from main import app
from tg_bots.listening_manager import MyListeningTGBotManager
from tg_bots.services import get_tgbots_and_admins

logger = BaseLogger()

RETRY_TIMOUT = 3


def stop_manager_work(
        manager: Union[MyListeningTGBotManager]
) -> None:
    manager.stop()
    if manager.loop.is_running():
        manager.loop.stop()
    if not manager.loop.is_running():
        manager.loop.close()
        logger.aio_stop('info', 'Loop closed')
    else:
        logger.aio_stop('error', 'Loop is running')
    log_event_loop_info(manager.loop, logger)


def start_manager_pattern(
        self: 'celery.Task',
        manager_class: Union[MyListeningTGBotManager],
        manager_number: int = None
) -> None:
    tgbot_list, admin_list = get_tgbots_and_admins(
        archived=False, is_activated=True
    )
    manager = manager_class(admin_list, tgbot_list)
    try:
        manager.start_chatting()
    except Exception as exc:
        trace = traceback.format_exc()
        detailed_error = str_exception(exc)
        logger.responsible_manager(
            'error',
            f'{"" if manager_number is None else f"Number: {manager_number}."}'
            f'Error: {detailed_error} Traceback: {trace}'
        )
        stop_manager_work(manager)
        if not config.TEST_RUN:
            restart_redis_remote(
                config.REDIS_CACHE_CONFIG['REDIS_HOST'],
                config.REDIS_HOST_PORT,
                config.REDIS_HOST_USER,
                config.REDIS_HOST_PASSWORD,
                config.REDIS_HOST_CONTAINER
            )
        self.retry(countdown=RETRY_TIMOUT)


@app.task(bind=True, max_retries=None, queue='tg_bots')
def start_listening_manager(self, **kwargs):
    start_manager_pattern(self, MyListeningTGBotManager)


@worker_ready.connect
def at_start(sender, **kwargs):
    queues_listened = [queue.name for queue in sender.task_consumer.queues]
    if 'tg_bots' not in queues_listened:
        return

    with sender.app.connection() as conn:
        i = Inspect(app=sender.app, destination=['tg_bots'])
        active_tasks = i.active() or {}
        active_task_names = [
            task['name'] for worker_tasks in
            active_tasks.values() for task in worker_tasks
        ]
        reserved_tasks = i.reserved() or {}
        reserved_task_names = [
            task['name'] for worker_tasks in
            reserved_tasks.values() for task in worker_tasks
        ]
        active_task_names.extend(reserved_task_names)

        listening_manager = 'tg_bots.tasks.start_listening_manager'
        if listening_manager not in active_task_names:
            sender.app.send_task(
                listening_manager,
                connection=conn,
                queue='tg_bots',
                task_id=listening_manager
            )
