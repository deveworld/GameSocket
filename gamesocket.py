import sys
import socket
from network import network
from typing import Callable, Any, Dict

# PoC Code -------
PORT = 12345

def binder(sock: socket.socket, addr: tuple):
    sys.stdout.write('\rconnected: %s\nMe: ' % str(addr))
    gs.network.start_receive(rece_handler, sock)

def rece_handler(msg):
    sys.stdout.write('\rThe other: %s\nMe: ' % msg)

class gamesocket:
    def __init__(self, port: int):
        self.network = network()
        self.port = port

    def server(self, binder: Callable[[socket.socket, tuple], Any]):
        self.network.server(self.port, binder)
    
    def client(self, host: str, str_handler: Callable[[str], Any]):
        self.network.client(host, self.port)
        self.network.start_receive(str_handler)

if __name__ == "__main__":
    if input("s or c?: ") == "s":
        gs = gamesocket(PORT)
        gs.server(binder)
        while True:
            gs.network.sendAll(input("Me: "))
    else:
        gs = gamesocket(PORT)
        gs.client("localhost", rece_handler)
        while True:
            gs.network.send(input("Me: "))