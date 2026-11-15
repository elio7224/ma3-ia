import threading
from contextlib import contextmanager

from pythonosc.udp_client import SimpleUDPClient

import journal
from i18n import tr

# Mode validation : dans un bloc `with capture() as cmds`, les commandes sont gardées au lieu d'être envoyées.
_local = threading.local()


@contextmanager
def capture():
    cmds = []
    _local.capture = cmds
    try:
        yield cmds
    finally:
        _local.capture = None


def en_capture() -> bool:
    return getattr(_local, "capture", None) is not None


class MA3:
    def __init__(self, host="127.0.0.1", port=8000):
        self.cible = f"{host}:{port}"
        self.client = SimpleUDPClient(host, port)

    def send(self, cmd: str) -> str:
        cmds = getattr(_local, "capture", None)
        if cmds is not None:
            cmds.append(cmd)
            return tr("préparé (pas encore envoyé)", "prepared (not sent yet)")
        self.client.send_message("/cmd", cmd)
        journal.noter(cmd, self.cible)
        return tr("envoyé", "sent")
