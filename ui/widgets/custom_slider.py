"""自定义滑块组件，Canvas 绘制"""

import tkinter as tk
from tkinter import ttk
from ..theme import Theme


class CustomSlider(tk.Frame):
    """Canvas 绘制的滑块：圆角轨道 + 圆形手柄 + 标签 + 数值输入"""

    def __init__(self, parent, label_text, min_val, max_val, default_val,
                 resolution=0.1, unit='', callback=None, snap_points=None, snap_tolerance=15):
        super().__init__(parent)
        self.configure(bg=Theme.GLASS_BG)

        self._callback = callback
        self._unit = unit
        self._min_val = min_val
        self._max_val = max_val
        self._resolution = resolution
        self._snap_points = snap_points or []
        self._snap_tolerance = snap_tolerance
        self._setting_value = False
        self._dragging = False

        # Layout: label | canvas | entry + unit
        header = tk.Frame(self, bg=Theme.GLASS_BG)
        header.pack(fill=tk.X, padx=10, pady=(6, 2))

        self.label = tk.Label(
            header, text=label_text,
            fg=Theme.ON_SURFACE_VARIANT, bg=Theme.GLASS_BG,
            font=(Theme.FONT_FAMILY, 10, 'bold'), anchor='w'
        )
        self.label.pack(side=tk.LEFT)

        self._entry_var = tk.StringVar(value=self._format_val(default_val))
        self._entry = ttk.Entry(
            header, textvariable=self._entry_var, width=8,
            font=(Theme.FONT_MONO, 10)
        )
        self._entry.pack(side=tk.RIGHT)
        self._entry.bind('<Return>', self._on_entry_return)
        self._entry.bind('<FocusOut>', self._on_entry_return)
        self._entry.bind('<Key>', self._validate_entry_input)

        if unit:
            unit_lbl = tk.Label(
                header, text=unit, width=4,
                fg=Theme.ON_SURFACE_VARIANT, bg=Theme.GLASS_BG,
                font=(Theme.FONT_FAMILY, 9), anchor='e'
            )
            unit_lbl.pack(side=tk.RIGHT, padx=(0, 4))

        # Canvas area - increased height to fit handle
        self._canvas_h = 24
        self._canvas = tk.Canvas(
            self, bg=Theme.GLASS_BG, highlightthickness=0, height=self._canvas_h
        )
        self._canvas.pack(fill=tk.X, padx=10, pady=(0, 2))
        self._canvas.bind('<Configure>', lambda e: self._draw())

        # Mouse interaction
        self._canvas.bind('<ButtonPress-1>', self._on_press)
        self._canvas.bind('<B1-Motion>', self._on_drag)
        self._canvas.bind('<ButtonRelease-1>', self._on_release)

        # Value display
        self.value_label = tk.Label(
            self, text=self._format_val(default_val) + unit,
            fg=Theme.SECONDARY, bg=Theme.GLASS_BG,
            font=(Theme.FONT_MONO, 11, 'bold'), anchor='w'
        )
        self.value_label.pack(fill=tk.X, padx=10, pady=(0, 6))

        # Value
        self._value = default_val

        # Snap markers drawn on separate canvas below slider
        self._snap_canvas = tk.Canvas(self, bg=Theme.GLASS_BG, highlightthickness=0, height=14)
        if self._snap_points:
            self._snap_canvas.pack(fill=tk.X, padx=10)
            self._snap_canvas.bind('<Configure>', lambda e: self._draw_snap_markers())

        self.after(50, self._draw)

    # ---- Formatting ----

    def _format_val(self, v):
        if v == int(v):
            return str(int(v))
        return f'{v:.2f}'

    # ---- Drawing ----

    def _draw(self):
        c = self._canvas
        w = c.winfo_width()
        h = self._canvas_h
        c.delete('all')
        if w < 20:
            return

        pad = 8
        track_h = 6
        track_y = (h - track_h) // 2
        track_x0 = pad
        track_x1 = w - pad

        # Track background
        self._rounded_rect(c, track_x0, track_y, track_x1, track_y + track_h, 3,
                           fill=Theme.OUTLINE_VARIANT, outline='')

        # Filled portion
        ratio = (self._value - self._min_val) / max(self._max_val - self._min_val, 1)
        fill_x1 = track_x0 + ratio * (track_x1 - track_x0)
        if fill_x1 > track_x0:
            self._rounded_rect(c, track_x0, track_y, fill_x1, track_y + track_h, 3,
                               fill=Theme.PRIMARY, outline='')

        # Handle - 使用青色，与浅色背景形成对比
        handle_r = 8
        hx = fill_x1
        hy = h // 2
        # 外圈光晕
        c.create_oval(hx - handle_r - 3, hy - handle_r - 3, hx + handle_r + 3, hy + handle_r + 3,
                       fill='#b2dfdb', outline='', tags='handle_glow')
        # 手柄主体
        c.create_oval(hx - handle_r, hy - handle_r, hx + handle_r, hy + handle_r,
                       fill='#00bcd4', outline='#0097a7', width=1, tags='handle')

    def _rounded_rect(self, canvas, x0, y0, x1, y1, r, **kw):
        """Draw a rounded rectangle on canvas."""
        points = [
            x0 + r, y0,
            x1 - r, y0,
            x1, y0,
            x1, y0 + r,
            x1, y1 - r,
            x1, y1,
            x1 - r, y1,
            x0 + r, y1,
            x0, y1,
            x0, y1 - r,
            x0, y0 + r,
            x0, y0,
        ]
        return canvas.create_polygon(points, smooth=True, **kw)

    def _draw_snap_markers(self):
        if not self._snap_points:
            return
        c = self._snap_canvas
        w = c.winfo_width()
        if w < 10:
            return
        c.delete('all')
        span = self._max_val - self._min_val
        if span <= 0:
            return
        for p in self._snap_points:
            if self._min_val <= p <= self._max_val:
                x = ((p - self._min_val) / span) * w
                c.create_polygon(x, 0, x - 4, 8, x + 4, 8,
                                 fill=Theme.PRIMARY, outline='')
                c.create_text(x, 11, text=str(int(p)),
                              fill=Theme.PRIMARY, font=(Theme.FONT_MONO, 7))

    # ---- Mouse interaction ----

    def _on_press(self, event):
        self._dragging = True
        self._update_value_from_mouse(event)

    def _on_drag(self, event):
        if self._dragging:
            self._update_value_from_mouse(event)

    def _on_release(self, event):
        self._dragging = False
        self._snap_to_nearest()

    def _update_value_from_mouse(self, event):
        pad = 8
        w = self._canvas.winfo_width()
        ratio = (event.x - pad) / max(w - 2 * pad, 1)
        ratio = max(0.0, min(1.0, ratio))
        new_val = self._min_val + ratio * (self._max_val - self._min_val)
        new_val = round(new_val / self._resolution) * self._resolution
        new_val = max(self._min_val, min(self._max_val, new_val))
        self.set_value(new_val, fire_callback=True)

    # ---- Snap ----

    def _snap_to_nearest(self):
        if not self._snap_points:
            return
        best = None
        best_dist = float('inf')
        for p in self._snap_points:
            d = abs(p - self._value)
            if d <= self._snap_tolerance and d < best_dist:
                best_dist = d
                best = p
        if best is not None and abs(best - self._value) > 0.01:
            self.set_value(best, fire_callback=True)

    # ---- Entry ----

    def _on_entry_return(self, event=None):
        import re
        try:
            txt = self._entry_var.get().strip()
            if not re.match(r'^-?\d*\.?\d*$', txt):
                raise ValueError
            new_val = float(txt) if txt else self._min_val
            new_val = max(self._min_val, min(self._max_val, round(new_val, 2)))
            self.set_value(new_val, fire_callback=True)
        except ValueError:
            self._entry_var.set(self._format_val(self._value))

    def _validate_entry_input(self, event):
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab'):
            return
        if event.state & 0x4:  # Ctrl
            return
        if event.char and event.char not in set('0123456789.-'):
            return 'break'

    # ---- Public API ----

    def get_value(self):
        return self._value

    def set_value(self, value, fire_callback=False):
        self._setting_value = True
        self._value = max(self._min_val, min(self._max_val, value))
        self._entry_var.set(self._format_val(self._value))
        self.value_label.config(text=self._format_val(self._value) + self._unit)
        self._draw()
        self._setting_value = False
        if fire_callback and self._callback:
            self._callback(self._value)
