

from config import API_KEY, BLACKLIST
#from VastClient import VastClient
#from DbManager import DbManager


__db_manager = None
__vast_ai_cmd = None
_vast_client = None


def db_manager():
    global __db_manager
    return __db_manager


def set_db_manager(db_man):
    global __db_manager
    __db_manager = db_man


def vast_ai_command():
    global __vast_ai_cmd
    return __vast_ai_cmd


def set_vast_ai_command(vast):
    global __vast_ai_cmd
    __vast_ai_cmd = vast


def vast_client():
    global _vast_client
    print("3", _vast_client)
    return _vast_client


def set_vast_client(vast_client):
    print("2", vast_client)
    global _vast_client
    _vast_client = vast_client
