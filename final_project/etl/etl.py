from psycopg2.extras import RealDictCursor
import json
import requests
from urllib.parse import urljoin
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import DictCursor


def extract(pg_conn):
    cursor = pg_conn.cursor(cursor_factory=RealDictCursor)
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
            """
    cursor.execute(sql)
    data = cursor.fetchall()
    transformed_data = []
    for row in data:
        transformed_data.append(transform(row))
    load_to_es(transformed_data, 'movies')


def transform(row):
    return {
        'id': row['id'],
        'title': row['title'],
        'description': row['description'],
        'imdb_rating': row['rating'],
        'genre': row['genres'],
        'writers_names': row['writers'],
        'actors_names': row['actors'],
        'actors': [a for a in row['actors_json'] if a],
        'writers': [w for w in row['writers_json'] if w],
        'director': row['directors'],
    }


def load_to_es(records, index_name):
    prepared_query = []
    for row in records:
        prepared_query.extend([
            json.dumps({'index': {'_index': index_name, '_id': row['id']}}),
            json.dumps(row)
        ])
    str_query = '\n'.join(prepared_query) + '\n'

    response = requests.post(
        urljoin("http://localhost:9200/", '_bulk'),
        data=str_query,
        headers={'Content-Type': 'application/x-ndjson'}
    )

    json_response = json.loads(response.content.decode())
    print(json.dumps(json_response, indent=4))



@contextmanager
def conn_context(pg_dsl):
    pg_conn = psycopg2.connect(**pg_dsl, cursor_factory=DictCursor)
    pg_conn.autocommit = True
    yield pg_conn
    pg_conn.close()


if __name__ == "__main__":
    dsl = {'dbname': 'movies_database', 'user': 'app', 'password': '123qwe', 'host': 'localhost', 'port': 5432}
    with conn_context(dsl) as pg_conn:
        extract(pg_conn)
        print("etl is ready to ride!")
