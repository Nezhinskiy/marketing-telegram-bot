from config import POSTGRES_CONFIG


def get_postgres_dsn(is_async: bool = True, **options) -> str:
    """
    Return DSN for postgresql from options,
    if options is not passed then default option takes from config.
    """
    driver = 'asyncpg' if is_async else 'psycopg2'
    return 'postgresql+{driver}://{user}:{password}@{host}:{port}/{database}'.format(
        driver=driver,
        user=options.get('user', POSTGRES_CONFIG['POSTGRES_USER']),
        password=options.get('password', POSTGRES_CONFIG['POSTGRES_PASSWORD']),
        host=options.get('host', POSTGRES_CONFIG['POSTGRES_HOST']),
        port=options.get('port', POSTGRES_CONFIG['POSTGRES_PORT']),
        database=options.get('database', POSTGRES_CONFIG['POSTGRES_DB'])
    )
