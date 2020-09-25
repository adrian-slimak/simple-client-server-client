from message import Message, Header
from threading import Thread
from shutil import rmtree
from time import sleep
import logging
import struct
import socket
import zipfile
import os

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("Server")


class Client:
    def __init__(self, name='client', host='0.0.0.0', port=55555):
        self.name = name
        self.host = host
        self.port = port
        self.socket = None
        self.conn = None
        self.addr = None
        self.queue_receive = []
        self.connected = False

        self._thread_1 = Thread(target=self.try_connect_to_client)
        self._thread_2 = Thread(target=self.try_to_receive_message)

    def start(self):
        self._thread_1.start()
        self._thread_2.start()

    def stop(self):
        self._thread_1.join()
        self._thread_2.join()

    def reset(self):
        self.socket = None
        self.conn = None
        self.addr = None
        self.connected = False

    def try_connect_to_client(self):
        while True:
            if self.connected:
                sleep(3)
                continue

            _logger.info(f' Waiting for {self.name}...')

            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.bind((self.host, self.port))
                self.socket.listen()
                self.conn, self.addr = self.socket.accept()
                self.connected = True
                _logger.info(f' {self.name} successfully connected!')
            except Exception:
                _logger.info(' Attempt failed! Waiting before next try!')
                sleep(5)

    def try_to_receive_message(self):
        while True:
            if self.connected:
                try:
                    msg = self.receive_message()
                    if msg is not None:
                        self.queue_receive.append(msg)
                except Exception:
                    self.connected = False
                    _logger.info(f'Connection with {self.name} failed!')

            sleep(0.5)

    def send_message(self, msg):
        msg_bytes = msg.ToBytes()
        # Prefix each message with a 4-byte length (network byte order)
        msg_bytes = struct.pack('>I', len(msg_bytes)) + msg_bytes
        self.conn.sendall(msg_bytes)

    def receive_message(self):
        # Read message length and unpack it into an integer
        msg_len = self.receive_bytes(4)
        if not msg_len:
            return None
        msg_len = struct.unpack('>I', msg_len)[0]
        # Read the message data
        return Message.FromBytes(self.receive_bytes(msg_len))

    def receive_bytes(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = self.conn.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data


def zipdir(str_path):
    zipf = zipfile.ZipFile(f'zipped.zip', 'w', zipfile.ZIP_DEFLATED)
    base_name = os.path.basename(str_path)
    for root, dirs, files in os.walk(str_path):
        for file in files:
            zipf.write(os.path.join(root, file), f'{base_name}\\{file}')
    zipf.close()


class Server:
    def __init__(self, host='0.0.0.0', local_client_port=55554, remote_client_port=55555):
        self.host = host
        self.local_client_port = local_client_port
        self.remote_client_port = remote_client_port

        self.local_client = Client('Local Client', host=host, port=local_client_port)
        self.local_client.start()
        self.remote_client = Client('Remote Client', host=host, port=remote_client_port)
        self.remote_client.start()

    def run(self):
        while True:
            if self.local_client.connected and not self.remote_client.connected:
                self.single_connection(self.local_client)

            if self.remote_client.connected and not self.local_client.connected:
                self.single_connection(self.remote_client)

            if self.remote_client.connected and self.local_client.connected:

                # Send message from Local Client to Remote Client
                if len(self.local_client.queue_receive) > 0:
                    msg = self.local_client.queue_receive.pop(0)

                    # Send saved screens to Local Client
                    if msg.header == Header.AUTO_UPLOAD:
                        self.send_ss_to_local_client()
                        continue

                    self._send(self.remote_client, msg)

                # Send message from Remote Client to Local Client
                if len(self.remote_client.queue_receive) > 0:
                    msg = self.remote_client.queue_receive.pop(0)

                    # Save screens received from Remote Client
                    if msg.header == Header.AUTO_UPLOAD:
                        with open('./ss/' + msg.payload[0] + '.jpg', 'wb') as file:
                            file.write(msg.payload[1])
                        continue

                    self._send(self.local_client, msg)

            sleep(0.1)

    def single_connection(self, client):
        try:
            # _logger.info(f' {client.name} connection...')
            if len(client.queue_receive) > 0:
                msg = client.queue_receive.pop(0)

                if msg.header == Header.AUTO_UPLOAD:
                    if client.name == 'Local Client':
                        self.send_ss_to_local_client()
                    elif client.name == 'Remote Client':
                        with open('./ss/'+msg.payload[0]+'.jpg', 'wb') as file:
                            file.write(msg.payload[1])
                    return

                client.send_message(Message(Header.IDLE))

        except Exception:
            _logger.info(f' {client.name} disconnected...')
            client.reset()

    def _send(self, client, msg):
        try:
            client.send_message(msg)
        except ConnectionError:
            _logger.info(f' {client.name} disconnected...')
            self._connection = False
            client.reset()

    def send_ss_to_local_client(self):
        msg = Message(Header.AUTO_UPLOAD, None)

        try:
            zipdir('./ss')
            with open('zipped.zip', 'rb') as file:
                result = (os.path.basename('zipped.zip'), file.read())
            msg.payload = result
            rmtree('./ss')
            os.makedirs('./ss')
        except Exception:
            msg = Message(Header.WAITING)

        self._send(self.local_client, msg)

if __name__ == "__main__":
    _server = Server()
    _server.run()
