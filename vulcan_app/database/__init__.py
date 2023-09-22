from .tunnel import Tunnel_Session
from .postgre import Postgres, Base, TimeStamp
from .mongo import Mongo
import os

database = None
ssh_tunnel = None


def initialize(override_address=None, override_port=None):
    global database, ssh_tunnel

    override_address = None
    override_port = None
    if os.getenv("VULCAN_APP_TUNNEL_URL") is not None:
        credentials = os.getenv("VULCAN_APP_TUNNEL_URL")
        if credentials is not None:
            ssh_tunnel = Tunnel_Session(credentials)
            override_address, override_port = ssh_tunnel.get_bind_addresses()

    if os.getenv("VULCAN_APP_MONGO_CONNECTION") is not None:
        database = Mongo(os.getenv("VULCAN_APP_MONGO_CONNECTION"), os.getenv("VULCAN_APP_MONGO_DB"))


def get_session():
    # for postgres
    return database.get_session()


def terminate_connections():
    if ssh_tunnel is not None:
        ssh_tunnel.disconnect()
