from enum import Enum
import pickle


class Header(Enum):
    WAITING = 1
    COMMAND = 2
    RESPONSE = 3
    IDLE = 4
    EXIT = 5
    AUTO_UPLOAD = 6


class Command(Enum):
    LS = 'ls'
    LS_TREE = 'ls_tree'
    CREATE_FOLDER = 'create_folder'
    UPLOAD_FILE = 'download_file'
    UPLOAD_FOLDER = 'download_folder'
    DOWNLOAD_FILE = 'upload_file'
    REMOVE_FILE = 'remove_file'
    REMOVE_FOLDER = 'remove_folder'
    START_EXE = 'start_exe'
    CHECK_PROCESS_RUNNING = 'check_process'
    COMMAND_NOT_KNOWN = 'command_not_known'


class Message:
    header: Header
    command: Command

    def __init__(self, header, command=None, payload=None):
        self.header = header
        self.command = command
        self.payload = payload

    def ToBytes(self):
        return pickle.dumps(self)

    @staticmethod
    def FromBytes(bytes):
        return pickle.loads(bytes)
