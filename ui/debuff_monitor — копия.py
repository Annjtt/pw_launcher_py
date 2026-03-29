import cv2
import numpy as np
import pygetwindow as gw
from PIL import ImageGrab, Image, ImageTk
import time
import tkinter as tk
from tkinter import Label, Frame, Button, StringVar, BOTH, LEFT, RIGHT, TOP, messagebox, ttk, Checkbutton, BooleanVar, Toplevel, Scrollbar, Listbox, END
from pathlib import Path
import sys
import os
import threading

# ====== UI COLOR STYLES, matching @add_character_menu.py and @profile_menu.py ======
UI_BG = "#222222"
UI_ACCENT = "#333333"
UI_ACCENT_HOVER = "#606d7b"
UI_FG = "#ffffff"
UI_WARN = "#ff6666"
UI_OK = "#19e1a0"
UI_DISABLE = "#888888"
UI_FONT = ("Helvetica", 12)
UI_FONT_BOLD = ("Helvetica", 12, "bold")

ICON_SIZE = 28  # Make buff icon reasonable size for the list

class DebuffMonitorUI(tk.Frame):
    """
    UI для мониторинга дебаффов:
    - список обнаруживаемых дебаффов (чекбокс + мини-иконка)
    - можно выбрать конкретные для поиска
    - поиск окна: выпадающий список окон, выбор окна захвата
    - overlay-уведомления при обнаружении
    """
    def __init__(self, master, initial_window_title=None, **kwargs):
        super().__init__(master, bg=UI_BG, **kwargs)
        self.window_title = initial_window_title or ""
        self.templates = {}
        self.overlays = {}
        self.debuff_check_vars = {}
        self.monitoring = False
        self.monitor_thread = None
        self._stop_event = threading.Event()
        self.check_interval = 0.5
        self.active_debuffs = set()
        self.debug_mode = False
        self.err_label = None
        self.window_selection = None
        self.window_list = []
        self.selected_window_rect = None

        self.status_text = StringVar(value="")
        self.selected_window_text = StringVar(value="(Окно не выбрано)")
        self._build_ui()
        self.load_templates()
        self.load_overlay_images()
        self._populate_debuff_list()

    def _build_ui(self):
        title = Label(self, text="Мониторинг Дебаффов", bg=UI_BG, fg=UI_OK, font=UI_FONT_BOLD, pady=6)
        title.pack(fill=BOTH)

        # Окно для выбора окна игры
        win_fr = Frame(self, bg=UI_BG)
        win_fr.pack(pady=(6, 10), fill=BOTH)
        Label(win_fr, text="Окно:", bg=UI_BG, fg=UI_FG, font=UI_FONT).pack(side=LEFT)
        self.window_dropdown = ttk.Combobox(win_fr, width=32, state='readonly')
        self.window_dropdown.pack(side=LEFT, padx=5)
        self.window_dropdown.bind("<<ComboboxSelected>>", self._on_window_selected)
        Button(win_fr, text="Обновить", font=UI_FONT, bg=UI_ACCENT, fg=UI_FG,
               activebackground=UI_ACCENT_HOVER, activeforeground=UI_FG, relief=tk.FLAT,
               command=self.list_windows).pack(side=LEFT, padx=(10, 0))
        self.window_dropdown["values"] = []
        self.list_windows()

        win_sel_status = Label(self, textvariable=self.selected_window_text, bg=UI_BG, fg=UI_FG, font=UI_FONT)
        win_sel_status.pack(fill=BOTH, padx=10)

        # Статус мониторинга
        status_frame = Frame(self, bg=UI_BG)
        status_frame.pack(fill=BOTH, pady=(8, 5))
        status_lbl = Label(status_frame, textvariable=self.status_text, bg=UI_BG, fg=UI_FG, font=UI_FONT)
        status_lbl.pack(side=LEFT)

        # Панель управления
        ctrl_fr = Frame(self, bg=UI_BG)
        ctrl_fr.pack(pady=(5, 10))
        self.start_btn = Button(
            ctrl_fr, text="Старт мониторинга", font=UI_FONT_BOLD, bg=UI_ACCENT, fg=UI_FG,
            activebackground=UI_ACCENT_HOVER, activeforeground=UI_FG, relief=tk.FLAT,
            command=self.start_monitoring, width=18
        )
        self.start_btn.pack(side=LEFT, padx=(0, 8))
        self.stop_btn = Button(
            ctrl_fr, text="Стоп", font=UI_FONT, bg=UI_ACCENT, fg=UI_FG,
            activebackground=UI_WARN, activeforeground=UI_FG, relief=tk.FLAT,
            command=self.stop_monitoring, width=10, state=tk.DISABLED
        )
        self.stop_btn.pack(side=LEFT)

        # Список дебаффов с иконками и чекбоксами (скролл)
        debuff_frame = Frame(self, bg=UI_BG)
        debuff_frame.pack(fill=BOTH, expand=1, padx=(2, 2), pady=(0, 5))

        self.debuff_canvas = tk.Canvas(debuff_frame, borderwidth=0, bg=UI_BG, relief=tk.FLAT, highlightthickness=0)
        self.debuff_list_fr = Frame(self.debuff_canvas, bg=UI_BG)
        self.debuff_scrollbar = Scrollbar(debuff_frame, orient="vertical", command=self.debuff_canvas.yview)
        self.debuff_canvas.configure(yscrollcommand=self.debuff_scrollbar.set)
        self.debuff_scrollbar.pack(side=RIGHT, fill='y')
        self.debuff_canvas.pack(side=LEFT, fill=BOTH, expand=1)
        self.debuff_canvas.create_window((0, 0), window=self.debuff_list_fr, anchor="nw")
        self.debuff_list_fr.bind("<Configure>", lambda e: self.debuff_canvas.configure(scrollregion=self.debuff_canvas.bbox("all")))

    def _show_error(self, msg):
        if not self.err_label:
            self.err_label = Label(self, text=msg, fg=UI_WARN, bg=UI_BG, font=UI_FONT, wraplength=380)
            self.err_label.pack(fill=BOTH, padx=10, pady=10)
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
                    'image': img,
                    'w': img.shape[1],
                    'h': img.shape[0],
                    'has_alpha': len(img.shape) > 2 and img.shape[2] == 4
                }
        if not self.templates:
            self._show_error(
                "Нет PNG шаблонов в папке 'templates'. Добавьте шаблоны и перезапустите."
            )

    def load_overlay_images(self):
        images_dir = Path("images")
        images_dir.mkdir(exist_ok=True)
        for debuff_name in self.templates:
            image_path = images_dir / f"{debuff_name}.png"
            overlay_info = {}
            overlay_info["img_pil"] = None
            overlay_info["tk_image"] = None
            if image_path.exists():
                pil_image = Image.open(str(image_path)).convert("RGBA")
                new_size = (ICON_SIZE, ICON_SIZE)
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
                overlay_info["img_pil"] = pil_image
                overlay_info["tk_image"] = ImageTk.PhotoImage(pil_image)
            self.overlays[debuff_name] = {
                **overlay_info,
                "overlay_window": None
            }

    def _populate_debuff_list(self):
        for c in self.debuff_list_fr.winfo_children():
            c.destroy()
        if not self.templates:
            return
        for idx, name in enumerate(sorted(self.templates)):
            row = Frame(self.debuff_list_fr, bg=UI_BG)
            row.pack(fill=BOTH, pady=2)
            var = BooleanVar(value=True)
            self.debuff_check_vars[name] = var
            chk = Checkbutton(
                row, variable=var, bg=UI_BG, activebackground=UI_BG,
                selectcolor=UI_BG, highlightthickness=0
            )
            chk.pack(side=LEFT, padx=(4, 5))
            img = self.overlays.get(name, {}).get("tk_image")
            if img:
                lbl = Label(row, image=img, bg=UI_BG)
                lbl.image = img
                lbl.pack(side=LEFT, padx=(0, 5), pady=2)
            else:
                lbl = Label(row, text="⛔", font=UI_FONT_BOLD, fg=UI_WARN, bg=UI_BG)
                lbl.pack(side=LEFT, padx=(0, 6))
            Label(row, text=name, bg=UI_BG, fg=UI_FG, font=UI_FONT).pack(side=LEFT, padx=2)

    def list_windows(self):
        # Сканируем список окон, обновляем self.window_dropdown
        wins = gw.getAllTitles()
        filtered = [w for w in wins if w.strip()]
        self.window_list = filtered
        self.window_dropdown["values"] = filtered
        if self.window_title and self.window_title in filtered:
            idx = filtered.index(self.window_title)
            self.window_dropdown.current(idx)
            self._on_window_selected()
        elif filtered:
            self.window_dropdown.current(0)
            self._on_window_selected()
        else:
            self.selected_window_text.set("Нет открытых окон!")

    def _on_window_selected(self, event=None):
        selection = self.window_dropdown.get()
        self.window_title = selection
        self.selected_window_text.set(f"Текущее окно: {selection}")
        # Optional: refresh window_rect
        self.selected_window_rect = self.get_game_window()

    def get_game_window(self):
        # Вернуть (x, y, w, h) окна по self.window_title
        try:
            windows = gw.getWindowsWithTitle(self.window_title)
            if not windows:
                return None
            for w in windows:
                try:
                    if w.isActive and w.width > 0 and w.height > 0:
                        return (w.left, w.top, w.width, w.height)
                except Exception:
                    continue
            for w in windows:
                try:
                    if w.width > 0 and w.height > 0:
                        return (w.left, w.top, w.width, w.height)
                except Exception:
                    continue
            return None
        except Exception as e:
            if self.debug_mode:
                print(f"Ошибка при поиске окна: {e}")
            return None

    def capture_upper_center(self, window_rect):
        if not window_rect:
            return None
        x, y, w, h = window_rect
        if w <= 0 or h <= 0:
            return None
        capture_w = int(w * 0.4)
        capture_h = int(h * 0.15)
        capture_x = x + (w - capture_w) // 2
        capture_y = y + int(h * 0.1)
        try:
            screenshot = ImageGrab.grab(bbox=(
                capture_x, capture_y,
                capture_x + capture_w, capture_y + capture_h
            ))
            if screenshot is None:
                return None
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return img
        except Exception as e:
            if self.debug_mode:
                print(f"Ошибка захвата экрана: {e}")
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
                if best_val >= 0.65:
                    found_debuffs.add(name)
            except Exception as e:
                if self.debug_mode:
                    print(f"Ошибка при поиске {name}: {e}")
        return found_debuffs

    def show_overlay(self, debuff_name):
        info = self.overlays.get(debuff_name)
        if not info or info.get("overlay_window", None):
            return
        img = info.get("tk_image")
        overlay = Toplevel(self)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        overlay.attributes('-alpha', 0.98)
        overlay.config(bg="black")
        if img:
            lbl = Label(overlay, image=img, bg="black")
            lbl.image = img
        else:
            lbl = Label(
                overlay, text=f"⚠️ {debuff_name.upper()}! ⚠️",
                bg="black", fg=UI_WARN, font=UI_FONT_BOLD
            )
        lbl.pack(ipadx=12, ipady=8)
        # Smart overlay stack
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        base_x = sw - ICON_SIZE - 30
        base_y = 38 + (list(self.overlays.keys()).index(debuff_name) * (ICON_SIZE + 14))
        overlay.geometry(f"+{base_x}+{base_y}")
        overlay.lift()
        overlay.update()
        info["overlay_window"] = overlay

    def hide_overlay(self, debuff_name):
        info = self.overlays.get(debuff_name)
        ow = info.get("overlay_window") if info else None
        if ow:
            try:
                ow.destroy()
            except Exception:
                pass
            info["overlay_window"] = None

    def update_overlays(self, detected: set):
        for name in detected - self.active_debuffs:
            self.show_overlay(name)
        for name in self.active_debuffs - detected:
            self.hide_overlay(name)
        self.active_debuffs = detected

    def stop_all_overlays(self):
        for name, info in self.overlays.items():
            self.hide_overlay(name)

    def _monitor_loop(self):
        self.status_text.set("Ожидание окна игры...")
        ok_window = False
        attempts = 0
        while not self._stop_event.is_set():
            win = self.get_game_window()
            if win:
                ok_window = True
                self.selected_window_rect = win
                self.status_text.set("Мониторинг запущен")
                break
            attempts += 1
            if attempts > 2:
                self.status_text.set("Поиск окна игры...")
            time.sleep(1.0)
        last_visible_debuffs = set()
        try:
            while not self._stop_event.is_set():
                window = self.get_game_window()
                if not window:
                    self.status_text.set("Потеряно окно игры")
                    self.update_overlays(set())
                    self.stop_all_overlays()
                    time.sleep(self.check_interval)
                    continue
                scene = self.capture_upper_center(window)
                active = self.find_debuffs(scene)
                if active != last_visible_debuffs:
                    if active:
                        self.status_text.set(f"Обнаружено {len(active)} дебафф(ов)")
                    else:
                        self.status_text.set("Дебаффы не найдены")
                    self.update_overlays(active)
                last_visible_debuffs = set(active)
                self._update_result_in_list(active)
                time.sleep(self.check_interval)
        except Exception as e:
            if self.debug_mode:
                print(f"Ошибка в мониторинге: {e}")
            self.status_text.set("Произошла ошибка мониторинга.")
        finally:
            self.stop_all_overlays()

    def _update_result_in_list(self, active: set):
        for child in self.debuff_list_fr.winfo_children():
            for grand in child.winfo_children():
                if isinstance(grand, Label):
                    txt = grand.cget("text")
                    if txt and txt.lower() in active:
                        grand.config(fg=UI_OK)
                    elif txt and txt.lower() in self.templates:
                        grand.config(fg=UI_FG)

    def start_monitoring(self):
        if self.monitoring or not self.templates:
            return
        if not self.window_title:
            self._show_error("Выберите окно для мониторинга!")
            return
        self._clear_error()
        self.monitoring = True
        self._stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_text.set("Запуск мониторинга...")

    def stop_monitoring(self):
        if not self.monitoring:
            return
        self._stop_event.set()
        self.monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_text.set("Мониторинг остановлен")
        self.stop_all_overlays()
        self._clear_highlight_in_list()

    def _clear_highlight_in_list(self):
        for child in self.debuff_list_fr.winfo_children():
            for grand in child.winfo_children():
                if isinstance(grand, Label):
                    grand.config(fg=UI_FG)

    def on_close(self):
        self.stop_monitoring()
        self.stop_all_overlays()
        self.master.destroy()

# ============== Запуск UI mode ===================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Debuff Monitor — UI")
    root.configure(bg=UI_BG)
    root.geometry("420x480")
    app = DebuffMonitorUI(root)
    app.pack(fill=BOTH, expand=1, padx=10, pady=7)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()