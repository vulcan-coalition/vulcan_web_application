from .configuration import initialize as init_config, get_config
from .security import initialize as init_security, User
from .services import *
from .database import initialize as init_db, terminate_connections, Base, TimeStamp


def initialize(project_root, fast_api_app=None, security_prefix="", get_user=None):
    init_config(project_root)
    init_db(configuration.get_config_object())
    if fast_api_app is not None:
        return init_security(fast_api_app, security_prefix, get_user)
    return None


def terminate():
    terminate_connections()
