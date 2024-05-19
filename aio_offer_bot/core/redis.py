from typing import NamedTuple

import paramiko
import redis
from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis

from config import REDIS_CACHE_CONFIG, REDIS_LISTENER_DB

from loggers import get_logger

logger = get_logger()


class RedisParams(NamedTuple):
    host: str
    port: int
    db: int


def get_listener_redis_params() -> RedisParams:
    return RedisParams(
        host=REDIS_CACHE_CONFIG['REDIS_HOST'],
        port=REDIS_CACHE_CONFIG['REDIS_PORT'],
        db=REDIS_LISTENER_DB,
    )


class AsyncRestartedRedis(AsyncRedis):
    """
    Асинхронный Redis клиент
    """
    async def reset_connections(self):
        pool = redis.asyncio.ConnectionPool(
            connection_class=self.connection_pool.connection_class,
            max_connections=self.connection_pool.max_connections,
            **self.connection_pool.connection_kwargs
        )
        await self.connection_pool.disconnect()
        self.connection = None
        self.connection_pool = pool


def create_redis_connection(host, port, db=0, is_async=True):
    kwargs = dict(
        db=db,
        host=host,
        port=port,
        health_check_interval=10,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        socket_keepalive=True
    )
    _Redis = AsyncRestartedRedis if is_async else SyncRedis
    return _Redis(**kwargs)


def restart_redis_remote(
        host: str,
        port: int,
        username: str,
        password: str,
        container_name: str
) -> None:
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username,
                    password=password)
        stdin, stdout, stderr = ssh.exec_command(
            f'docker restart {container_name}')
        output = stdout.readlines()
        ssh.close()
    except Exception as exc:
        logger.restart_redis_remote('error', f'Redis restart error: {exc}')
    else:
        if isinstance(output, list) and output and container_name in output[0]:
            logger.restart_redis_remote('info',
                                        f'Redis restarted successfully')
        else:
            logger.restart_redis_remote('error', f'Redis not restarted')
