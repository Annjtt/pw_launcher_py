import tkinter as tk
from ui.main_menu import main_menu
from styles import StyleManager
from utils import MainApplication

if __name__ == "__main__":
    app = MainApplication()
    app.root.mainloop()

#ох, блять.....
class MainApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PW Launcher")
        self.root.configure(bg="#222222")
        self.root.attributes("-alpha", 0.97)
        self.root.iconbitmap(default="assets/icon.ico")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1) // 2
        y = (screen_height - 480) // 2
        self.root.geometry(f"460x650+{x}+{y}")
        
        # 👇 СОЗДАЁМ ОДИН ГЛАВНЫЙ ФРЕЙМ
        self.main_frame = tk.Frame(self.root, bg="#222222")
        self.main_frame.pack(fill="both", expand=True)
        
        # 👇 Сохраняем ссылку на мониторинг
        self.monitor_instance = None
        self.monitor_frame = None  # Фрейм, в котором находится монитор
        
        self.loading = True
        self.loading_bar_animating = False
        self.show_loading_screen()

    def show_loading_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.loading_label = tk.Label(
            self.main_frame,
            text="Loading...",
            font=("Helvetica", 36, "bold"),
            fg="#dddddd",
            bg="#222222"
        )
        self.loading_label.pack(expand=True)

        # ... (остальной код loading screen без изменений) ...
        
        self.root.after(1900, self.transition_to_main_menu)

    def transition_to_main_menu(self):
        self.loading = False
        self.loading_bar_animating = False
        if hasattr(self, 'text_animation'):
            self.text_animation.stop()
        self.show_main_menu()

    def show_main_menu(self):
        # 👇 Очищаем main_frame, НО НЕ мониторинг!
        for widget in self.main_frame.winfo_children():
            # Если это мониторинг — скрываем, но не уничтожаем
            if self.monitor_instance and widget == self.monitor_instance:
                widget.pack_forget()
            else:
                widget.destroy()
        
        self.profiles = load_config()
        
        from ui.main_menu import main_menu
        main_menu(self.root, self.main_frame, self.profiles)
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PW Launcher")
        self.root.configure(bg="#222222")
        self.root.attributes("-alpha", 0.97)
        self.root.iconbitmap(default="assets/icon.ico")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1) // 2
        y = (screen_height - 480) // 2
        self.root.geometry(f"460x650+{x}+{y}")
        
        # 👇 СОЗДАЁМ ОДИН ГЛАВНЫЙ ФРЕЙМ для всего приложения
        self.main_frame = tk.Frame(self.root, bg="#222222")
        self.main_frame.pack(fill="both", expand=True)
        
        self.loading = True
        self.loading_bar_animating = False
        self.show_loading_screen()

    def show_loading_screen(self):
        # Очищаем main_frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.loading_label = tk.Label(
            self.main_frame,  # 👇 Используем main_frame вместо self.root
            text="Loading...",
            font=("Helvetica", 36, "bold"),
            fg="#dddddd",
            bg="#222222"
        )
        self.loading_label.pack(expand=True)

        # ... остальной код loading screen ...
        
        self.root.after(1900, self.transition_to_main_menu)

    def transition_to_main_menu(self):
        self.loading = False
        self.loading_bar_animating = False
        if hasattr(self, 'text_animation'):
            self.text_animation.stop()
        self.show_main_menu()

    def clear_monitor_reference(self):
        """Очищает ссылку на монитор при закрытии"""
        if self.monitor_instance:
            if self.monitor_instance.monitoring:
                self.monitor_instance.stop_monitoring()
            self.monitor_instance = None

    def show_main_menu(self):
        # 👇 Очищаем main_frame ПОЛНОСТЬЮ
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.profiles = load_config()
        
        # 👇 Используем ТОТ ЖЕ main_frame
        from ui.main_menu import main_menu
        main_menu(self.root, self.main_frame, self.profiles)