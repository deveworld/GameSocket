import sys
import socket
from network import network
from typing import Callable, Any, Dict

# PoC Code -------
PORT = 12345

def binder(sock: socket.socket, addr: tuple):
    sys.stdout.write('\rconnected: %s\nMe: ' % str(addr))

def rece_handler(msg):
    sys.stdout.write('\rThe other: %s\nMe: ' % msg)

class gamesocket:
    def __init__(self, port: int):
        self.network = network()
        self.port = port

    def server(self):
        self.network.set_client_binder(binder)
        self.network.set_receive_handler(rece_handler)
        self.network.server(self.port)
    
    def client(self, host: str):
        self.network.set_receive_handler(rece_handler)
        self.network.client(host, self.port)

if __name__ == "__main__":
    if input("s or c?: ") == "s":
        gs = gamesocket(PORT)
        gs.server()
        while True:
            gs.network.sendAll(input("Me: "))
    else:
        gs = gamesocket(PORT)
        gs.client("localhost")
        while True:
            gs.network.send(input("Me: "))