import asyncio

from celery import Celery

app = Celery(
    'aio_neural',
    broker='redis://redis_aio_offer_bot:6733',
    backend='redis://redis_aio_offer_bot:6733',
    include=['tg_bots.tasks']
)


async def main():
    # Просто заглушка чтоб контейнер работал
    print('start')
    while True:
        print(f'Main working...')
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
