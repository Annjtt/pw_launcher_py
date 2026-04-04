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
import json


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

    # Переменные для Drag & Drop
    drag_start_index = None
    drag_target_index = None
    drag_start_x = 0
    drag_start_y = 0
    drag_start_time = 0
    drag_threshold = 10  # минимальное перемещение для определения драга (пикселей)
    long_press_threshold = 300  # миллисекунды для определения долгого нажатия
    is_dragging = False
    long_press_triggered = False
    after_id = None

    def on_press(event, idx):
        nonlocal drag_start_index, drag_start_x, drag_start_y, drag_start_time, is_dragging, long_press_triggered, after_id
        drag_start_index = idx
        drag_start_x = event.x_root
        drag_start_y = event.y_root
        drag_start_time = event.time
        is_dragging = False
        long_press_triggered = False
        
        # Отменяем предыдущий таймер, если есть
        if after_id:
            root.after_cancel(after_id)
        
        # Запускаем таймер для долгого нажатия
        after_id = root.after(long_press_threshold, lambda: on_long_press(event, idx))
    
    def on_long_press(event, idx):
        nonlocal long_press_triggered, after_id, is_dragging
        long_press_triggered = True
        is_dragging = True
        after_id = None
        
        # Визуально подсвечиваем строку при начале перетаскивания (цвет при зажатии)
        highlight_drag_start(idx)
    
    def highlight_drag_start(idx):
        """Подсвечивает строку, которую перетаскивают (цвет как при клике в main_menu)"""
        for i, child in enumerate(scrollable_frame.winfo_children()):
            if i == idx:
                child.config(bg="#555555")  # Цвет при клике/драге
                for widget in child.winfo_children():
                    if isinstance(widget, (tk.Label, tk.Checkbutton)):
                        widget.config(bg="#555555")
            else:
                child.config(bg="#333333")
                for widget in child.winfo_children():
                    if isinstance(widget, (tk.Label, tk.Checkbutton)):
                        widget.config(bg="#333333")

    def on_motion(event):
        nonlocal drag_target_index, is_dragging, long_press_triggered
        if drag_start_index is None:
            return
        
        # Если долгое нажатие не сработало, проверяем перемещение
        if not long_press_triggered:
            dx = abs(event.x_root - drag_start_x)
            dy = abs(event.y_root - drag_start_y)
            
            # Если переместили мышь до срабатывания долгого нажатия - отменяем
            if dx > drag_threshold or dy > drag_threshold:
                if after_id:
                    root.after_cancel(after_id)
                return
        
        if not is_dragging:
            return
        
        # Поиск целевого индекса для перетаскивания
        current_y = event.y_root
        for i, child in enumerate(scrollable_frame.winfo_children()):
            if i == drag_start_index:
                continue
            y1 = child.winfo_rooty()
            y2 = y1 + child.winfo_height()
            if y1 <= current_y <= y2:
                if drag_target_index != i:
                    # Сбрасываем подсветку у предыдущего
                    if drag_target_index is not None:
                        prev_child = scrollable_frame.winfo_children()[drag_target_index]
                        prev_child.config(bg="#333333")
                        for widget in prev_child.winfo_children():
                            if isinstance(widget, (tk.Label, tk.Checkbutton)):
                                widget.config(bg="#333333")
                    drag_target_index = i
                    # Подсвечиваем место вставки (цвет ховера)
                    child.config(bg="#3a3a3a")
                    for widget in child.winfo_children():
                        if isinstance(widget, (tk.Label, tk.Checkbutton)):
                            widget.config(bg="#3a3a3a")
                break
            else:
                child.config(bg="#333333")
                for widget in child.winfo_children():
                    if isinstance(widget, (tk.Label, tk.Checkbutton)):
                        widget.config(bg="#333333")
    
    def on_release(event):
        nonlocal drag_start_index, drag_target_index, is_dragging, long_press_triggered, after_id
        
        # Сбрасываем подсветку всех строк
        for child in scrollable_frame.winfo_children():
            child.config(bg="#333333")
            for widget in child.winfo_children():
                if isinstance(widget, (tk.Label, tk.Checkbutton)):
                    widget.config(bg="#333333")
        
        # Отменяем таймер, если он ещё активен
        if after_id:
            root.after_cancel(after_id)
            after_id = None
        
        if is_dragging and drag_start_index is not None and drag_target_index is not None and drag_start_index != drag_target_index:
            # Переставляем в списке characters
            char = characters.pop(drag_start_index)
            characters.insert(drag_target_index, char)
            
            # Полностью обновляем список
            refresh_characters_list()
            
            # Сохраняем порядок
            save_characters_order(characters)
        elif not is_dragging and not long_press_triggered and drag_start_index is not None:
            # Это был клик, а не перетаскивание
            toggle_character(drag_start_index)
        
        drag_start_index = None
        drag_target_index = None
        is_dragging = False
        long_press_triggered = False
    
    def refresh_characters_list():
        """Полностью пересоздаёт список персонажей"""
        nonlocal checkbox_vars, selected_characters
        # Сохраняем позицию прокрутки
        yview = canvas.yview()
        # Очищаем списки
        checkbox_vars.clear()
        selected_characters.clear()
        # Очищаем scrollable_frame
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        # Заново отрисовываем всех персонажей
        for i, char in enumerate(characters):
            create_character_row(i, char)
        
        # Восстанавливаем позицию прокрутки
        canvas.yview_moveto(yview[0])

    def save_characters_order(characters_list):
        """Сохраняет новый порядок персонажей в профиль"""
        nonlocal profile
        if not profile:
            return
        profile["characters"] = characters_list
        profile_name = profiles.get("active_profile")
        if profile_name:
            update_profile(profile_name, profile, profiles)

    def create_character_row(i, char):
        char_frame = tk.Frame(
            scrollable_frame,
            bg="#333333",
            highlightthickness=0,
        )
        char_frame.pack(pady=5, padx=10, fill="x")
        char_frame.config(cursor="hand2")
        
        # Привязываем события для Drag & Drop и клика
        char_frame.bind("<Button-1>", lambda e, idx=i: on_press(e, idx))
        char_frame.bind("<B1-Motion>", on_motion)
        char_frame.bind("<ButtonRelease-1>", on_release)
        
        # При наведении — меняем цвет фона как в main_menu
        def on_enter(e, f=char_frame):
            if not is_dragging or i != drag_start_index:
                f.config(bg="#3a3a3a")
                for widget in f.winfo_children():
                    if isinstance(widget, (tk.Label, tk.Checkbutton)):
                        widget.config(bg="#3a3a3a")
        
        def on_leave(e, f=char_frame):
            if not is_dragging or i != drag_start_index:
                f.config(bg="#333333")
                for widget in f.winfo_children():
                    if isinstance(widget, (tk.Label, tk.Checkbutton)):
                        widget.config(bg="#333333")

        char_frame.bind("<Enter>", on_enter)
        char_frame.bind("<Leave>", on_leave)
        
        # Чекбокс (без command)
        var = tk.IntVar(value=1 if i in selected_characters else 0)
        checkbox_vars.append(var)
        
        check_button = tk.Checkbutton(
            char_frame, variable=var, font=("Helvetica", 12),
            bg="#333333", fg="#19e1a0", selectcolor="#222222",
            activebackground="#3a3a3a",  # Цвет при наведении на чекбокс
            highlightthickness=0
        )
        check_button.pack(side="left", padx=2)
        
        # Иконка класса
        icon_name = char.get("icon")
        icon_image = get_icon_image(icon_name)
        if icon_image:
            icon_label = tk.Label(char_frame, image=icon_image, bg="#333333")
            icon_label.pack(side="left", padx=0)
            frame.icon_images.append(icon_image)
        
        # Ник персонажа
        char_info = f"{char.get('char', '')}"
        char_label = tk.Label(char_frame, text=char_info, font=("Fixedsys", 12),
                 bg="#333333", fg="#dedede")
        char_label.pack(side="left", padx=5)
        
        # Кнопки
        buttons = [
            {"text": "❌", "command": lambda i=i: delete_character(i), "bg": "#424242", "fg": "#d42d52", "hover_bg": "#555555"},
            {"text": "✎", "command": lambda i=i: edit_character(i), "bg": "#424242", "fg": "#f39c12", "hover_bg": "#555555"},
            {"text": "▶", "command": lambda i=i: start_game_for_char(i), "bg": "#424242", "fg": "#19e1a0", "hover_bg": "#555555"}
        ]
        for button in buttons:
            btn = tk.Button(char_frame, text=button["text"], command=button["command"],
                            font=("Helvetica", 10, "bold"), bg=button["bg"], fg=button["fg"], relief="flat", highlightthickness=0)
            btn.pack(side="right", padx=5)
            
            # Кастомные события для кнопок с цветом при наведении
            def on_btn_enter(e, b=btn, bg=button["hover_bg"], fg=button["fg"]):
                b.config(bg=bg)
            
            def on_btn_leave(e, b=btn, bg=button["bg"], fg=button["fg"]):
                b.config(bg=bg)
            
            btn.bind("<Enter>", on_btn_enter)
            btn.bind("<Leave>", on_btn_leave)

    def create_character():
        # Новый персонаж создаётся только после сохранения в редакторе,
        # поэтому здесь не добавляем пустой объект в список
        add_character_menu(root, frame, None, profiles)
        
    header = tk.Label(frame, text="Персонажи", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=20)
    style.animate_text(header, "Персонажи", loop=True)
    
    button_frame = tk.Frame(frame, bg="#222222")
    button_frame.pack(pady=1, padx=5, fill="x")
    
    btn_select_all = tk.Button(button_frame, text="✅", command=select_all_characters, font=("Helvetica", 10), 
                               bg="#333333", fg="#19e1a0", relief="flat", highlightthickness=0)
    btn_select_all.pack(side="left", padx=7)
    btn_select_all.bind("<Enter>", lambda e: btn_select_all.config(bg="#3a3a3a"))
    btn_select_all.bind("<Leave>", lambda e: btn_select_all.config(bg="#333333"))
    
    def go_to_profile_menu():
        from ui.profile_menu import profile_menu
        profile_menu(root, frame, profiles)

    gear_btn = tk.Button(button_frame, text="⚙", command=go_to_profile_menu,
                        font=("Helvetica", 10, "bold"), bg="#333333", fg="#f39c12", relief="flat", highlightthickness=0)
    gear_btn.pack(side="left", padx=2)
    gear_btn.bind("<Enter>", lambda e: gear_btn.config(bg="#3a3a3a"))
    gear_btn.bind("<Leave>", lambda e: gear_btn.config(bg="#333333"))
    
    profile_label = tk.Label(button_frame, text=f"Профиль: {profile_name}", 
                             font=("Fixedsys", 16), bg="#222222", fg="#dedede")
    profile_label.pack(side="left", padx=5)

    # Область со скроллом для списка персонажей
    canvas = tk.Canvas(frame, bg="#222222", highlightthickness=0, borderwidth=0)
    canvas.config(background="#222222")
    canvas.configure(highlightthickness=0)
    scrollable_frame = tk.Frame(canvas, bg="#222222")
    
    # Создаём вложенный фрейм
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def _update_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _resize_inner(event):
        canvas.itemconfig(window_id, width=event.width)

    scrollable_frame.bind("<Configure>", _update_scrollregion)
    canvas.bind("<Configure>", _resize_inner)

    canvas.pack(pady=5, padx=2, fill="both", expand=True)

    # Глобальная прокрутка колёсиком по всему окну приложения
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
                image = image.resize((16, 16), Image.LANCZOS)
                img = ImageTk.PhotoImage(image)
            else:
                img = tk.PhotoImage(file=icon_path)
        except Exception:
            if icon_path.lower().endswith(".webp") and (Image is None or ImageTk is None) and not pillow_warning_shown["value"]:
                pillow_warning_shown["value"] = True
                messagebox.showwarning(
                    "Иконки классов",
                    "Для отображения иконок .webp установите пакет Pillow:\n\npip install pillow"
                )
            return None
        icon_cache[icon_name] = img
        return img

    # Создаём строки персонажей
    for i, char in enumerate(characters):
        create_character_row(i, char)

    button_frame_bottom = tk.Frame(frame, bg="#222222")
    button_frame_bottom.pack(pady=10, padx=10, fill="x")
    
    btn_run_selected = tk.Button(button_frame_bottom, text="▶ Запустить выбранных", command=start_selected_games, 
                                 font=("Helvetica", 10, "bold"), bg="#333333", fg="#dedede", relief="flat", highlightthickness=0)
    btn_run_selected.pack(side="left", padx=1)
    btn_run_selected.bind("<Enter>", lambda e: btn_run_selected.config(bg="#3a3a3a"))
    btn_run_selected.bind("<Leave>", lambda e: btn_run_selected.config(bg="#333333"))

    # Кнопки импорта/экспорта
    def import_profile():
        messagebox.showinfo("Импорт профиля", "Функция импорта будет добавлена позже")

    def export_profile():
        messagebox.showinfo("Экспорт профиля", "Функция экспорта будет добавлена позже")

    import_btn = tk.Button(button_frame_bottom, text="📥", command=import_profile,
                        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0", relief="flat", highlightthickness=0)
    import_btn.pack(side="left", padx=10, expand=True)
    import_btn.bind("<Enter>", lambda e: import_btn.config(bg="#3a3a3a"))
    import_btn.bind("<Leave>", lambda e: import_btn.config(bg="#333333"))

    export_btn = tk.Button(button_frame_bottom, text="📤", command=export_profile,
                        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0", relief="flat", highlightthickness=0)
    export_btn.pack(side="left", padx=10, expand=True)
    export_btn.bind("<Enter>", lambda e: export_btn.config(bg="#3a3a3a"))
    export_btn.bind("<Leave>", lambda e: export_btn.config(bg="#333333"))
    
    btn_add_character = tk.Button(button_frame_bottom, text="➕ Добавить", command=create_character, 
                                  font=("Helvetica", 10, "bold"), bg="#333333", fg="#dedede", relief="flat", highlightthickness=0)
    btn_add_character.pack(side="right", padx=1)
    btn_add_character.bind("<Enter>", lambda e: btn_add_character.config(bg="#3a3a3a"))
    btn_add_character.bind("<Leave>", lambda e: btn_add_character.config(bg="#333333"))
    
    btn_back = tk.Button(frame, text="Назад", command=lambda: navigate_to("Главная", root, frame, profiles),
                         font=("Helvetica", 11, "bold"), bg="#333333", fg="#d42d52", relief="flat", highlightthickness=0)
    btn_back.pack(pady=10)
    btn_back.bind("<Enter>", lambda e: btn_back.config(bg="#3a3a3a"))
    btn_back.bind("<Leave>", lambda e: btn_back.config(bg="#333333"))

    ToolTip(import_btn, "Импорт профиля")
    ToolTip(export_btn, "Экспорт профиля")