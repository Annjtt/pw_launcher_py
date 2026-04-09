import os
import tkinter as tk
from tkinter import messagebox, filedialog
import json
from datetime import datetime
from utils import StyleManager

def export_profiles_menu(root, frame, profiles):
    """Форма для экспорта выбранных профилей в JSON файл"""
    style = StyleManager()
    
    # Очищаем фрейм
    for widget in frame.winfo_children():
        widget.destroy()
    
    # Заголовок
    header = tk.Label(frame, text="Экспорт профилей", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=20)
    style.animate_text(header, "Экспорт профилей", loop=True)
    
    # Разделительная линия
    separator = tk.Frame(frame, height=2, bg="#333333")
    separator.pack(fill="x", padx=20, pady=5)
    
    # Переменные
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
    
    # Функция экспорта
    def do_export():
        selected = [(name, data) for name, data in profiles["profiles"].items() 
                    if profile_vars.get(name, tk.BooleanVar()).get()]
        
        if not selected:
            messagebox.showwarning("Предупреждение", "Не выбран ни один профиль для экспорта")
            return
        
        export_data = {
            "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_file": "config.json",
            "profiles": {}
        }
        
        for name, data in selected:
            export_data["profiles"][name] = data
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить профили как",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="profiles_export.json"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("Успех", f"Экспортировано профилей: {len(selected)}\nСохранено в: {file_path}")
            
            # 👇 ПРИНУДИТЕЛЬНЫЙ ПЕРЕХОД С ОЧИСТКОЙ
            for widget in frame.winfo_children():
                widget.destroy()
            frame.update_idletasks()
            from ui.profile_menu import profile_menu
            profile_menu(root, frame, profiles)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    # Кнопка назад
    def go_back():
        from ui.profile_menu import profile_menu
        profile_menu(root, frame, profiles)
    
    # Заполняем список профилей
    if not profiles.get("profiles"):
        tk.Label(
            scrollable_frame, 
            text="Нет доступных профилей для экспорта",
            font=("Helvetica", 14, "bold"), bg="#222222", fg="#d42d52"
        ).pack(pady=20)
    else:
        for profile_name, profile_data in profiles["profiles"].items():
            row = tk.Frame(scrollable_frame, bg="#333333")
            row.pack(pady=3, padx=10, fill="x")
            row.config(cursor="hand2")
            
            var = tk.BooleanVar(value=False)
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
            
            # 👇 ПЕРЕМЕННАЯ ДОЛЖНА БЫТЬ ОПРЕДЕЛЕНА ДО ИСПОЛЬЗОВАНИЯ
            characters_count = len(profile_data.get("characters", []))
            
            label = tk.Label(
                row, 
                text=f"{profile_name} (персонажей: {characters_count})", 
                font=("Fixedsys", 11),
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
            
            characters_count = len(profile_data.get("characters", []))
            
            label = tk.Label(
                row, 
                text=f"{profile_name} (персонажей: {characters_count})", 
                font=("Fixedsys", 11),
                bg="#333333", fg="#dedede"
            )
            label.pack(side="left", padx=5)
    
    # Упаковываем canvas
    canvas.pack(pady=10, padx=10, fill="both", expand=True)
    
    # Инструкция
    info_label = tk.Label(
        frame, 
        text="Выберите профили для экспорта.\nБудут сохранены все данные профилей (персонажи, настройки и т.д.)",
        font=("Helvetica", 9), bg="#222222", fg="#888888", justify="center"
    )
    info_label.pack(pady=10)

    # Фрейм с основными кнопками
    btn_frame = tk.Frame(frame, bg="#222222")
    btn_frame.pack(pady=20, fill="x")
    
    btn_export = tk.Button(
        btn_frame, text="📤 Экспортировать выбранные", command=do_export,
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
    
    