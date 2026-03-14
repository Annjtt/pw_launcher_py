import tkinter as tk
import random

class StyleManager:
    def __init__(self):
        self.colors = {
            "bg_main": "#222222",
            "fg_main": "#dedede",
            "fg_error": "#d42d52",
            "fg_warning": "#f39c12",
            "fg_button": "#dedede",
            # Цвета кнопок при наведении
            "fg_button_hover": "#dedede",   # тёмный текст
            "bg_button": "#333333",
            "bg_button_hover": "#444444",   # светло‑серый фон ховера
            "bg_button_active": "#444444",
            "font_title": ("Helvetica", 24, "bold"),
            "font_subtitle": ("Helvetica", 20, "bold"),
            "font_label": ("Helvetica", 12, "bold"),
            "font_button": ("Helvetica", 10, "bold"),
        }

    def animate_text(self, label, text, delay=200, loop=False):
        """Анимация текста (Глитч + Волна)"""
        def update_text():
            current_text = ''.join(
                random.choice('!@#$%^&*()_+<>?') if random.random() < 0.05 and i in random.sample(range(len(text)), 3) and c != ' '  # Редкий глитч (5%)
                else c.upper() if i % 3 == 0 and random.random() < 0.1 and c != ' '  # Редкая волна (каждая 4-я буква, шанс 20%)
                else c
                for i, c in enumerate(text)
            )
            label.config(text=current_text)
            if loop:
                label.after(delay, update_text)
        update_text()

    def on_hover(self, event):
        event.widget.config(bg=self.colors["bg_button_hover"], fg=self.colors["fg_button_hover"])

    def on_leave(self, event, original_bg, original_fg):
        event.widget.config(bg=original_bg, fg=original_fg)