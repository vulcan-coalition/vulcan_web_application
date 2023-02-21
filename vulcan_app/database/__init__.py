from .tunnel import Tunnel_Session
from .postgre import Postgres, Base, TimeStamp
from .mongo import Mongo

database = None
ssh_tunnel = None


def initialize(config, override_address=None, override_port=None):
    global database, ssh_tunnel

    override_address = None
    override_port = None
    if config["ssh_tunnel"] is not None:
        credentials = config["ssh_tunnel"]
        if credentials is not None:
            ssh_tunnel = Tunnel_Session(credentials)
            override_address, override_port = ssh_tunnel.get_bind_addresses()

    if config["postgre_connection"] is not None:
        connection_str = config["postgre_connection"]
        if not isinstance(connection_str, str):
            username = connection_str["username"]
            password = connection_str["password"]
            hostname = connection_str["hostname"] if override_address is None else override_address
            port = connection_str["port"] if override_port is None else str(override_port)
            db_name = connection_str["db_name"]
            connection_str = username + ":" + password + "@" + hostname + ":" + port + "/" + db_name
        database = Postgres(connection_str)
    elif config["mongo_connection"] is not None:
        url = config["mongo_connection"]
        table = config["mongo_database"]
        database = Mongo(url, table)


def get_session():
    return database.get_session()


def terminate_connections():
    if ssh_tunnel is not None:
        ssh_tunnel.disconnect()
