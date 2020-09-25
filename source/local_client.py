from message import Message, Header, Command
from client import Client
from time import sleep
import threading

_commands = set(item.value for item in Command)


def connection_with_server(_client):
    while True:
        try:
            # Try to send message from queue
            if len(_client.queue_send) > 0:
                _client.log('Sending command to server...')
                msg = _client.queue_send.pop(0)
                _client.send_message(msg)

            # Try to process message from queue
            if len(_client.queue_receive) > 0:
                msg = _client.queue_receive.pop(0)

                if msg.header == Header.IDLE:
                    _client.log('Remote Client not connected!')

                if msg.header == Header.RESPONSE:
                    _handle_response(msg, _client.log)

                if msg.header == Header.AUTO_UPLOAD:
                    with open(msg.payload[0], 'wb') as file:
                        file.write(msg.payload[1])
                    _client.log(f"File saved as: {msg.payload[0]}")

        except ConnectionError:
            _client.connected_to_server = False
            _client.log('Connection with server failed!')

        sleep(0.1)


def _handle_response(msg, log):
    log(f'Response from command: {msg.command.name}')

    if isinstance(msg.payload, Exception):
        log('Exception occured!')
        log(msg.payload)
        return

    if msg.command in [Command.UPLOAD_FILE, Command.UPLOAD_FOLDER]:
        file_name = msg.payload[0] + ('.zip' if msg.command == Command.UPLOAD_FOLDER else '')
        with open(file_name, 'wb') as file:
            file.write(msg.payload[1])
        log(f"File saved as: {file_name}")

    else:
        if isinstance(msg.payload, str):
            print(msg.payload)


def command_thread(_client):
    _current_remote_path = ''

    while True:
        if not _client.connected_to_server:
            continue

        # Get input command from console
        str_input = input(f"{_current_remote_path}>")
        args = str_input.split(' ')
        str_command = args.pop(0)

        if str_command == 'help':
            print('AVAILABLE COMMANDS:\n' +
                  'exit\n' +
                  'cd\n' +
                  'cd..\n' +
                  'auto_upload\n' +
                  str(_commands))
            continue

        if str_command == 'cd':
            if(len(_current_remote_path)>0):
                _current_remote_path += f'\\{args.pop(0)}'
            else:
                _current_remote_path = args.pop(0)
            continue

        if str_command == 'cd..':
            while(len(_current_remote_path) > 0 and _current_remote_path[-1] != '\\'):
                _current_remote_path = _current_remote_path[:-1]
            _current_remote_path = _current_remote_path[:-1]
            continue

        if str_command == 'auto_upload':
            _client.queue_send.append(Message(Header.AUTO_UPLOAD))
            pass

        if str_command == 'exit':
            _client.queue_send.append(Message(Header.EXIT))
            continue

        if str_command not in _commands:
            if str_command != '':
                _client.log(f'Command "{str_command}" not found.')
            continue

        command = Command(str_command)
        if(len(_current_remote_path) > 0):
            _remote_path = _current_remote_path + '\\' + ' '.join(args)
        else:
            _remote_path = ' '.join(args)

        msg = Message(Header.COMMAND, command)

        if command == Command.DOWNLOAD_FILE:
            file_path = input("Enter file path: ")
            try:
                with open(file_path, 'rb') as file:
                    data = file.read()
                    msg.payload = (_remote_path, data)
            except Exception as e:
                print(e)
        else:
            msg.payload = _remote_path

        _client.queue_send.append(msg)


if __name__ == "__main__":
    # _client = Client('Local Client', '127.0.0.1', 55554)
    _client = Client('Local Client', 'server_ip', 55554)

    _command_thread = threading.Thread(target=command_thread, args=[_client])
    _command_thread.start()

    connection_with_server(_client)
