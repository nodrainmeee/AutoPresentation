"""Point d'entrée d'AutoPrésentation."""

import tkinter as tk


def principal() -> None:
    try:  # netteté sur les écrans à haute résolution (Windows)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    from autopresentation.interface import Application
    racine = tk.Tk()
    Application(racine)
    racine.mainloop()


if __name__ == "__main__":
    principal()
