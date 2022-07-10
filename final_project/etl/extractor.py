from psycopg2.extras import RealDictCursor


class PostgresExtractor:
    data = []

    def __init__(self, pg_conn):
        self.cursor = pg_conn.cursor(cursor_factory=RealDictCursor)

    def extract(self):
        sql = """SELECT
                            fw.id, 
                            fw.title, 
                            fw.description, 
                            fw.rating, 
                            fw.type,
                            ARRAY_REMOVE(ARRAY_AGG(distinct CASE
                                WHEN pfw.role = 'actor' 
                                THEN p.full_name
                            END), NULL) AS actors,
                            JSONB_AGG(distinct CASE
                                WHEN pfw.role = 'actor' 
                                THEN jsonb_build_object(
                                    'id', p.id,
                                    'name', p.full_name
                                )
                            END) AS actors_json,
                            ARRAY_REMOVE(ARRAY_AGG(distinct CASE
                                WHEN pfw.role = 'writer' 
                                THEN p.full_name
                            END), NULL) AS writers,
                            JSONB_AGG(distinct CASE
                                WHEN pfw.role = 'writer'
                                THEN jsonb_build_object(
                                    'id', p.id,
                                    'name', p.full_name
                                )
                            END) AS writers_json,
                            ARRAY_REMOVE(ARRAY_AGG(distinct CASE
                                WHEN pfw.role = 'director' 
                                THEN p.full_name
                            END), NULL) AS directors,
                        ARRAY_REMOVE(ARRAY_AGG(distinct g.name), NULL) AS genres
                        FROM film_work as fw
                        LEFT JOIN person_film_work pfw ON pfw.film_work_id = fw.id
                        LEFT JOIN person p ON p.id = pfw.person_id
                        LEFT JOIN genre_film_work gfw ON gfw.film_work_id = fw.id
                        LEFT JOIN genre g ON g.id = gfw.genre_id
                        GROUP BY
                            1,2,3,4,5    
                        HAVING fw.search_indexed IS NULL OR fw.search_indexed=0
                        LIMIT 100
                    """
        self.cursor.execute(sql)
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
