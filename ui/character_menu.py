import os
import tkinter as tk
from tkinter import messagebox
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None
from utils import get_active_profile, start_game_async, update_profile, navigate_to, StyleManager
from .add_character_menu import add_character_menu
from ui.tooltip import ToolTip


def character_menu(root, frame, profiles):
    style = StyleManager()
    profile_name = profiles.get("active_profile", "Не выбран")
    profile = get_active_profile(profiles)
    if not profile:
        messagebox.showwarning("Предупреждение", "Активный профиль не выбран. Персонажи не загружены.")
        return
    characters = profile.get("characters", [])
    # Удаляем "пустых" персонажей, которые могли остаться после старой логики добавления
    cleaned_characters = []
    for ch in characters:
        if ch.get("acc") or ch.get("pwd") or ch.get("char"):
            cleaned_characters.append(ch)
    if len(cleaned_characters) != len(characters):
        profile["characters"] = cleaned_characters
        update_profile(profiles["active_profile"], profile, profiles)
        characters = cleaned_characters

    selected_characters = [] 
    checkbox_vars = []
    frame.icon_images = []
    
    # def toggle_character(index):
    #     if index in selected_characters:
    #         selected_characters.remove(index)
    #     else:
    #         selected_characters.append(index)

    def toggle_character(index):
        if index in selected_characters:
            selected_characters.remove(index)
            checkbox_vars[index].set(0)
        else:
            selected_characters.append(index)
            checkbox_vars[index].set(1)

    def select_all_characters():
        if len(selected_characters) == len(characters):
            selected_characters.clear()
            for var in checkbox_vars:
                var.set(0)
        else:
            selected_characters.clear()
            for i, var in enumerate(checkbox_vars):
                var.set(1)
                selected_characters.append(i)
    
    def start_selected_games():
        delay = 10
        for idx in selected_characters:
            root.after(delay, start_game_async, characters[idx], profiles)
            delay += 15000
    
    def start_game_for_char(index):
        start_game_async(characters[index], profiles)
    
    def edit_character(index):
        from ui.add_character_menu import add_character_menu
        add_character_menu(root, frame, index, profiles)
    
    def delete_character(index):
        if 0 <= index < len(characters):
            char_name = f"{characters[index]['char']}"
            characters.pop(index)
            profile["characters"] = characters
            update_profile(profiles["active_profile"], profile, profiles)
            character_menu(root, frame, profiles)
        else:
            messagebox.showerror("Ошибка", "Неверный индекс персонажа.")
    
    def create_character():
        # Новый персонаж создаётся только после сохранения в редакторе,
        # поэтому здесь не добавляем пустой объект в список
        add_character_menu(root, frame, None, profiles)
    
    #for widget in frame.winfo_children(): убрал уничтожение мониторинга
    #    widget.destroy()
    
    header = tk.Label(frame, text="Персонажи", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=20)
    style.animate_text(header, "Персонажи", loop=True)
    
    button_frame = tk.Frame(frame, bg="#222222")
    button_frame.pack(pady=1, padx=5, fill="x")
    
    btn_select_all = tk.Button(button_frame, text="✅", command=select_all_characters, font=("Helvetica", 10), 
                               bg="#333333", fg="#19e1a0", relief="flat")
    btn_select_all.pack(side="left", padx=7)
    btn_select_all.bind("<Enter>", style.on_hover)
    btn_select_all.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#19e1a0"))
    
    def go_to_profile_menu():
        from ui.profile_menu import profile_menu
        profile_menu(root, frame, profiles)

    gear_btn = tk.Button(button_frame, text="⚙", command=go_to_profile_menu,
                        font=("Helvetica", 10, "bold"), bg="#333333", fg="#f39c12", relief="flat")
    gear_btn.pack(side="left", padx=2)
    gear_btn.bind("<Enter>", style.on_hover)
    gear_btn.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#f39c12"))
    profile_label = tk.Label(button_frame, text=f"Профиль: {profile_name}", 
                             font=("Fixedsys", 16), bg="#222222", fg="#dedede")
    profile_label.pack(side="left", padx=5)

    # Область со скроллом для списка персонажей (используем только Canvas, без видимых скроллбаров)
    canvas = tk.Canvas(frame, bg="#222222", highlightthickness=0, borderwidth=0)
    scrollable_frame = tk.Frame(canvas, bg="#222222")

    # Создаём вложенный фрейм и заставляем его всегда быть по ширине канваса,
    # чтобы не оставалось пустой полосы справа
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def _update_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _resize_inner(event):
        canvas.itemconfig(window_id, width=event.width)

    scrollable_frame.bind("<Configure>", _update_scrollregion)
    canvas.bind("<Configure>", _resize_inner)

    # Паддинги как у старого списка, чтобы визуал остался тем же
    canvas.pack(pady=5, padx=2, fill="both", expand=True)

    # Глобальная прокрутка колёсиком по всему окну приложения
    def _on_mousewheel(event):
        # На Windows event.delta кратен 120
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # отвязываем старые бинды и вешаем новый на всё приложение
    root.unbind_all("<MouseWheel>")
    root.bind_all("<MouseWheel>", _on_mousewheel)

    if not characters:
        tk.Label(scrollable_frame, text="Нет персонажей", font=("Helvetica", 14, "bold"), bg="#222222", fg="#d42d52").pack(pady=10)

    # Поддерживаем несколько стандартных путей для иконок
    icon_dirs = [
        os.path.join("assets", "prof"),
        os.path.join("assets", "prof"),
    ]
    icon_cache = {}
    pillow_warning_shown = {"value": False}

    def get_icon_image(icon_name):
        if not icon_name:
            return None
        if icon_name in icon_cache:
            return icon_cache[icon_name]
        # Ищем файл иконки в одном из каталогов
        icon_path = None
        for d in icon_dirs:
            candidate = os.path.join(d, icon_name)
            if os.path.isfile(candidate):
                icon_path = candidate
                break
        if not icon_path:
            return None
        try:
            if icon_path.lower().endswith(".webp") and Image is not None and ImageTk is not None:
                image = Image.open(icon_path)
                # Ещё немного уменьшаем иконку для более аккуратного вида
                image = image.resize((16, 16), Image.LANCZOS)
                img = ImageTk.PhotoImage(image)
            else:
                img = tk.PhotoImage(file=icon_path)
        except Exception:
            # Если webp, но Pillow не установлен — один раз предупредим
            if icon_path.lower().endswith(".webp") and (Image is None or ImageTk is None) and not pillow_warning_shown["value"]:
                pillow_warning_shown["value"] = True
                messagebox.showwarning(
                    "Иконки классов",
                    "Для отображения иконок .webp установите пакет Pillow:\n\npip install pillow"
                )
            return None
        icon_cache[icon_name] = img
        return img

    for i, char in enumerate(characters):
        char_frame = tk.Frame(
            scrollable_frame, 
            bg="#333333",
            highlightthickness=2,           # толщина рамки
            highlightbackground="#333333",   # цвет рамки по умолчанию
            highlightcolor="#19e1a0"         # цвет рамки при фокусе (опционально)
        )
        # отступы как раньше (pady=5, padx=10), но внутри скролл-контейнера
        char_frame.pack(pady=5, padx=10, fill="x")
        char_frame.config(cursor="hand2") # курсор-рука, мб удалить.
        # При наведении — меняем цвет рамки
        def on_enter(e, f=char_frame):
            f.config(highlightbackground="#19e1a0")  # яркий зелёный при наведении
        
        def on_leave(e, f=char_frame):
            f.config(highlightbackground="#333333")  # возвращаем исходный цвет
        char_frame.bind("<Enter>", on_enter)
        char_frame.bind("<Leave>", on_leave)
        # Клик по строке переключает чекбокс
        char_frame.bind("<Button-1>", lambda e, idx=i: toggle_character(idx))

        char_info = f"{char.get('char', '')}"
        var = tk.IntVar()
        checkbox_vars.append(var)

        # Чекбокс выбора персонажа
        check_button = tk.Checkbutton(
            char_frame, variable=var, font=("Helvetica", 12), bg="#333333", fg="#19e1a0", selectcolor="#222222",
            command=lambda i=i: toggle_character(i)
        )
        check_button.pack(side="left", padx=2)

        # Иконка класса — сразу после чекбокса
        icon_name = char.get("icon")
        icon_image = get_icon_image(icon_name)
        if icon_image:
            icon_label = tk.Label(char_frame, image=icon_image, bg="#333333")
            icon_label.pack(side="left", padx=0)
            frame.icon_images.append(icon_image)

        # Ник + логин
        tk.Label(char_frame, text=char_info, font=("Fixedsys", 12), bg="#333333", fg="#dedede").pack(side="left", padx=5)
        buttons = [
            {"text": "❌", "command": lambda i=i: delete_character(i), "bg": "#424242", "fg": "#d42d52"},
            {"text": "✎", "command": lambda i=i: edit_character(i), "bg": "#424242", "fg": "#f39c12"},
            {"text": "▶", "command": lambda i=i: start_game_for_char(i), "bg": "#424242", "fg": "#19e1a0"}
        ]
        for button in buttons:
            btn = tk.Button(char_frame, text=button["text"], command=button["command"], 
                            font=("Helvetica", 10, "bold"), bg=button["bg"], fg=button["fg"], relief="flat")
            btn.pack(side="right", padx=5)
            btn.bind("<Enter>", style.on_hover)
            btn.bind("<Leave>", lambda event, bg=button["bg"], fg=button["fg"]: style.on_leave(event, bg, fg))
    
    button_frame = tk.Frame(frame, bg="#222222")
    button_frame.pack(pady=10, padx=10, fill="x")
    
    btn_run_selected = tk.Button(button_frame, text="▶ Запустить выбранных", command=start_selected_games, 
                                 font=("Helvetica", 10, "bold"), bg="#333333", fg="#dedede", relief="flat")
    btn_run_selected.pack(side="left", padx=1)
    btn_run_selected.bind("<Enter>", style.on_hover)
    btn_run_selected.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#dedede"))

    # Кнопки импорта/экспорта
    def import_profile():
        # TODO: логика импорта профиля
        messagebox.showinfo("Импорт профиля", "Функция импорта будет добавлена позже")

    def export_profile():
        # TODO: логика экспорта профиля
        messagebox.showinfo("Экспорт профиля", "Функция экспорта будет добавлена позже")

    import_btn = tk.Button(button_frame, text="📥", command=import_profile,
                        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0", relief="flat")
    import_btn.pack(side="left", padx=10, expand=True)
    import_btn.bind("<Enter>", style.on_hover)
    import_btn.bind("<Leave>", lambda e: style.on_leave(e, "#333333", "#19e1a0"))

    export_btn = tk.Button(button_frame, text="📤", command=export_profile,
                        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0", relief="flat")
    export_btn.pack(side="left", padx=10, expand=True)
    export_btn.bind("<Enter>", style.on_hover)
    export_btn.bind("<Leave>", lambda e: style.on_leave(e, "#333333", "#19e1a0"))
    
    btn_add_character = tk.Button(button_frame, text="➕ Добавить", command=create_character, 
                                  font=("Helvetica", 10, "bold"), bg="#333333", fg="#dedede", relief="flat")
    btn_add_character.pack(side="right", padx=1)
    btn_add_character.bind("<Enter>", style.on_hover)
    btn_add_character.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#dedede"))
    
    btn_back = tk.Button(frame, text="Назад", command=lambda: navigate_to("Главная", root, frame, profiles),
                         font=("Helvetica", 11, "bold"), bg="#333333", fg="#d42d52", relief="flat")
    btn_back.pack(pady=10)
    btn_back.bind("<Enter>", style.on_hover)
    btn_back.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#d42d52"))

    ToolTip(import_btn, "Импорт профиля")
    ToolTip(export_btn, "Экспорт профиля")