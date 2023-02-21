from .configuration import initialize as init_config, get_config
from .security import initialize as init_security, User, get_active_current_user, check_is_admin
from .services import *
from .database import initialize as init_db, terminate_connections, Base, TimeStamp


def initialize(project_root, fast_api_app):
    init_config(project_root)
    init_security(fast_api_app)
    init_db(configuration.get_config_object())


def terminate():
    terminate_connections()
