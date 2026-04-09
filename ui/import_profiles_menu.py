import os
import tkinter as tk
from tkinter import messagebox, filedialog
import json
from utils import StyleManager, save_config

def import_profiles_menu(root, frame, profiles):
    """Форма для импорта профилей из внешнего JSON файла"""
    style = StyleManager()
    
    # Очищаем фрейм
    for widget in frame.winfo_children():
        widget.destroy()
    
    # Заголовок
    header = tk.Label(frame, text="Импорт профилей", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=20)
    style.animate_text(header, "Импорт профилей", loop=True)
    
    
    # Переменные
    imported_profiles = []
    profile_vars = {}
    selected_count_var = tk.StringVar(value="Выбрано: 0")
    
    # Функции для работы с чекбоксами
    def update_selected_count():
        count = sum(1 for var in profile_vars.values() if var.get())
        selected_count_var.set(f"Выбрано: {count}")
    
    def select_all():
        for var in profile_vars.values():
            var.set(True)
        update_selected_count()
    
    def deselect_all():
        for var in profile_vars.values():
            var.set(False)
        update_selected_count()
    
    # Фрейм с кнопками управления
    control_frame = tk.Frame(frame, bg="#222222")
    control_frame.pack(pady=10)
    
    btn_select_all = tk.Button(
        control_frame, text="✅ Выбрать все", command=select_all,
        font=("Helvetica", 10, "bold"), bg="#333333", fg="#19e1a0",
        relief="flat", highlightthickness=0
    )
    btn_select_all.pack(side="left", padx=5)
    btn_select_all.bind("<Enter>", lambda e: btn_select_all.config(bg="#3a3a3a"))
    btn_select_all.bind("<Leave>", lambda e: btn_select_all.config(bg="#333333"))
    
    btn_deselect_all = tk.Button(
        control_frame, text="❌ Снять все", command=deselect_all,
        font=("Helvetica", 10, "bold"), bg="#333333", fg="#d42d52",
        relief="flat", highlightthickness=0
    )
    btn_deselect_all.pack(side="left", padx=5)
    btn_deselect_all.bind("<Enter>", lambda e: btn_deselect_all.config(bg="#3a3a3a"))
    btn_deselect_all.bind("<Leave>", lambda e: btn_deselect_all.config(bg="#333333"))
    
    selected_label = tk.Label(
        control_frame, textvariable=selected_count_var,
        font=("Helvetica", 10, "bold"), bg="#222222", fg="#19e1a0"
    )
    selected_label.pack(side="left", padx=15)
    
    # Фрейм для списка профилей (с прокруткой)
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
    
    # Кнопка выбора файла
    def select_json_file():
        file_path = filedialog.askopenfilename(
            title="Выберите JSON файл с профилями",
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
            imported_profiles.clear()
            
            for profile_name, profile_data in data["profiles"].items():
                if profile_name in profiles["profiles"]:
                    continue
                
                imported_profiles.append({
                    "name": profile_name,
                    "data": profile_data
                })
                
                row = tk.Frame(scrollable_frame, bg="#333333")
                row.pack(pady=3, padx=10, fill="x")
                row.config(cursor="hand2")
                
                var = tk.BooleanVar(value=True)
                profile_vars[profile_name] = var
                
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
                
                characters_count = len(profile_data.get("characters", []))

                label = tk.Label(
                    row, text=profile_name, font=("Fixedsys", 11),
                    bg="#333333", fg="#dedede"
                )
                label.pack(side="left", padx=5)
                label.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
                
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
            
            if not imported_profiles:
                tk.Label(
                    scrollable_frame, 
                    text="Нет новых профилей для импорта (все уже существуют)",
                    font=("Helvetica", 11), bg="#222222", fg="#f39c12"
                ).pack(pady=20)
            else:
                import_btn.pack(side="left", padx=10)
                
        except json.JSONDecodeError:
            messagebox.showerror("Ошибка", "Неверный формат JSON файла")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")
    
    # Кнопка импорта выбранных профилей
    def do_import():
        selected = [p for p in imported_profiles if profile_vars.get(p["name"], tk.BooleanVar()).get()]
        
        if not selected:
            messagebox.showwarning("Предупреждение", "Не выбран ни один профиль для импорта")
            return
        
        for profile in selected:
            name = profile["name"]
            data = profile["data"]
            profiles["profiles"][name] = data
        
        save_config(profiles)
        messagebox.showinfo("Успех", f"Импортировано профилей: {len(selected)}")
        
        for widget in frame.winfo_children():
            widget.destroy()
        frame.update_idletasks()
        from ui.profile_menu import profile_menu
        profile_menu(root, frame, profiles)   

    # Кнопка назад
    def go_back():
        from ui.profile_menu import profile_menu
        profile_menu(root, frame, profiles)
    
    # Упаковываем canvas
    canvas.pack(pady=10, padx=10, fill="both", expand=True)
    
    # Инструкция
    info_label = tk.Label(
        frame, 
        text="Выберите JSON файл, содержащий профили.\nБудут показаны только новые профили (которых ещё нет в системе).",
        font=("Helvetica", 9), bg="#222222", fg="#888888", justify="center"
    )
    info_label.pack(pady=10)

    # Фрейм с основными кнопками
    btn_frame = tk.Frame(frame, bg="#222222")
    btn_frame.pack(pady=20, fill="x")
    
    btn_select_file = tk.Button(
        btn_frame, text="Выбрать JSON файл", command=select_json_file,
        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0",
        relief="flat", highlightthickness=0
    )
    btn_select_file.pack(side="left", padx=10, expand=True)
    btn_select_file.bind("<Enter>", lambda e: btn_select_file.config(bg="#3a3a3a"))
    btn_select_file.bind("<Leave>", lambda e: btn_select_file.config(bg="#333333"))
    
    import_btn = tk.Button(
        btn_frame, text="⬇️️️ Импортировать выбранные", command=do_import,
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