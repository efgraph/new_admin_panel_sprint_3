from contextlib import contextmanager

from functools import wraps

import psycopg2
from psycopg2.extras import DictCursor
from extractor import PostgresExtractor
from storage import JsonFileStorage, State
from loader import ESLoader
from settings import Settings
import time
import logging
from time import sleep
from postman_tests_runner import run_postman_tests

logger = logging.getLogger()


def etl(pg_conn, state):
    extractor = PostgresExtractor(pg_conn)
    data = extractor.extract()
    extractor.set_indexed()
    loader = ESLoader()
    if not state.get_state('es_schema'):
        loader.set_schema_index()
        state.set_state('es_schema', True)
    loader.load(data)


@contextmanager
def conn_context(pg_dsl):
    pg_conn = psycopg2.connect(**pg_dsl, cursor_factory=DictCursor)
    pg_conn.autocommit = True
    yield pg_conn
    pg_conn.close()


def retry(exception_to_check, delay=3, backoff=2):
    def deco_retry(func):
        @wraps(func)
        def f_retry(*args, **kwargs):
            m_delay = delay
            while True:
                try:
                    return func(*args, **kwargs)
                except exception_to_check as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), m_delay)
                    logger.error(msg)
                    time.sleep(m_delay)
                    m_delay *= backoff

        return f_retry

    return deco_retry


@retry(Exception, delay=2, backoff=2)
def run():
    with psycopg2.connect(**Settings().postgres_conn.dict()) as pg_conn:
        storage = JsonFileStorage(Settings().etl_state.state_file)
        state = State(storage)
        count = 100
        while count > 0:
            etl(pg_conn, state)
            count -= 1
        time.sleep(3)
        run_postman_tests(state)
        while True:
            etl(pg_conn, state)
            sleep(3)


if __name__ == "__main__":
    run()
