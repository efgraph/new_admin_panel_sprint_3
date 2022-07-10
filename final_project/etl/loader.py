import http
import json

import requests
from urllib.parse import urljoin

from settings import Settings
from transformer import TransformerUtil


class ESLoader:

    def set_schema_index(self):
        f = open('search_schema.json')
        body = json.dumps(json.load(f))
        response = requests.put(
            urljoin(Settings().elastic_conn.es_uri, 'movies'),
            data=body,
            headers={'Content-Type': 'application/x-ndjson'},
            verify=False,
            timeout=10
        )
        if response.status_code != http.HTTPStatus.OK:
            raise Exception('es schema is not set')

    def load(self, data):
        if not data:
            return

        transformed_data = []
        for row in data:
            transformed_data.append(TransformerUtil.transform(row))

        prepared_query = []
        for row in transformed_data:
            prepared_query.extend([
                json.dumps({'index': {'_index': 'movies', '_id': row['id']}}),
                json.dumps(row)
            ])
        str_query = '\n'.join(prepared_query) + '\n'

        response = requests.post(
            urljoin(Settings().elastic_conn.es_uri, '_bulk'),
            data=str_query,
            headers={'Content-Type': 'application/x-ndjson'},
            verify=False,
            timeout=10
        )

        if response.status_code != http.HTTPStatus.OK:
            raise Exception('check if vpn is on')
