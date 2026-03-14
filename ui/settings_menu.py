import os
import tkinter as tk
from tkinter import messagebox, filedialog
from utils import get_active_profile, update_profile, open_telegram_channel, open_telegram, navigate_to, StyleManager

def settings_menu(root, frame, profiles):
    style = StyleManager()
    profile = get_active_profile(profiles)
    if not profile:
        messagebox.showerror("Ошибка", "Активный профиль не выбран!")
        return
    
    def browse_file():
        file_path = filedialog.askopenfilename(
            title="Выбрать файл игры",
            filetypes=[("Executable files", "*.exe")]
        )
        if file_path:
            game_path_entry.delete(0, tk.END)
            game_path_entry.insert(0, file_path)
    
    def save_settings():
        profile = get_active_profile(profiles)
        if profile:
            game_path = game_path_entry.get()
            if not game_path.endswith(".exe"):
                messagebox.showerror("Ошибка", "Вы должны выбрать файл с расширением .exe!")
                return
            if not os.path.isfile(game_path):
                messagebox.showerror("Ошибка", "Указанный файл недействителен. Проверьте путь.")
                return
            profile["game_path"] = game_path
            update_profile(profiles["active_profile"], profile, profiles)
            messagebox.showinfo("Сохранено", "Настройки успешно сохранены.")
    
    def navigate_back():
        navigate_to("Главная", root, frame, profiles)
    
    for widget in frame.winfo_children():
        widget.destroy()
    
    header = tk.Label(frame, text="Настройки запуска", font=("Helvetica", 20, "bold"), bg="#222222", fg="#19e1a0")
    header.pack(pady=30)
    style.animate_text(header, "Настройки запуска", loop=True)
    
    tk.Label(frame, text="Укажите путь до исполняемого файла", font=("Helvetica", 12, "bold"), bg="#222222", fg="#dedede").pack(pady=5)
    game_path_entry = tk.Entry(frame, font=("Fixedsys", 14), bg="#333333", fg="#dedede", relief="flat")
    game_path_entry.pack(pady=20, ipadx=119)
    if profile and "game_path" in profile:
        game_path_entry.insert(0, profile["game_path"])
    
    button_frame = tk.Frame(frame, bg="#222222")
    button_frame.pack(pady=10, fill="x")
    
    # Create an inner frame to center the buttons
    inner_button_frame = tk.Frame(button_frame, bg="#222222")
    inner_button_frame.pack(expand=True)
    
    btn_browse = tk.Button(inner_button_frame, text="Выбрать файл", command=browse_file, 
                          font=("Helvetica", 10, "bold"), bg="#333333", fg="#dedede", relief="flat")
    btn_browse.pack(side="left", padx=8)
    btn_browse.bind("<Enter>", style.on_hover)
    btn_browse.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#dedede"))
    
    btn_save = tk.Button(inner_button_frame, text="Сохранить", command=save_settings, 
                        font=("Helvetica", 10, "bold"), bg="#333333", fg="#dedede", relief="flat")
    btn_save.pack(side="left", padx=8)
    btn_save.bind("<Enter>", style.on_hover)
    btn_save.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#dedede"))
    
    btn_back = tk.Button(frame, text="Назад", command=navigate_back,
                        font=("Helvetica", 12, "bold"), bg="#333333", fg="#d42d52", relief="flat")
    btn_back.pack(pady=50)
    btn_back.bind("<Enter>", style.on_hover)
    btn_back.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#d42d52"))
    
    developer_info_frame = tk.Frame(frame, bg="#333333", padx=1, pady=18)
    developer_info_frame.pack(pady=0, fill="x")
    
    telegram_link = tk.Label(developer_info_frame, text="Автор проекта: @santhouse", font=("Helvetica", 11), fg="#19e1a0", bg="#333333", cursor="hand2")
    telegram_link.pack(pady=3)
    telegram_link.bind("<Button-1>", lambda e: open_telegram())
    telegram_link.bind("<Enter>", style.on_hover)
    telegram_link.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#19e1a0"))
    
    telegram_link = tk.Label(developer_info_frame, text="Подписывайтесь на мой Telegram-канал", font=("Helvetica", 12, "bold"), fg="#d42d52", bg="#333333", cursor="hand2")
    telegram_link.pack(pady=3)
    style.animate_text(telegram_link, "Подписывайтесь на мой Telegram-канал", loop=True)
    telegram_link.bind("<Button-1>", lambda e: open_telegram_channel())
    telegram_link.bind("<Enter>", style.on_hover)
    telegram_link.bind("<Leave>", lambda event: style.on_leave(event, "#333333", "#d42d52"))
    
    developer_details = tk.Label(developer_info_frame, text="v.3.1.1", font=("Fixedsys", 10), bg="#333333", fg="#19e1a0")
    developer_details.pack(pady=1)