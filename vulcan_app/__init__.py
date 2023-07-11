from .configuration import initialize as init_config, get_config
from .security import initialize as init_security, User
from .services import *
from .database import initialize as init_db, terminate_connections, Base, TimeStamp


def initialize(project_root, fast_api_app, security_prefix=""):
    init_config(project_root)
    init_db(configuration.get_config_object())
    return init_security(fast_api_app, security_prefix)


def terminate():
    terminate_connections()
