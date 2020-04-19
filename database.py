import psycopg2
from urllib.parse import urlparse


class Database:

    def __init__(self, conn=None):
        self.conn = conn
        self.cur = None if self.conn is None else self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.cur.close()
            self.conn.commit()
            self.conn.close()

    @classmethod
    def connect(cls, uri):
        params = urlparse(uri)
        conn = psycopg2.connect(
            database=params.path[1:],
            user=params.username,
            password=params.password,
            host=params.hostname
        )
        return cls(conn)

if __name__ == "__main__":
    from config import config
    with Database.connect(config["POSTGRE_URI"]) as conn:
        for table in ['tokens', 'users']:
            conn.cur.execute("DROP TABLE " + table)

        conn.cur.execute("""
                    CREATE TABLE IF NOT EXISTS users(
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        password VARCHAR(255) NOT NULL
                    )
                """)
        conn.cur.execute("""
            CREATE TABLE IF NOT EXISTS tokens(
                token VARCHAR(255),
                user_id INTEGER REFERENCES users(id)
            )
        """)

        conn.cur.execute("""
            SELECT * FROM users
        """)

        for user in conn.cur.fetchall():
            print(user)
