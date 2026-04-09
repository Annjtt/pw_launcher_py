import os
import tkinter as tk
from tkinter import messagebox, filedialog
import re
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None
from utils import StyleManager, get_active_profile, update_profile, get_icon_image

# Словарь соответствия имени файла и человеческого названия
ICON_LABELS = {
    "bard": "Бард",
    "dk": "Дух Крови",
    "dru": "Друид",
    "gan": "Стрелок",
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
    "var": "Воен",
}

def get_available_icons():
    """Возвращает список доступных иконок (label, filename)"""
    icon_dirs = [
        os.path.join("assets", "prof"),
        os.path.join("web", "assets", "prof"),
    ]
    available = []
    for icons_dir in icon_dirs:
        if os.path.isdir(icons_dir):
            for name in os.listdir(icons_dir):
                lower = name.lower()
                if lower.endswith((".png", ".gif", ".jpg", ".jpeg", ".webp")):
                    base = os.path.splitext(name)[0].lower()
                    label = ICON_LABELS.get(base, base.upper())
                    if (label, name) not in available:
                        available.append((label, name))
    available.sort(key=lambda x: x[0])
    return available

def import_from_bat_menu(root, frame, profiles):
    """Форма для импорта персонажа из BAT файла"""
    style = StyleManager()
    
    # Очищаем фрейм
    for widget in frame.winfo_children():
        widget.destroy()
    
    # Заголовок
    header = tk.Label(frame, text="Импорт из BAT файла", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=20)
    style.animate_text(header, "Импорт из BAT файла", loop=True)
    
    # Разделительная линия
    separator = tk.Frame(frame, height=2, bg="#333333")
    separator.pack(fill="x", padx=20, pady=5)
    
    # Распорка сверху
    spacer_top = tk.Frame(frame, height=40, bg="#222222")
    spacer_top.pack()
    
    # Переменные
    parsed_data = {"login": "", "password": "", "nickname": ""}
    icon_var = tk.StringVar(value="")
    icon_filename = tk.StringVar(value="")
    
    # Пути для иконок
    icon_dirs = [
        os.path.join("assets", "prof"),
        os.path.join("web", "assets", "prof"),
    ]
    
    # Функция парсинга BAT файла
    def parse_bat_file(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            user_match = re.search(r'user:([^\s]+)', content, re.IGNORECASE)
            pwd_match = re.search(r'pwd:([^\s]+)', content, re.IGNORECASE)
            role_match = re.search(r'role:([^\s]+)', content, re.IGNORECASE)
            
            if not user_match or not pwd_match:
                messagebox.showerror("Ошибка", "Не удалось найти логин и/или пароль в файле")
                return False
            
            parsed_data["login"] = user_match.group(1)
            parsed_data["password"] = pwd_match.group(1)
            parsed_data["nickname"] = role_match.group(1) if role_match else ""
            
            login_entry.config(state="normal")
            login_entry.delete(0, tk.END)
            login_entry.insert(0, parsed_data["login"])
            login_entry.config(state="readonly")
            
            password_entry.config(state="normal")
            password_entry.delete(0, tk.END)
            password_entry.insert(0, parsed_data["password"])
            password_entry.config(state="readonly")
            
            if parsed_data["nickname"]:
                nickname_entry.delete(0, tk.END)
                nickname_entry.insert(0, parsed_data["nickname"])
            
            messagebox.showinfo("Успех", f"Данные загружены из файла\nЛогин: {parsed_data['login']}\nНик: {parsed_data['nickname'] or 'не указан'}")
            return True
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл: {e}")
            return False
    
    # Выбор BAT файла
    def select_bat_file():
        file_path = filedialog.askopenfilename(
            title="Выберите BAT файл",
            filetypes=[("BAT files", "*.bat"), ("All files", "*.*")]
        )
        if not file_path:
            return
        parse_bat_file(file_path)
    
    # Функция обновления превью иконки
    def update_preview():
        label_value = icon_var.get()
        filename = label_to_file.get(label_value)
        if not filename:
            preview_label.config(image="", text="")
            icon_frame.preview_image = None
            icon_filename.set("")
            return
        icon_path = None
        for d in icon_dirs:
            candidate = os.path.join(d, filename)
            if os.path.isfile(candidate):
                icon_path = candidate
                break
        if not icon_path:
            preview_label.config(image="", text="")
            icon_frame.preview_image = None
            icon_filename.set("")
            return
        try:
            if icon_path.lower().endswith(".webp") and Image is not None and ImageTk is not None:
                image = Image.open(icon_path)
                image = image.resize((20, 20), Image.Resampling.LANCZOS)
                img = ImageTk.PhotoImage(image)
            else:
                img = tk.PhotoImage(file=icon_path)
        except Exception:
            preview_label.config(image="", text="")
            icon_frame.preview_image = None
            icon_filename.set("")
            return
        preview_label.config(image=img)
        icon_frame.preview_image = img
        icon_filename.set(filename)
    
    # Импорт персонажа
    def do_import():
        login = login_entry.get().strip()
        password = password_entry.get().strip()
        nickname = nickname_entry.get().strip()
        selected_icon = icon_filename.get() or None
        
        if not login or not password:
            messagebox.showerror("Ошибка", "Логин и пароль обязательны для заполнения")
            return
        
        if not nickname:
            from tkinter import simpledialog
            nickname = simpledialog.askstring("Имя персонажа", "Введите имя персонажа:", parent=frame)
            if not nickname:
                messagebox.showwarning("Предупреждение", "Имя персонажа обязательно")
                return
        
        profile = get_active_profile(profiles)
        if not profile:
            messagebox.showerror("Ошибка", "Нет активного профиля для импорта персонажа")
            return
        
        characters = profile.get("characters", [])
        existing_names = [c.get("char", "") for c in characters]
        if nickname in existing_names:
            messagebox.showerror("Ошибка", f"Персонаж с именем '{nickname}' уже существует в этом профиле")
            return
        
        new_character = {
            "acc": login,
            "pwd": password,
            "char": nickname,
            "icon": selected_icon
        }
        
        characters.append(new_character)
        profile["characters"] = characters
        update_profile(profiles["active_profile"], profile, profiles)
        
        messagebox.showinfo("Успех", f"Персонаж '{nickname}' успешно импортирован")
        
        for widget in frame.winfo_children():
            widget.destroy()
        frame.update_idletasks()
        from ui.character_menu import character_menu
        character_menu(root, frame, profiles)

    def go_back():
        for widget in frame.winfo_children():
            widget.destroy()
        from ui.character_menu import character_menu
        character_menu(root, frame, profiles)
    
    # ========== ИНТЕРФЕЙС ==========
    
    # Форма с данными (поля ввода)
    form_frame = tk.Frame(frame, bg="#222222")
    form_frame.pack(pady=20)
    
    # Логин
    tk.Label(form_frame, text="Логин:", font=("Helvetica", 11, "bold"), bg="#222222", fg="#dedede").grid(row=0, column=0, padx=5, pady=10, sticky="e")
    login_entry = tk.Entry(form_frame, font=("Fixedsys", 11), bg="#333333", fg="#dedede", width=25, relief="flat", state="readonly", readonlybackground="#333333")
    login_entry.grid(row=0, column=1, padx=5, pady=10)
    
    # Пароль
    tk.Label(form_frame, text="Пароль:", font=("Helvetica", 11, "bold"), bg="#222222", fg="#dedede").grid(row=1, column=0, padx=5, pady=10, sticky="e")
    password_entry = tk.Entry(form_frame, font=("Fixedsys", 11), bg="#333333", fg="#dedede", width=25, relief="flat", show="*", state="readonly", readonlybackground="#333333")
    password_entry.grid(row=1, column=1, padx=5, pady=10)
    
    # Ник
    tk.Label(form_frame, text="Ник персонажа:", font=("Helvetica", 11, "bold"), bg="#222222", fg="#dedede").grid(row=2, column=0, padx=5, pady=10, sticky="e")
    nickname_entry = tk.Entry(form_frame, font=("Fixedsys", 11), bg="#333333", fg="#dedede", width=25, relief="flat")
    nickname_entry.grid(row=2, column=1, padx=5, pady=10)
    
    # Чекбокс показать пароль
    show_password_var = tk.BooleanVar(value=False)
    def toggle_password():
        if show_password_var.get():
            password_entry.config(show="")
        else:
            password_entry.config(show="*")
    
    show_password_cb = tk.Checkbutton(
        form_frame, text="Показать пароль", variable=show_password_var, command=toggle_password,
        bg="#222222", fg="#19e1a0", selectcolor="#222222", activebackground="#222222",
        font=("Helvetica", 9)
    )
    show_password_cb.grid(row=3, column=1, padx=5, pady=10, sticky="w")
    
    # Блок выбора иконки
    tk.Label(form_frame, text="Иконка класса:", font=("Helvetica", 11, "bold"), 
             bg="#222222", fg="#dedede").grid(row=4, column=0, padx=5, pady=10, sticky="e")
    
    icon_frame = tk.Frame(form_frame, bg="#222222")
    icon_frame.grid(row=4, column=1, padx=5, pady=10, sticky="w")
    
    # Превью выбранной иконки
    preview_label = tk.Label(icon_frame, bg="#222222")
    preview_label.pack(side="left", padx=(0, 10))
    
    available_icons = get_available_icons()
    label_to_file = {label: filename for label, filename in available_icons}
    
    if available_icons:
        icon_menu_button = tk.Menubutton(
            icon_frame,
            textvariable=icon_var,
            font=("Helvetica", 10, "bold"),
            bg="#333333",
            fg="#dedede",
            relief="flat",
            highlightthickness=0
        )
        icon_menu = tk.Menu(icon_menu_button, tearoff=0, font=("Helvetica", 10, "bold"), 
                           bg="#222222", fg="#dedede")
        icon_menu_button.config(menu=icon_menu)
        icon_menu_button.pack(side="left", padx=5)
        
        icon_frame.menu_images = []
        
        for label, filename in available_icons:
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
                        image = image.resize((16, 16), Image.Resampling.LANCZOS)
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
        
        # Выбираем первую иконку по умолчанию
        if available_icons:
            icon_var.set(available_icons[0][0])
            update_preview()
    else:
        icon_var.set("")
        tk.Label(icon_frame, text="Иконки не найдены", font=("Helvetica", 9),
                bg="#222222", fg="#d42d52").pack(side="left")
    
    # Распорка между формой и инструкцией
    spacer_mid = tk.Frame(frame, height=20, bg="#222222")
    spacer_mid.pack()
    
    # Инструкция
    info_label = tk.Label(
        frame,
        text="💡 Выберите BAT файл → данные подгрузятся автоматически.\nУкажите ник персонажа (если не найден) и нажмите Импортировать.",
        font=("Helvetica", 9), bg="#222222", fg="#888888", justify="center", wraplength=380
    )
    info_label.pack(pady=15)
    
    # Распорка между инструкцией и кнопками
    spacer_bottom = tk.Frame(frame, height=30, bg="#222222")
    spacer_bottom.pack()
    
    # Кнопки
    btn_frame = tk.Frame(frame, bg="#222222")
    btn_frame.pack(pady=20, fill="x", side="bottom")
    
    btn_select_file = tk.Button(
        btn_frame, text="📂 Выбрать BAT файл", command=select_bat_file,
        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0",
        relief="flat", highlightthickness=0
    )
    btn_select_file.pack(side="left", padx=10, expand=True)
    btn_select_file.bind("<Enter>", lambda e: btn_select_file.config(bg="#3a3a3a"))
    btn_select_file.bind("<Leave>", lambda e: btn_select_file.config(bg="#333333"))
    
    btn_import = tk.Button(
        btn_frame, text="⬇️ Импортировать", command=do_import,
        font=("Helvetica", 11, "bold"), bg="#333333", fg="#dedede",
        relief="flat", highlightthickness=0
    )
    btn_import.pack(side="left", padx=10, expand=True)
    btn_import.bind("<Enter>", lambda e: btn_import.config(bg="#3a3a3a"))
    btn_import.bind("<Leave>", lambda e: btn_import.config(bg="#333333"))
    
    btn_back = tk.Button(
        btn_frame, text="← Назад", command=go_back,
        font=("Helvetica", 11, "bold"), bg="#333333", fg="#d42d52",
        relief="flat", highlightthickness=0
    )
    btn_back.pack(side="right", padx=10, expand=True)
    btn_back.bind("<Enter>", lambda e: btn_back.config(bg="#3a3a3a"))
    btn_back.bind("<Leave>", lambda e: btn_back.config(bg="#333333"))