# RePyX
# Remote Python eXecutor

import inspect
import os
import socket
import time
from threading import Thread
from traceback import format_exc, print_exc

autoStartStack = None
READ_LEN = 8192
VERBOSE = False

def runCmd(cmd: str) -> str:
    globs = autoStartStack.f_globals if autoStartStack else globals()

    try:
        if cmd.startswith("exec "):
            cmd = cmd[5:]
            return repr(exec(cmd, globals=globs))  # noqa: S102  # pyright: ignore[reportUnknownArgumentType, reportCallIssue]
        return repr(eval(cmd, globals=globs))  # pyright: ignore[reportUnknownArgumentType, reportCallIssue]

    except Exception:
        return format_exc()


def closeSocket(s: socket.socket, extra: str = ""):
    if VERBOSE: print(f"repyx: Closing connection. {extra}")
    try: s.close()
    except Exception: pass


class Server:

    def __init__(self, ip: str = "127.0.0.1", port: int = 1337):

        self.ip: str   = ip
        self.port: int = port
        self.socket: socket.socket


    def accepter(self):
        # loop to continuously accept new incoming connections

        shutup = False
        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.bind((self.ip, self.port))
                self.socket.listen(5)
                break

            except OSError:
                if not shutup:
                    print("repyx: Address already in use. Retrying indefinitely...")
                    shutup = True
                time.sleep(4)

        print("repyx: receiver started, accepting clients.")

        while True:
            try:
                client, address = self.socket.accept()  # pyright: ignore[reportAny]
                client.send(b"Connected to RePyX.")

                print(f"repyx: Connection from {address} has been accepted.")
                Thread(target=self.recver, args=[client], daemon=True).start()
                # TODO: Make this thread killable in the case where the client accidentally runs an endless loop
                # ^ https://stackoverflow.com/a/325528

            except OSError:
                # from previous testing, "self.socket.accept()" throws an OSError
                # when the socket is shutdown, so we want to exit quietely.
                pass


    def start(self):
        Thread(target=self.accepter, daemon=True).start()


    def recver(self, client: socket.socket):
        while True:
            try: received = client.recv(READ_LEN)
            except Exception: return closeSocket(client, format_exc())

            if not (msg := received.decode(errors="replace")):
                continue

            response = runCmd(msg)

            try: client.send(response.encode(errors="replace"))
            except Exception: return closeSocket(client, format_exc())



class Client:

    def __init__(self, ip: str = "127.0.0.1", port: int = 1337):

        self.ip: str   = ip
        self.port: int = port
        self.server: socket.socket


    def connect(self):
        retryCount = 0

        while True:
            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.connect((self.ip, self.port))
                print("connected")
                break

            except ConnectionRefusedError:
                print("Address already in use. Waiting 4 seconds.", retryCount)
                retryCount+=1
                time.sleep(4)

        Thread(target=self.recver, args=(self.server,), daemon=True).start()


    def recver(self, server: socket.socket):
        while True:
            try:
                received = server.recv(READ_LEN)

                if received:
                    print(received.decode(errors="replace"))

            except Exception:
                closeSocket(server)
                print("Error receiving from server:")
                print_exc()
                return


    def start(self):
        print("Connected to RePyX server, starting client\nType \"exit\" to exit out of console.")

        while True:
            try: cmd = input("RPX: ")
            except KeyboardInterrupt:
                print()
                continue

            if cmd == "exit":
                return print("Exiting JC.")

            self.server.send( cmd.encode(errors="replace") )


# here we perform logic to detect if AutoStart has been explicity imported I.E
# "from repyx import AutoStart" as opposed to "import repyx" or "from repyx import Server"

class AutoStart: pass
# I chose to use a class here arbitrarily, any type of variable should work really

stacks = inspect.stack()

def _autoStart():
    global autoStartStack
    time.sleep(1)

    for frame in stacks:

        if os.path.basename(__file__) in frame.filename:
            # exclude occurrences of AutoStart in this file (stack)
            continue

        if ("AutoStart" in frame.frame.f_globals and
            frame.frame.f_globals["AutoStart"] is AutoStart):
                print("repyx: Auto starting...")
                autoStartStack = frame.frame
                Server().start()
                return

if __name__ != "__main__":
    Thread(target=_autoStart).start()

else:
    # we try to connect to open RePyX servers
    print("Attempting to connect to local RePyX server...")
    c = Client()
    c.connect()
    c.start()
