import os
import tkinter as tk
from tkinter import messagebox
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None
from utils import get_active_profile, update_profile, navigate_to, StyleManager


def add_character_menu(root, frame, index, profiles):
    style = StyleManager()
    profile = get_active_profile(profiles)
    if not profile:
        messagebox.showerror("Ошибка", "Активный профиль не выбран!")
        return
    characters = profile.get("characters", [])

    # Человеческие названия классов по имени файла (без расширения)
    icon_labels_map = {
        "bard": "Бард",
        "dk": "ДК",
        "dru": "Друид",
        "gan": "Ганнер",
        "gost": "Призрак",
        "kosa": "Жнец",
        "luk": "Лучник",
        "mag": "Маг",
        "mist": "Мистик",
        "mk": "Странник",
        "pal": "Паладин",
        "prist": "Прист",
        "sham": "Шаман",
        "sik": "Сикер",
        "sin": "Син",
        "tank": "Танк",
        "var": "Вар",
    }

    # Ищем иконки в нескольких стандартных путях
    icon_dirs = [
        os.path.join("assets", "prof"),
        os.path.join("web", "assets", "prof"),
    ]
    # список (label, filename)
    available_icons = []
    for icons_dir in icon_dirs:
        if os.path.isdir(icons_dir):
            for name in os.listdir(icons_dir):
                lower = name.lower()
                if lower.endswith((".png", ".gif", ".jpg", ".jpeg", ".webp")):
                    base = os.path.splitext(name)[0].lower()
                    label = icon_labels_map.get(base, base.upper())
                    if (label, name) not in available_icons:
                        available_icons.append((label, name))
    # сортируем по человекочитаемым названиям
    available_icons.sort(key=lambda x: x[0])

    char = characters[index] if index is not None else {"acc": "", "pwd": "", "char": "", "icon": None}

    # Сопоставление label -> filename для сохранения
    label_to_file = {label: filename for label, filename in available_icons}

    current_icon_file = char.get("icon")
    if current_icon_file and current_icon_file in label_to_file.values():
        # ищем label по сохранённому имени файла
        current_label = next(
            (label for label, filename in available_icons if filename == current_icon_file),
            available_icons[0][0] if available_icons else ""
        )
    else:
        current_label = available_icons[0][0] if available_icons else ""

    icon_var = tk.StringVar(value=current_label)
    
    def save_character():
        char.update({
            "acc": acc_entry.get(),
            "pwd": pwd_entry.get(),
            "char": char_entry.get(),
            # сохраняем именно имя файла, а не label
            "icon": label_to_file.get(icon_var.get()) if icon_var.get() in label_to_file else None,
        })
        if index is None:
            characters.append(char)
        profile["characters"] = characters
        update_profile(profiles["active_profile"], profile, profiles)
        from ui.character_menu import character_menu
        character_menu(root, frame, profiles)
    
    def toggle_password_visibility():
        if pwd_entry.cget('show') == '*':
            pwd_entry.config(show='')  # Показываем пароль
        else:
            pwd_entry.config(show='*')  # Скрываем пароль

    for widget in frame.winfo_children():
        widget.destroy()
    
    header = tk.Label(frame, text="Редактор персонажа", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=35)
    style.animate_text(header, "Редактор персонажа", loop=True)
    
    fields = [("Логин", "acc"), ("Пароль", "pwd"), ("Имя персонажа", "char")]
    entries = {}
    for label, key in fields:
        tk.Label(frame, text=label, font=("Helvetica", 12, "bold"), bg="#222222", fg="#dedede").pack(pady=7)
        
        if key == "pwd":  # Специальное поле для пароля с маскировкой и чекбоксом
            # Фрейм для объединения поля ввода и чекбокса в одну строку
            pwd_frame = tk.Frame(frame, bg="#222222")
            pwd_frame.pack(pady=5)
            
            # Поле ввода пароля
            entry = tk.Entry(pwd_frame, font=("Fixedsys", 12), bg="#333333", fg="#dedede", show="*", width=23)  # show="*" скрывает пароль
            entry.insert(0, char.get(key, ""))
            entry.pack(side="left", padx=(40, 1), pady=3)
            
            # Чекбокс для отображения пароля ◎ ◉ 
            toggle_pwd_btn = tk.Checkbutton(pwd_frame, command=toggle_password_visibility, 
                                            font=("Helvetica", 12), bg="#222222", fg="#19e1a0", 
                                            selectcolor="#333333", activebackground="#222222", activeforeground="#19e1a0",
                                            relief="flat")
            toggle_pwd_btn.pack(side="left", padx=5)
        
        else:
            entry = tk.Entry(frame, font=("Helvetica", 12), bg="#333333", fg="#dedede")
            entry.insert(0, char.get(key, ""))
            entry.pack(pady=5)
        
        entries[key] = entry
    
    acc_entry = entries.get("acc", tk.Entry())
    pwd_entry = entries.get("pwd", tk.Entry())
    char_entry = entries.get("char", tk.Entry())

    # Блок выбора иконки персонажа
    tk.Label(frame, text="Иконка класса", font=("Helvetica", 12, "bold"), bg="#222222", fg="#dedede").pack(pady=7)
    icon_frame = tk.Frame(frame, bg="#222222")
    icon_frame.pack(pady=5)

    # Превью выбранной иконки
    preview_label = tk.Label(icon_frame, bg="#222222")
    preview_label.pack(side="left", padx=(0, 10))

    # Вспомогательная функция для обновления превью
    icon_frame.preview_image = None

    def update_preview(*_args):
        label_value = icon_var.get()
        filename = label_to_file.get(label_value)
        if not filename:
            preview_label.config(image="", text="")
            icon_frame.preview_image = None
            return
        # Пытаемся найти файл в одном из каталогов
        icon_path = None
        for d in icon_dirs:
            candidate = os.path.join(d, filename)
            if os.path.isfile(candidate):
                icon_path = candidate
                break
        if not icon_path:
            preview_label.config(image="", text="")
            icon_frame.preview_image = None
            return
        try:
            if icon_path.lower().endswith(".webp") and Image is not None and ImageTk is not None:
                image = Image.open(icon_path)
                # небольшой размер, чтобы не перетягивать внимание
                image = image.resize((20, 20), Image.LANCZOS)
                img = ImageTk.PhotoImage(image)
            else:
                img = tk.PhotoImage(file=icon_path)
        except Exception:
            preview_label.config(image="", text="")
            icon_frame.preview_image = None
            return
        preview_label.config(image=img)
        icon_frame.preview_image = img

    if available_icons:
        # собственный выпадающий список, чтобы в нём тоже были иконки
        icon_menu_button = tk.Menubutton(
            icon_frame,
            textvariable=icon_var,
            font=("Helvetica", 12, "bold"),
            bg="#333333",
            fg="#dedede",
            relief="flat",
            highlightthickness=0
        )
        icon_menu = tk.Menu(icon_menu_button, tearoff=0, font=("Helvetica", 10, "bold"), bg="#222222", fg="#dedede")
        icon_menu_button.config(menu=icon_menu)
        icon_menu_button.pack(side="left", padx=5)

        # храним ссылки на изображения, чтобы их не съел GC
        icon_frame.menu_images = []

        for label, filename in available_icons:
            # грузим маленькую иконку для пункта меню
            icon_path = None
            for d in icon_dirs:
                candidate = os.path.join(d, filename)
                if os.path.isfile(candidate):
                    icon_path = candidate
                    break
            img = None
            if icon_path:
                try:
                    if icon_path.lower().endswith(".webp") and Image is not None and ImageTk is not None:
                        image = Image.open(icon_path)
                        image = image.resize((16, 16), Image.LANCZOS)
                        img = ImageTk.PhotoImage(image)
                    else:
                        img = tk.PhotoImage(file=icon_path)
                except Exception:
                    img = None
            icon_frame.menu_images.append(img)
            icon_menu.add_command(
                label=label,
                image=img if img is not None else "",
                compound="left",
                command=lambda v=label: (icon_var.set(v), update_preview())
            )

        # Инициализируем превью текущего значения
        update_preview()
    else:
        icon_var.set("")
        tk.Label(
            icon_frame,
            text="Иконки не найдены (папка assets/prof или web/assets/prof пуста)",
            font=("Helvetica", 9),
            bg="#222222",
            fg="#d42d52",
        ).pack(padx=5)
    
    save_btn = tk.Button(frame, text="Сохранить", command=save_character, font=("Helvetica", 11, "bold"), bg="#333333", fg="#dedede", relief="flat")
    save_btn.pack(pady=20)
    save_btn.bind("<Enter>", style.on_hover)
    save_btn.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#dedede"))
    
    back_btn = tk.Button(frame, text="Назад", command=lambda: navigate_to("Персонажи", root, frame, profiles),
                         font=("Helvetica", 11, "bold"), bg="#333333", fg="#d42d52", relief="flat")
    back_btn.pack(pady=10)
    back_btn.bind("<Enter>", style.on_hover)
    back_btn.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#d42d52"))