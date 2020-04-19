from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from threading import Thread
import json

AUTH_HOST = 'localhost'
AUTH_PORT = 1234

ACTIONS = {
    "l": "login",
    "r": "register",
    "x": "cancel"
}

BUFSIZ = 512

class Client:

    def __init__(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.token = None
        self._auth = False

    def ready(self):
        """Ready client by authenticating with authentication services and loading internal cache"""
        with open("cache.json", "r") as f:
            cache = json.load(f)

        self.token = cache["token"] if cache["token"] is not None else "aaaaa"

        headers, content, message = self.request((AUTH_HOST, AUTH_PORT), headers="token", data=self.token)

        print(message, content)

        if headers == "success":
            return

        while True:
            action = input("What do you want to do?\n"
                           "l : login\n"
                           "r : register\n"
                           "x : exit\n"
                           "-----------------------\n")
            if action == "x":
                raise OSError("You exited the program!")
            username = input("Please input your username:\n")
            password = input("Please input your password:\n")

            headers, content, message = self.request((AUTH_HOST, AUTH_PORT),
                                                     headers=ACTIONS[action],
                                                     data=username + ":" + password)

            print(headers, content, message)

            if headers == "success":
                self.token = content
                with open("cache.json", "w") as f:
                    json.dump({"token": content}, f)
                break

    def request(self, addr, headers="NULL", data="NULL", message="NULL"):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect(addr)
        payload = headers + "|" + data + "|" + message
        print(payload)
        self.socket.send(bytes(payload, "utf8"))
        headers, content, message = self.socket.recv(BUFSIZ).decode("utf8").split("|")
        self.socket.close()
        return headers, content, message



if __name__ == "__main__":
    client = Client()
    client.ready()