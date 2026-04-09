import tkinter as tk
from tkinter import messagebox, simpledialog
from utils import load_config, save_config, set_active_profile, delete_profile, update_profile, navigate_to, StyleManager
from ui.tooltip import ToolTip

def profile_menu(root, frame, profiles):
    style = StyleManager()
    
    # Очищаем фрейм
    for widget in frame.winfo_children():
        widget.destroy()
    
    # Заголовок
    header = tk.Label(frame, text="Управление профилем", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=20)
    style.animate_text(header, "Управление профилем", loop=True)
    
    # Область со скроллом
    canvas = tk.Canvas(frame, bg="#222222", highlightthickness=0, borderwidth=0)
    scrollable_frame = tk.Frame(canvas, bg="#222222")
    
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
    def _update_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def _resize_inner(event):
        canvas.itemconfig(window_id, width=event.width)
    
    scrollable_frame.bind("<Configure>", _update_scrollregion)
    canvas.bind("<Configure>", _resize_inner)
    
    # Прокрутка колёсиком
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    root.unbind_all("<MouseWheel>")
    root.bind_all("<MouseWheel>", _on_mousewheel)
    
    # Упаковываем canvas
    canvas.pack(pady=5, padx=10, fill="both", expand=True)

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
            if new_name in profiles["profiles"]:
                messagebox.showerror("Ошибка", "Профиль с таким именем уже существует.")
                return
            profiles["profiles"][new_name] = profiles["profiles"].pop(old_name)
            if profiles.get("active_profile") == old_name:
                profiles["active_profile"] = new_name
            save_config(profiles)
            profile_menu(root, frame, profiles)

    def navigate_back():
        navigate_to("Главная", root, frame, profiles)

    def select_and_activate_profile(name):
        """Выбирает профиль и сразу активирует его"""
        # Активируем профиль
        set_active_profile(name, root, frame, profiles)
        # Очищаем фрейм перед загрузкой персонажей
        for widget in frame.winfo_children():
            widget.destroy()
        # Запускаем меню персонажей
        from ui.character_menu import character_menu
        character_menu(root, frame, profiles)
    
    if profiles["profiles"]:
        for profile_name in profiles["profiles"]:
            profile_frame = tk.Frame(
                scrollable_frame,
                bg="#333333",
                highlightthickness=0,
            )
            profile_frame.pack(pady=5, padx=10, fill="x")
            profile_frame.profile_name = profile_name
            profile_frame.config(cursor="hand2")
            
            # Функция активации с фиксацией значения
            def activate(n=profile_name):
                select_and_activate_profile(n)
            
            # Клик по рамке
            profile_frame.bind("<Button-1>", lambda e, n=profile_name: select_and_activate_profile(n))
            
            # Название профиля
            name_label = tk.Label(profile_frame, text=profile_name, font=("Fixedsys", 12), bg="#333333", fg="#dedede")
            name_label.pack(side="left", padx=10)
            name_label.bind("<Button-1>", lambda e, n=profile_name: select_and_activate_profile(n))
            
            # Индикатор активного профиля
            if profiles.get("active_profile") == profile_name:
                active_label = tk.Label(profile_frame, text="✓", font=("Helvetica", 12, "bold"), 
                                        bg="#333333", fg="#19e1a0")
                active_label.pack(side="left", padx=5)
                active_label.bind("<Button-1>", lambda e, n=profile_name: select_and_activate_profile(n))
            
            # Кнопки: удалить и редактировать
            buttons = [
                {"text": "❌", "command": lambda n=profile_name: delete_profile(n, root, frame, profiles), 
                 "bg": "#424242", "fg": "#d42d52", "hover_bg": "#555555"},
                {"text": "✎", "command": lambda n=profile_name: edit_profile_name(n), 
                 "bg": "#424242", "fg": "#f39c12", "hover_bg": "#555555"},
            ]
            for button in buttons:
                btn = tk.Button(profile_frame, text=button["text"], command=button["command"], 
                                font=("Fixedsys", 10, "bold"), bg=button["bg"], fg=button["fg"], 
                                relief="flat", highlightthickness=0,  padx=6, pady=2, width=2)
                btn.pack(side="right", padx=7)
                
                # Кастомные события для кнопок
                def on_btn_enter(e, b=btn, bg=button["hover_bg"], fg=button["fg"]):
                    b.config(bg=bg)
                
                def on_btn_leave(e, b=btn, bg=button["bg"], fg=button["fg"]):
                    b.config(bg=bg)
                
                btn.bind("<Enter>", on_btn_enter)
                btn.bind("<Leave>", on_btn_leave)
    else:
        tk.Label(scrollable_frame, text="Нет созданных профилей", font=("Helvetica", 15, "bold"), 
                 bg="#222222", fg="#d42d52").pack(pady=15)
    
    # Кнопки внизу
    btn_frame = tk.Frame(frame, bg="#222222")
    btn_frame.pack(pady=20, fill="x")
    
    btn_create_profile = tk.Button(btn_frame, text="➕ Создать новый профиль", command=create_new_profile,
                                   font=("Helvetica", 11, "bold"), bg="#333333", fg="#dedede", 
                                   relief="flat", highlightthickness=0)
    btn_create_profile.pack(side="left", padx=10, expand=True)
    btn_create_profile.bind("<Enter>", lambda e: btn_create_profile.config(bg="#3a3a3a"))
    btn_create_profile.bind("<Leave>", lambda e: btn_create_profile.config(bg="#333333"))
    
    # Кнопки импорта/экспорта
    def import_profile():
        from ui.import_profiles_menu import import_profiles_menu
        import_profiles_menu(root, frame, profiles)

    def export_profile():
        from ui.export_profiles_menu import export_profiles_menu
        export_profiles_menu(root, frame, profiles)

    import_btn = tk.Button(btn_frame, text=" ⬇ ", command=import_profile,
                        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0", 
                        relief="flat", highlightthickness=0)
    import_btn.pack(side="left", padx=10, expand=True)
    import_btn.bind("<Enter>", lambda e: import_btn.config(bg="#3a3a3a"))
    import_btn.bind("<Leave>", lambda e: import_btn.config(bg="#333333"))

    export_btn = tk.Button(btn_frame, text=" ⬆ ", command=export_profile,
                        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0", 
                        relief="flat", highlightthickness=0)
    export_btn.pack(side="left", padx=10, expand=True)
    export_btn.bind("<Enter>", lambda e: export_btn.config(bg="#3a3a3a"))
    export_btn.bind("<Leave>", lambda e: export_btn.config(bg="#333333"))
    
    btn_back = tk.Button(btn_frame, text="← Назад", command=navigate_back,
                         font=("Helvetica", 11, "bold"), bg="#333333", fg="#d42d52", 
                         relief="flat", highlightthickness=0)
    btn_back.pack(side="right", padx=10, expand=True)
    btn_back.bind("<Enter>", lambda e: btn_back.config(bg="#3a3a3a"))
    btn_back.bind("<Leave>", lambda e: btn_back.config(bg="#333333"))

    ToolTip(import_btn, "Импорт профиля")
    ToolTip(export_btn, "Экспорт профиля")