from db import repositorio as repo
from ui.app import App

# Hito de arranque del sistema: inicializa la estructura de datos y enciende el bucle principal de la aplicación.
if __name__ == "__main__":
    repo.inicializar()
    App().mainloop()
