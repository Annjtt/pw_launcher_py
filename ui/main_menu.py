import tkinter as tk
from utils import navigate_to, StyleManager

def main_menu(root, frame, profiles):
    style = StyleManager()
    
    def navigate_to_option(option):
        navigate_to(option, root, frame, profiles)
    
    # НЕ ПРОВЕРЯЕМ на дубликаты - просто создаём меню
    # (navigate_to уже очистил фрейм)
    
    title = tk.Label(frame, text="PW Launcher", font=("Helvetica", 24, "bold"), fg="#19e1a0", bg="#222222")
    title.pack(pady=20)
    style.animate_text(title, "PW Launcher", loop=True)
    
    button_frame = tk.Frame(frame, bg="#222222")
    button_frame.pack(pady=10)
    buttons = ["Персонажи", "Мониторинг", "Профиль", "Настройки", "Выход"]
    for btn_text in buttons:
        btn = tk.Button(
            button_frame, 
            text=btn_text, 
            command=lambda t=btn_text: root.destroy() if t == "Выход" else navigate_to_option(t),
            font=("Helvetica", 13, "bold"), 
            bg="#333333",  
            fg="#dedede",  
            relief="flat",  
            highlightbackground="#19e1a0",  
            highlightthickness=10,  
            width=20,  
            height=2,  
            bd=0  
        )
        btn.pack(pady=10)
        btn.bind("<Enter>", style.on_hover)
        btn.bind("<Leave>", lambda event, bg="#333333", fg="#dedede": style.on_leave(event, bg, fg))