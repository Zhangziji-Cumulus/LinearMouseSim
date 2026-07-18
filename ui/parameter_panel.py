"""参数调节面板模块 — 标签页布局"""

import tkinter as tk
from tkinter import ttk, messagebox
from .theme import Theme
from .widgets.custom_slider import CustomSlider


class ParameterPanel(tk.Frame):
    """参数调节面板类 — 标签页切换布局"""

    TAB_ACTIVE_BG = '#4caf50'
    TAB_ACTIVE_FG = '#ffffff'
    TAB_INACTIVE_BG = '#f0f0f0'
    TAB_INACTIVE_FG = '#333333'
    TAB_BAR_BG = '#ffffff'
    CARD_BG = '#f8f9fa'
    BTN_BORDER = '#4caf50'
    BTN_FG = '#4caf50'

    TABS = [
        ('basic',    '基础设置'),
        ('assist',   '辅助回中'),
        ('mapping',  '映射参数'),
        ('hotkey',   '快捷键'),
    ]

    def __init__(self, parent, app=None, presets=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.presets = presets or {}
        self.configure(bg=Theme.SURFACE)

        self._sliders = {}
        self._on_preset_callback = None
        self._on_change_callback = None
        self._hotkey_display = {}
        self._hotkey_buttons = {}
        self._hotkey_manager = None
        self._recording_action = None
        self._cancel_id = None
        self._active_tab = None
        self._tab_buttons = {}
        self._tab_frames = {}

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        # Title
        tk.Label(
            self, text='参数设置',
            fg=Theme.ON_SURFACE, bg=Theme.SURFACE,
            font=(Theme.FONT_FAMILY, 16, 'bold'), anchor='w'
        ).pack(fill=tk.X, padx=15, pady=(15, 4))

        # Preset selector (always visible above tabs)
        self._build_preset_bar()

        # Tab bar with horizontal scroll
        tab_container = tk.Frame(self, bg=self.TAB_BAR_BG)
        tab_container.pack(fill=tk.X, padx=12, pady=(8, 0))
        
        self._tab_canvas = tk.Canvas(tab_container, bg=self.TAB_BAR_BG, highlightthickness=0, height=32)
        self._tab_canvas.pack(fill=tk.X)
        
        self._tab_bar = tk.Frame(self._tab_canvas, bg=self.TAB_BAR_BG)
        self._tab_canvas_window = self._tab_canvas.create_window((0, 0), window=self._tab_bar, anchor='nw')
        
        for key, label in self.TABS:
            btn = tk.Label(
                self._tab_bar, text=label, bd=0, padx=14, pady=6,
                font=(Theme.FONT_FAMILY, 9, 'bold'),
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=(0, 2))
            btn.bind('<Button-1>', lambda e, k=key: self._switch_tab(k))
            self._tab_buttons[key] = btn
        
        # Bind horizontal scroll
        self._tab_bar.bind('<Configure>', lambda e: self._tab_canvas.configure(scrollregion=self._tab_canvas.bbox('all')))
        self._tab_canvas.bind('<MouseWheel>', self._on_tab_scroll)
        
        # Build content area (must be after tab bar)
        self._build_content_area()
    
    def _on_tab_scroll(self, event):
        self._tab_canvas.xview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _build_content_area(self):
        # Separator below tab bar
        tk.Frame(self, bg=Theme.OUTLINE, height=1).pack(fill=tk.X, padx=12, pady=(4, 0))

        # Tab content container
        self._content_frame = tk.Frame(self, bg=Theme.SURFACE)
        self._content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Build each tab's content inside the content frame
        self._build_basic_tab()
        self._build_assist_tab()
        self._build_mapping_tab()
        self._build_hotkey_tab()

        self._switch_tab('basic')

    # ---- Preset bar ----

    def _build_preset_bar(self):
        bar = tk.Frame(self, bg=Theme.SURFACE)
        bar.pack(fill=tk.X, padx=15, pady=(4, 0))
        tk.Label(bar, text='用户预设', fg=Theme.ON_SURFACE_VARIANT,
                 bg=Theme.SURFACE, font=(Theme.FONT_FAMILY, 10)).pack(side=tk.LEFT)

        # 自定义下拉框
        self._dropdown_frame = tk.Frame(bar, bg=Theme.SURFACE)
        self._dropdown_frame.pack(side=tk.LEFT, padx=(8, 0))

        # 显示框
        self._dropdown_var = tk.StringVar(value='')
        self._dropdown_display = tk.Frame(self._dropdown_frame, bg='#e0e0e0',
                                           highlightthickness=1, highlightbackground='#bdbdbd')
        self._dropdown_display.pack(fill=tk.X)

        self._dropdown_label = tk.Label(
            self._dropdown_display, textvariable=self._dropdown_var,
            bg='#e0e0e0', fg=Theme.ON_SURFACE, font=(Theme.FONT_FAMILY, 9),
            anchor='w', padx=6, pady=4, cursor='hand2'
        )
        self._dropdown_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._dropdown_label.bind('<Button-1>', self._toggle_dropdown)

        self._dropdown_arrow = tk.Label(
            self._dropdown_display, text='▼', bg='#e0e0e0',
            fg=Theme.ON_SURFACE_VARIANT, font=(Theme.FONT_FAMILY, 8),
            padx=4, cursor='hand2'
        )
        self._dropdown_arrow.pack(side=tk.RIGHT)
        self._dropdown_arrow.bind('<Button-1>', self._toggle_dropdown)

        # 下拉列表（初始隐藏）
        self._dropdown_list = None
        self._dropdown_open = False
        self._selected_preset_id = None
        self._context_menu_open = False

        # 保存按钮
        btn_style = {'font': (Theme.FONT_FAMILY, 9), 'bd': 0, 'padx': 6, 'pady': 2, 'cursor': 'hand2'}
        self._save_preset_btn = tk.Button(
            bar, text='保存', fg=Theme.PRIMARY, bg=Theme.SURFACE,
            command=self._on_save_preset, **btn_style
        )
        self._save_preset_btn.pack(side=tk.LEFT, padx=(8, 0))

        # 创建右键菜单
        self._preset_menu = tk.Menu(self, tearoff=0)
        self._preset_menu.add_command(label='重命名', command=self._on_rename_preset)
        self._preset_menu.add_command(label='删除', command=self._on_delete_preset)

        # 初始显示
        self._update_dropdown_display()

    def _toggle_dropdown(self, event=None):
        """切换下拉列表显示/隐藏"""
        if self._dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        """打开下拉列表"""
        if self._dropdown_open:
            return

        self._dropdown_list = tk.Toplevel(self)
        self._dropdown_list.wm_overrideredirect(True)
        self._dropdown_list.wm_attributes('-topmost', True)

        # 固定宽度 200px
        dropdown_width = 200

        # 计算位置
        x = self._dropdown_display.winfo_rootx()
        y = self._dropdown_display.winfo_rooty() + self._dropdown_display.winfo_height()

        # 动态计算高度（考虑文本换行）
        total_height = 4
        for preset_info in self.presets.values():
            name = preset_info['name']
            # 估算文本行数（每行约15个字符）
            lines = max(1, (len(name) * 8 + dropdown_width - 30) // (dropdown_width - 30))
            total_height += lines * 18 + 16  # 每行高度 + padding
        total_height = max(total_height, len(self.presets) * 36 + 4)

        self._dropdown_list.geometry(f'{dropdown_width}x{total_height}+{x}+{y}')

        # 列表容器
        list_frame = tk.Frame(self._dropdown_list, bg='#ffffff',
                              highlightthickness=1, highlightbackground='#bdbdbd')
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 添加预设项
        for preset_id, preset_info in self.presets.items():
            self._add_preset_item(list_frame, preset_id, preset_info)

        # 绑定点击外部区域关闭
        self._dropdown_list.bind('<FocusOut>', self._on_dropdown_focus_out)
        self._dropdown_list.focus_set()

        self._dropdown_open = True

    def _add_preset_item(self, parent, preset_id, preset_info):
        """添加一个预设项到下拉列表"""
        is_default = (preset_id == 'default')
        is_selected = (preset_id == self._selected_preset_id)

        bg = '#e3f2fd' if is_selected else '#ffffff'
        item_frame = tk.Frame(parent, bg=bg, cursor='hand2')
        item_frame.pack(fill=tk.X, padx=2, pady=1)

        # 预设名（固定宽度 200px，文本自动换行）
        label = tk.Label(
            item_frame, text=preset_info['name'], bg=bg,
            fg=Theme.ON_SURFACE, font=(Theme.FONT_FAMILY, 9),
            anchor='w', padx=8, pady=6, wraplength=160, justify='left'
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # "..." 按钮
        more_btn = tk.Label(
            item_frame, text='...', bg=bg,
            fg=Theme.ON_SURFACE_VARIANT, font=(Theme.FONT_FAMILY, 10, 'bold'),
            padx=6, cursor='hand2'
        )
        more_btn.pack(side=tk.RIGHT)

        # 绑定事件
        def on_click(e):
            self._select_preset(preset_id)

        def on_right_click(e):
            # 先选择该预设（不关闭菜单），再打开菜单
            self._select_preset_no_close(preset_id)
            self._show_item_menu(e, preset_id, is_default)

        def on_more_click(e):
            # 先选择该预设（不关闭菜单），再打开菜单
            self._select_preset_no_close(preset_id)
            self._show_item_menu_at_widget(e, more_btn, preset_id, is_default)

        def on_enter(e):
            if not is_selected:
                item_frame.configure(bg='#f5f5f5')
                label.configure(bg='#f5f5f5')
                more_btn.configure(bg='#f5f5f5')
            # 右键菜单打开时，悬停自动切换到该预设的菜单
            if self._context_menu_open:
                self._show_item_menu_at_widget(e, more_btn, preset_id, is_default)

        def on_leave(e):
            if not is_selected:
                item_frame.configure(bg='#ffffff')
                label.configure(bg='#ffffff')
                more_btn.configure(bg='#ffffff')

        for widget in [item_frame, label]:
            widget.bind('<Button-1>', on_click)
            widget.bind('<Button-3>', on_right_click)
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)

        more_btn.bind('<Button-1>', on_more_click)
        more_btn.bind('<Button-3>', on_right_click)
        more_btn.bind('<Enter>', on_enter)
        more_btn.bind('<Leave>', on_leave)

    def _close_dropdown(self):
        """关闭下拉列表"""
        if self._dropdown_list:
            self._dropdown_list.destroy()
            self._dropdown_list = None
        self._dropdown_open = False

    def _on_dropdown_focus_out(self, event):
        """下拉列表失去焦点时关闭"""
        # 延迟关闭，避免点击菜单项时立即关闭
        self.after(150, self._close_dropdown)

    def _select_preset(self, preset_id):
        """选择预设"""
        self._selected_preset_id = preset_id
        self._update_dropdown_display()
        self._close_dropdown()

        if self._on_preset_callback:
            self._on_preset_callback(preset_id)

    def _select_preset_no_close(self, preset_id):
        """选择预设但不关闭下拉菜单"""
        self._selected_preset_id = preset_id
        self._update_dropdown_display()

        if self._on_preset_callback:
            self._on_preset_callback(preset_id)

    def _update_dropdown_display(self):
        """更新显示框的文本"""
        if self._selected_preset_id and self._selected_preset_id in self.presets:
            self._dropdown_var.set(self.presets[self._selected_preset_id]['name'])
        elif self.presets:
            first_id = list(self.presets.keys())[0]
            self._selected_preset_id = first_id
            self._dropdown_var.set(self.presets[first_id]['name'])
        else:
            self._dropdown_var.set('')

    def _show_item_menu(self, event, preset_id, is_default):
        """在鼠标位置显示菜单"""
        self._preset_menu.entryconfigure('重命名', state='normal' if not is_default else 'disabled')
        self._preset_menu.entryconfigure('删除', state='normal' if not is_default else 'disabled')
        self._preset_menu.tk_popup(event.x_root, event.y_root)

    def _show_item_menu_at_widget(self, event, widget, preset_id, is_default):
        """在控件位置显示菜单"""
        self._preset_menu.entryconfigure('重命名', state='normal' if not is_default else 'disabled')
        self._preset_menu.entryconfigure('删除', state='normal' if not is_default else 'disabled')
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height()
        self._context_menu_open = True
        self._preset_menu.tk_popup(x, y)
        # 菜单关闭后重置状态
        self._preset_menu.grab_release()
        self._context_menu_open = False

    # ---- Tab switching ----

    def _switch_tab(self, tab_key):
        if self._active_tab == tab_key:
            return
        self._active_tab = tab_key
        for key, btn in self._tab_buttons.items():
            if key == tab_key:
                btn.configure(bg=self.TAB_ACTIVE_BG, fg=self.TAB_ACTIVE_FG)
            else:
                btn.configure(bg=self.TAB_INACTIVE_BG, fg=self.TAB_INACTIVE_FG)
        for key, frame in self._tab_frames.items():
            frame.pack_forget()
        if tab_key in self._tab_frames:
            self._tab_frames[tab_key].pack(fill=tk.BOTH, expand=True)

    # ---- Card helper ----

    def _build_card(self, parent, title, build_fn):
        card = tk.Frame(parent, bg=self.CARD_BG, highlightthickness=1,
                        highlightbackground=Theme.GLASS_BORDER, bd=0)
        card.pack(fill=tk.X, pady=(0, 10), ipadx=12, ipady=4)
        header = tk.Frame(card, bg=self.CARD_BG)
        header.pack(fill=tk.X, padx=12, pady=(8, 2))
        tk.Label(header, text=title, fg=Theme.PRIMARY, bg=self.CARD_BG,
                 font=(Theme.FONT_FAMILY, 11, 'bold'), anchor='w').pack(side=tk.LEFT)
        sep = tk.Frame(card, bg=Theme.OUTLINE, height=1)
        sep.pack(fill=tk.X, padx=12, pady=(2, 4))
        body = tk.Frame(card, bg=self.CARD_BG)
        body.pack(fill=tk.X, padx=4, pady=(0, 8))
        build_fn(body)

    # ---- Tab: 基础设置 ----

    def _build_basic_tab(self):
        frame = tk.Frame(self._content_frame, bg=Theme.SURFACE)
        self._tab_frames['basic'] = frame

        self._build_card(frame, '基础设置', self._build_basic_card)

    def _build_basic_card(self, parent):
        defs = [
            ('sensitivity',      '灵敏度', 0.1, 5.0, 1.0, 0.1, 'x', None, None),
            ('smoothing_factor', '平滑系数', 0.0, 0.99, 0.3, 0.01, '', None, None),
            ('deadzone',         '死区', 0, 50, 3, 1, 'px', None, None),
            ('max_angle',        '最大舵角', 10, 1800, 90, 1, '°', None, None),
            ('dpi',              '鼠标DPI', 50, 25600, 800, 50, '', None, None),
        ]
        for key, lbl, lo, hi, default, res, unit, snap, snap_tol in defs:
            s = CustomSlider(parent, lbl, lo, hi, default, resolution=res, unit=unit,
                             callback=self._on_parameter_change,
                             snap_points=snap, snap_tolerance=snap_tol or 15)
            s.pack(fill=tk.X)
            self._sliders[key] = s

        # Reverse checkbox
        self._reverse_var = tk.BooleanVar(value=False)
        self._reverse_checkbox = tk.Checkbutton(
            parent, text='反转方向盘方向',
            variable=self._reverse_var, command=self._on_parameter_change,
            bg=self.CARD_BG, activebackground=self.CARD_BG,
            fg=Theme.ON_SURFACE, activeforeground=Theme.ON_SURFACE,
            selectcolor=self.CARD_BG, font=(Theme.FONT_FAMILY, 9)
        )
        self._reverse_checkbox.pack(fill=tk.X, padx=8, pady=(4, 0), anchor='w')

    # ---- Tab: 辅助回中 ----

    def _build_assist_tab(self):
        frame = tk.Frame(self._content_frame, bg=Theme.SURFACE)
        self._tab_frames['assist'] = frame
        self._build_card(frame, '辅助回中', self._build_assist_card)

    def _build_assist_card(self, parent):
        defs = [
            ('assist_rate_window',    '回打检测时长', 0, 500, 100, 10, 'ms'),
            ('assist_rate_threshold', '回打位移阈值', 0, 2000, 100, 10, 'px'),
            ('assist_threshold',      '辅助触发角度', 0, 900, 300, 10, '°'),
            ('assist_return_rate',    '归中缩减比例', 0, 100, 20, 1, '%'),
            ('near_center_threshold', '中心检测边界', 0, 500, 50, 1, 'px'),
            ('center_hold_ms', '中心保持时长', 0, 1000, 100, 10, 'ms'),
            ('center_release_threshold', '释放位移阈值', 0, 2000, 200, 10, 'px'),
        ]
        for key, lbl, lo, hi, default, res, unit in defs:
            s = CustomSlider(parent, lbl, lo, hi, default, resolution=res, unit=unit,
                             callback=self._on_parameter_change)
            s.pack(fill=tk.X)
            self._sliders[key] = s

    # ---- Tab: 映射参数 ----

    def _build_mapping_tab(self):
        frame = tk.Frame(self._content_frame, bg=Theme.SURFACE)
        self._tab_frames['mapping'] = frame
        self._build_card(frame, '映射参数', self._build_mapping_card)

    def _build_mapping_card(self, parent):
        s = CustomSlider(parent, '像素→角度映射', 10, 5000, 500,
                         resolution=10, unit='px',
                         callback=self._on_parameter_change)
        s.pack(fill=tk.X)
        self._sliders['linear_end'] = s

    # ---- Tab: 快捷键 ----

    def _build_hotkey_tab(self):
        frame = tk.Frame(self._content_frame, bg=Theme.SURFACE)
        self._tab_frames['hotkey'] = frame
        self._build_card(frame, '快捷键配置', self._build_hotkey_card)

    def _build_hotkey_card(self, parent):
        self._hotkey_actions = {
            'toggle':               '开启/关闭',
            'temp_sensitivity_half': '临时降敏',
        }
        for action, label_text in self._hotkey_actions.items():
            hk_frame = tk.Frame(parent, bg=self.CARD_BG)
            hk_frame.pack(fill=tk.X, padx=8, pady=3)

            tk.Label(hk_frame, text=label_text, width=14,
                     fg=Theme.ON_SURFACE, bg=self.CARD_BG,
                     font=(Theme.FONT_FAMILY, 9), anchor='w').pack(side=tk.LEFT)

            display_var = tk.StringVar(value='')
            tk.Label(hk_frame, textvariable=display_var, width=8,
                     fg=Theme.SECONDARY, bg=self.CARD_BG,
                     font=(Theme.FONT_MONO, 10, 'bold'), anchor='w').pack(
                         side=tk.LEFT, padx=(8, 4))

            change_btn = tk.Label(
                hk_frame, text='修改', width=5, cursor='hand2',
                fg=self.BTN_FG, bg=self.CARD_BG,
                font=(Theme.FONT_FAMILY, 9, 'bold'),
                highlightthickness=1, highlightbackground=self.BTN_BORDER,
                padx=6, pady=2
            )
            change_btn.pack(side=tk.RIGHT)
            change_btn.bind('<Button-1>',
                            lambda e, a=action: self._start_hotkey_recording(a))
            change_btn.bind('<Enter>',
                            lambda e, b=change_btn: b.configure(
                                bg=self.TAB_ACTIVE_BG, fg=self.TAB_ACTIVE_FG))
            change_btn.bind('<Leave>',
                            lambda e, b=change_btn: b.configure(
                                bg=self.CARD_BG, fg=self.BTN_FG))

            self._hotkey_display[action] = display_var
            self._hotkey_buttons[action] = change_btn

    # ------------------------------------------------------------------ Preset

    def _on_save_preset(self):
        dialog = tk.Toplevel(self)
        dialog.title('保存预设')
        dialog.geometry('300x120')
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text='请输入预设名称:', font=(Theme.FONT_FAMILY, 10)).pack(padx=15, pady=(15, 5))

        name_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=name_var, font=(Theme.FONT_FAMILY, 10), width=25)
        entry.pack(padx=15, pady=5)
        entry.focus_set()

        auto_name = f'用户预设{len(self.presets)}'
        name_var.set(auto_name)
        entry.select_range(0, tk.END)

        def on_confirm():
            name = name_var.get().strip() or auto_name
            if self._on_save_preset_callback:
                self._on_save_preset_callback(name)
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='确定', command=on_confirm, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='取消', command=dialog.destroy, width=8).pack(side=tk.LEFT, padx=5)

        entry.bind('<Return>', lambda e: on_confirm())

    def _on_rename_preset(self):
        current_id = self._get_current_preset_id()
        if not current_id or current_id == 'default':
            messagebox.showinfo('提示', '默认预设不可重命名')
            return

        dialog = tk.Toplevel(self)
        dialog.title('重命名预设')
        dialog.geometry('300x120')
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text='请输入新名称:', font=(Theme.FONT_FAMILY, 10)).pack(padx=15, pady=(15, 5))

        name_var = tk.StringVar(value=self.presets[current_id]['name'])
        entry = tk.Entry(dialog, textvariable=name_var, font=(Theme.FONT_FAMILY, 10), width=25)
        entry.pack(padx=15, pady=5)
        entry.focus_set()
        entry.select_range(0, tk.END)

        def on_confirm():
            new_name = name_var.get().strip()
            if new_name and self._on_rename_preset_callback:
                self._on_rename_preset_callback(current_id, new_name)
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='确定', command=on_confirm, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='取消', command=dialog.destroy, width=8).pack(side=tk.LEFT, padx=5)

        entry.bind('<Return>', lambda e: on_confirm())

    def _on_delete_preset(self):
        current_id = self._get_current_preset_id()
        if not current_id or current_id == 'default':
            messagebox.showinfo('提示', '默认预设不可删除')
            return

        if messagebox.askyesno('确认删除', f'确定要删除预设 "{self.presets[current_id]["name"]}" 吗？'):
            if self._on_delete_preset_callback:
                self._on_delete_preset_callback(current_id)

    def _get_current_preset_id(self):
        return self._selected_preset_id

    def set_on_preset_callback(self, callback):
        self._on_preset_callback = callback

    def set_on_save_preset_callback(self, callback):
        self._on_save_preset_callback = callback

    def set_on_rename_preset_callback(self, callback):
        self._on_rename_preset_callback = callback

    def set_on_delete_preset_callback(self, callback):
        self._on_delete_preset_callback = callback

    def select_preset(self, preset_id):
        if preset_id in self.presets:
            self._selected_preset_id = preset_id
            self._update_dropdown_display()

    def update_presets(self, presets):
        self.presets = presets
        if presets:
            if self._selected_preset_id not in presets:
                self._selected_preset_id = list(presets.keys())[0]
            self._update_dropdown_display()

    # ------------------------------------------------------------------ Parameter change

    def _on_parameter_change(self, value=None):
        if self._on_change_callback:
            self._on_change_callback(self.get_parameters())

    def set_on_change_callback(self, callback):
        self._on_change_callback = callback

    def get_parameters(self):
        return {
            'sensitivity':           self._sliders['sensitivity'].get_value(),
            'smoothing_factor':      self._sliders['smoothing_factor'].get_value(),
            'deadzone':              self._sliders['deadzone'].get_value(),
            'max_angle':             self._sliders['max_angle'].get_value(),
            'dpi':                   self._sliders['dpi'].get_value(),
            'return_speed':          (self._sliders['return_speed'].get_value()
                                     if 'return_speed' in self._sliders else 0) / 100.0,
            'reverse_direction':     self._reverse_var.get(),
            'assist_rate_window':    self._sliders['assist_rate_window'].get_value() / 1000.0,
            'assist_rate_threshold': self._sliders['assist_rate_threshold'].get_value(),
            'linear_end':            self._sliders['linear_end'].get_value(),
            'assist_threshold':      self._sliders['assist_threshold'].get_value(),
            'assist_return_rate':    self._sliders['assist_return_rate'].get_value() / 100.0,
            'near_center_threshold': self._sliders['near_center_threshold'].get_value(),
            'center_hold_ms': self._sliders['center_hold_ms'].get_value(),
            'center_release_threshold': self._sliders['center_release_threshold'].get_value(),
        }

    def set_parameters(self, params):
        for key, value in params.items():
            if key == 'return_speed':
                value = value * 100.0
            elif key == 'assist_rate_window':
                value = value * 1000.0
            elif key == 'assist_return_rate':
                value = value * 100.0
            if key in self._sliders:
                self._sliders[key].set_value(value)
        if 'reverse_direction' in params and hasattr(self, '_reverse_var'):
            self._reverse_var.set(bool(params['reverse_direction']))

    def set_hotkey_manager(self, hotkey_manager):
        self._hotkey_manager = hotkey_manager
        self.update_hotkey_display()

    def update_hotkey_display(self):
        if self._hotkey_manager and hasattr(self, '_hotkey_actions'):
            for action in self._hotkey_actions:
                hotkey = self._hotkey_manager.get_hotkey(action)
                self._hotkey_display[action].set(hotkey)

    def _start_hotkey_recording(self, action):
        if self._recording_action is not None:
            messagebox.showinfo('提示', '请先完成当前热键的录制')
            return

        self._recording_action = action
        self._hotkey_display[action].set('...')
        btn = self._hotkey_buttons[action]
        btn.config(text='取消')
        btn.unbind('<Button-1>')
        btn.bind('<Button-1>', lambda e: self._cancel_hotkey_recording())

        self.focus_set()
        self.bind('<Key>', self._on_key_press)
        self._cancel_id = self.after(10000, self._cancel_hotkey_recording)

    def _cancel_hotkey_recording(self):
        if self._recording_action is not None:
            self.unbind('<Key>')
            if self._cancel_id:
                self.after_cancel(self._cancel_id)

            action = self._recording_action
            self._recording_action = None

            btn = self._hotkey_buttons[action]
            btn.config(text='修改')
            btn.unbind('<Button-1>')
            btn.bind('<Button-1>',
                     lambda e, a=action: self._start_hotkey_recording(a))
            self.update_hotkey_display()

    def _on_key_press(self, event):
        if self._recording_action is None:
            return

        key = event.keysym
        if key in ['Escape']:
            self._cancel_hotkey_recording()
            return
        if len(key) > 1 and key not in [
            'space', 'Tab', 'Return', 'BackSpace', 'Delete',
            'Insert', 'Home', 'End', 'Prior', 'Next'
        ]:
            key = key.lower()

        if self._hotkey_manager:
            success = self._hotkey_manager.set_hotkey(self._recording_action, key)
            if success:
                self._hotkey_display[self._recording_action].set(key)
                messagebox.showinfo('成功', f'快捷键已修改为: {key}')
            else:
                messagebox.showerror('错误', '设置快捷键失败')

        self._cancel_hotkey_recording()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('参数面板测试')
    root.geometry('320x600')
    root.configure(bg=Theme.SURFACE)

    panel = ParameterPanel(root)
    panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def on_params_change(params):
        print('参数变化:', params)

    panel.set_on_change_callback(on_params_change)

    root.mainloop()
