class TransformerUtil:

    @staticmethod
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
