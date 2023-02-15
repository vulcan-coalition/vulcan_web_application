from sshtunnel import SSHTunnelForwarder
import os


dir_path = os.path.dirname(os.path.realpath(__file__))


class Tunnel_Session:
    def __init__(self, credentials):
        self.server = SSHTunnelForwarder(
            credentials["host"],
            ssh_username=credentials["username"],
            ssh_pkey=os.path.join(dir_path, "..", "..", "artifacts", credentials["pkey"]),
            remote_bind_address=(credentials["bind_host"], credentials["bind_port"])
        )
        self.server.start()
        print("Tunneling start")

    def get_bind_addresses(self):
        return '127.0.0.1', self.server.local_bind_port

    def disconnect(self):
        self.server.stop()
