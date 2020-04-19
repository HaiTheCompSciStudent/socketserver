from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import secrets

from database import Database
from task import task

from config import config

BUFSIZ = 512


class Server:

    def __init__(self, host, port):
        self.addr = (host, port)
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind(self.addr)
        self._task_queue = []

    def handle_queue(self):
        """Thread that handles queue"""
        while True:
            if self._task_queue:
                client, addr = self._task_queue[0]
                print("HANDLING TASK FROM", addr)
                header, content, message = client.recv(512).decode("utf8").split("|")
                print("TASK", header, content, message)
                task.resolve(header, content, client)
                client.close()
                self._task_queue.pop(0)


    def wait_for_connections(self):
        """Thread that wait for connections"""
        print("WAITING FOR CONNECTIONS...")
        while True:
            client, addr = self.socket.accept()
            print("CONNECTION ESTABLISHED AT", addr)
            self._task_queue.append((client, addr))
            print(self._task_queue)

    @classmethod
    def start(cls, host, port):
        """Entry method for starting authentication server"""
        server = cls(host, port)
        server.socket.listen()
        WAIT_THREAD = Thread(target=server.wait_for_connections)
        QUEUE_THREAD = Thread(target=server.handle_queue)
        WAIT_THREAD.start()
        QUEUE_THREAD.start()

    @task.task("token")
    def handle_token(self, content, client):
        with Database.connect(config["POSTGRE_URI"]) as conn:
            conn.cur.execute("""
                SELECT users.name FROM tokens
                INNER JOIN users ON tokens.user_id = users.id
                WHERE tokens.token = %s
            """, (content,))
            user = conn.cur.fetchone()
            client.send(bytes("reg/log|NULL|Please login or register."
                              if user is None else
                              f"success|{user}|Welcome back {user}!", "utf8"))
            print("this runs?")

    @task.task("login")
    def handle_user_login(self, content, client):
        username, password = content.split(":")
        with Database.connect(config["POSTGRE_URI"]) as conn:
            conn.cur.execute("""
                SELECT tokens.token, users.name FROM tokens
                INNER JOIN users ON tokens.user_id = users.id
                WHERE (users.name = %s AND users.password = %s)
            """, (username, password,))
            token_user = conn.cur.fetchone()
            client.send(bytes("reject|NULL|Your login credentials are incorrect, please try again or register."
                              if token_user is None else
                              f"success|{token_user[0]}|Welcome back {token_user[1]}!", "utf8"))

    @task.task("register")
    def handle_user_register(self, content, client):
        username, password = content.split(":")
        with Database.connect(config["POSTGRE_URI"]) as conn:
            conn.cur.execute("""
                SELECT users.name FROM users
                WHERE users.name = %s
            """, (username,))

            user = conn.cur.fetchone()

            if user:
                return client.send(bytes("reject|NULL|Your username has already taken, please try again.", "utf8"))

            token = secrets.token_urlsafe()

            conn.cur.execute("""
                INSERT INTO users(name, password)
                VALUES(%s, %s) RETURNING id
            """, (username, password,))

            user_id = conn.cur.fetchone()
            conn.cur.execute("""
                INSERT INTO tokens(token, user_id)
                VALUES(%s, %s)
            """, (token, user_id))

            client.send(bytes(f"success|{token}|Welcome {username}, your account has been created!", "utf8"))


if __name__ == "__main__":
    Server.start("localhost", 1234)
