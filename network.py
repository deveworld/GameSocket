from http import client
import socket
from struct import pack
import threading
import packet
from typing import Callable, Any, Dict, Tuple, List

class network:
    def __init__(self):
        self.socket: socket.socket = None
        self.isServer = False
        self.isClient = False
        self.clients: Dict[str, socket.socket] = {}
        self.anonyclients: List[socket.socket] = []
        self.receive_hadler: Callable[[str], Any] = None
        self.client_binder: Callable[[socket.socket, tuple], Any] = None

    def set_receive_handler(self, receive_hadler: Callable[[str], Any]):
        """Set receive handler

        Args:
            receive_hadler (Callable[[str], Any]): Receive str handler
        """
        self.receive_hadler = receive_hadler
        if self.isServer or self.isClient:
            raise ValueError('To change handler while running might be not safe')

    def set_client_binder(self, client_binder: Callable[[socket.socket, tuple], Any]):
        """Set client binder(it will be call once at connect client)

        Args:
            client_binder (Callable[[socket.socket, tuple], Any]): Client binder
        """
        self.client_binder = client_binder
        if self.isServer or self.isClient:
            raise ValueError('To change handler while running might be not safe')

    def disconnected(self, sock: socket.socket):
        try:
            self.clients = {key:val for key, val in self.clients.items() if val == sock}
        except ValueError or KeyError:
            self.anonyclients.pop(self.anonyclients.index(sock))

    def start_receive(self, sock: socket.socket = None):
        """Start receive loop in other thread

        Args:
            sock (`socket.socket`): Scoket
            str_handler (`Callable[[str], Any]`): String data handler func
        """
        if self.isClient:
            sock = self.socket
        receiver = threading.Thread(target=self.receiveLoop, args=(sock, ))
        receiver.daemon = True
        receiver.start()

    def receive(self, sock: socket.socket) -> Tuple[bytes, packet.flags]:
        """Receive data through socket

        Args:
            sock (`socket.socket`): Socket
            bufsize (`int`): Receive bufsize

        Returns:
            data, flag (`Tuple[bytes, packet.flags]`): Received data and flag
        """
        try:
            flag: packet.flags = packet.flags(int.from_bytes(sock.recv(4), "little"))
            length = int.from_bytes(sock.recv(4), "little")
            data: bytes = sock.recv(length)
        except ConnectionResetError:
            self.disconnected(sock)
        else:
            return (data, flag)
        return ("Disconnected".encode('utf-8'), packet.flags.ERROR) # Not Real Packet!!

    def receiveLoop(self, sock: socket.socket):
        """
        Receiving Loop

        Args:
            sock (`socket.socket`): Socket
            string_handler (`Callable[[str], Any]`): String data handler func
        """
        while True:
            data, flag = self.receive(sock)
            if flag == packet.flags.STRING_PACKET:
                if self.receive_hadler != None:
                    self.receive_hadler(data.decode('utf-8'))
            elif flag == packet.flags.ERROR:
                if self.receive_hadler != None:
                    self.receive_hadler(data.decode('utf-8'))
                break

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

    def sendAllAnony(self, data: str, flag: packet.flags = packet.flags.STRING_PACKET):
        """
        Send data to all Anony client

        Raises:
            Exception: client CANNOT use this
        """
        if self.isClient:
            raise Exception("Use send instead if you're using client.")
        for client_sock in self.anonyclients:
            self.send(data, client_sock, flag)

    def sendTo(self, userID: str, data: str, flag: packet.flags = packet.flags.STRING_PACKET):
        """
        Send data to specific client

        Raises:
            Exception: client CANNOT use this
        """
        if self.isClient:
            raise Exception("Use send instead if you're using client.")
        self.send(data, self.clients[userID], flag)

    def send(self, data: str, sock: socket.socket = None, flag: packet.flags = packet.flags.STRING_PACKET):
        """
        Send data through socket

        Args:
            sock (`socket.socket`): Socket
            data (`bytes`): Data to send
        """
        if sock == None and self.isClient:
            sock = self.socket
        try:
            sock.sendall(int(flag.value).to_bytes(4, byteorder="little"))
            # Send Socket Type Flags
            sock.sendall(len(data.encode('utf-8')).to_bytes(4, byteorder="little"))
            # Send Socket Byte Size At First with int(4 bytes) little endian
            sock.sendall(data.encode('utf-8'))
            # Send Data
        except ConnectionResetError:
            self.disconnected(sock)

    def server(self, port: int):
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

        server = threading.Thread(target=self.server_thread)
        server.daemon = True
        server.start()

    def clientLoad(self, client_socket: socket.socket, addr: tuple):
        data, flag = self.receive(client_socket)
        if flag == packet.flags.ID_HANDSHAKE:
            if not data.decode('utf-8') in self.clients:
                self.clients[data.decode('utf-8')] = client_socket
            elif data.decode('utf-8') == "Anony":
                self.anonyclients.append(client_socket)
            else:
                self.send("Not unique id.", client_socket, packet.flags.ERROR)
                client_socket.close()
                raise Exception("Not unique id, so didn't connecting.")
            self.start_receive(client_socket)
            if self.client_binder != None:
                thread = threading.Thread(target=self.client_binder, args=(client_socket, addr, ))
                thread.start()
        else:
            self.send("No id handshake.", client_socket, packet.flags.ERROR)
            client_socket.close()
            raise Exception("No id handshake, so didn't connecting.")

    def server_thread(self):
        """
        Client wait thread

        Args:
            binder (`Callable[[socket.socket, tuple], Any]`): Client connect binder func(socket, address)
        """
        try:
            while True:
                client_socket, addr = self.socket.accept()
                thread = threading.Thread(target=self.clientLoad, args=(client_socket, addr, ))
                thread.start()
        finally:
            self.socket.close()

    def client(self, host: str, port: int, id: str = None):
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
        if id == None:
            id = "Anony" # It can be NOT unique!
        self.send(id, None, packet.flags.ID_HANDSHAKE)
        self.start_receive()

    def close(self):
        self.socket.close()