from pythonosc.udp_client import SimpleUDPClient

import journal
from i18n import tr


class MA3:
    def __init__(self, host="127.0.0.1", port=8000):
        self.cible = f"{host}:{port}"
        self.client = SimpleUDPClient(host, port)

    def send(self, cmd: str) -> str:
        self.client.send_message("/cmd", cmd)
        journal.noter(cmd, self.cible)
        return tr("envoyé", "sent")
