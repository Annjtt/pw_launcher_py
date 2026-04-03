import tkinter as tk
from tkinter import Toplevel, Label

# ====== ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ ======
class ToolTip:
    """Всплывающая подсказка при наведении на виджет"""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
    
    def show_tip(self, event=None):
        """Показывает подсказку"""
        if self.tooltip_window or not self.text:
            return
        
        # Получаем координаты виджета
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Создаём всплывающее окно
        self.tooltip_window = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Стиль подсказки
        label = Label(
            tw, text=self.text,
            justify="left",
            background="#333333",
            foreground="#19e1a0",
            relief="solid",
            borderwidth=1,
            font=("Helvetica", 9, "italic"),
            padx=8,
            pady=4
        )
        label.pack()
    
    def hide_tip(self, event=None):
        """Скрывает подсказку"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None