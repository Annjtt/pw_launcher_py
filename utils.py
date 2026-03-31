import os
import json
import subprocess
import webbrowser
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from styles import StyleManager

config_file = "config.json"
_navigation_lock = False


def load_config():
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            data = json.load(file)
        profiles = data.get("profiles", {})
        for profile in profiles.values():
            characters = profile.get("characters", [])
            for char in characters:
                if "icon" not in char:
                    char["icon"] = None
        return data
    else:
        default_profiles = {"active_profile": None, "profiles": {}}
        save_config(default_profiles)
        return default_profiles


def save_config(profiles):
    with open(config_file, "w") as file:
        json.dump(profiles, file, indent=4)


def get_active_profile(profiles):
    profile_name = profiles.get("active_profile")
    return profiles["profiles"].get(profile_name) if profile_name else None


def set_active_profile(profile_name, root, frame, profiles):
    profiles["active_profile"] = profile_name
    save_config(profiles)
    from ui.character_menu import character_menu
    character_menu(root, frame, profiles)


def update_profile(profile_name, data, profiles):
    profiles["profiles"][profile_name] = data
    save_config(profiles)


def delete_profile(profile_name, root, frame, profiles):
    if profile_name in profiles["profiles"]:
        del profiles["profiles"][profile_name]
        save_config(profiles)
        from ui.profile_menu import profile_menu
        profile_menu(root, frame, profiles)
    else:
        messagebox.showerror("Ошибка", "Профиль не найден.")


def start_game_async(account, profiles):
    profile = get_active_profile(profiles)
    if not profile:
        messagebox.showerror("Ошибка", "Профиль не выбран!")
        return
    game_path = profile.get("game_path")
    if not game_path or not os.path.exists(game_path):
        messagebox.showerror("Ошибка", "Путь к клиенту игры не найден!")
        return

    def run_game():
        game_dir = os.path.dirname(game_path)
        os.chdir(game_dir)

        args = (
            f"nocheck no check startbypatcher game:cpw console:1 "
            f"user:{account['acc']} pwd:{account['pwd']} role:{account['char']}"
        )

        powershell_command = (
            'powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command '
            "\"$p = Start-Process '%s' -ArgumentList '%s' -PassThru; "
            "while ($p.MainWindowHandle -eq 0) { Start-Sleep -Milliseconds 200; $p.Refresh() } "
            "Add-Type -Name Win32 -Namespace Native -MemberDefinition '[DllImport(\\\"user32.dll\\\", CharSet=CharSet.Auto)] public static extern bool SetWindowText(IntPtr hWnd, string lpString);'; "
            "[Native.Win32]::SetWindowText($p.MainWindowHandle, '%s') | Out-Null\""
            % (game_path, args, account["char"])
        )

        subprocess.run(powershell_command, shell=True)

    threading.Thread(target=run_game, daemon=True).start()

def open_telegram_channel():
    webbrowser.open("https://t.me/santhouse_life")

def open_telegram():
    webbrowser.open("https://t.me/santhouse")

def navigate_to(option, root, frame, profiles):
    """Навигация по меню"""
    global _navigation_lock
    if _navigation_lock:
        print(f"⚠️ [NAV] Навигация заблокирована, пропускаем")
        return

    _navigation_lock = True

    try:
        if option == "Мониторинг":
            from ui.debuff_monitor import DebuffMonitorUI
            print(f"🔍 [NAV] Поиск существующего монитора в {frame.winfo_children()}")

            # Находим MainApplication
            app = None
            print(f"🔍 [NAV] Ищем MainApplication среди дочерних root.winfo_children():")
            for child in root.winfo_children():
                print(f"    - child: {child}, hasattr show_loading_for_monitor: {hasattr(child, 'show_loading_for_monitor')}")
                if hasattr(child, 'show_loading_for_monitor'):
                    app = child
                    print(f"✅ [NAV] Найден MainApplication: {app}")
                    break
            if not app:
                print(f"⚠️ [NAV] MainApplication НЕ НАЙДЕН!")
            # Ищем существующий монитор
            existing_monitor = None
            for child in frame.winfo_children():
                if isinstance(child, DebuffMonitorUI):
                    existing_monitor = child
                    print(f"✅ Найден существующий монитор")
                    break

            # Очищаем фрейм
            for w in frame.winfo_children():
                w.pack_forget()

            if existing_monitor:
                existing_monitor.show_monitor(app)
                print(f"🔄 [MONITOR] Восстановлен интерфейс")
            else:
                monitor_page = DebuffMonitorUI(frame, profiles)
                monitor_page.show_monitor(app)
                print(f"🆕 [MONITOR] Создан новый экземпляр")

        elif option == "Персонажи":
            from ui.character_menu import character_menu
            for w in frame.winfo_children():
                w.destroy()
            character_menu(root, frame, profiles)

        elif option == "Профиль":
            from ui.profile_menu import profile_menu
            for w in frame.winfo_children():
                w.destroy()
            profile_menu(root, frame, profiles)

        elif option == "Настройки":
            from ui.settings_menu import settings_menu
            for w in frame.winfo_children():
                w.destroy()
            settings_menu(root, frame, profiles)

        elif option == "Главная":
            from ui.main_menu import main_menu
            for w in frame.winfo_children():
                w.destroy()
            main_menu(root, frame, profiles)
    finally:
        _navigation_lock = False


class MainApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PW Launcher")
        self.root.configure(bg="#222222")
        self.root.attributes("-alpha", 0.97)
        try:
            self.root.iconbitmap(default="assets/icon.ico")
        except:
            pass
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 460) // 2
        y = (screen_height - 650) // 2
        self.root.geometry(f"460x650+{x}+{y}")

        # 👇 СОЗДАЁМ ГЛАВНЫЙ ФРЕЙМ
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
            self.main_frame,
            text="Loading...",
            font=("Helvetica", 36, "bold"),
            fg="#dddddd",
            bg="#222222"
        )
        self.loading_label.pack(expand=True)

        # Полоска загрузки
        self.loading_bar_canvas = tk.Canvas(
            self.main_frame,
            width=220,
            height=8,
            bg="#444444",
            highlightthickness=0
        )
        self.loading_bar_canvas.pack(pady=(1, 40))
        self._loading_bar_rect = self.loading_bar_canvas.create_rectangle(
            0, 0, 0, 10, fill="#19e1a0", outline="#19e1a0"
        )
        self._bar_fill = 0
        self._bar_max = 220
        self.loading_bar_animating = True

        def animate_bar():
            if not self.loading_bar_animating:
                return
            if self._bar_fill < self._bar_max:
                self._bar_fill += 3
                if self._bar_fill > self._bar_max:
                    self._bar_fill = self._bar_max
                try:
                    self.loading_bar_canvas.coords(self._loading_bar_rect, 0, 0, self._bar_fill, 10)
                except tk.TclError:
                    return
                self.root.after(16, animate_bar)
            else:
                self.loading_bar_animating = False

        animate_bar()

        style = StyleManager()
        style.animate_text(self.loading_label, "Loading...", loop=True)

        # Version at the very bottom
        self.version_label = tk.Label(
            self.main_frame,
            text="v.3.1.2",
            font=("Fixedsys", 10),
            fg="#dedede",
            bg="#222222"
        )
        self.version_label.pack(side="bottom", pady=(0, 20))

        # Footer note
        self.footer_label = tk.Label(
            self.main_frame,
            text="by santhouse",
            font=("Fixedsys", 15),
            fg="#19e1a0",
            bg="#222222"
        )
        self.footer_label.pack(side="bottom", pady=(0, 2))

        self.root.after(1900, self.transition_to_main_menu)

    def transition_to_main_menu(self):
        self.loading = False
        self.loading_bar_animating = False
        if hasattr(self, 'text_animation'):
            self.text_animation.stop()
        self.show_main_menu()

    def show_main_menu(self):
        # Очищаем main_frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.profiles = load_config()
        from ui.main_menu import main_menu
        main_menu(self.root, self.main_frame, self.profiles)

    def show_loading_for_monitor(self, callback):
        """Показывает загрузку для мониторинга"""
        print(f"🔄 [LOAD] show_loading_for_monitor вызван")
        # Очищаем main_frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        print(f"🔄 [LOAD] main_frame очищен")

        self.loading_label = tk.Label(
            self.main_frame,
            text="Загрузка мониторинга...",
            font=("Helvetica", 24, "bold"),
            fg="#19e1a0",
            bg="#222222"
        )
        self.loading_label.pack(expand=True)

        # Полоска загрузки
        self.loading_bar_canvas = tk.Canvas(
            self.main_frame,
            width=220,
            height=8,
            bg="#444444",
            highlightthickness=0
        )
        self.loading_bar_canvas.pack(pady=(10, 40))
        self._loading_bar_rect = self.loading_bar_canvas.create_rectangle(
            0, 0, 0, 10, fill="#19e1a0", outline="#19e1a0"
        )

        self._bar_fill = 0
        self._bar_max = 220
        self.loading_bar_animating = True

        def animate_bar():
            if not self.loading_bar_animating:
                return
            if self._bar_fill < self._bar_max:
                self._bar_fill += 5
                if self._bar_fill > self._bar_max:
                    self._bar_fill = self._bar_max
                self.loading_bar_canvas.coords(self._loading_bar_rect, 0, 0, self._bar_fill, 10)
                self.main_frame.after(20, animate_bar)
            else:
                self.loading_bar_animating = False
                print(f"🔄 [LOAD] Анимация завершена, вызываем callback")
                callback()

        animate_bar()
        self.main_frame.update_idletasks()
        self.main_frame.update()
        print(f"🔄 [LOAD] main_frame обновлен")

    def hide_loading(self):
        """Скрывает загрузку"""
        self.loading_bar_animating = False