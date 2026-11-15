"""Point d'entrée de l'application de bureau : serveur FastAPI local en arrière-plan + fenêtre native (pywebview).

Lancement : `python desktop.py` (ou run_bureau.bat, ou l'exécutable MA3-IA.exe créé par construire_exe.bat).
"""
import os
import socket
import sys
import threading
import time
import urllib.request

import reglages

# Les messages contiennent des emojis : évite un plantage si la console / la redirection est en cp1252.
for _flux in (sys.stdout, sys.stderr):
    if _flux is not None and hasattr(_flux, "reconfigure"):
        _flux.reconfigure(encoding="utf-8", errors="replace")

# L'historique du chat vit dans le dossier de config de l'utilisateur (pas dans le dépôt / le dossier du .exe).
os.makedirs(reglages.dossier_config(), exist_ok=True)
os.environ.setdefault("MA3IA_HISTORIQUE", os.path.join(reglages.dossier_config(), "memoire_chat.json"))


def port_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def demarrer_serveur(port: int):
    import uvicorn
    import app as application
    config = uvicorn.Config(application.app, host="127.0.0.1", port=port, log_config=None)
    serveur = uvicorn.Server(config)
    threading.Thread(target=serveur.run, daemon=True).start()
    return serveur


def attendre_serveur(port: int, delai: float = 20.0) -> bool:
    fin = time.time() + delai
    while time.time() < fin:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


ICONE = os.path.join(reglages.dossier_ressources(), "ma3ia.ico")
# Couleurs de la barre de titre Windows, alignées sur les thèmes de index.html : (fond, texte, mode sombre)
BARRE_TITRE = {"sombre": ("#0b0d14", "#e8eaf0", 1), "clair": ("#f4f5fa", "#1b1e2b", 0)}


def identifier_application():
    """Sans AppUserModelID, Windows regroupe la fenêtre sous pythonw.exe (logo Python dans la barre des tâches)."""
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MA3IA.Desktop")
    except Exception:
        pass


def _colorref(hexa: str) -> int:
    r, g, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
    return r | (g << 8) | (b << 16)


def colorer_barre_titre(fenetre, theme: str):
    """Barre de titre et bordure de la couleur de l'app (Windows 11 ; ignoré silencieusement ailleurs)."""
    try:
        import ctypes
        fond, texte, sombre = BARRE_TITRE.get(theme, BARRE_TITRE["sombre"])
        hwnd = fenetre.native.Handle.ToInt32()
        dwm = ctypes.windll.dwmapi.DwmSetWindowAttribute
        for attr, val in ((20, sombre),               # DWMWA_USE_IMMERSIVE_DARK_MODE
                          (34, _colorref(fond)),      # DWMWA_BORDER_COLOR
                          (35, _colorref(fond)),      # DWMWA_CAPTION_COLOR
                          (36, _colorref(texte))):    # DWMWA_TEXT_COLOR
            v = ctypes.c_int(val)
            dwm(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))
    except Exception:
        pass


class ApiFenetre:
    """Exposé à la page (window.pywebview.api) : la barre de titre suit le thème choisi dans les réglages."""
    def __init__(self):
        self._fenetre = None

    def theme(self, theme):
        if self._fenetre is not None:
            colorer_barre_titre(self._fenetre, theme)


def main():
    import webview
    identifier_application()
    icone = ICONE if os.path.isfile(ICONE) else None
    port = port_libre()
    serveur = demarrer_serveur(port)
    if not attendre_serveur(port):
        f = webview.create_window("MA3-IA", html="<body style='background:#0b0d14;color:#e8eaf0;font-family:sans-serif;padding:40px'>"
                                  "<h2>Le serveur local n'a pas démarré.</h2><p>Relance l'application.</p>")
        f.events.shown += lambda: colorer_barre_titre(f, "sombre")
        webview.start(icon=icone)
        return
    api = ApiFenetre()
    f = webview.create_window("grandMA3 AI Control", f"http://127.0.0.1:{port}/", width=1280, height=820,
                              min_size=(900, 600), background_color="#0b0d14", text_select=True, js_api=api)
    api._fenetre = f
    f.events.shown += lambda: colorer_barre_titre(f, reglages.charger().get("theme", "sombre"))
    webview.start(icon=icone)          # bloque jusqu'à la fermeture de la fenêtre
    serveur.should_exit = True


if __name__ == "__main__":
    sys.exit(main())
