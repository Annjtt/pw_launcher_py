import tkinter as tk
from ui.main_menu import main_menu
from styles import StyleManager
from utils import MainApplication

if __name__ == "__main__":
    app = MainApplication()
    app.root.app = app  # Сохраняем ссылку в корневом окне  
    app.root.mainloop()
