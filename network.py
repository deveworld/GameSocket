import socket
import threading
import packet
from typing import Callable, Any, Dict

class network:
    def __init__(self):
        self.socket: socket.socket = None
        self.isServer = False
        self.isClient = False
        self.clients: Dict[tuple, socket.socket] = {}

    def start_receive(self, str_handler: Callable[[str], Any], sock: socket.socket = None):
        """Start receive loop in other thread

        Args:
            sock (`socket.socket`): Scoket
            str_handler (`Callable[[str], Any]`): String data handler func
        """
        if self.isClient:
            sock = self.socket
        receiver = threading.Thread(target=self.receiveLoop, args=(sock, str_handler, ))
        receiver.daemon = True
        receiver.start()

    def receive(self, sock: socket.socket, bufsize: int) -> bytes:
        """Receive data through socket

        Args:
            sock (`socket.socket`): Socket
            bufsize (`int`): Receive bufsize

        Returns:
            data (`bytes`): Received data
        """
        try:
            data = sock.recv(bufsize)
        except ConnectionResetError:
            raise Exception('Disconnected')
        if not data:
            raise ValueError('Receive error')
        else:
            return data

    def receiveLoop(self, sock: socket.socket, str_handler: Callable[[str], Any]):
        """
        Receiving Loop

        Args:
            sock (`socket.socket`): Socket
            string_handler (`Callable[[str], Any]`): String data handler func
        """
        while True:
            flag: packet.flags = packet.flags(int.from_bytes(self.receive(sock, 4), "little"))
            length = int.from_bytes(self.receive(sock, 4), "little")
            data: bytes = self.receive(sock, length)
            if flag == packet.flags.STRING_PACKET:
                str_handler(data.decode('utf-8'))

    def sendAll(self, data: str, flag: packet.flags = packet.flags.STRING_PACKET):
        """
        Send data to all client

        Raises:
            Exception: client CANNOT use this
        """
        if self.isClient:
            raise Exception("Use send instead if you're using client.")
        for client_sock in self.clients.values():
            self.send(data, client_sock, flag)

    def send(self, data: str, sock: socket.socket = None, flag: packet.flags = packet.flags.STRING_PACKET):
        """
        Send data through socket

        Args:
            sock (`socket.socket`): Socket
            data (`bytes`): Data to send
        """
        if sock == None and self.isClient:
            sock = self.socket
        sock.sendall(int(flag.value).to_bytes(4, byteorder="little"))
        # Send Socket Type Flags
        sock.sendall(len(data.encode('utf-8')).to_bytes(4, byteorder="little"))
        # Send Socket Byte Size At First with int(4 bytes) little endian
        sock.sendall(data.encode('utf-8'))
        # Send Data

    def server(self, port: int, binder: Callable[[socket.socket, tuple], Any]):
        """
        Setup Server

        Args:
            port (`int`): Server port
            binder (`Callable[[socket.socket, tuple], Any]`): Client connect binder func(socket, address)
        """
        if self.isServer or self.isClient:
            return
        self.isServer = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', int(port)))
        self.socket.listen()

        server = threading.Thread(target=self.server_thread, args=(binder, ))
        server.daemon = True
        server.start()

    def server_thread(self, binder: Callable[[socket.socket, tuple], Any]):
        """
        Client wait thread

        Args:
            binder (`Callable[[socket.socket, tuple], Any]`): Client connect binder func(socket, address)
        """
        try:
            while True:
                client_socket, addr = self.socket.accept()
                self.clients[addr] = client_socket
                thread = threading.Thread(target=binder, args=(client_socket, addr, ))
                thread.start()
        finally:
            self.socket.close()

    def client(self, host: str, port: int):
        """
        Setup Client

        Args:
            host (`str`): Server IP address
            port (`int`): Server port
        """
        if self.isServer or self.isClient:
            return
        self.isClient = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, int(port)))

    def close(self):
        self.socket.close()