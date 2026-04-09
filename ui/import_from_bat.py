import os
import tkinter as tk
from tkinter import messagebox, filedialog
import re
from utils import StyleManager, get_active_profile, update_profile

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
    
    # Импорт персонажа
    def do_import():
        login = login_entry.get().strip()
        password = password_entry.get().strip()
        nickname = nickname_entry.get().strip()
        
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
            "icon": None
        }
        
        characters.append(new_character)
        profile["characters"] = characters
        update_profile(profiles["active_profile"], profile, profiles)
        
        messagebox.showinfo("Успех", f"Персонаж '{nickname}' успешно импортирован")
        
        # 👇 ПРИНУДИТЕЛЬНЫЙ ПЕРЕХОД С ОЧИСТКОЙ
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
    
    tk.Label(form_frame, text="Логин:", font=("Helvetica", 11, "bold"), bg="#222222", fg="#dedede").grid(row=0, column=0, padx=5, pady=10, sticky="e")
    login_entry = tk.Entry(form_frame, font=("Fixedsys", 11), bg="#333333", fg="#dedede", width=25, relief="flat", state="readonly", readonlybackground="#333333")
    login_entry.grid(row=0, column=1, padx=5, pady=10)
    
    tk.Label(form_frame, text="Пароль:", font=("Helvetica", 11, "bold"), bg="#222222", fg="#dedede").grid(row=1, column=0, padx=5, pady=10, sticky="e")
    password_entry = tk.Entry(form_frame, font=("Fixedsys", 11), bg="#333333", fg="#dedede", width=25, relief="flat", show="*", state="readonly", readonlybackground="#333333")
    password_entry.grid(row=1, column=1, padx=5, pady=10)
    
    tk.Label(form_frame, text="Ник персонажа:", font=("Helvetica", 11, "bold"), bg="#222222", fg="#dedede").grid(row=2, column=0, padx=5, pady=10, sticky="e")
    nickname_entry = tk.Entry(form_frame, font=("Fixedsys", 11), bg="#333333", fg="#dedede", width=25, relief="flat")
    nickname_entry.grid(row=2, column=1, padx=5, pady=10)
    
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