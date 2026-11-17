"""Point d'entrée de l'application de bureau : serveur FastAPI local en arrière-plan + fenêtre native (pywebview).

Lancement : `python ma3ia/desktop.py` (ou scripts/run.bat / scripts/run.command, ou l'app construite par
scripts/construire_exe.bat sous Windows, scripts/construire_app.sh sous macOS).
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


ICONE = os.path.join(reglages.dossier_ressources(), "assets", "ma3ia.ico")
# Couleurs de la barre de titre (Windows), alignées sur les thèmes de index.html : (fond, texte, mode sombre)
BARRE_TITRE = {"sombre": ("#141517", "#e7e6e2", 1), "clair": ("#f7f7f5", "#1e1f22", 0)}


def identifier_application():
    """Sans AppUserModelID, Windows regroupe la fenêtre sous pythonw.exe (logo Python dans la barre des tâches)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MA3IA.Desktop")
    except Exception:
        pass


def _colorref(hexa: str) -> int:
    r, g, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
    return r | (g << 8) | (b << 16)


def _apparence_mac(theme: str):
    """macOS : barre de titre claire ou sombre selon le thème (apparence de l'application, sur le fil principal)."""
    try:
        from AppKit import NSAppearance, NSApplication
        from PyObjCTools import AppHelper
        nom = "NSAppearanceNameDarkAqua" if theme != "clair" else "NSAppearanceNameAqua"
        AppHelper.callAfter(lambda: NSApplication.sharedApplication().setAppearance_(NSAppearance.appearanceNamed_(nom)))
    except Exception:
        pass


def colorer_barre_titre(fenetre, theme: str):
    """Barre de titre de la couleur de l'app (Windows 11 : couleurs exactes ; macOS : clair / sombre)."""
    if sys.platform == "darwin":
        return _apparence_mac(theme)
    if sys.platform != "win32":
        return
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

    def ouvrir_lien(self, url):
        """Ouvre un lien dans le navigateur par défaut (seulement les pages GitHub du projet)."""
        if str(url).startswith("https://github.com/elio7224/ma3-ia"):
            import webbrowser
            webbrowser.open(url)


def page_chargement(theme: str) -> str:
    """Page affichée tout de suite à l'ouverture de la fenêtre, le temps que le serveur local démarre."""
    from i18n import tr
    fond, texte = ("#f7f7f5", "#1e1f22") if theme == "clair" else ("#141517", "#e7e6e2")
    return (f"<body style='margin:0;height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;"
            f"background:{fond};color:{texte};font-family:Segoe UI,system-ui,sans-serif'>"
            "<style>@keyframes t{to{transform:rotate(360deg)}}"
            ".r{width:44px;height:44px;border:4px solid #8886;border-top-color:#e3c07a;border-radius:50%;animation:t .9s linear infinite}</style>"
            "<div class='r'></div>"
            f"<h2 style='margin:22px 0 6px;font-weight:500'>{tr('MA3-IA démarre…', 'MA3-IA is starting…')}</h2>"
            f"<div style='opacity:.65;font-size:14px'>{tr('Chargement en cours, quelques secondes…', 'Loading, this takes a few seconds…')}</div>")


def main():
    import webview
    identifier_application()
    icone = ICONE if os.path.isfile(ICONE) else None
    theme = reglages.charger().get("theme", "sombre")
    port = port_libre()
    etat = {}
    api = ApiFenetre()
    # La fenêtre s'ouvre tout de suite sur un écran de chargement ; le serveur démarre en parallèle.
    f = webview.create_window("grandMA3 AI Control", html=page_chargement(theme), width=1280, height=820,
                              min_size=(900, 600), background_color="#141517", text_select=True, js_api=api)
    api._fenetre = f
    f.events.shown += lambda: colorer_barre_titre(f, theme)

    def demarrer():
        etat["serveur"] = demarrer_serveur(port)
        if attendre_serveur(port):
            f.load_url(f"http://127.0.0.1:{port}/")
        else:
            from i18n import tr
            f.load_html("<body style='background:#141517;color:#e7e6e2;font-family:sans-serif;padding:40px'>"
                        + tr("<h2>Le serveur local n'a pas démarré.</h2><p>Relance l'application.</p>",
                             "<h2>The local server did not start.</h2><p>Restart the application.</p>"))

    webview.start(demarrer, icon=icone)          # bloque jusqu'à la fermeture de la fenêtre
    if etat.get("serveur"):
        etat["serveur"].should_exit = True


if __name__ == "__main__":
    sys.exit(main())
