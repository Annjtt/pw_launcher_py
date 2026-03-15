import tkinter as tk
from tkinter import messagebox, simpledialog
from utils import load_config, save_config, set_active_profile, delete_profile, update_profile, navigate_to, StyleManager

def profile_menu(root, frame, profiles):
    style = StyleManager()
    
    def create_new_profile():
        new_name = simpledialog.askstring("Имя профиля", "Введите имя нового профиля:")
        if new_name:
            profiles["profiles"][new_name] = {"game_path": "", "characters": []}
            set_active_profile(new_name, root, frame, profiles)
            update_profile(new_name, profiles["profiles"][new_name], profiles)
            profile_menu(root, frame, profiles)

    def edit_profile_name(old_name):
        new_name = simpledialog.askstring("Редактировать профиль", f"Новое имя для профиля '{old_name}':")
        if new_name and new_name != old_name:
            # Проверка на дубликат имени
            if new_name in profiles["profiles"]:
                messagebox.showerror("Ошибка", "Профиль с таким именем уже существует.")
                return
            # Копируем данные профиля
            profiles["profiles"][new_name] = profiles["profiles"].pop(old_name)
            # Обновим active_profile если редактируемый был активным
            if profiles.get("active_profile") == old_name:
                profiles["active_profile"] = new_name
            save_config(profiles)
            profile_menu(root, frame, profiles)

    def navigate_back():
        navigate_to("Главная", root, frame, profiles)
    
    for widget in frame.winfo_children():
        widget.destroy()
    
    header = tk.Label(frame, text="Управление профилем", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=20)
    style.animate_text(header, "Управление профилем", loop=True)
    
    if profiles["profiles"]:
        for profile_name in profiles["profiles"]:
            profile_frame = tk.Frame(frame, bg="#333333", borderwidth=4)
            profile_frame.pack(pady=5, padx=10, fill="x")
            tk.Label(profile_frame, text=profile_name, font=("Fixedsys", 10), bg="#333333", fg="#dedede").pack(side="left", padx=5)
            buttons = [
                {"text": "❌", "command": lambda name=profile_name: delete_profile(name, root, frame, profiles), "bg": "#424242", "fg": "#d42d52"},
                # Исправлено: кнопка ✎ теперь вызывает edit_profile_name
                {"text": "✎", "command": lambda name=profile_name: edit_profile_name(name), "bg": "#424242", "fg": "#f39c12"},
                {"text": "✅", "command": lambda name=profile_name: set_active_profile(name, root, frame, profiles), "bg": "#424242", "fg": "#19e1a0"}
            ]
            for button in buttons:
                btn = tk.Button(profile_frame, text=button["text"], command=button["command"], 
                                font=("Fixedsys", 10, "bold"), bg=button["bg"], fg=button["fg"], relief="flat")
                btn.pack(side="right", padx=7)
                btn.bind("<Enter>", style.on_hover)
                btn.bind("<Leave>", lambda event, bg=button["bg"], fg=button["fg"]: style.on_leave(event, bg, fg))
    else:
        tk.Label(frame, text="Нет созданных профилей", font=("Helvetica", 15, "bold"), bg="#222222", fg="#d42d52").pack(pady=15)
    btn_create_profile = tk.Button(frame, text="Создать новый профиль", command=create_new_profile,
                                   font=("Helvetica", 11, "bold"), bg="#333333", fg="#dedede", relief="flat")
    btn_create_profile.pack(pady=10)
    btn_create_profile.bind("<Enter>", style.on_hover)
    btn_create_profile.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#dedede"))
    
    btn_back = tk.Button(frame, text="Назад", command=navigate_back,
                         font=("Helvetica", 11, "bold"), bg="#333333", fg="#d42d52", relief="flat")
    btn_back.pack(pady=10)
    btn_back.bind("<Enter>", style.on_hover)
    btn_back.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#d42d52"))