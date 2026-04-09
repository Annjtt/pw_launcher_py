import os
import tkinter as tk
from tkinter import messagebox, filedialog
import json
from datetime import datetime
from utils import StyleManager, get_active_profile, get_icon_image

def export_characters_menu(root, frame, profiles):
    """Форма для экспорта выбранных персонажей в JSON файл"""
    style = StyleManager()
    
    # Очищаем фрейм
    for widget in frame.winfo_children():
        widget.destroy()
    
    # Заголовок
    header = tk.Label(frame, text="Экспорт персонажей", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=20)
    style.animate_text(header, "Экспорт персонажей", loop=True)
        
    
    # Получаем активный профиль и его персонажей
    profile = get_active_profile(profiles)
    if not profile:
        messagebox.showerror("Ошибка", "Нет активного профиля для экспорта персонажей")
        from ui.profile_menu import profile_menu
        profile_menu(root, frame, profiles)
        return
    
    characters = profile.get("characters", [])
    if not characters:
        messagebox.showwarning("Предупреждение", "В активном профиле нет персонажей для экспорта")
        from ui.character_menu import character_menu
        character_menu(root, frame, profiles)
        return
    
    # Переменные
    char_vars = {}
    selected_count_var = tk.StringVar(value="Выбрано: 0")
    
    # Функции для работы с чекбоксами
    def update_selected_count():
        count = sum(1 for var in char_vars.values() if var.get())
        selected_count_var.set(f"Выбрано: {count}")
    
    def select_all():
        for var in char_vars.values():
            var.set(True)
        update_selected_count()
    
    def deselect_all():
        for var in char_vars.values():
            var.set(False)
        update_selected_count()
    
    # Фрейм с кнопками управления
    control_frame = tk.Frame(frame, bg="#222222")
    control_frame.pack(pady=10)
    
    btn_select_all = tk.Button(
        control_frame, text="✅ Выбрать всех", command=select_all,
        font=("Helvetica", 10, "bold"), bg="#333333", fg="#19e1a0",
        relief="flat", highlightthickness=0
    )
    btn_select_all.pack(side="left", padx=5)
    btn_select_all.bind("<Enter>", lambda e: btn_select_all.config(bg="#3a3a3a"))
    btn_select_all.bind("<Leave>", lambda e: btn_select_all.config(bg="#333333"))
    
    btn_deselect_all = tk.Button(
        control_frame, text="❌ Снять всех", command=deselect_all,
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
    
    # Фрейм для списка персонажей (с прокруткой)
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
    
    # Заполняем список персонажей
    for idx, char in enumerate(characters):
        row = tk.Frame(scrollable_frame, bg="#333333")
        row.pack(pady=3, padx=10, fill="x")
        row.config(cursor="hand2")
        
        var = tk.BooleanVar(value=False)
        char_vars[idx] = var
        
        def toggle_row(row_var=var):
            row_var.set(not row_var.get())
            update_selected_count()
        
        # Привязываем клик к САМОЙ СТРОКЕ
        row.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
        
        cb = tk.Checkbutton(
            row, variable=var, bg="#333333", fg="#19e1a0",
            activebackground="#333333", selectcolor="#222222",
            highlightthickness=0,
            command=update_selected_count
        )
        cb.pack(side="left", padx=5)
        # Привязываем клик к ЧЕКБОКСУ
        #cb.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
        
        # Иконка класса
        icon_name = char.get("icon")
        if icon_name:
            icon_img = get_icon_image(icon_name, (20, 20))
            if icon_img:
                icon_label = tk.Label(row, image=icon_img, bg="#333333")
                icon_label.image = icon_img  # сохраняем ссылку
                icon_label.pack(side="left", padx=2)
                icon_label.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
            else:
                # если иконка не загрузилась, показываем эмодзи
                icon_label = tk.Label(row, text="🎭", font=("Helvetica", 10),
                                      bg="#333333", fg="#19e1a0")
                icon_label.pack(side="left", padx=2)
                icon_label.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
            # Привязываем клик к ИКОНКЕ
            icon_label.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
        
        label = tk.Label(
            row,
            text=f"{char.get('char', 'Без имени')} (логин: {char.get('acc', '')})",
            font=("Fixedsys", 11), bg="#333333", fg="#dedede"
        )
        label.pack(side="left", padx=5)
        # Привязываем клик к ЛЕЙБЛУ
        label.bind("<Button-1>", lambda e, rv=var: toggle_row(rv))
        
        # Ховер эффект для строки и всех дочерних виджетов
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
    
    # Упаковываем canvas
    canvas.pack(pady=10, padx=10, fill="both", expand=True)
    
    # Инструкция
    info_label = tk.Label(
        frame, 
        text="Выберите персонажей для экспорта.\nБудут сохранены все данные (логин, пароль, иконка и т.д.)",
        font=("Helvetica", 9), bg="#222222", fg="#888888", justify="center"
    )
    info_label.pack(pady=10)
    
    # Функция экспорта
    def do_export():
        selected = [(idx, char) for idx, char in enumerate(characters) if char_vars.get(idx, tk.BooleanVar()).get()]
        
        if not selected:
            messagebox.showwarning("Предупреждение", "Не выбран ни один персонаж для экспорта")
            return
        
        export_data = {
            "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_profile": profiles.get("active_profile", "unknown"),
            "profiles": {
                profiles.get("active_profile", "unknown"): {
                    "characters": [char for _, char in selected]
                }
            }
        }
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить персонажей как",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="characters_export.json"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("Успех", f"Экспортировано персонажей: {len(selected)}\nСохранено в: {file_path}")
            
            for widget in frame.winfo_children():
                widget.destroy()
            frame.update_idletasks()
            from ui.character_menu import character_menu
            character_menu(root, frame, profiles)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    def go_back():
        for widget in frame.winfo_children():
            widget.destroy()
        from ui.character_menu import character_menu
        character_menu(root, frame, profiles)
    
    # Фрейм с основными кнопками
    btn_frame = tk.Frame(frame, bg="#222222")
    btn_frame.pack(pady=20, fill="x")
    
    btn_export = tk.Button(
        btn_frame, text="⬆ Экспорт выбранных", command=do_export,
        font=("Helvetica", 11, "bold"), bg="#333333", fg="#19e1a0",
        relief="flat", highlightthickness=0
    )
    btn_export.pack(side="left", padx=10, expand=True)
    btn_export.bind("<Enter>", lambda e: btn_export.config(bg="#3a3a3a"))
    btn_export.bind("<Leave>", lambda e: btn_export.config(bg="#333333"))
    
    btn_back = tk.Button(
        btn_frame, text="← Назад", command=go_back,
        font=("Helvetica", 11, "bold"), bg="#333333", fg="#d42d52",
        relief="flat", highlightthickness=0
    )
    btn_back.pack(side="right", padx=10, expand=True)
    btn_back.bind("<Enter>", lambda e: btn_back.config(bg="#3a3a3a"))
    btn_back.bind("<Leave>", lambda e: btn_back.config(bg="#333333"))