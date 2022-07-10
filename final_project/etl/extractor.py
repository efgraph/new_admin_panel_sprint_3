from psycopg2.extras import RealDictCursor
from sql_requests import *

class PostgresExtractor:
    data = []

    def __init__(self, pg_conn):
        self.cursor = pg_conn.cursor(cursor_factory=RealDictCursor)

    def extract(self):
        self.cursor.execute(sql_join)
        self.data = self.cursor.fetchall()
        return self.data

    def set_indexed(self):
        if not self.data:
            return

        data = ','.join(self.cursor.mogrify('%s', (item['id'],)).decode()
                        for item in self.data)

        sql = f"""UPDATE film_work
                  SET search_indexed = 1
                  WHERE id in ({data});"""

        self.cursor.execute(sql, (data,))
