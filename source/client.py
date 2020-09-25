from message import Message
from time import sleep
import threading
import logging
import socket
import struct

logging.basicConfig(level=logging.INFO)


class Client:
    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port
        self.socket = None
        self.connected_to_server = False
        self.connected = False
        self.queue_send = []
        self.queue_receive = []
        self._logger = logging.getLogger(self.name)
        self._thread_1 = threading.Thread(target=self.try_connect_to_server)
        self._thread_1.start()
        self._thread_2 = threading.Thread(target=self.try_to_receive_message)
        self._thread_2.start()

    def try_connect_to_server(self):
        while True:
            if self.connected_to_server:
                sleep(3)
                continue

            self.log('Trying to connect to server...')

            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                self.connected_to_server = True
                self.log('Successfully connected to server!')
            except Exception:
                self.log('Attempt failed! Waiting before next try...')
                sleep(5)

    def try_to_receive_message(self):
        while True:
            if self.connected_to_server:
                try:
                    msg = self.receive_message()
                    if msg is not None:
                        self.queue_receive.append(msg)
                except Exception:
                    self.connected_to_server = False
                    self.log('Connection with server failed!')

            sleep(0.5)

    def send_message(self, msg):
        msg_bytes = msg.ToBytes()
        # Prefix each message with a 4-byte length (network byte order)
        msg_bytes = struct.pack('>I', len(msg_bytes)) + msg_bytes
        self.socket.sendall(msg_bytes)

    def receive_message(self):
        # Read message length and unpack it into an integer
        msg_len = self._receive_bytes(4)
        if not msg_len:
            return None
        msg_len = struct.unpack('>I', msg_len)[0]
        # Read the message data
        return Message.FromBytes(self._receive_bytes(msg_len))

    def _receive_bytes(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = self.socket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def log(self, text):
        self._logger.info(' ' + str(text))
