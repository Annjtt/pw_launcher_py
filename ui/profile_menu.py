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
                highlightthickness=1,
                highlightbackground="#333333",
                highlightcolor="#19e1a0"
            )
            profile_frame.pack(pady=5, padx=10, fill="x")
            profile_frame.profile_name = profile_name
            profile_frame.config(cursor="hand2")
            
            # Клик по рамке активирует профиль
            profile_frame.bind("<Button-1>", lambda e, n=profile_name: select_and_activate_profile(n))
            
            # Подсветка при наведении (без сохранения выбора)
            def on_enter(e, f=profile_frame):
                f.config(highlightbackground="#19e1a0")
            
            def on_leave(e, f=profile_frame):
                f.config(highlightbackground="#333333")
            
            profile_frame.bind("<Enter>", on_enter)
            profile_frame.bind("<Leave>", on_leave)
            
            # Название профиля
            name_label = tk.Label(profile_frame, text=profile_name, font=("Fixedsys", 12), bg="#333333", fg="#dedede")
            name_label.pack(side="left", padx=10)
            name_label.bind("<Button-1>", lambda e, n=profile_name: select_and_activate_profile(n))
            
            # Индикатор активного профиля
            if profiles.get("active_profile") == profile_name:
                active_label = tk.Label(profile_frame, text="✓", font=("Helvetica", 12, "bold"), 
                                        bg="#333333", fg="#19e1a0")
                active_label.pack(side="left", padx=5)
            
            # Кнопки: удалить и редактировать
            buttons = [
                {"text": "❌", "command": lambda n=profile_name: delete_profile(n, root, frame, profiles), 
                 "bg": "#424242", "fg": "#d42d52"},
                {"text": "✎", "command": lambda n=profile_name: edit_profile_name(n), 
                 "bg": "#424242", "fg": "#f39c12"},
            ]
            for button in buttons:
                btn = tk.Button(profile_frame, text=button["text"], command=button["command"], 
                                font=("Fixedsys", 10, "bold"), bg=button["bg"], fg=button["fg"], relief="flat")
                btn.pack(side="right", padx=7)
                btn.bind("<Enter>", style.on_hover)
                btn.bind("<Leave>", lambda e, bg=button["bg"], fg=button["fg"]: style.on_leave(e, bg, fg))
    else:
        tk.Label(scrollable_frame, text="Нет созданных профилей", font=("Helvetica", 15, "bold"), 
                 bg="#222222", fg="#d42d52").pack(pady=15)
    
    # Кнопки внизу
    btn_frame = tk.Frame(frame, bg="#222222")
    btn_frame.pack(pady=20, fill="x")
    
    btn_create_profile = tk.Button(btn_frame, text="➕ Создать новый профиль", command=create_new_profile,
                                   font=("Helvetica", 11, "bold"), bg="#333333", fg="#dedede", relief="flat")
    btn_create_profile.pack(side="left", padx=10, expand=True)
    btn_create_profile.bind("<Enter>", style.on_hover)
    btn_create_profile.bind("<Leave>", lambda e: style.on_leave(e, "#333333", "#dedede"))
    # Кнопки импорта/экспорта
    def import_profile():
        # TODO: логика импорта профиля
        messagebox.showinfo("Импорт профиля", "Функция импорта будет добавлена позже")

    def export_profile():
        # TODO: логика экспорта профиля
        messagebox.showinfo("Экспорт профиля", "Функция экспорта будет добавлена позже")

    import_btn = tk.Button(btn_frame, text="📥", command=import_profile,
                        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0", relief="flat")
    import_btn.pack(side="left", padx=10, expand=True)
    import_btn.bind("<Enter>", style.on_hover)
    import_btn.bind("<Leave>", lambda e: style.on_leave(e, "#333333", "#19e1a0"))

    export_btn = tk.Button(btn_frame, text="📤", command=export_profile,
                        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0", relief="flat")
    export_btn.pack(side="left", padx=10, expand=True)
    export_btn.bind("<Enter>", style.on_hover)
    export_btn.bind("<Leave>", lambda e: style.on_leave(e, "#333333", "#19e1a0"))
    
    btn_back = tk.Button(btn_frame, text="← Назад", command=navigate_back,
                         font=("Helvetica", 11, "bold"), bg="#333333", fg="#d42d52", relief="flat")
    btn_back.pack(side="right", padx=10, expand=True)
    btn_back.bind("<Enter>", style.on_hover)
    btn_back.bind("<Leave>", lambda e: style.on_leave(e, "#333333", "#d42d52"))

    ToolTip(import_btn, "Импорт профиля")
    ToolTip(export_btn, "Экспорт профиля")