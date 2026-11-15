from pythonosc.udp_client import SimpleUDPClient

class MA3:
    def __init__(self, host="127.0.0.1", port=8000):
        self.client = SimpleUDPClient(host, port)

    def send(self, cmd: str) -> str:
        self.client.send_message("/cmd", cmd)
        return "envoyé"