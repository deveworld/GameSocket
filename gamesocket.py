import sys
import socket
from network import network

# PoC Code -------
PORT = 12345

def rece_handler(msg):
    sys.stdout.write('\rThe other: %s\nMe: ' % msg)

class gamesocket:
    def __init__(self, port: int, host: str = "localhost", server: bool = False):
        self.network = network()
        if server:
            self.network.server(port, self.binder)
        else:
            self.network.client(host, port)
    
    def binder(self, socket: socket.socket, addr: str):
        sys.stdout.write('\rconnect: %s\nMe: ' % str(addr))
        self.network.start_receive(rece_handler, socket)

if __name__ == "__main__":
    if input("s or c?: ") == "s":
        gs = gamesocket(PORT, "localhost", True)
        while True:
            gs.network.sendAll(input("Me: "))
    else:
        gs = gamesocket(PORT, "localhost")
        gs.network.start_receive(rece_handler)
        while True:
            gs.network.send(input("Me: "))