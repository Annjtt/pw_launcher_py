import cv2
import numpy as np
import pygetwindow as gw
from PIL import ImageGrab, Image, ImageTk
import time
import tkinter as tk
from tkinter import (
    Label, Frame, Button, StringVar, BOTH, LEFT, RIGHT, TOP, 
    messagebox, ttk, Checkbutton, BooleanVar, Toplevel, 
    Scrollbar, Listbox, END, Entry, LabelFrame
)
from pathlib import Path
import sys
import os
import threading

# Импорт системных модулей приложения
from styles import StyleManager
from utils import get_active_profile, update_profile, navigate_to
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
# ====== КОНСТАНТЫ ======
ICON_SIZE_LIST = 28      # Размер иконки в списке
# ICON_SIZE_OVERLAY = 48   # Размер иконки в оверлее (увеличил)
DEFAULT_ICON_SIZE_OVERLAY = 48   # Значение по умолчанию
DEFAULT_CAPTURE_AREA = {"x": 30, "y": 10, "w": 40, "h": 15}
DEFAULT_OVERLAY_POS = {"preset": "top_right", "x": None, "y": None}
DEFAULT_CHECK_INTERVAL = 0.3  # 👇 Частота сканирования (секунды)


class DebuffMonitorUI(tk.Frame):
    def __init__(self, master, profiles, **kwargs):
        self.profiles = profiles
        self.profile = get_active_profile(profiles) if profiles else None
        
        super().__init__(master, bg=StyleManager().colors["bg_main"], **kwargs)
        
        self.style = StyleManager()
        self.window_title = profiles.get("window_title", "") if profiles else ""
        
        self.templates = {}
        self.overlays = {}
        self.debuff_check_vars = {}
        
        self.monitoring = False
        self.monitor_thread = None
        self._stop_event = threading.Event()
        self.check_interval = 0.3
        self.active_debuffs = set()
        self.debug_mode = False
        
        self.capture_area = DEFAULT_CAPTURE_AREA.copy()
        self.overlay_pos = DEFAULT_OVERLAY_POS.copy()        
        self.icon_size_overlay = DEFAULT_ICON_SIZE_OVERLAY  # Размер иконки оверлея (загружается из профиля)      
        self.check_interval = DEFAULT_CHECK_INTERVAL  # Частота сканирования дебаффов
        
        self.status_text = StringVar(value="")
        self.selected_window_text = StringVar(value="(Окно не выбрано)")
        self.window_list = []
        self.selected_window_rect = None
        
        self.capture_vars = {}
        self.overlay_preset_var = StringVar()
        self.overlay_x_var = StringVar()
        self.overlay_y_var = StringVar()
        
        # Для хранения оригинальных PIL изображений (чтобы можно было ресайзить)
        self.original_overlay_images = {}
        
        self._load_profile_settings()
        self._build_ui()
        self.load_templates()
        self.load_overlay_images()
        self._populate_debuff_list()

    def _load_profile_settings(self):
        # Always reset to defaults first!
        self.capture_area = DEFAULT_CAPTURE_AREA.copy()
        self.overlay_pos = DEFAULT_OVERLAY_POS.copy()
        self.saved_enabled_debuffs = set()

        if not self.profile:
            return

        monitor_config = self.profile.get("debuff_monitor", {})

        # Подставить capture_area (или default)
        if isinstance(monitor_config.get("capture_area", None), dict):
            self.capture_area.update({
                k: monitor_config["capture_area"].get(k, self.capture_area[k])
                for k in self.capture_area
            })

        # Подставить overlay_pos (или default)
        if isinstance(monitor_config.get("overlay_pos", None), dict):
            self.overlay_pos.update({
                k: monitor_config["overlay_pos"].get(k, self.overlay_pos[k])
                for k in self.overlay_pos
            })

        # enabled/checked debuffs (или пусто)
        self.saved_enabled_debuffs = set(monitor_config.get("enabled", []))

        # Обновить значения в окне, если они уже инициализированы
        # (Чтобы записи/виджеты обновили свои значения при запуске)
        for key, var in self.capture_vars.items():
            if key in self.capture_area:
                var.set(str(self.capture_area[key]))
        if self.overlay_preset_var is not None and "preset" in self.overlay_pos:
            self.overlay_preset_var.set(self.overlay_pos["preset"])
        if self.overlay_x_var is not None and self.overlay_pos.get("x") is not None:
            self.overlay_x_var.set(str(self.overlay_pos["x"]))
        if self.overlay_y_var is not None and self.overlay_pos.get("y") is not None:
            self.overlay_y_var.set(str(self.overlay_pos["y"]))
        # 👇 Загрузка размера иконки из профиля
        if monitor_config.get("icon_size_overlay"): 
            self.icon_size_overlay = monitor_config["icon_size_overlay"]
        # 👇 Загрузка интервала сканирования из профиля
        if monitor_config.get("check_interval"):
            self.check_interval = monitor_config["check_interval"]

    def _save_profile_settings(self):
        if not self.profile or not self.profiles:
            return

        enabled = [name for name, var in self.debuff_check_vars.items() if var.get()]

        if "debuff_monitor" not in self.profile:
            self.profile["debuff_monitor"] = {}

        # Обновляем профиль согласно UI
        self.profile["debuff_monitor"].update({
            "enabled": enabled,
            "capture_area": self.capture_area,
            "overlay_pos": self.overlay_pos,
            "icon_size_overlay": self.icon_size_overlay,  # 👇 сохранение размера иконки оверлея
            "check_interval": self.check_interval  # 👇 сохранение частоты чтения
        })

        profile_name = self.profiles.get("active_profile")
        if profile_name:
            update_profile(profile_name, self.profile, self.profiles)

    def _build_ui(self):
        """Построение интерфейса - КОМПАКТНЫЙ ВАРИАНТ"""
        
        # === Заголовок ===
        title = Label(
            self, text="Мониторинг Дебаффов", 
            font=("Helvetica", 18, "bold"),  # Уменьшил шрифт
            fg="#19e1a0", bg=self.style.colors["bg_main"]
        )
        title.pack(pady=(5, 3))  # Уменьшил отступы
        self.style.animate_text(title, "Мониторинг Дебаффов", loop=False)  # Отключил анимацию для экономии ресурсов

        # === Выбор окна (ЦЕНТРИРОВАНО) ===
        win_fr = Frame(self, bg=self.style.colors["bg_main"])
        win_fr.pack(pady=2, fill=BOTH, padx=10)
        
        win_inner = Frame(win_fr, bg=self.style.colors["bg_main"])
        win_inner.pack(anchor='center')
        
        Label(win_inner, text="Окно:", font=("Helvetica", 9),  # Уменьшил шрифт
              bg=self.style.colors["bg_main"], fg=self.style.colors["fg_main"]).pack(side=LEFT)
        
        self.window_dropdown = ttk.Combobox(win_inner, width=20, state='readonly', font=("Helvetica", 9))
        self.window_dropdown.pack(side=LEFT, padx=5)
        self.window_dropdown.bind("<<ComboboxSelected>>", self._on_window_selected)
        
        btn_refresh = Button(
            win_inner, text="⟳", font=("Helvetica", 9, "bold"),
            bg=self.style.colors["bg_button"], fg="#f39c12",
            relief="flat", cursor="hand2", width=3, command=self.list_windows
        )
        btn_refresh.pack(side=LEFT, padx=(3, 0))
        btn_refresh.bind("<Enter>", self.style.on_hover)
        btn_refresh.bind("<Leave>", lambda e: self.style.on_leave(e, self.style.colors["bg_button"], "#f39c12"))
        
        self.window_dropdown["values"] = []
        self.list_windows()

        # === Область захвата (КОМПАКТНО) ===
        capture_frame = LabelFrame(
            self, text="Область захвата (%)", 
            font=("Helvetica", 9, "bold"),
            bg=self.style.colors["bg_main"], fg="#19e1a0",
            padx=5, pady=3
        )
        capture_frame.pack(fill=BOTH, padx=10, pady=2)
        # 👇 Добавляем подсказку
        ToolTip(capture_frame, "Проценты от размера окна игры.\nX,Y — начало области\nW,H — ширина и высота")
        
        capture_grid = Frame(capture_frame, bg=self.style.colors["bg_main"])
        capture_grid.pack()
        
        labels = ["X%", "Y%", "W%", "H%"]
        for i, (lbl, default) in enumerate(zip(labels, [30, 10, 40, 15])):
            Label(capture_grid, text=lbl, font=("Helvetica", 8), 
                  bg=self.style.colors["bg_main"], fg=self.style.colors["fg_main"]).grid(row=0, column=i*2, padx=3)
            
            var = StringVar(value=str(self.capture_area.get(lbl.lower().replace("%",""), default)))
            self.capture_vars[lbl] = var
            
            entry = Entry(capture_grid, textvariable=var, width=4,  # Уменьшил ширину
                         font=("Fixedsys", 8), bg=self.style.colors["bg_button"], 
                         fg=self.style.colors["fg_main"], relief="flat", justify="center")
            entry.grid(row=0, column=i*2+1, padx=1)
            entry.bind("<FocusOut>", lambda e: self._on_capture_area_change())

        # === Позиция оверлея (КОМПАКТНО) ===
        overlay_frame = LabelFrame(
            self, text="Позиция оверлея", 
            font=("Helvetica", 9, "bold"),
            bg=self.style.colors["bg_main"], fg="#19e1a0",
            padx=5, pady=3
        )
        overlay_frame.pack(fill=BOTH, padx=10, pady=2)
        # 👇 Добавляем подсказку
        ToolTip(overlay_frame, "Где показывать иконки дебаффов.\n↖↗↙↘ — углы экрана\nX,Y — точные координаты")
        
        # Кнопки-пресеты в 2 ряда для компактности
        preset_fr = Frame(overlay_frame, bg=self.style.colors["bg_main"])
        preset_fr.pack(pady=2)
        
        preset_buttons = [
            ("↖", "top_left"),
            ("↗", "top_right"),
            ("↙", "bottom_left"),
            ("↘", "bottom_right"),
        ]
        
        # Первый ряд: ↗ ↖
        for i, (text, preset) in enumerate(preset_buttons[:2]):
            btn = Button(
                preset_fr, text=text, font=("Helvetica", 10),
                bg=self.style.colors["bg_button"], fg=self.style.colors["fg_main"],
                relief="flat", cursor="hand2", width=6,
                command=lambda p=preset: self._set_overlay_preset(p)
            )
            btn.grid(row=0, column=i, padx=2)
            btn.bind("<Enter>", self.style.on_hover)
            btn.bind("<Leave>", lambda e: self.style.on_leave(e, self.style.colors["bg_button"], self.style.colors["fg_main"]))
        
        # Второй ряд: ↘ ↙
        for i, (text, preset) in enumerate(preset_buttons[2:]):
            btn = Button(
                preset_fr, text=text, font=("Helvetica", 10),
                bg=self.style.colors["bg_button"], fg=self.style.colors["fg_main"],
                relief="flat", cursor="hand2", width=6,
                command=lambda p=preset: self._set_overlay_preset(p)
            )
            btn.grid(row=1, column=i, padx=2, pady=2)
            btn.bind("<Enter>", self.style.on_hover)
            btn.bind("<Leave>", lambda e: self.style.on_leave(e, self.style.colors["bg_button"], self.style.colors["fg_main"]))
        
        # Ручная настройка - в одну строку
        coords_fr = Frame(overlay_frame, bg=self.style.colors["bg_main"])
        coords_fr.pack(pady=2)
        
        Label(coords_fr, text="X:", font=("Helvetica", 8), 
              bg=self.style.colors["bg_main"], fg=self.style.colors["fg_main"]).pack(side=LEFT, padx=2)
        
        Entry(coords_fr, textvariable=self.overlay_x_var, width=5, 
              font=("Fixedsys", 8), bg=self.style.colors["bg_button"], 
              fg=self.style.colors["fg_main"], relief="flat", justify="center").pack(side=LEFT)
        
        Label(coords_fr, text="Y:", font=("Helvetica", 8), 
              bg=self.style.colors["bg_main"], fg=self.style.colors["fg_main"]).pack(side=LEFT, padx=(5, 0))
        
        Entry(coords_fr, textvariable=self.overlay_y_var, width=5, 
              font=("Fixedsys", 8), bg=self.style.colors["bg_button"], 
              fg=self.style.colors["fg_main"], relief="flat", justify="center").pack(side=LEFT)
        
        Button(coords_fr, text="OK", font=("Helvetica", 8, "bold"),
               bg=self.style.colors["bg_button"], fg="#19e1a0",
               relief="flat", cursor="hand2", width=4, command=self._save_overlay_settings).pack(side=LEFT, padx=5)
        
        # === Размер иконки оверлея ===
        icon_frame = LabelFrame(
            self, text="Размер иконки (px)", 
            font=("Helvetica", 9, "bold"),
            bg=self.style.colors["bg_main"], fg="#19e1a0",
            padx=5, pady=3
        )
        icon_frame.pack(fill=BOTH, padx=10, pady=2)

        icon_inner = Frame(icon_frame, bg=self.style.colors["bg_main"])
        icon_inner.pack(pady=2)
        # 👇 Добавляем подсказку
        ToolTip(icon_frame, "Размер плавающих иконок.\nРекомендуется: 48-80 px\nМин: 16, Макс: 200")

        Label(icon_inner, text="Размер:", font=("Helvetica", 8), 
            bg=self.style.colors["bg_main"], fg=self.style.colors["fg_main"]).pack(side=LEFT, padx=5)

        self.icon_size_var = StringVar(value=str(self.icon_size_overlay))
        self.icon_size_entry = Entry(icon_inner, textvariable=self.icon_size_var, width=5, 
                                    font=("Fixedsys", 9), bg=self.style.colors["bg_button"], 
                                    fg=self.style.colors["fg_main"], relief="flat", justify="center")
        self.icon_size_entry.pack(side=LEFT, padx=5)
        # Разрешаем только цифры
        def validate_int(P):
            return P.isdigit() or P == ""
        vcmd = (self.register(validate_int), '%P')
        self.icon_size_entry.config(validate='key', validatecommand=vcmd)

        Button(icon_inner, text="OK", font=("Helvetica", 8, "bold"),
            bg=self.style.colors["bg_button"], fg="#19e1a0",
            relief="flat", cursor="hand2", width=4, 
            command=self._apply_icon_size).pack(side=LEFT, padx=5)

        # === Частота сканирования ===
        scan_frame = LabelFrame(
            self, text="Частота сканирования (сек)", 
            font=("Helvetica", 9, "bold"),
            bg=self.style.colors["bg_main"], fg="#19e1a0",
            padx=5, pady=3
        )
        scan_frame.pack(fill=BOTH, padx=10, pady=2)

        scan_inner = Frame(scan_frame, bg=self.style.colors["bg_main"])
        scan_inner.pack(pady=2)
        # 👇 Добавляем подсказку
        ToolTip(scan_frame, "Как часто проверять экран.\n0.1-0.3 — быстро (высокая нагрузка)\n0.5-1.0 — нормально\n2.0+ — экономно")

        Label(scan_inner, text="Интервал:", font=("Helvetica", 8), 
            bg=self.style.colors["bg_main"], fg=self.style.colors["fg_main"]).pack(side=LEFT, padx=5)

        self.check_interval_var = StringVar(value=str(self.check_interval))
        self.check_interval_entry = Entry(scan_inner, textvariable=self.check_interval_var, width=5, 
                                        font=("Fixedsys", 9), bg=self.style.colors["bg_button"], 
                                        fg=self.style.colors["fg_main"], relief="flat", justify="center")
        self.check_interval_entry.pack(side=LEFT, padx=5)

        # Валидация только цифры и точка
        def validate_float(P):
            return (P.isdigit() or P == "" or (P.replace('.', '', 1).isdigit() and P.count('.') <= 1))
        vcmd = (self.register(validate_float), '%P')
        self.check_interval_entry.config(validate='key', validatecommand=vcmd)

        Button(scan_inner, text="OK", font=("Helvetica", 8, "bold"),
            bg=self.style.colors["bg_button"], fg="#19e1a0",
            relief="flat", cursor="hand2", width=4, 
            command=self._apply_check_interval).pack(side=LEFT, padx=5)
        
        # === Статус и кнопки (В ОДНУ ЛИНИЮ) ===
        ctrl_fr = Frame(self, bg=self.style.colors["bg_main"])
        ctrl_fr.pack(pady=3)
        
        Label(ctrl_fr, textvariable=self.status_text, 
              bg=self.style.colors["bg_main"], fg=self.style.colors["fg_main"], 
              font=("Fixedsys", 8), width=20).pack(side=LEFT, padx=5)
        # === кнопочка отладки ===
        self.debug_btn = Button(
            ctrl_fr, text="🟢 Отладка OFF", font=("Helvetica", 9, "bold"), 
            bg=self.style.colors["bg_button"], fg="#f39c12",
            relief="flat", cursor="hand2", width=12,
            command=self.toggle_debug_mode
        )
        self.debug_btn.pack(side=LEFT, padx=3)
        self.debug_btn.bind("<Enter>", self.style.on_hover)
        self.debug_btn.bind("<Leave>", lambda e: self.style.on_leave(e, self.style.colors["bg_button"], "#f39c12"))
        self.start_btn = Button(
            ctrl_fr, text="▶ Старт", font=("Helvetica", 9, "bold"), 
            bg=self.style.colors["bg_button"], fg="#19e1a0",
            relief="flat", cursor="hand2", width=10,
            command=self.start_monitoring
        )
        self.start_btn.pack(side=LEFT, padx=3)
        self.start_btn.bind("<Enter>", self.style.on_hover)
        self.start_btn.bind("<Leave>", lambda e: self.style.on_leave(e, self.style.colors["bg_button"], "#19e1a0"))
        
        self.stop_btn = Button(
            ctrl_fr, text="■ Стоп", font=("Helvetica", 9, "bold"), 
            bg=self.style.colors["bg_button"], fg="#d42d52",
            relief="flat", cursor="hand2", width=10,
            state=tk.DISABLED, command=self.stop_monitoring
        )
        self.stop_btn.pack(side=LEFT, padx=3)
        self.stop_btn.bind("<Enter>", self.style.on_hover)
        self.stop_btn.bind("<Leave>", lambda e: self.style.on_leave(e, self.style.colors["bg_button"], "#d42d52"))

        # === Список дебаффов (ФИКСИРОВАННАЯ ВЫСОТА) ===
        Label(self, text="Дебаффы:", font=("Helvetica", 9, "bold"),
              bg=self.style.colors["bg_main"], fg=self.style.colors["fg_main"]).pack(pady=2)
        
        debuff_frame = Frame(self, bg=self.style.colors["bg_main"])
        debuff_frame.pack(fill=BOTH, expand=False, padx=10, pady=2)  # expand=False!

        self.debuff_canvas = tk.Canvas(
            debuff_frame, borderwidth=0, bg=self.style.colors["bg_main"], 
            relief=tk.FLAT, highlightthickness=0, selectborderwidth=0, takefocus=False,
            height=180  # 👇 ФИКСИРОВАННАЯ ВЫСОТА (примерно 4-5 иконок)
        )
        self.debuff_list_fr = Frame(self.debuff_canvas, bg=self.style.colors["bg_main"])
        
        self.debuff_scrollbar = Scrollbar(
            debuff_frame, orient="vertical", command=self.debuff_canvas.yview,
            bg=self.style.colors["bg_main"], troughcolor=self.style.colors["bg_main"],
            activebackground=self.style.colors["bg_button_hover"], width=6
        )
        self.debuff_scrollbar.pack(side=RIGHT, fill='y')
        self.debuff_canvas.configure(yscrollcommand=self.debuff_scrollbar.set)
        self.debuff_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.debuff_canvas.create_window((0, 0), window=self.debuff_list_fr, anchor="nw")
        self.debuff_list_fr.bind("<Configure>", lambda e: self.debuff_canvas.configure(scrollregion=self.debuff_canvas.bbox("all")))
        self.debuff_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # === Кнопки внизу (В ОДНУ ЛИНИЮ) ===
        btn_fr = Frame(self, bg=self.style.colors["bg_main"])
        btn_fr.pack(pady=3)
        
        Button(btn_fr, text="Сохранить", font=("Helvetica", 9),
               bg=self.style.colors["bg_button"], fg="#19e1a0",
               relief="flat", cursor="hand2", width=12,
               command=self._save_all_settings).pack(side=LEFT, padx=2)
        
        Button(btn_fr, text="← Назад", font=("Helvetica", 9, "bold"),
               bg=self.style.colors["bg_button"], fg="#d42d52",
               relief="flat", cursor="hand2", width=12,
               command=self._go_back).pack(side=LEFT, padx=10)

        self.err_label = None

    def _apply_icon_size(self):
        """Применяет новый размер иконки"""
        try:
            new_size = int(self.icon_size_var.get())
            if 16 <= new_size <= 200:  # Ограничение разумных значений
                self.icon_size_overlay = new_size
                self._save_profile_settings()  # Сразу сохраняем в профиль
                
                # 👇 1. Сначала скрываем все активные оверлеи (пока ссылки ещё целые!)
                if self.monitoring:
                    self.stop_all_overlays()
                
                # 👇 2. Теперь безопасно перезагружаем изображения с новым размером
                self.load_overlay_images()
                
                # 👇 3. Если мониторинг активен — пересоздаём оверлеи с новым размером
                if self.monitoring:
                    for name in self.active_debuffs:
                        self.show_overlay(name)
                
                messagebox.showinfo("Успех", f"Размер изменен на {new_size}px", parent=self)
            else:
                messagebox.showwarning("Внимание", "Размер должен быть от 16 до 200 px", parent=self)
                self.icon_size_var.set(str(self.icon_size_overlay))
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число", parent=self)
            self.icon_size_var.set(str(self.icon_size_overlay))

    def _apply_check_interval(self):
        """Применяет новый интервал сканирования"""
        try:
            new_interval = float(self.check_interval_var.get())
            if 0.1 <= new_interval <= 5.0:  # Ограничение от 0.1 до 5 секунд
                self.check_interval = new_interval
                self._save_profile_settings()
                messagebox.showinfo("Успех", f"Интервал изменен на {new_interval} сек", parent=self)
            else:
                messagebox.showwarning("Внимание", "Интервал должен быть от 0.1 до 5.0 сек", parent=self)
                self.check_interval_var.set(str(self.check_interval))
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число", parent=self)
            self.check_interval_var.set(str(self.check_interval))

    def create_debug_windows(self):
        """Создает окна для отладочных рамок"""
        try:
            # Красная рамка (область поиска)
            self.red_border = tk.Toplevel(self)
            self.red_border.overrideredirect(True)
            self.red_border.attributes('-topmost', True)
            self.red_border.attributes('-alpha', 0.4)
            self.red_border.configure(bg='red')
            self.red_border.withdraw()
            
            # Зеленая рамка (область вывода)
            self.green_border = tk.Toplevel(self)
            self.green_border.overrideredirect(True)
            self.green_border.attributes('-topmost', True)
            self.green_border.attributes('-alpha', 0.4)
            self.green_border.configure(bg='green')
            self.green_border.withdraw()
            
            self.debug_windows_created = True
        except Exception as e:
            print(f"Ошибка создания рамок: {e}")
            self.debug_windows_created = False
    
    def update_debug_borders(self):
        """Обновляет позиции отладочных рамок"""
        if not hasattr(self, 'debug_windows_created') or not self.debug_windows_created:
            return
        
        if not self.debug_mode:
            return
        
        window = self.get_game_window()
        if not window:
            return
        
        # Красная рамка - область поиска
        x, y, w, h = window
        cap_x = x + int(w * self.capture_area["x"] / 100)
        cap_y = y + int(h * self.capture_area["y"] / 100)
        cap_w = int(w * self.capture_area["w"] / 100)
        cap_h = int(h * self.capture_area["h"] / 100)
        
        if hasattr(self, 'red_border'):
            try:
                self.red_border.geometry(f"{cap_w}x{cap_h}+{cap_x}+{cap_y}")
                self.red_border.deiconify()
            except:
                pass
        
        # Зеленая рамка - область вывода, защита от ошибок. 
        try:
            if hasattr(self, 'overlay_win') and self.overlay_win:
                try:
                    # Пытаемся получить координаты. Если окно уничтожено — будет ошибка
                    ox = self.overlay_win.winfo_x()
                    oy = self.overlay_win.winfo_y()
                    ow = self.overlay_win.winfo_width()
                    oh = self.overlay_win.winfo_height()
                except tk.TclError:
                    # Окно уничтожено, сбрасываем ссылку
                    self.overlay_win = None
                    ox, oy, ow, oh = None, None, None, None
            else:
                ox, oy, ow, oh = None, None, None, None

            # Если ссылка сбросилась или окна нет — считаем координаты по пресету
            if ox is None:
                sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
                if self.overlay_pos.get("preset") == "custom" and self.overlay_pos.get("x") is not None:
                    ox, oy = self.overlay_pos["x"], self.overlay_pos["y"]
                else:
                    positions = {
                        "top_right": (sw - self.icon_size_overlay - 20, 20),
                        "top_left": (20, 20),
                        "bottom_right": (sw - self.icon_size_overlay - 20, sh - self.icon_size_overlay - 20),
                        "bottom_left": (20, sh - self.icon_size_overlay - 20)
                    }
                    ox, oy = positions.get(self.overlay_pos.get("preset", "top_right"), (sw - 100, 20))
                ow, oh = self.icon_size_overlay, self.icon_size_overlay
            # Обновляем зеленую рамку
            if hasattr(self, 'green_border'):
                self.green_border.geometry(f"{ow}x{oh}+{ox}+{oy}")
                self.green_border.deiconify()
        except Exception as e:
             # На случай любых других ошибок — просто игнорируем, чтобы не спамить в консоль
            if self.debug_mode:
                print(f"Debug border update error: {e}")       
    
    def hide_debug_borders(self):
        """Скрывает отладочные рамки"""
        if hasattr(self, 'red_border'):
            self.red_border.withdraw()
        if hasattr(self, 'green_border'):
            self.green_border.withdraw()
    
    def toggle_debug_mode(self):
        """Включает/выключает режим отладки"""
        self.debug_mode = not self.debug_mode
        
        if self.debug_mode:
            if not hasattr(self, 'debug_windows_created') or not self.debug_windows_created:
                self.create_debug_windows()
            self.update_debug_borders()
            self.debug_btn.config(text="🔴 Отладка ON", bg="#d42d52")
            self.status_text.set("Режим отладки ВКЛЮЧЕН")
            # Запускаем обновление рамок в цикле
            self._start_debug_updater()
        else:
            self.hide_debug_borders()
            self.debug_btn.config(text="🟢 Отладка OFF", bg=self.style.colors["bg_button"])
            self.status_text.set("Режим отладки ВЫКЛЮЧЕН")
            if hasattr(self, '_debug_updater_running'):
                self._debug_updater_running = False
    
    def _start_debug_updater(self):
        """Запускает поток для обновления рамок в реальном времени"""
        self._debug_updater_running = True
        
        def update_loop():
            while self.debug_mode and self._debug_updater_running:
                if self.debug_mode:
                    self.update_debug_borders()
                time.sleep(0.2)
        
        threading.Thread(target=update_loop, daemon=True).start()

    def _on_frame_configure(self, event):
        self.debuff_canvas.configure(scrollregion=self.debuff_canvas.bbox("all"))
        
    def _on_mousewheel(self, event):
        self.debuff_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_capture_area_change(self):
        try:
            for key, var in zip(["x", "y", "w", "h"], 
                               [self.capture_vars["X%"], self.capture_vars["Y%"], 
                                self.capture_vars["W%"], self.capture_vars["H%"]]):
                val = int(var.get())
                if 0 <= val <= 100:
                    self.capture_area[key] = val
                else:
                    var.set(str(self.capture_area[key]))
        except ValueError:
            pass

    def _set_overlay_preset(self, preset):
        """Установка пресета позиции оверлея"""
        self.overlay_pos["preset"] = preset
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        
        positions = {
            "top_right": (sw - self.icon_size_overlay - 20, 20),
            "top_left": (20, 20),
            "bottom_right": (sw - self.icon_size_overlay - 20, sh - self.icon_size_overlay - 20),
            "bottom_left": (20, sh - self.icon_size_overlay - 20)
        }
        
        if preset in positions:
            x, y = positions[preset]
            self.overlay_x_var.set(str(x))
            self.overlay_y_var.set(str(y))
            self.overlay_pos["x"], self.overlay_pos["y"] = x, y
            self._save_profile_settings()

    def _save_overlay_settings(self):
        try:
            x = int(self.overlay_x_var.get())
            y = int(self.overlay_y_var.get())
            self.overlay_pos.update({"x": x, "y": y, "preset": "custom"})
            self._save_profile_settings()
            messagebox.showinfo("OK", "Позиция сохранена", parent=self)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные координаты", parent=self)

    def _save_all_settings(self):
        self._on_capture_area_change()
        self._save_profile_settings()
        messagebox.showinfo("Сохранено", "Настройки сохранены в профиль", parent=self)

    def _go_back(self):
        """Возврат в главное меню БЕЗ остановки мониторинга"""
        self._save_profile_settings()
        navigate_to("Главная", self.master, self, self.profiles)

    def _show_error(self, msg):
        if not self.err_label:
            self.err_label = Label(self, text=msg, fg=self.style.colors["fg_error"], 
                                   bg=self.style.colors["bg_main"], font=("Helvetica", 9), wraplength=380)
            self.err_label.pack(fill=BOTH, padx=10, pady=5)
        else:
            self.err_label.config(text=msg)

    def _clear_error(self):
        if self.err_label:
            self.err_label.destroy()
            self.err_label = None

    def load_templates(self):
        template_dir = Path("templates")
        template_dir.mkdir(exist_ok=True)
        template_files = list(template_dir.glob("*.png"))
        
        for path in template_files:
            name = path.stem
            img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if img is not None:
                self.templates[name] = {
                    'image': img, 'w': img.shape[1], 'h': img.shape[0],
                    'has_alpha': len(img.shape) > 2 and img.shape[2] == 4
                }
        
        if not self.templates:
            self._show_error("Нет PNG шаблонов в папке 'templates'")

    def load_overlay_images(self):
        images_dir = Path("images")
        images_dir.mkdir(exist_ok=True)
        
        for debuff_name in self.templates:
            image_path = images_dir / f"{debuff_name}.png"
            overlay_info = {"img_pil": None, "tk_image": None}
            
            if image_path.exists():
                try:
                    # Сохраняем оригинальное PIL изображение для ресайза
                    pil_image = Image.open(str(image_path)).convert("RGBA")
                    self.original_overlay_images[debuff_name] = pil_image
                    
                    # Создаём иконку для списка (28x28)
                    list_img = pil_image.resize((ICON_SIZE_LIST, ICON_SIZE_LIST), Image.Resampling.LANCZOS)
                    overlay_info["tk_image"] = ImageTk.PhotoImage(list_img)
                except Exception:
                    pass
            
            self.overlays[debuff_name] = {**overlay_info, "overlay_window": None}

    def _populate_debuff_list(self):
        for c in self.debuff_list_fr.winfo_children():
            c.destroy()
        
        if not self.templates:
            return
        
        for name in sorted(self.templates):
            row = Frame(self.debuff_list_fr, bg=self.style.colors["bg_main"])
            row.pack(fill=BOTH, pady=2)
            
            var = BooleanVar(value=name in self.saved_enabled_debuffs)
            self.debuff_check_vars[name] = var
            
            Checkbutton(row, variable=var, bg=self.style.colors["bg_main"], 
                       activebackground=self.style.colors["bg_main"],
                       selectcolor=self.style.colors["bg_button"], 
                       fg="#19e1a0", highlightthickness=0, cursor="hand2").pack(side=LEFT, padx=(4, 5))
            
            img = self.overlays.get(name, {}).get("tk_image")
            if img:
                lbl = Label(row, image=img, bg=self.style.colors["bg_main"])
                lbl.image = img
                lbl.pack(side=LEFT, padx=(0, 5))
            else:
                Label(row, text="⛔", font=("Helvetica", 12, "bold"), 
                     fg=self.style.colors["fg_error"], bg=self.style.colors["bg_main"]).pack(side=LEFT, padx=(0, 6))
            
            Label(row, text=name, bg=self.style.colors["bg_main"], 
                  fg=self.style.colors["fg_main"], font=("Helvetica", 10)).pack(side=LEFT, padx=2)

    def list_windows(self):
        try:
            wins = gw.getAllTitles()
            filtered = [w for w in wins if w.strip()]
            self.window_list = filtered
            self.window_dropdown["values"] = filtered
            
            if self.window_title and self.window_title in filtered:
                self.window_dropdown.current(filtered.index(self.window_title))
                self._on_window_selected()
            elif filtered:
                self.window_dropdown.current(0)
                self._on_window_selected()
            else:
                self.selected_window_text.set("Нет открытых окон")
        except Exception as e:
            self.selected_window_text.set(f"Ошибка: {e}")

    def _on_window_selected(self, event=None):
        selection = self.window_dropdown.get()
        self.window_title = selection
        self.selected_window_text.set(f"Окно: {selection[:30]}...")
        self.selected_window_rect = self.get_game_window()

    def get_game_window(self):
        try:
            windows = gw.getWindowsWithTitle(self.window_title)
            if not windows:
                return None
            for w in windows:
                try:
                    if w.isActive and w.width > 0 and w.height > 0:
                        return (w.left, w.top, w.width, w.height)
                except:
                    continue
            for w in windows:
                try:
                    if w.width > 0 and w.height > 0:
                        return (w.left, w.top, w.width, w.height)
                except:
                    continue
            return None
        except:
            return None

    def capture_upper_center(self, window_rect):
        if not window_rect:
            return None
        x, y, w, h = window_rect
        
        if w <= 0 or h <= 0:
            return None
        
        cap_x = x + int(w * self.capture_area["x"] / 100)
        cap_y = y + int(h * self.capture_area["y"] / 100)
        cap_w = int(w * self.capture_area["w"] / 100)
        cap_h = int(h * self.capture_area["h"] / 100)
        
        try:
            screenshot = ImageGrab.grab(bbox=(cap_x, cap_y, cap_x + cap_w, cap_y + cap_h))
            if screenshot is None:
                return None
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return img
        except:
            return None

    def find_debuffs(self, scene):
        if scene is None:
            return set()
        try:
            scene_gray = cv2.cvtColor(scene, cv2.COLOR_BGR2GRAY)
        except:
            return set()
        
        found_debuffs = set()
        
        for name, template_data in self.templates.items():
            if not self.debuff_check_vars.get(name, BooleanVar()).get():
                continue
                
            try:
                template = template_data['image']
                th, tw = template_data['h'], template_data['w']
                
                if template_data['has_alpha']:
                    template_gray = cv2.cvtColor(template[:,:,:3], cv2.COLOR_BGR2GRAY)
                else:
                    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                
                best_val = 0
                for scale in np.arange(0.8, 1.21, 0.05):
                    new_w = int(tw * scale)
                    new_h = int(th * scale)
                    if new_w > scene.shape[1] or new_h > scene.shape[0]:
                        continue
                    scaled = cv2.resize(template_gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                    result = cv2.matchTemplate(scene_gray, scaled, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(result)
                    if max_val > best_val:
                        best_val = max_val
                
                if best_val >= 0.8:
                    found_debuffs.add(name)
            except:
                pass
        
        return found_debuffs

    def show_overlay(self, debuff_name):
        """Показ оверлея — изменено: смещение дополнительных иконок теперь влево, а не вверх"""
        info = self.overlays.get(debuff_name)
        if not info or info.get("overlay_window"):
            return
        
        # 👇 Берём оригинальное PIL изображение и ресайзим для оверлея
        pil_img = self.original_overlay_images.get(debuff_name)
        
        overlay = Toplevel(self)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        overlay.attributes('-alpha', 0.98)
        overlay.config(bg="black")
        overlay.wm_attributes("-transparentcolor", "black")
        
        if pil_img:
            # Ресайз для оверлея (48x48)
            overlay_img = pil_img.resize((self.icon_size_overlay, self.icon_size_overlay), Image.Resampling.LANCZOS)
            overlay_tk_img = ImageTk.PhotoImage(overlay_img)
            
            lbl = Label(overlay, image=overlay_tk_img, bg="black")
            lbl.image = overlay_tk_img
        else:
            lbl = Label(overlay, text=f"⚠️ {debuff_name.upper()}! ⚠️",
                       bg="black", fg=self.style.colors["fg_error"], 
                       font=("Helvetica", 14, "bold"))
        
        lbl.pack()
        
        # Позиционирование
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        
        if self.overlay_pos.get("preset") == "custom" and self.overlay_pos.get("x") is not None:
            pos_x, pos_y = self.overlay_pos["x"], self.overlay_pos["y"]
        else:
            positions = {
                "top_right": (sw - self.icon_size_overlay - 20, 20),
                "top_left": (20, 20),
                "bottom_right": (sw - self.icon_size_overlay - 20, sh - self.icon_size_overlay - 20),
                "bottom_left": (20, sh - self.icon_size_overlay - 20)
            }
            pos_x, pos_y = positions.get(self.overlay_pos.get("preset", "top_right"), (sw - 100, 20))
        
        # Новый расчет смещения: теперь делаем отступ влево от основной иконки
        offset = list(self.overlays.keys()).index(debuff_name) * (self.icon_size_overlay + 5)
        pos_x -= offset  # Двигаем каждую дополнительную иконку влево от основного положения

        # По вертикали больше не сдвигаем, только горизонтальное выравнивание
        
        overlay.geometry(f"+{pos_x}+{pos_y}")
        overlay.lift()
        overlay.update()
        info["overlay_window"] = overlay
        # Сохранение для зеленой рамки
        self.overlay_win = overlay  

    def hide_overlay(self, debuff_name):
        info = self.overlays.get(debuff_name)
        ow = info.get("overlay_window") if info else None
        if ow:
            try:
                ow.destroy()
            except:
                pass
            info["overlay_window"] = None

    def update_overlays(self, detected: set):
        for name in detected - self.active_debuffs:
            self.show_overlay(name)
        for name in self.active_debuffs - detected:
            self.hide_overlay(name)
        self.active_debuffs = detected

    def stop_all_overlays(self):
        for name in list(self.overlays.keys()):
            self.hide_overlay(name)

    def _monitor_loop(self):
        self.status_text.set("Поиск окна игры...")
        
        attempts = 0
        while not self._stop_event.is_set():
            win = self.get_game_window()
            if win:
                self.selected_window_rect = win
                self.status_text.set("✓ Мониторинг активен")
                break
            attempts += 1
            if attempts > 3:
                self.status_text.set("Ожидание окна...")
            time.sleep(1.0)
        
        last_visible = set()
        
        try:
            while not self._stop_event.is_set():
                window = self.get_game_window()
                if not window:
                    self.status_text.set("⚠ Окно потеряно")
                    self.update_overlays(set())
                    time.sleep(self.check_interval)
                    continue
                
                scene = self.capture_upper_center(window)
                active = self.find_debuffs(scene)
                
                if active != last_visible:
                    self.status_text.set(f"Найдено: {len(active)}" if active else "Дебаффов нет")
                    self.update_overlays(active)
                    self._update_result_in_list(active)
                    last_visible = set(active)
                
                time.sleep(self.check_interval)
                
        except Exception as e:
            if self.debug_mode:
                print(f"Monitor error: {e}")
            self.status_text.set("❌ Ошибка мониторинга")
        finally:
            self.stop_all_overlays()

    def _update_result_in_list(self, active: set):
        for child in self.debuff_list_fr.winfo_children():
            for grand in child.winfo_children():
                if isinstance(grand, Label):
                    txt = grand.cget("text")
                    if txt and txt in active:
                        grand.config(fg="#19e1a0")
                    elif txt and txt in self.templates:
                        grand.config(fg=self.style.colors["fg_main"])

    def start_monitoring(self):
        if self.monitoring or not self.templates:
            return
        if not self.window_title:
            self._show_error("Выберите окно игры!")
            return
        
        self._clear_error()
        self._save_profile_settings()
        
        self.monitoring = True
        self._stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.start_btn.config(state=tk.DISABLED, fg=self.style.colors["fg_main"])
        self.stop_btn.config(state=tk.NORMAL)
        self.status_text.set("Запуск...")

    def stop_monitoring(self):
        if not self.monitoring:
            return
        self._stop_event.set()
        self.monitoring = False
        self.start_btn.config(state=tk.NORMAL, fg="#19e1a0")
        self.stop_btn.config(state=tk.DISABLED)
        self.status_text.set("Остановлен")
        self.stop_all_overlays()
        self._clear_highlight_in_list()

    def _clear_highlight_in_list(self):
        for child in self.debuff_list_fr.winfo_children():
            for grand in child.winfo_children():
                if isinstance(grand, Label):
                    grand.config(fg=self.style.colors["fg_main"])

    def on_close(self):
        self._save_profile_settings()
        self.stop_monitoring()
        self.stop_all_overlays()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Debuff Monitor — Test")
    root.configure(bg="#222222")
    root.geometry("440x600")
    
    mock_profiles = {
        "active_profile": "Test",
        "profiles": {
            "Test": {
                "game_path": "",
                "characters": [],
                "debuff_monitor": {
                    "enabled": [],
                    "capture_area": DEFAULT_CAPTURE_AREA,
                    "overlay_pos": DEFAULT_OVERLAY_POS
                }
            }
        }
    }
    
    app = DebuffMonitorUI(root, mock_profiles)
    app.pack(fill=BOTH, expand=1, padx=10, pady=7)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()