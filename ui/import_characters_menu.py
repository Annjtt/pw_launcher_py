import os
import tkinter as tk
from tkinter import messagebox, filedialog
import json
from utils import StyleManager, save_config, get_active_profile, get_icon_image

def import_characters_menu(root, frame, profiles):
    """Форма для импорта персонажей из внешнего JSON файла"""
    style = StyleManager()
    
    # Очищаем фрейм
    for widget in frame.winfo_children():
        widget.destroy()
    
    # Заголовок
    header = tk.Label(frame, text="Импорт персонажей", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=20)
    style.animate_text(header, "Импорт персонажей", loop=True)
    
    # Разделительная линия
    separator = tk.Frame(frame, height=2, bg="#333333")
    separator.pack(fill="x", padx=20, pady=5)
    
    # Переменные
    imported_characters = []
    profile_vars = {}
    char_vars = {}
    selected_profile = None
    current_characters = []
    selected_count_var = tk.StringVar(value="Выбрано персонажей: 0")
    
    # Функции для работы с чекбоксами
    def update_selected_count():
        count = sum(1 for var in char_vars.values() if var.get())
        selected_count_var.set(f"Выбрано персонажей: {count}")
    
    def select_all():
        for var in char_vars.values():
            var.set(True)
        update_selected_count()
    
    def deselect_all():
        for var in char_vars.values():
            var.set(False)
        update_selected_count()
    
    # Функция очистки списка персонажей
    def clear_characters_list():
        nonlocal current_characters, selected_profile
        current_characters = []
        selected_profile = None
        char_vars.clear()
        imported_characters.clear()
        
        for widget in scrollable_frame.winfo_children():
            if widget != scrollable_frame.winfo_children()[0]:
                widget.destroy()
        
        import_btn.pack_forget()
        selected_count_var.set("Выбрано персонажей: 0")
    
    def show_profile_characters(profile_name, profile_data, characters):
        nonlocal current_characters, selected_profile
        
        selected_profile = profile_name
        current_characters = characters
        
        # Очищаем список персонажей (оставляем только заголовок выбора профиля)
        for widget in scrollable_frame.winfo_children():
            if widget != scrollable_frame.winfo_children()[0]:
                widget.destroy()
        
        # Добавляем заголовок с персонажами
        tk.Label(
            scrollable_frame,
            text=f"Персонажи из профиля '{profile_name}':",
            font=("Helvetica", 11, "bold"), bg="#222222", fg="#19e1a0"
        ).pack(pady=(10, 5))
        
        # Фрейм для кнопок управления персонажами
        control_char_frame = tk.Frame(scrollable_frame, bg="#222222")
        control_char_frame.pack(pady=5)
        
        btn_select_all_chars = tk.Button(
            control_char_frame, text="✅ Выбрать всех", command=select_all,
            font=("Helvetica", 9, "bold"), bg="#333333", fg="#19e1a0",
            relief="flat", highlightthickness=0
        )
        btn_select_all_chars.pack(side="left", padx=5)
        btn_select_all_chars.bind("<Enter>", lambda e: btn_select_all_chars.config(bg="#3a3a3a"))
        btn_select_all_chars.bind("<Leave>", lambda e: btn_select_all_chars.config(bg="#333333"))
        
        btn_deselect_all_chars = tk.Button(
            control_char_frame, text="❌ Снять всех", command=deselect_all,
            font=("Helvetica", 9, "bold"), bg="#333333", fg="#d42d52",
            relief="flat", highlightthickness=0
        )
        btn_deselect_all_chars.pack(side="left", padx=5)
        btn_deselect_all_chars.bind("<Enter>", lambda e: btn_deselect_all_chars.config(bg="#3a3a3a"))
        btn_deselect_all_chars.bind("<Leave>", lambda e: btn_deselect_all_chars.config(bg="#333333"))
        
        # Счётчик персонажей
        selected_label = tk.Label(
            control_char_frame, textvariable=selected_count_var,
            font=("Helvetica", 10, "bold"), bg="#222222", fg="#19e1a0"
        )
        selected_label.pack(side="left", padx=15)
        
        char_vars.clear()
        imported_characters.clear()
        
        for idx, char in enumerate(characters):
            char_name = char.get("char", "Без имени")
            
            target_profile = get_active_profile(profiles)
            if target_profile:
                existing_names = [c.get("char", "") for c in target_profile.get("characters", [])]
                if char_name in existing_names:
                    continue
            
            row = tk.Frame(scrollable_frame, bg="#333333")
            row.pack(pady=2, padx=20, fill="x")
            row.config(cursor="hand2")
            
            var = tk.BooleanVar(value=True)
            char_vars[idx] = var
            
            def toggle_row(row_var=var):
                row_var.set(not row_var.get())
                update_selected_count()
            
            row.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
            
            cb = tk.Checkbutton(
                row, variable=var, bg="#333333", fg="#19e1a0",
                activebackground="#333333", selectcolor="#222222",
                highlightthickness=0,
                command=update_selected_count
            )
            cb.pack(side="left", padx=5)
            #cb.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
            
            # Иконка класса
            icon_name = char.get("icon")
            if icon_name:
                icon_img = get_icon_image(icon_name, (20, 20))
                if icon_img:
                    icon_label = tk.Label(row, image=icon_img, bg="#333333")
                    icon_label.image = icon_img
                    icon_label.pack(side="left", padx=2)
                    icon_label.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
            
            label = tk.Label(
                row, text=f"{char_name} (логин: {char.get('acc', '')})",
                font=("Fixedsys", 10), bg="#333333", fg="#dedede"
            )
            label.pack(side="left", padx=5)
            label.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
            
            imported_characters.append({
                "char": char,
                "profile_name": profile_name
            })
            
            # Ховер эффект
            def on_enter(e, r=row):
                r.config(bg="#3a3a3a")
                for w in r.winfo_children():
                    w.config(bg="#3a3a3a")
            
            def on_leave(e, r=row):
                r.config(bg="#333333")
                for w in r.winfo_children():
                    w.config(bg="#333333")
            
            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)
        
        update_selected_count()
        
        if not char_vars:
            tk.Label(
                scrollable_frame,
                text="Нет новых персонажей для импорта (все уже существуют в текущем профиле)",
                font=("Helvetica", 10), bg="#222222", fg="#f39c12"
            ).pack(pady=10)
        else:
            import_btn.pack(side="left", padx=10)
    
    # Функция выбора файла
    def select_json_file():
        nonlocal imported_characters, current_characters
        
        file_path = filedialog.askopenfilename(
            title="Выберите JSON файл с персонажами",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "profiles" not in data:
                messagebox.showerror("Ошибка", "Файл не содержит секции 'profiles'")
                return
            
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            profile_vars.clear()
            char_vars.clear()
            imported_characters.clear()
            current_characters = []
            selected_count_var.set("Выбрано персонажей: 0")
            
            tk.Label(
                scrollable_frame,
                text="Выберите профиль для импорта персонажей:",
                font=("Helvetica", 11, "bold"), bg="#222222", fg="#19e1a0"
            ).pack(pady=10)
            
            for profile_name, profile_data in data["profiles"].items():
                characters = profile_data.get("characters", [])
                if not characters:
                    continue
                
                row = tk.Frame(scrollable_frame, bg="#333333")
                row.pack(pady=3, padx=10, fill="x")
                row.config(cursor="hand2")
                
                var = tk.BooleanVar(value=False)
                profile_vars[profile_name] = var
                
                # Сохраняем значения для замыкания
                p_name = profile_name
                p_data = profile_data
                p_chars = characters
                
                # Функция переключения
                def toggle_profile(check_var=var, name=p_name, data=p_data, chars=p_chars):
                    check_var.set(not check_var.get())
                    if check_var.get():
                        show_profile_characters(name, data, chars)
                    else:
                        clear_characters_list()
                
                # Клик по строке
                row.bind("<Button-1>", lambda e, cv=var, n=p_name, d=p_data, c=p_chars: toggle_profile(cv, n, d, c))
                
                cb = tk.Checkbutton(
                    row, variable=var, bg="#333333", fg="#19e1a0",
                    activebackground="#333333", selectcolor="#222222",
                    highlightthickness=0,
                    command=lambda cv=var, n=p_name, d=p_data, c=p_chars: toggle_profile(cv, n, d, c)
                )
                cb.pack(side="left", padx=5)
                
                label = tk.Label(
                    row, text=f"{profile_name} (персонажей: {len(characters)})",
                    font=("Fixedsys", 11), bg="#333333", fg="#dedede"
                )
                label.pack(side="left", padx=5)
                label.bind("<Button-1>", lambda e, cv=var, n=p_name, d=p_data, c=p_chars: toggle_profile(cv, n, d, c))
                # Ховер эффект
                def on_enter(e, r=row):
                    r.config(bg="#3a3a3a")
                    for w in r.winfo_children():
                        w.config(bg="#3a3a3a")
                
                def on_leave(e, r=row):
                    r.config(bg="#333333")
                    for w in r.winfo_children():
                        w.config(bg="#333333")
                
                row.bind("<Enter>", on_enter)
                row.bind("<Leave>", on_leave)
            
            if not profile_vars:
                tk.Label(
                    scrollable_frame,
                    text="Нет профилей с персонажами в выбранном файле",
                    font=("Helvetica", 11), bg="#222222", fg="#f39c12"
                ).pack(pady=20)
            
        except json.JSONDecodeError:
            messagebox.showerror("Ошибка", "Неверный формат JSON файла")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")  
    # Кнопка импорта
    def do_import():
        if not selected_profile:
            messagebox.showwarning("Предупреждение", "Сначала выберите профиль из файла")
            return
        
        selected = [item for idx, item in enumerate(imported_characters) if char_vars.get(idx, tk.BooleanVar()).get()]
        
        if not selected:
            messagebox.showwarning("Предупреждение", "Не выбран ни один персонаж для импорта")
            return
        
        target_profile = get_active_profile(profiles)
        if not target_profile:
            messagebox.showerror("Ошибка", "Нет активного профиля для импорта персонажей")
            return
        
        if "characters" not in target_profile:
            target_profile["characters"] = []
        
        imported_count = 0
        for item in selected:
            char_data = item["char"].copy()
            existing_names = [c.get("char", "") for c in target_profile["characters"]]
            if char_data.get("char", "") not in existing_names:
                target_profile["characters"].append(char_data)
                imported_count += 1
        
        if imported_count > 0:
            from utils import update_profile
            update_profile(profiles["active_profile"], target_profile, profiles)
            messagebox.showinfo("Успех", f"Импортировано персонажей: {imported_count}")
        else:
            messagebox.showinfo("Информация", "Нет новых персонажей для импорта")
        
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
    
    # ========== СОЗДАНИЕ ИНТЕРФЕЙСА ==========
    
    # Фрейм для списка (с прокруткой)
    canvas = tk.Canvas(frame, bg="#222222", highlightthickness=0, borderwidth=0)
    scrollable_frame = tk.Frame(canvas, bg="#222222")
    
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
    def _update_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def _resize_inner(event):
        canvas.itemconfig(window_id, width=event.width)
    
    scrollable_frame.bind("<Configure>", _update_scrollregion)
    canvas.bind("<Configure>", _resize_inner)
    
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    root.bind_all("<MouseWheel>", _on_mousewheel)
    
    canvas.pack(pady=10, padx=10, fill="both", expand=True)
    
    # Инструкция
    info_label = tk.Label(
        frame,
        text="Выберите JSON файл → выберите профиль → отметьте персонажей для импорта\n(будут показаны только новые персонажи, которых ещё нет в текущем профиле)",
        font=("Helvetica", 9), bg="#222222", fg="#888888", justify="center", wraplength=380
    )
    info_label.pack(pady=10)
    
    # Фрейм с основными кнопками
    btn_frame = tk.Frame(frame, bg="#222222")
    btn_frame.pack(pady=20, fill="x")
    
    btn_select_file = tk.Button(
        btn_frame, text="📂 Выбрать JSON файл", command=select_json_file,
        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0",
        relief="flat", highlightthickness=0
    )
    btn_select_file.pack(side="left", padx=10, expand=True)
    btn_select_file.bind("<Enter>", lambda e: btn_select_file.config(bg="#3a3a3a"))
    btn_select_file.bind("<Leave>", lambda e: btn_select_file.config(bg="#333333"))
    
    import_btn = tk.Button(
        btn_frame, text="⬇️ Импортировать выбранных", command=do_import,
        font=("Helvetica", 11, "bold"), bg="#333333", fg="#dedede",
        relief="flat", highlightthickness=0
    )
    import_btn.pack(side="left", padx=10, expand=True)
    import_btn.bind("<Enter>", lambda e: import_btn.config(bg="#3a3a3a"))
    import_btn.bind("<Leave>", lambda e: import_btn.config(bg="#333333"))
    import_btn.pack_forget()
    
    btn_back = tk.Button(
        btn_frame, text="← Назад", command=go_back,
        font=("Helvetica", 11, "bold"), bg="#333333", fg="#d42d52",
        relief="flat", highlightthickness=0
    )
    btn_back.pack(side="right", padx=10, expand=True)
    btn_back.bind("<Enter>", lambda e: btn_back.config(bg="#3a3a3a"))
    btn_back.bind("<Leave>", lambda e: btn_back.config(bg="#333333"))