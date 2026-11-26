# -*- coding: utf-8 -*-
# 导入标准库与第三方库 / Import standard and third-party libraries
import os
import sys
import time
import re
from datetime import datetime
import numpy as np
import pandas as pd

# 锁定 Windows 高分屏 DPI 感知，防止文件弹窗右键重命名等操作引发界面分辨率突变
# Lock Windows DPI awareness before creating Tk root to prevent scaling shifts in file dialogs
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
from threading import Thread

# 强制使用 TkAgg 后端弹出独立 3D 窗口 / Force TkAgg backend to pop up independent 3D window
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 尝试导入核心计算库，如果失败则弹窗报错并退出 / Attempt to import the core calculation library; show error and exit if failed
try:
    import treelight as tl
    from treelight.ies_parser import get_interpolated_intensity
    from treelight.light_analysis import compute_ies_angles
    from treelight.light_analysis import compute_ies_angles
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("环境错误", "未能找到 treelight 核心库！请在环境中执行 'pip install .'")
    sys.exit(1)

# 设置数学公式字体 / Set mathematical formula font
rcParams['mathtext.fontset'] = 'stix'

# 定义多语言UI字典（包含中英文文本） / Define multi-language UI dictionary (contains English and Chinese texts)
LANGUAGES = {
    "en": {
        "language_label": "Language", "lang_en": "English", "lang_zh": "Chinese",
        "app_title": "Tree Lighting & Carbon Reduction Analysis System v1.1",
        "tab_single": " Single Tree Analysis (Visualization) ",
        "tab_batch": " Multi-Tree Analysis (Batch) ",
        "tab_point": " Free-Space Point Analysis (Receptor) ",
        "confirm": "Confirm", "cancel": "Cancel", "warning": "Warning", "error": "Error", "success": "Success",
        "tip": "Tip", "not_loaded": "Not Loaded", "loaded": "Loaded", "close": "Close",
        "tree_morphology": "1. Tree Morphology", "species": "Tree Species:", "tree_height": "Tree Height (m):",
        "branch_height": "Under-branch Height (m):", "crown_width": "Crown Width (m):", "canopy_shape": "Canopy Shape:",
        "light_config": "2. Street Light Configuration", "light_x": "Light X (m):", "light_y": "Light Arm Y (m):",
        "light_z": "Light Height Z (m):", "light_yaw": "Light Yaw (°):", "light_tilt": "Light Tilt (°):",
        "orient_hint": "Yaw: 0°=+X, 90°=+Y, 180°=-X | Tilt: upward elevation (°)",
        "load_ies": "Load IES File",
        "multi_light_toggle": "Enable Multiple Light Sources",
        "add_light_btn": "+ Add Light", "update_light_ies_btn": "Update Selected IES", "remove_light_btn": "Remove Selected", "clear_light_btn": "Clear Extra",
        "extra_ies_btn": "Choose IES", "extra_ies_same": "IES: Same as primary", "select_extra_first": "Please select an additional light in the list first!",
        "extra_lights_label": "Additional Lights (X, Y, Z, Yaw°, Tilt°):",
        "calc_params": "3. Calculation Parameters", "grid_precision": "Grid Precision (m²):",
        "maintenance_factor": "Maintenance Factor:", "color_temp_factor": "Color Temp Factor:",
        "cosine_toggle": "Apply Cosine Correction (cos α)",
        "run_calc": "Start Calculation", "3d_visual": "3D Visualization", "analysis_report": "Analysis Report",
        "export_script": "Export Reproducible Script (.py)",
        "batch_file_config": "1. Batch File Configuration", "load_ies_batch": "① Load Default IES File",
        "select_ies_dir": "② Select IES Folder (Optional, for Excel 'IES File' column)",
        "default_ies_dir": "Default: Folder of default IES file",
        "load_excel": "③ Select Excel/CSV for Processing", "load_excel_step": "③ Select Excel/CSV for Processing",
        "select_out_dir": "④ Select Output Folder (Optional)",
        "default_out_dir": "Default: Same directory as input file",
        "global_calc_params": "2. Global Calculation Parameters", "add_species_btn": "Add/Update Tree Species Params",
        "run_batch_calc": "Start Batch Analysis", "running_log": "Running Log",
        "point_origin_frame": "1. Relative Target Coordinates (Lamp at Origin 0, 0, 0)",
        "point_dx": "Relative ΔX (m):", "point_dy": "Relative ΔY (m):", "point_dz": "Relative ΔZ (m):",
        "point_dz_hint": "Note: Lamp is at (0, 0, 0); negative ΔZ means below the luminaire (e.g., -5.0 m).",
        "point_ies_frame": "2. Luminaire & Calculation Settings",
                "point_cosine_toggle": "Apply Horizontal Cosine Correction (cos α)",
        "point_cosine_note": (
            "Note: OFF by default for scalar irradiance (I/d²), suited to non-planar receptors (e.g., buds, animal eyes). "
            "Turn ON for horizontal planar irradiance (I/d²·cos α, e.g., horizontal PPFD sensors)."
        ),
        "point_run_calc": "Calculate Point PPFD",
        "point_report_title": "Point Light-Field Report",
        "point_zero_dist": "Target point cannot coincide with any luminaire position!",
        "point_extra_lights_label": "Additional Lights (X, Y, Z relative to Lamp 1 at 0,0,0):",
        "species_dialog_title": "Add/Update Tree Species Parameters", "species_name": "Species Name:",
        "alpha": "Apparent Quantum Efficiency (α):", "rd": "Dark Respiration Rate (Rd):", "lcp": "Light Compensation Point (LCP):",
        "save_config": "Save Configuration", "colortemp_dialog_title": "Add Color Temp Factor",
        "ct_identifier": "Identifier (e.g. 6000K LED):", "ct_factor": "PPFD Conversion Factor:",
        "del_species_title": "Manage / Delete Tree Species",
        "del_light_title": "Manage / Delete Light Factors",
        "del_dialog_hint": "Select one or more custom items to delete (built-in defaults are protected):",
        "del_selected_btn": "Delete Selected",
        "no_selection_warning": "Please select at least one item to delete.",
        "confirm_delete_items": "Confirm deletion of {0} selected item(s)?",
        "delete_summary": "Deleted {0} item(s). Skipped built-in: {1}.",
        "tag_builtin": "[Built-in]", "tag_custom": "[Custom]",
        "name_empty": "Name cannot be empty!", "invalid_number": "Parameters must be valid numbers!",
        "positive_param_warning": "Tree height, crown width, grid precision, and maintenance factor must be > 0 (and tree height > branch height).",
        "batch_param_warning": "Grid precision and maintenance factor must be > 0.",
        "species_saved": "Species {0} has been saved!", "colortemp_saved": "Color Temperature {0} has been added!",
        "no_ies_warning": "Please load the IES file first!", "no_excel_warning": "Please select the file to process first!",
        "invalid_param": "Invalid parameter input!", "no_calc_warning": "Please run the calculation first!",
        "batch_finished": "Batch calculation completed!", "system_log": "[System]",
        "excel_loaded": "Data file loaded: {0}", "simulating": ">>> Performing physical lighting simulation...",
        "analysis_finish": "Analysis Completed: {0}", "canopy_type": "Canopy Type: {0}", "grid_points": "Grid Points: {0}",
        "total_area": "Total Surface Area: {0:.2f} m²", "max_ppfd": "Max PPFD: {0:.2f} μmol/m²/s", "avg_ppfd": "Average Effective PPFD: {0:.2f} μmol/m²/s",
        "yearly_carbon": "Annual Carbon Reduction: {0:.4f} g", "area_distribution": "【Light Area Distribution Statistics】",
        "interval": "  Interval [{0}]: {1:.2f} m²", "reading_excel": ">>> Reading file data: {0}",
        "excel_read_fail": "!!! File read failed: {0}", "total_data": ">>> Total {0} entries to process...",
        "progress": "  -> Progress: {0}/{1} ...", "batch_complete": ">>> Batch processing completed! Time elapsed: {0:.1f}s",
        "result_saved": ">>> Results saved to:\n{0}", "script_exported": "Script successfully exported to:\n{0}",
        "using_default_ies": "⚠️ No IES loaded manually. Using default built-in IES.",
        "visual_title": "PPFD Heatmap (Academic Visualization)",
        "light_count_info": "Light Sources Used: {0} | Cosine Correction: {1}"
    },
    "zh": {
        "language_label": "语言", "lang_en": "英文", "lang_zh": "中文",
        "app_title": "树木光照与碳减排综合分析系统 v1.1",
        "tab_single": " 单棵树分析 (可视化) ",
        "tab_batch": " 多棵树分析 (批量处理) ",
        "tab_point": " 空间单点分析 (非冠层受体) ",
        "confirm": "确认", "cancel": "取消", "warning": "提示", "error": "错误", "success": "成功",
        "tip": "提示", "not_loaded": "未加载", "loaded": "已加载", "close": "关闭",
        "tree_morphology": "1. 树木形态", "species": "树种:", "tree_height": "树高 (m):",
        "branch_height": "枝下高 (m):", "crown_width": "冠幅 (m):", "canopy_shape": "冠形:",
        "light_config": "2. 路灯配置", "light_x": "灯距X (m):", "light_y": "灯臂Y (m):",
        "light_z": "灯高Z (m):", "light_yaw": "水平朝向 Yaw (°):", "light_tilt": "灯具仰角 Tilt (°):",
        "orient_hint": "Yaw: 0°=+X, 90°=+Y, 180°=-X | Tilt: 向上仰角 (°)",
        "load_ies": "加载IES文件",
        "multi_light_toggle": "启用多光源叠加",
        "add_light_btn": "+ 添加光源", "update_light_ies_btn": "更换选中IES", "remove_light_btn": "删除选中", "clear_light_btn": "清空附加光源",
        "extra_ies_btn": "选择独立IES", "extra_ies_same": "IES: 同主光源", "select_extra_first": "请先在列表中选中要更换 IES 的附加光源！",
        "extra_lights_label": "附加光源 (X, Y, Z, Yaw°, Tilt°):",
        "calc_params": "3. 计算参数", "grid_precision": "网格精度(m²):",
        "maintenance_factor": "维护系数:", "color_temp_factor": "色温因子:",
        "cosine_toggle": "启用余弦校正 (cos α)",
        "run_calc": "开始计算", "3d_visual": "3D 可视化", "analysis_report": "分析报告",
        "export_script": "导出可复现执行脚本 (.py)",
        "batch_file_config": "1. 批量文件配置", "load_ies_batch": "① 加载默认 IES 文件",
        "select_ies_dir": "② 选择 IES 文件夹 (可选，按表内 IES File 列匹配)",
        "default_ies_dir": "默认: 与默认 IES 文件同级目录",
        "load_excel": "③ 选择待处理 Excel/CSV", "load_excel_step": "③ 选择待处理 Excel/CSV",
        "select_out_dir": "④ 选择输出文件夹 (可选)",
        "default_out_dir": "默认: 待处理文件同级目录",
        "global_calc_params": "2. 全局计算参数", "add_species_btn": "添加/更新树种参数",
        "run_batch_calc": "开始批量分析", "running_log": "运行日志",
        "point_origin_frame": "1. 目标点相对坐标 (以光源为原点 0, 0, 0)",
        "point_dx": "相对 ΔX (m):", "point_dy": "相对 ΔY (m):", "point_dz": "相对 ΔZ (m):",
        "point_dz_hint": "提示：光源位于原点 (0, 0, 0)；ΔZ 为负值表示在灯具下方（如 -5.0 m）。",
        "point_ies_frame": "2. 灯具与计算参数",
                "point_cosine_toggle": "启用水平余弦校正 (cos α)",
        "point_cosine_note": (
            "备注：默认关闭以计算标量辐照度 (I/d²)，适用于芽体、生物眼睛等非平面受体。"
            "勾选后计算水平面辐照度 (I/d²·cos α)，适用于水平 PPFD 传感器。"
        ),
        "point_run_calc": "计算该点光照",
        "point_report_title": "空间单点光场分析报告",
        "point_zero_dist": "目标点不能与任一光源坐标重合！",
        "point_extra_lights_label": "附加光源 (相对主灯 0,0,0 的 X, Y, Z, Yaw°, Tilt°):",
        "species_dialog_title": "添加/更新树种参数", "species_name": "树种名称:",
        "alpha": "表观量子效率 (α):", "rd": "暗呼吸速率 (Rd):", "lcp": "光补偿点 (LCP):",
        "save_config": "保存配置", "colortemp_dialog_title": "添加色温转换因子",
        "ct_identifier": "标识 (如 6000K LED):", "ct_factor": "PPFD 转换因子:",
        "del_species_title": "管理 / 删除树种配置",
        "del_light_title": "管理 / 删除光源因子配置",
        "del_dialog_hint": "可多选需要删除的自定义配置（内置默认项受保护不可删除）：",
        "del_selected_btn": "删除选中项",
        "no_selection_warning": "请先选择至少一项需要删除的配置。",
        "confirm_delete_items": "确认删除所选的 {0} 项配置吗？",
        "delete_summary": "已删除 {0} 项自定义配置（跳过内置项：{1} 项）。",
        "tag_builtin": "[内置]", "tag_custom": "[自定义]",
        "name_empty": "名称不能为空！", "invalid_number": "参数必须是有效数字！",
        "positive_param_warning": "请先输入大于 0 的树高、冠幅、网格精度与维护系数（且树高需大于枝下高）。",
        "batch_param_warning": "请先输入大于 0 的网格精度与维护系数。",
        "species_saved": "树种 {0} 已保存并同步！", "colortemp_saved": "色温 {0} 已添加！",
        "no_ies_warning": "请先加载IES文件！", "no_excel_warning": "请先选择需要处理的文件！",
        "invalid_param": "参数输入无效！", "no_calc_warning": "请先执行计算！",
        "batch_finished": "批量计算完成！", "system_log": "[系统]",
        "excel_loaded": "已加载文件: {0}", "simulating": ">>> 正在进行物理光照模拟...",
        "analysis_finish": "分析完成：{0}", "canopy_type": "树冠类型：{0}", "grid_points": "网格点数：{0}",
        "total_area": "总表面积: {0:.2f} m²", "max_ppfd": "最大PPFD: {0:.2f} μmol/m²/s", "avg_ppfd": "平均有效PPFD: {0:.2f} μmol/m²/s",
        "yearly_carbon": "年碳减排量: {0:.4f} g", "area_distribution": "【受光面积分布统计】",
        "interval": "  区间 [{0}]: {1:.2f} m²", "reading_excel": ">>> 开始读取文件数据: {0}",
        "excel_read_fail": "!!! 读取失败: {0}", "total_data": ">>> 共有 {0} 条数据待处理...",
        "progress": "  -> 进度: {0}/{1} ...", "batch_complete": ">>> 处理完成！耗时: {0:.1f}s",
        "result_saved": ">>> 结果已保存至:\n{0}", "script_exported": "脚本已成功导出至:\n{0}",
        "using_default_ies": "⚠️ 未手动加载配光文件，已启用系统默认 IES。",
        "visual_title": "PPFD热力图 (学术可视化)",
        "light_count_info": "参与计算光源数: {0} | 余弦校正: {1}"
    }
}


class TreeLightingGUI:
    # 主GUI类定义 / Main GUI class definition
    def __init__(self, root):
        self.root = root
        self.current_lang = "en"
        self.translatable_widgets = []
        self.root.resizable(True, True)

        # 统一全局字体（解决 Windows 高分屏下标签、输入框、下拉框与选项卡字号不一致的问题）
        # Unify all Tk and ttk widget fonts for consistent High-DPI rendering
        ui_font = ("Microsoft YaHei", 9)
        ui_font_bold = ("Microsoft YaHei", 9, "bold")
        for fname in ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont", "TkCaptionFont"):
            try:
                tkfont.nametofont(fname).configure(family="Microsoft YaHei", size=9)
            except Exception:
                pass
        self.root.option_add("*Font", ui_font)
        self.root.option_add("*TCombobox*Listbox.font", ui_font)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", font=ui_font)
        style.configure("TLabel", font=ui_font)
        style.configure("TButton", font=ui_font, padding=[6, 2])
        style.configure("TEntry", font=ui_font)
        style.configure("TCombobox", font=ui_font)
        style.configure("TCheckbutton", font=ui_font)
        style.configure("TLabelframe.Label", font=ui_font_bold)
        style.configure("TNotebook.Tab", font=ui_font, padding=[8, 3])

        # 初始化文件路径和缓存变量 / Initialize file paths and cache variables
        self.ies_path_single = None
        self.ies_data_single = None
        self.ies_path_batch = None
        self.ies_data_batch = None
        self.ies_path_point = None
        self.ies_data_point = None
        self.ies_dir_batch = None
        self.excel_path = None
        self.output_dir = None
        self.last_physics_res = None
        self.last_species = None
        self.last_point_res = None

        # 附加光源列表（用于单树多光源叠加）/ Extra light sources list
        self.extra_lights = []
        self.pending_extra_ies_path = None
        self.pending_extra_ies_data = None
        self.extra_lights_point = []
        self.pending_point_ies_path = None
        self.pending_point_ies_data = None

        # 开关状态变量 / Boolean toggle variables
        self.var_multi_light = tk.BooleanVar(value=False)
        self.var_multi_light_point = tk.BooleanVar(value=False)
        self.var_cosine_single = tk.BooleanVar(value=True)
        self.var_cosine_batch = tk.BooleanVar(value=True)
        self.var_cosine_point = tk.BooleanVar(value=False)  # 单点模式默认关闭余弦校正

        # 构建界面并应用语言、字体与自适应初始尺寸 / Build UI, apply language/font, and auto-fit window
        self.build_ui()
        self.refresh_ui_language()
        self.refresh_font()
        self._fit_main_window()

    def _fit_main_window(self):
        """Auto-size the main window using the true inner panel height so every control is visible on launch."""
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        left_w = self._left_panel_single.winfo_reqwidth()
        left_h = self._left_panel_single.winfo_reqheight()
        # Account for language bar + notebook tabs + borders (~105 px)
        needed_w = left_w + 540
        needed_h = left_h + 115
        init_w = min(max(needed_w, 1080), int(sw * 0.92))
        init_h = min(max(needed_h, 680), int(sh * 0.90))
        x = max(0, (sw - init_w) // 2)
        y = max(0, (sh - init_h) // 2)
        self.root.geometry(f"{init_w}x{init_h}+{x}+{y}")
        self.root.minsize(min(860, int(sw * 0.72)), min(580, int(sh * 0.68)))

    def _finalize_dialog(self, win, pad_w=40, pad_h=24):
        """Auto-size and center any popup dialog so all widgets are fully visible and resizable."""
        win.transient(self.root)
        win.resizable(True, True)
        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        w = min(win.winfo_reqwidth() + pad_w, int(sw * 0.85))
        h = min(win.winfo_reqheight() + pad_h, int(sh * 0.85))
        x = max(0, self.root.winfo_rootx() + (self.root.winfo_width() - w) // 2)
        y = max(0, self.root.winfo_rooty() + (self.root.winfo_height() - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.minsize(w, h)

    def _create_scrollable_left_pane(self, paned_parent):
        """Create a responsive left pane that expands with window resize and scrolls only if shrunk too small."""
        container = ttk.Frame(paned_parent)
        canvas = tk.Canvas(container, highlightthickness=0, borderwidth=0)
        vbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)

        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)

        def _on_inner_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 自动调整最小宽度以防控件被裁切 / Keep canvas wide enough for controls
            min_w = inner.winfo_reqwidth()
            if canvas.winfo_width() < min_w:
                canvas.configure(width=min_w)

        def _on_canvas_configure(event):
            canvas.itemconfigure(inner_id, width=event.width)

        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # 鼠标滚轮支持 / Mouse wheel scrolling when needed
        def _on_mousewheel(event):
            if inner.winfo_reqheight() > canvas.winfo_height():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        return container, inner

    def get_text(self, key, *args):
        text = LANGUAGES[self.current_lang].get(key, key)
        if args:
            text = text.format(*args)
        return text

    def register_text(self, widget, lang_key, attr="text"):
        try:
            widget.config(**{attr: self.get_text(lang_key)})
        except Exception:
            pass
        self.translatable_widgets.append((widget, lang_key, attr))
        return widget

    def refresh_ui_language(self):
        self.root.title(self.get_text("app_title"))
        self.notebook.tab(0, text=self.get_text("tab_single"))
        self.notebook.tab(1, text=self.get_text("tab_batch"))
        self.notebook.tab(2, text=self.get_text("tab_point"))

        # Preserve already-loaded file/folder display names when toggling language
        loaded_skip = set()
        if self.ies_path_single: loaded_skip.add(getattr(self, "lbl_ies1", None))
        if self.ies_path_batch: loaded_skip.add(getattr(self, "lbl_ies2", None))
        if self.ies_path_point: loaded_skip.add(getattr(self, "lbl_ies3", None))
        if self.ies_dir_batch: loaded_skip.add(getattr(self, "lbl_iesdir", None))
        if self.excel_path: loaded_skip.add(getattr(self, "lbl_excel", None))
        if self.output_dir: loaded_skip.add(getattr(self, "lbl_outdir", None))
        if self.pending_extra_ies_path: loaded_skip.add(getattr(self, "lbl_extra_ies", None))
        if self.pending_point_ies_path: loaded_skip.add(getattr(self, "lbl_pt_extra_ies", None))

        for widget, key, attr in self.translatable_widgets:
            if widget in loaded_skip:
                continue
            try:
                widget.config(**{attr: self.get_text(key)})
            except Exception:
                pass

        self.cb_language['values'] = [self.get_text("lang_en"), self.get_text("lang_zh")]
        if self.current_lang == "en":
            self.cb_language.current(0)
        else:
            self.cb_language.current(1)

    def on_language_selected(self, event):
        selected_text = self.cb_language.get()
        if selected_text == self.get_text("lang_en"):
            self.current_lang = "en"
        elif selected_text == self.get_text("lang_zh"):
            self.current_lang = "zh"
        self.refresh_ui_language()
        self.refresh_font()

    def refresh_font(self):
        if self.current_lang == "zh":
            rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'Times New Roman']
        else:
            rcParams['font.family'] = 'Times New Roman'
        plt.rcParams.update(rcParams)

    def create_entry(self, parent, lang_key, default, row, width=14):
        parent.columnconfigure(1, weight=1)
        label = self.register_text(ttk.Label(parent), lang_key)
        label.grid(row=row, column=0, sticky="e", padx=5, pady=2)
        entry = ttk.Entry(parent, width=width)
        entry.insert(0, default)
        entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=2)
        return label, entry

    def create_combobox_with_add(self, parent, lang_key, values, row, add_cmd, del_cmd=None):
        parent.columnconfigure(1, weight=1)
        label = self.register_text(ttk.Label(parent), lang_key)
        label.grid(row=row, column=0, sticky="e", padx=5, pady=2)
        cb = ttk.Combobox(parent, values=values, state="readonly", width=24)
        if values:
            cb.current(0)
        cb.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        btn_box = ttk.Frame(parent)
        btn_box.grid(row=row, column=2, sticky="w", padx=3, pady=3)
        ttk.Button(btn_box, text="+", width=3, command=add_cmd).pack(side=tk.LEFT, padx=1)
        if del_cmd is not None:
            ttk.Button(btn_box, text="-", width=3, command=del_cmd).pack(side=tk.LEFT, padx=1)
        return label, cb

    def _log(self, text_widget, msg_key, *args):
        if msg_key == "raw":
            msg = args[0]
        else:
            msg = self.get_text(msg_key, *args)
        self.root.after(0, lambda: [text_widget.insert(tk.END, msg + "\n"), text_widget.see(tk.END)])

    def build_ui(self):
        self.lang_bar = ttk.Frame(self.root)
        self.lang_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=4)
        self.register_text(ttk.Label(self.lang_bar), "language_label").pack(side=tk.RIGHT, padx=5, pady=2)

        self.cb_language = ttk.Combobox(self.lang_bar, state="readonly", width=12)
        self.cb_language.pack(side=tk.RIGHT, padx=5, pady=2)
        self.cb_language.bind("<<ComboboxSelected>>", self.on_language_selected)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.tab_single = ttk.Frame(self.notebook)
        self.tab_batch = ttk.Frame(self.notebook)
        self.tab_point = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_single, text="")
        self.notebook.add(self.tab_batch, text="")
        self.notebook.add(self.tab_point, text="")

        self.setup_single_tab()
        self.setup_batch_tab()
        self.setup_point_tab()

    # =====================================================================
    # Tab 1: Single Tree Analysis / 单棵树分析
    # =====================================================================
    def setup_single_tab(self):
        paned = ttk.PanedWindow(self.tab_single, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        left_container, left_panel = self._create_scrollable_left_pane(paned)
        self._left_panel_single = left_panel
        paned.add(left_container, weight=1)

        # 1. 树木形态设置区域（默认输入均为 0）/ Tree morphology (all numeric defaults = 0)
        self.lf_tree = self.register_text(ttk.LabelFrame(left_panel), "tree_morphology")
        self.lf_tree.pack(fill=tk.X, padx=4, pady=2)
        self.lb_species, self.cb_species = self.create_combobox_with_add(
            self.lf_tree, "species", tl.get_available_species(), 0,
            self.add_species_dialog, self.delete_species_dialog
        )
        self.lb_height, self.en_height = self.create_entry(self.lf_tree, "tree_height", "0", 1)
        self.lb_branch, self.en_branch = self.create_entry(self.lf_tree, "branch_height", "0", 2)
        self.lb_crown, self.en_crown = self.create_entry(self.lf_tree, "crown_width", "0", 3)

        self.register_text(ttk.Label(self.lf_tree), "canopy_shape").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        self.cb_shape = ttk.Combobox(
            self.lf_tree,
            values=["半椭球体/Half Ellipsoid", "圆锥体/Cone", "圆柱体/Cylinder"],
            state="readonly", width=24
        )
        self.cb_shape.current(0)
        self.cb_shape.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=2)

        # 2. 路灯配置区域（含多光源开关，默认坐标均为 0）/ Street light config (defaults = 0)
        self.lf_light = self.register_text(ttk.LabelFrame(left_panel), "light_config")
        self.lf_light.pack(fill=tk.X, padx=4, pady=2)
        self.lb_lx, self.en_lx = self.create_entry(self.lf_light, "light_x", "0", 0)
        self.lb_ly, self.en_ly = self.create_entry(self.lf_light, "light_y", "0", 1)
        self.lb_lz, self.en_lz = self.create_entry(self.lf_light, "light_z", "0", 2)
        self.lb_lyaw, self.en_lyaw = self.create_entry(self.lf_light, "light_yaw", "0", 3)
        self.lb_ltilt, self.en_ltilt = self.create_entry(self.lf_light, "light_tilt", "0", 4)

        self.lbl_orient_hint = self.register_text(
            ttk.Label(self.lf_light, foreground="#555555"), "orient_hint"
        )
        self.lbl_orient_hint.grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=1)

        self.chk_multi_light = self.register_text(
            ttk.Checkbutton(self.lf_light, variable=self.var_multi_light, command=self.toggle_multi_light_panel),
            "multi_light_toggle"
        )
        self.chk_multi_light.grid(row=6, column=0, columnspan=3, sticky="w", padx=8, pady=2)

        self.multi_light_frame = ttk.Frame(self.lf_light)
        for col in (1, 3, 5):
            self.multi_light_frame.columnconfigure(col, weight=1)
        self.register_text(ttk.Label(self.multi_light_frame), "extra_lights_label").grid(
            row=0, column=0, columnspan=6, sticky="w", padx=4, pady=1
        )
        ttk.Label(self.multi_light_frame, text="X:").grid(row=1, column=0, sticky="e", padx=2)
        self.en_extra_x = ttk.Entry(self.multi_light_frame, width=6)
        self.en_extra_x.insert(0, "0")
        self.en_extra_x.grid(row=1, column=1, sticky="ew", padx=2)

        ttk.Label(self.multi_light_frame, text="Y:").grid(row=1, column=2, sticky="e", padx=2)
        self.en_extra_y = ttk.Entry(self.multi_light_frame, width=6)
        self.en_extra_y.insert(0, "0")
        self.en_extra_y.grid(row=1, column=3, sticky="ew", padx=2)

        ttk.Label(self.multi_light_frame, text="Z:").grid(row=1, column=4, sticky="e", padx=2)
        self.en_extra_z = ttk.Entry(self.multi_light_frame, width=6)
        self.en_extra_z.insert(0, "0")
        self.en_extra_z.grid(row=1, column=5, sticky="ew", padx=2)

        ttk.Label(self.multi_light_frame, text="Yaw:").grid(row=2, column=0, sticky="e", padx=2, pady=2)
        self.en_extra_yaw = ttk.Entry(self.multi_light_frame, width=6)
        self.en_extra_yaw.insert(0, "0")
        self.en_extra_yaw.grid(row=2, column=1, sticky="ew", padx=2, pady=2)

        ttk.Label(self.multi_light_frame, text="Tilt:").grid(row=2, column=2, sticky="e", padx=2, pady=2)
        self.en_extra_tilt = ttk.Entry(self.multi_light_frame, width=6)
        self.en_extra_tilt.insert(0, "0")
        self.en_extra_tilt.grid(row=2, column=3, sticky="ew", padx=2, pady=2)

        ttk.Label(self.multi_light_frame, text="CCT/k:").grid(row=2, column=4, sticky="e", padx=2, pady=2)
        self.cb_extra_temp = ttk.Combobox(self.multi_light_frame, values=["Same / 同主灯"] + tl.get_available_lights(), state="readonly", width=11)
        self.cb_extra_temp.current(0)
        self.cb_extra_temp.grid(row=2, column=5, sticky="ew", padx=2, pady=2)

        ies_row = ttk.Frame(self.multi_light_frame)
        ies_row.grid(row=3, column=0, columnspan=6, sticky="ew", padx=2, pady=2)
        self.register_text(ttk.Button(ies_row, command=self.choose_pending_extra_ies), "extra_ies_btn").pack(side=tk.LEFT, padx=2)
        self.lbl_extra_ies = self.register_text(ttk.Label(ies_row, foreground="#475569"), "extra_ies_same")
        self.lbl_extra_ies.pack(side=tk.LEFT, padx=4)

        btn_row = ttk.Frame(self.multi_light_frame)
        btn_row.grid(row=4, column=0, columnspan=6, sticky="ew", pady=2)
        self.register_text(ttk.Button(btn_row, command=self.add_extra_light), "add_light_btn").pack(side=tk.LEFT, padx=2)
        self.register_text(ttk.Button(btn_row, command=self.update_selected_extra_ies), "update_light_ies_btn").pack(side=tk.LEFT, padx=2)
        self.register_text(ttk.Button(btn_row, command=self.remove_extra_light), "remove_light_btn").pack(side=tk.LEFT, padx=2)
        self.register_text(ttk.Button(btn_row, command=self.clear_extra_lights), "clear_light_btn").pack(side=tk.LEFT, padx=2)

        self.lb_extra_lights = tk.Listbox(self.multi_light_frame, height=3, font=("Consolas", 9))
        self.lb_extra_lights.grid(row=5, column=0, columnspan=6, sticky="ew", padx=4, pady=2)

        self.btn_ies1 = self.register_text(ttk.Button(self.lf_light, command=lambda: self.load_ies(1)), "load_ies")
        self.btn_ies1.grid(row=8, column=0, columnspan=3, pady=3, sticky="ew", padx=10)
        self.lbl_ies1 = self.register_text(ttk.Label(self.lf_light, foreground="red"), "not_loaded")
        self.lbl_ies1.grid(row=9, column=0, columnspan=3, pady=1)

        # 3. 计算参数区域（默认输入为 0）/ Calculation parameters (defaults = 0)
        self.lf_calc1 = self.register_text(ttk.LabelFrame(left_panel), "calc_params")
        self.lf_calc1.pack(fill=tk.X, padx=4, pady=2)
        self.lb_prec1, self.en_prec1 = self.create_entry(self.lf_calc1, "grid_precision", "0.05", 0)
        self.lb_mf1, self.en_mf1 = self.create_entry(self.lf_calc1, "maintenance_factor", "1", 1)
        self.lb_temp1, self.cb_temp1 = self.create_combobox_with_add(
            self.lf_calc1, "color_temp_factor", tl.get_available_lights(), 2,
            self.add_colortemp_dialog, self.delete_colortemp_dialog
        )
        self.chk_cosine1 = self.register_text(
            ttk.Checkbutton(self.lf_calc1, variable=self.var_cosine_single),
            "cosine_toggle"
        )
        self.chk_cosine1.grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=4)

        # 按钮控制区域 / Button control area
        self.btn_calc1 = self.register_text(ttk.Button(left_panel, command=self.run_single_calc), "run_calc")
        self.btn_calc1.pack(fill=tk.X, padx=4, pady=2)
        self.btn_visual = self.register_text(ttk.Button(left_panel, command=self.show_visual), "3d_visual")
        self.btn_visual.pack(fill=tk.X, padx=4, pady=2)
        self.btn_export1 = self.register_text(ttk.Button(left_panel, command=self.export_single_script), "export_script")
        self.btn_export1.pack(fill=tk.X, padx=4, pady=3)

        # 右侧分析报告输出框 / Right analysis report pane
        self.lf_report = self.register_text(ttk.LabelFrame(paned), "analysis_report")
        paned.add(self.lf_report, weight=2)
        scroll1 = ttk.Scrollbar(self.lf_report)
        scroll1.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_out1 = tk.Text(self.lf_report, font=("Consolas", 9), yscrollcommand=scroll1.set)
        self.txt_out1.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll1.config(command=self.txt_out1.yview)

    def toggle_multi_light_panel(self):
        if self.var_multi_light.get():
            self.multi_light_frame.grid(row=7, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        else:
            self.multi_light_frame.grid_forget()

    def choose_pending_extra_ies(self):
        f = filedialog.askopenfilename(parent=self.root, filetypes=[("IES Files", "*.ies")])
        if f:
            data, msg = tl.parse_ies_full(f)
            if "✅" in msg:
                self.pending_extra_ies_path = f
                self.pending_extra_ies_data = data
                self.lbl_extra_ies.config(text=f"IES: {os.path.basename(f)}", foreground="green")
            else:
                messagebox.showerror("IES Parse Error", msg, parent=self.root)

    def update_selected_extra_ies(self):
        sel = self.lb_extra_lights.curselection()
        if not sel:
            return messagebox.showwarning(self.get_text("warning"), self.get_text("select_extra_first"), parent=self.root)
        f = filedialog.askopenfilename(parent=self.root, filetypes=[("IES Files", "*.ies")])
        if f:
            data, msg = tl.parse_ies_full(f)
            if "✅" in msg:
                idx = sel[0]
                self.extra_lights[idx]["ies_path"] = f
                self.extra_lights[idx]["ies_data"] = data
                self._refresh_extra_lights_listbox()
                self._log(self.txt_out1, "raw", f"Updated Lamp {idx + 2} IES: {os.path.basename(f)}")
            else:
                messagebox.showerror("IES Parse Error", msg, parent=self.root)

    def add_extra_light(self):
        try:
            x = float(self.en_extra_x.get())
            y = float(self.en_extra_y.get())
            z = float(self.en_extra_z.get())
            yaw = float(self.en_extra_yaw.get())
            tilt = float(self.en_extra_tilt.get())
            sel_temp = self.cb_extra_temp.get()
            is_same_k = (not sel_temp) or sel_temp.startswith("Same")
            lamp_light_name = None if is_same_k else sel_temp
            lamp_k = None if is_same_k else float(tl.get_ppfd_factor(sel_temp))
            self.extra_lights.append({
                "x": x, "y": y, "z": z, "yaw": yaw, "tilt": tilt,
                "light_name": lamp_light_name, "ppfd_factor": lamp_k,
                "ies_path": self.pending_extra_ies_path,
                "ies_data": self.pending_extra_ies_data
            })
            self.cb_extra_temp.current(0)
            self.pending_extra_ies_path = None
            self.pending_extra_ies_data = None
            self.lbl_extra_ies.config(text=self.get_text("extra_ies_same"), foreground="#475569")
            self._refresh_extra_lights_listbox()
        except ValueError:
            messagebox.showerror(self.get_text("error"), self.get_text("invalid_number"))

    def remove_extra_light(self):
        sel = self.lb_extra_lights.curselection()
        if sel:
            self.extra_lights.pop(sel[0])
            self._refresh_extra_lights_listbox()

    def clear_extra_lights(self):
        self.extra_lights.clear()
        self._refresh_extra_lights_listbox()

    def _refresh_extra_lights_listbox(self):
        self.lb_extra_lights.delete(0, tk.END)
        for i, lp in enumerate(self.extra_lights, start=2):
            ies_tag = os.path.basename(lp["ies_path"]) if lp.get("ies_path") else "Primary IES"
            k_tag = lp["light_name"] if lp.get("light_name") else "Primary k"
            self.lb_extra_lights.insert(
                tk.END,
                f"Lamp {i}: ({lp['x']}, {lp['y']}, {lp['z']}) | yaw={lp['yaw']}°, tilt={lp['tilt']}° | {k_tag} | {ies_tag}"
            )

    def _get_single_light_pos_list(self):
        primary_k = float(tl.get_ppfd_factor(self.cb_temp1.get()))
        primary = {
            "x": float(self.en_lx.get()), "y": float(self.en_ly.get()), "z": float(self.en_lz.get()),
            "yaw": float(self.en_lyaw.get()), "tilt": float(self.en_ltilt.get()),
            "ppfd_factor": primary_k,
            "ies_path": self.ies_path_single, "ies_data": self.ies_data_single
        }
        if self.var_multi_light.get() and self.extra_lights:
            out = [primary]
            for lp in self.extra_lights:
                out.append({
                    "x": lp["x"], "y": lp["y"], "z": lp["z"],
                    "yaw": lp["yaw"], "tilt": lp["tilt"],
                    "ppfd_factor": lp["ppfd_factor"] if lp.get("ppfd_factor") is not None else primary_k,
                    "ies_path": lp.get("ies_path") or self.ies_path_single,
                    "ies_data": lp.get("ies_data") or self.ies_data_single
                })
            return out
        return [primary]

    # =====================================================================
    # Tab 2: Batch Tree Analysis / 多棵树批量分析
    # =====================================================================
    def setup_batch_tab(self):
        paned = ttk.PanedWindow(self.tab_batch, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        left_container, left_panel = self._create_scrollable_left_pane(paned)
        paned.add(left_container, weight=1)

        self.lf_file = self.register_text(ttk.LabelFrame(left_panel), "batch_file_config")
        self.lf_file.pack(fill=tk.X, padx=4, pady=5)

        self.btn_ies2 = self.register_text(ttk.Button(self.lf_file, command=lambda: self.load_ies(2)), "load_ies_batch")
        self.btn_ies2.pack(fill=tk.X, padx=10, pady=4)
        self.lbl_ies2 = self.register_text(ttk.Label(self.lf_file, foreground="red"), "not_loaded")
        self.lbl_ies2.pack(pady=1)

        self.btn_iesdir = self.register_text(ttk.Button(self.lf_file, command=self.choose_ies_dir), "select_ies_dir")
        self.btn_iesdir.pack(fill=tk.X, padx=10, pady=4)
        self.lbl_iesdir = self.register_text(ttk.Label(self.lf_file, foreground="gray"), "default_ies_dir")
        self.lbl_iesdir.pack(pady=1)

        self.btn_excel = self.register_text(ttk.Button(self.lf_file, command=self.load_excel), "load_excel_step")
        self.btn_excel.pack(fill=tk.X, padx=10, pady=4)
        self.lbl_excel = self.register_text(ttk.Label(self.lf_file, foreground="red"), "not_loaded")
        self.lbl_excel.pack(pady=1)

        self.btn_outdir = self.register_text(ttk.Button(self.lf_file, command=self.choose_out_dir), "select_out_dir")
        self.btn_outdir.pack(fill=tk.X, padx=10, pady=5)
        self.lbl_outdir = self.register_text(ttk.Label(self.lf_file, foreground="gray"), "default_out_dir")
        self.lbl_outdir.pack(pady=2)

        self.lf_calc2 = self.register_text(ttk.LabelFrame(left_panel), "global_calc_params")
        self.lf_calc2.pack(fill=tk.X, padx=4, pady=8)

        self.lb_prec2, self.en_prec2 = self.create_entry(self.lf_calc2, "grid_precision", "0.05", 0)
        self.lb_mf2, self.en_mf2 = self.create_entry(self.lf_calc2, "maintenance_factor", "1", 1)
        self.lb_temp2, self.cb_temp2 = self.create_combobox_with_add(
            self.lf_calc2, "color_temp_factor", tl.get_available_lights(), 2,
            self.add_colortemp_dialog, self.delete_colortemp_dialog
        )
        self.chk_cosine2 = self.register_text(
            ttk.Checkbutton(self.lf_calc2, variable=self.var_cosine_batch),
            "cosine_toggle"
        )
        self.chk_cosine2.grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=4)

        self.btn_add_species_batch = self.register_text(ttk.Button(self.lf_calc2, command=self.add_species_dialog), "add_species_btn")
        self.btn_add_species_batch.grid(row=4, column=0, columnspan=3, pady=8, sticky="ew", padx=10)

        self.btn_calc2 = self.register_text(ttk.Button(left_panel, command=self.run_batch_calc), "run_batch_calc")
        self.btn_calc2.pack(fill=tk.X, padx=4, pady=8)
        self.btn_export2 = self.register_text(ttk.Button(left_panel, command=self.export_batch_script), "export_script")
        self.btn_export2.pack(fill=tk.X, padx=4, pady=2)

        self.lf_log = self.register_text(ttk.LabelFrame(paned), "running_log")
        paned.add(self.lf_log, weight=2)
        scroll2 = ttk.Scrollbar(self.lf_log)
        scroll2.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_out2 = tk.Text(self.lf_log, font=("Consolas", 9), yscrollcommand=scroll2.set)
        self.txt_out2.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll2.config(command=self.txt_out2.yview)

    # =====================================================================
    # Tab 3: Free-Space Point Analysis (Lamp at Origin) / 空间单点分析
    # =====================================================================
    def setup_point_tab(self):
        paned = ttk.PanedWindow(self.tab_point, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        left_container, left_panel = self._create_scrollable_left_pane(paned)
        paned.add(left_container, weight=1)

        self.lf_pt_coord = self.register_text(ttk.LabelFrame(left_panel), "point_origin_frame")
        self.lf_pt_coord.pack(fill=tk.X, padx=4, pady=5)
        self.lb_pt_dx, self.en_pt_dx = self.create_entry(self.lf_pt_coord, "point_dx", "0", 0)
        self.lb_pt_dy, self.en_pt_dy = self.create_entry(self.lf_pt_coord, "point_dy", "0", 1)
        self.lb_pt_dz, self.en_pt_dz = self.create_entry(self.lf_pt_coord, "point_dz", "0", 2)

        self.lbl_pt_dz_hint = self.register_text(
            ttk.Label(self.lf_pt_coord, foreground="#555555", justify="left"),
            "point_dz_hint"
        )
        self.lbl_pt_dz_hint.grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=4)
        self.lf_pt_coord.bind(
            "<Configure>",
            lambda e: self.lbl_pt_dz_hint.configure(wraplength=max(260, e.width - 28))
        )

        self.lf_pt_ies = self.register_text(ttk.LabelFrame(left_panel), "point_ies_frame")
        self.lf_pt_ies.pack(fill=tk.X, padx=4, pady=5)

        self.btn_ies3 = self.register_text(ttk.Button(self.lf_pt_ies, command=lambda: self.load_ies(3)), "load_ies")
        self.btn_ies3.grid(row=0, column=0, columnspan=3, pady=5, sticky="ew", padx=10)
        self.lbl_ies3 = self.register_text(ttk.Label(self.lf_pt_ies, foreground="red"), "not_loaded")
        self.lbl_ies3.grid(row=1, column=0, columnspan=3, pady=2)

        self.lb_yaw3, self.en_yaw3 = self.create_entry(self.lf_pt_ies, "light_yaw", "0", 2)
        self.lb_tilt3, self.en_tilt3 = self.create_entry(self.lf_pt_ies, "light_tilt", "0", 3)
        self.lb_mf3, self.en_mf3 = self.create_entry(self.lf_pt_ies, "maintenance_factor", "1", 4)
        self.lb_temp3, self.cb_temp3 = self.create_combobox_with_add(
            self.lf_pt_ies, "color_temp_factor", tl.get_available_lights(), 5,
            self.add_colortemp_dialog, self.delete_colortemp_dialog
        )

        self.chk_multi_light_pt = self.register_text(
            ttk.Checkbutton(self.lf_pt_ies, variable=self.var_multi_light_point, command=self.toggle_point_multi_light_panel),
            "multi_light_toggle"
        )
        self.chk_multi_light_pt.grid(row=6, column=0, columnspan=3, sticky="w", padx=8, pady=2)

        self.pt_multi_light_frame = ttk.Frame(self.lf_pt_ies)
        for col in (1, 3, 5):
            self.pt_multi_light_frame.columnconfigure(col, weight=1)
        self.register_text(ttk.Label(self.pt_multi_light_frame), "point_extra_lights_label").grid(
            row=0, column=0, columnspan=6, sticky="w", padx=4, pady=1
        )
        ttk.Label(self.pt_multi_light_frame, text="X:").grid(row=1, column=0, sticky="e", padx=2)
        self.en_pt_ex = ttk.Entry(self.pt_multi_light_frame, width=6)
        self.en_pt_ex.insert(0, "0")
        self.en_pt_ex.grid(row=1, column=1, sticky="ew", padx=2)

        ttk.Label(self.pt_multi_light_frame, text="Y:").grid(row=1, column=2, sticky="e", padx=2)
        self.en_pt_ey = ttk.Entry(self.pt_multi_light_frame, width=6)
        self.en_pt_ey.insert(0, "0")
        self.en_pt_ey.grid(row=1, column=3, sticky="ew", padx=2)

        ttk.Label(self.pt_multi_light_frame, text="Z:").grid(row=1, column=4, sticky="e", padx=2)
        self.en_pt_ez = ttk.Entry(self.pt_multi_light_frame, width=6)
        self.en_pt_ez.insert(0, "0")
        self.en_pt_ez.grid(row=1, column=5, sticky="ew", padx=2)

        ttk.Label(self.pt_multi_light_frame, text="Yaw:").grid(row=2, column=0, sticky="e", padx=2, pady=2)
        self.en_pt_eyaw = ttk.Entry(self.pt_multi_light_frame, width=6)
        self.en_pt_eyaw.insert(0, "0")
        self.en_pt_eyaw.grid(row=2, column=1, sticky="ew", padx=2, pady=2)

        ttk.Label(self.pt_multi_light_frame, text="Tilt:").grid(row=2, column=2, sticky="e", padx=2, pady=2)
        self.en_pt_etilt = ttk.Entry(self.pt_multi_light_frame, width=6)
        self.en_pt_etilt.insert(0, "0")
        self.en_pt_etilt.grid(row=2, column=3, sticky="ew", padx=2, pady=2)

        ttk.Label(self.pt_multi_light_frame, text="CCT/k:").grid(row=2, column=4, sticky="e", padx=2, pady=2)
        self.cb_pt_extra_temp = ttk.Combobox(self.pt_multi_light_frame, values=["Same / 同主灯"] + tl.get_available_lights(), state="readonly", width=11)
        self.cb_pt_extra_temp.current(0)
        self.cb_pt_extra_temp.grid(row=2, column=5, sticky="ew", padx=2, pady=2)

        pt_ies_row = ttk.Frame(self.pt_multi_light_frame)
        pt_ies_row.grid(row=3, column=0, columnspan=6, sticky="ew", padx=2, pady=2)
        self.register_text(ttk.Button(pt_ies_row, command=self.choose_pending_point_ies), "extra_ies_btn").pack(side=tk.LEFT, padx=2)
        self.lbl_pt_extra_ies = self.register_text(ttk.Label(pt_ies_row, foreground="#475569"), "extra_ies_same")
        self.lbl_pt_extra_ies.pack(side=tk.LEFT, padx=4)

        pt_btn_row = ttk.Frame(self.pt_multi_light_frame)
        pt_btn_row.grid(row=4, column=0, columnspan=6, sticky="ew", pady=2)
        self.register_text(ttk.Button(pt_btn_row, command=self.add_point_extra_light), "add_light_btn").pack(side=tk.LEFT, padx=2)
        self.register_text(ttk.Button(pt_btn_row, command=self.update_selected_point_ies), "update_light_ies_btn").pack(side=tk.LEFT, padx=2)
        self.register_text(ttk.Button(pt_btn_row, command=self.remove_point_extra_light), "remove_light_btn").pack(side=tk.LEFT, padx=2)
        self.register_text(ttk.Button(pt_btn_row, command=self.clear_point_extra_lights), "clear_light_btn").pack(side=tk.LEFT, padx=2)

        self.lb_pt_extra_lights = tk.Listbox(self.pt_multi_light_frame, height=3, font=("Consolas", 9))
        self.lb_pt_extra_lights.grid(row=5, column=0, columnspan=6, sticky="ew", padx=4, pady=2)

        self.chk_cosine3 = self.register_text(
            ttk.Checkbutton(self.lf_pt_ies, variable=self.var_cosine_point),
            "point_cosine_toggle"
        )
        self.chk_cosine3.grid(row=8, column=0, columnspan=3, sticky="w", padx=8, pady=4)

        self.lbl_pt_note = self.register_text(
            ttk.Label(self.lf_pt_ies, foreground="#444444", justify="left"),
            "point_cosine_note"
        )
        self.lbl_pt_note.grid(row=9, column=0, columnspan=3, sticky="ew", padx=10, pady=3)
        self.lf_pt_ies.bind(
            "<Configure>",
            lambda e: self.lbl_pt_note.configure(wraplength=max(260, e.width - 30))
        )

        self.btn_calc3 = self.register_text(ttk.Button(left_panel, command=self.run_point_calc), "point_run_calc")
        self.btn_calc3.pack(fill=tk.X, padx=4, pady=8)
        self.btn_export3 = self.register_text(ttk.Button(left_panel, command=self.export_point_script), "export_script")
        self.btn_export3.pack(fill=tk.X, padx=4, pady=2)

        self.lf_pt_report = self.register_text(ttk.LabelFrame(paned), "point_report_title")
        paned.add(self.lf_pt_report, weight=2)
        scroll3 = ttk.Scrollbar(self.lf_pt_report)
        scroll3.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_out3 = tk.Text(self.lf_pt_report, font=("Consolas", 9), yscrollcommand=scroll3.set)
        self.txt_out3.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll3.config(command=self.txt_out3.yview)

    # =====================================================================
    # Dialogs (Auto-sized & Resizable) / 自适应弹窗
    # =====================================================================
    def add_species_dialog(self):
        win = tk.Toplevel(self.root)
        win.title(self.get_text("species_dialog_title"))
        body = ttk.Frame(win, padding=12)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(1, weight=1)

        _, e_name = self.create_entry(body, "species_name", "", 0, 22)
        _, e_alpha = self.create_entry(body, "alpha", "0", 1, 22)
        _, e_rd = self.create_entry(body, "rd", "0", 2, 22)
        _, e_lcp = self.create_entry(body, "lcp", "0", 3, 22)

        def save():
            name = e_name.get().strip()
            if not name:
                return messagebox.showwarning(self.get_text("warning"), self.get_text("name_empty"), parent=win)
            try:
                tl.register_species(name, float(e_alpha.get()), float(e_rd.get()), float(e_lcp.get()))
                self.cb_species['values'] = tl.get_available_species()
                self.cb_species.set(name)
                messagebox.showinfo(self.get_text("success"), self.get_text("species_saved", name), parent=win)
                win.destroy()
            except Exception as e:
                messagebox.showerror(self.get_text("error"), str(e), parent=win)

        ttk.Button(body, text=self.get_text("save_config"), command=save).grid(
            row=4, column=0, columnspan=3, pady=(14, 4), sticky="ew"
        )
        self._finalize_dialog(win)

    def add_colortemp_dialog(self):
        win = tk.Toplevel(self.root)
        win.title(self.get_text("colortemp_dialog_title"))
        body = ttk.Frame(win, padding=12)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(1, weight=1)

        _, e_name = self.create_entry(body, "ct_identifier", "", 0, 22)
        _, e_factor = self.create_entry(body, "ct_factor", "0", 1, 22)

        def save():
            name, factor_str = e_name.get().strip(), e_factor.get().strip()
            if not name:
                return messagebox.showwarning(self.get_text("warning"), self.get_text("name_empty"), parent=win)
            try:
                factor = float(factor_str)
                full_name = f"{name} ({factor})"
                tl.register_light(full_name, factor)
                lights = tl.get_available_lights()
                for cb in (self.cb_temp1, self.cb_temp2, self.cb_temp3):
                    cb['values'] = lights
                    cb.set(full_name)
                extra_vals = ["Same / 同主灯"] + lights
                for cb in (self.cb_extra_temp, self.cb_pt_extra_temp):
                    cb['values'] = extra_vals
                messagebox.showinfo(self.get_text("success"), self.get_text("colortemp_saved", full_name), parent=win)
                win.destroy()
            except Exception as e:
                messagebox.showerror(self.get_text("error"), str(e), parent=win)

        ttk.Button(body, text=self.get_text("save_config"), command=save).grid(
            row=2, column=0, columnspan=3, pady=(14, 4), sticky="ew"
        )
        self._finalize_dialog(win)

    def _open_delete_config_dialog(self, kind):
        """Show ALL configured species or light factors in a resizable dialog for free selection & deletion."""
        from treelight.config import _manager

        win = tk.Toplevel(self.root)
        win.title(self.get_text("del_species_title" if kind == "species" else "del_light_title"))
        body = ttk.Frame(win, padding=12)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        hint_lbl = ttk.Label(body, text=self.get_text("del_dialog_hint"), justify="left")
        hint_lbl.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        list_frame = ttk.Frame(body)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        scroll = ttk.Scrollbar(list_frame)
        scroll.grid(row=0, column=1, sticky="ns")
        lb = tk.Listbox(list_frame, selectmode=tk.EXTENDED, width=52, height=12, yscrollcommand=scroll.set)
        lb.grid(row=0, column=0, sticky="nsew")
        scroll.config(command=lb.yview)

        item_keys = []

        def populate():
            lb.delete(0, tk.END)
            item_keys.clear()
            builtin_set = set(_manager._builtin_species.keys()) if kind == "species" else set(_manager._builtin_lights.keys())
            names = tl.get_available_species() if kind == "species" else tl.get_available_lights()
            for name in names:
                is_builtin = name in builtin_set
                tag = self.get_text("tag_builtin") if is_builtin else self.get_text("tag_custom")
                if kind == "species":
                    p = tl.get_species_params(name)
                    display = f"{tag} {name}  (α={p['alpha']}, Rd={p['Rd']}, LCP={p['LCP']})"
                else:
                    k_val = tl.get_ppfd_factor(name)
                    display = f"{tag} {name}  (k={k_val})"
                lb.insert(tk.END, display)
                item_keys.append((name, is_builtin))

        populate()

        def do_delete():
            sel = lb.curselection()
            if not sel:
                return messagebox.showwarning(self.get_text("warning"), self.get_text("no_selection_warning"), parent=win)
            if not messagebox.askyesno(self.get_text("confirm"), self.get_text("confirm_delete_items", len(sel)), parent=win):
                return

            deleted_cnt = 0
            skipped_cnt = 0
            for idx in sel:
                name, is_builtin = item_keys[idx]
                if is_builtin:
                    skipped_cnt += 1
                    continue
                try:
                    if kind == "species":
                        if hasattr(tl, "delete_species"):
                            tl.delete_species(name)
                        else:
                            _manager.delete_species(name)
                    else:
                        if hasattr(tl, "delete_light"):
                            tl.delete_light(name)
                        else:
                            _manager.delete_light(name)
                    deleted_cnt += 1
                except Exception:
                    skipped_cnt += 1

            # 刷新主界面下拉框 / Refresh comboboxes in main UI
            if kind == "species":
                sp_list = tl.get_available_species()
                cur = self.cb_species.get()
                self.cb_species['values'] = sp_list
                if cur in sp_list:
                    self.cb_species.set(cur)
                elif sp_list:
                    self.cb_species.current(0)
            else:
                lights = tl.get_available_lights()
                for cb in (self.cb_temp1, self.cb_temp2, self.cb_temp3):
                    cur = cb.get()
                    cb['values'] = lights
                    if cur in lights:
                        cb.set(cur)
                    elif lights:
                        cb.current(0)
                extra_vals = ["Same / 同主灯"] + lights
                for cb in (self.cb_extra_temp, self.cb_pt_extra_temp):
                    cur = cb.get()
                    cb['values'] = extra_vals
                    if cur in extra_vals:
                        cb.set(cur)
                    else:
                        cb.current(0)

            populate()
            messagebox.showinfo(self.get_text("success"), self.get_text("delete_summary", deleted_cnt, skipped_cnt), parent=win)

        btn_bar = ttk.Frame(body)
        btn_bar.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(btn_bar, text=self.get_text("del_selected_btn"), command=do_delete).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text=self.get_text("close"), command=win.destroy).pack(side=tk.RIGHT, padx=4)

        self._finalize_dialog(win, pad_w=48, pad_h=30)

    def delete_species_dialog(self):
        self._open_delete_config_dialog("species")

    def delete_colortemp_dialog(self):
        self._open_delete_config_dialog("light")

    # =====================================================================
    # File Loaders / 文件加载
    # =====================================================================
    def load_ies(self, tab_id):
        f = filedialog.askopenfilename(parent=self.root, filetypes=[("IES Files", "*.ies")])
        if f:
            data, msg = tl.parse_ies_full(f)
            if "✅" in msg:
                if tab_id == 1:
                    self.ies_path_single = f
                    self.ies_data_single = data
                    self.lbl_ies1.config(text=os.path.basename(f), foreground="green")
                    self._log(self.txt_out1, "raw", msg)
                elif tab_id == 2:
                    self.ies_path_batch = f
                    self.ies_data_batch = data
                    self.lbl_ies2.config(text=os.path.basename(f), foreground="green")
                    self._log(self.txt_out2, "raw", msg)
                else:
                    self.ies_path_point = f
                    self.ies_data_point = data
                    self.lbl_ies3.config(text=os.path.basename(f), foreground="green")
                    self._log(self.txt_out3, "raw", msg)
            else:
                messagebox.showerror("IES Parse Error", msg)

    def load_excel(self):
        f = filedialog.askopenfilename(parent=self.root, filetypes=[("Excel/CSV Files", "*.xlsx *.xls *.csv"), ("All Files", "*.*")])
        if f:
            self.excel_path = f
            self.lbl_excel.config(text=os.path.basename(f), foreground="green")

    def choose_ies_dir(self):
        d = filedialog.askdirectory(parent=self.root)
        if d:
            self.ies_dir_batch = d
            self.lbl_iesdir.config(text=d, foreground="green")

    def choose_out_dir(self):
        d = filedialog.askdirectory(parent=self.root)
        if d:
            self.output_dir = d
            self.lbl_outdir.config(text=d, foreground="green")

    # =====================================================================
    # Calculations / 核心计算逻辑
    # =====================================================================
    def run_single_calc(self):
        if not self.ies_data_single:
            return messagebox.showwarning(self.get_text("warning"), self.get_text("no_ies_warning"))

        try:
            tree_h = float(self.en_height.get())
            branch_h = float(self.en_branch.get())
            crown_w = float(self.en_crown.get())
            prec = float(self.en_prec1.get())
            mf = float(self.en_mf1.get())
            light_pos_list = self._get_single_light_pos_list()
        except Exception:
            return messagebox.showerror(self.get_text("error"), self.get_text("invalid_param"))

        if tree_h <= 0 or crown_w <= 0 or prec <= 0 or mf <= 0 or tree_h <= branch_h:
            return messagebox.showwarning(self.get_text("warning"), self.get_text("positive_param_warning"))

        try:
            self.txt_out1.delete(1.0, tk.END)
            self._log(self.txt_out1, "simulating")

            geo_params = {
                "canopy_type": self.cb_shape.get(),
                "tree_height": tree_h,
                "branch_height": branch_h,
                "crown_width": crown_w
            }
            use_cosine = self.var_cosine_single.get()

            env_params = {
                "precision": prec,
                "maintenance_factor": mf,
                "light_output_ratio": 0.9,
                "ppfd_factor": tl.get_ppfd_factor(self.cb_temp1.get()),
                "cosine_correction": use_cosine
            }
            species_name = self.cb_species.get()

            def task():
                physics_result = tl.calculate_canopy_ppfd(geo_params, light_pos_list, self.ies_data_single, env_params)
                self.last_physics_res = physics_result
                self.last_species = species_name

                grade_stats = tl.grade_light_environment(physics_result, species_name)
                carbon_stats = tl.calculate_implicit_carbon(physics_result, species_name)

                self.root.after(
                    0,
                    lambda: self.display_single_result(
                        grade_stats, carbon_stats, len(physics_result['centers']), len(light_pos_list), use_cosine
                    )
                )

            Thread(target=task, daemon=True).start()
        except Exception as e:
            messagebox.showerror(self.get_text("error"), f"Calculate Error: {e}")

    def display_single_result(self, grade, carbon, pts_count, n_lights, use_cosine):
        t = self.txt_out1
        self._log(t, "raw", "=" * 48)
        self._log(t, "analysis_finish", datetime.now().strftime('%H:%M:%S'))
        self._log(t, "light_count_info", n_lights, "ON" if use_cosine else "OFF (Scalar)")
        self._log(t, "grid_points", pts_count)
        self._log(t, "raw", "-" * 48)
        self._log(t, "total_area", grade['total_area'])
        self._log(t, "max_ppfd", grade['max_ppfd'])
        self._log(t, "avg_ppfd", grade['avg_ppfd'])
        self._log(t, "yearly_carbon", carbon['carbon_g'])
        self._log(t, "raw", "-" * 48)
        self._log(t, "area_distribution")
        for k, v in grade.get('grade_stats_area', {}).items():
            self._log(t, "interval", k, v)
        self._log(t, "raw", "=" * 48)

    def show_visual(self):
        if not self.last_physics_res:
            return messagebox.showwarning(self.get_text("warning"), self.get_text("no_calc_warning"))
        tl.visualize_ppfd_3d(self.last_physics_res, self.last_species, show=True)

    @staticmethod
    def _parse_light_coords_str(light_str):
        coords = re.findall(r"[-+]?\d*\.\d+|\d+", str(light_str))
        n_triplets = len(coords) // 3
        if n_triplets >= 1:
            return [
                {"x": float(coords[3 * i]), "y": float(coords[3 * i + 1]), "z": float(coords[3 * i + 2])}
                for i in range(n_triplets)
            ]
        return [{"x": 1.8, "y": 2.5, "z": 9.5}]

    @staticmethod
    def _parse_angle_list(val, count, default=0.0):
        if pd.isna(val):
            return [default] * count
        nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", str(val))]
        if not nums:
            return [default] * count
        if len(nums) == 1:
            return [nums[0]] * count
        return [nums[i] if i < len(nums) else nums[-1] for i in range(count)]

    @staticmethod
    def _resolve_batch_ies(name_token, search_dirs, default_ies_data, ies_cache):
        tok = str(name_token).strip()
        if not tok or tok.lower() in ("nan", "none", "default"):
            return default_ies_data, "Default IES"
        cand_paths = []
        if os.path.isabs(tok):
            cand_paths.append(tok)
            if not tok.lower().endswith(".ies"):
                cand_paths.append(tok + ".ies")
        else:
            for d in search_dirs:
                if d:
                    cand_paths.append(os.path.join(d, tok))
                    if not tok.lower().endswith(".ies"):
                        cand_paths.append(os.path.join(d, tok + ".ies"))
        for p in cand_paths:
            if os.path.exists(p):
                if p not in ies_cache:
                    d_ies, msg = tl.parse_ies_full(p)
                    if "✅" in msg:
                        ies_cache[p] = d_ies
                    else:
                        return default_ies_data, f"Fallback(Default): {tok}"
                return ies_cache[p], os.path.basename(p)
        return default_ies_data, f"NotFound(Default): {tok}"

    def run_batch_calc(self):
        if not self.ies_data_batch:
            return messagebox.showwarning(self.get_text("warning"), self.get_text("no_ies_warning"))
        if not self.excel_path:
            return messagebox.showwarning(self.get_text("warning"), self.get_text("no_excel_warning"))

        try:
            prec = float(self.en_prec2.get())
            mf = float(self.en_mf2.get())
            env_params = {
                "precision": prec,
                "maintenance_factor": mf,
                "light_output_ratio": 0.9,
                "ppfd_factor": tl.get_ppfd_factor(self.cb_temp2.get()),
                "cosine_correction": self.var_cosine_batch.get()
            }
        except Exception:
            return messagebox.showerror(self.get_text("error"), self.get_text("invalid_param"))

        if prec <= 0 or mf <= 0:
            return messagebox.showwarning(self.get_text("warning"), self.get_text("batch_param_warning"))

        self.txt_out2.delete(1.0, tk.END)

        def batch_task():
            if self.excel_path.lower().endswith('.csv'):
                try:
                    df_input = pd.read_csv(self.excel_path, encoding='utf-8-sig')
                except Exception:
                    df_input = pd.read_csv(self.excel_path, encoding='gbk')
            else:
                df_input = pd.read_excel(self.excel_path)

            total, results, start_t = len(df_input), [], time.time()
            ies_cache = {}
            ies_search_dirs = [self.ies_dir_batch, os.path.dirname(self.ies_path_batch) if self.ies_path_batch else None, os.path.dirname(self.excel_path)]
            self._log(self.txt_out2, "total_data", total)

            for index, row in df_input.iterrows():
                try:
                    th_val = row.get("Total Tree Height (m)", 8.0)
                    if pd.isna(th_val):
                        continue

                    batch_geo = {
                        "canopy_type": row.get("Canopy Type", "半椭球体/Half Ellipsoid"),
                        "tree_height": float(th_val),
                        "branch_height": float(row.get("Under-branch Height (m)", 2.5)),
                        "crown_width": float(row.get("Crown Diameter (m)", 4.0))
                    }

                    raw_species = str(row.get("Tree Species", "default")).strip().lower()
                    species = "默认阔叶树 (Default Broadleaf)"
                    for available_sp in tl.get_available_species():
                        if raw_species in available_sp.lower():
                            species = available_sp
                            break

                    light_pos_list = self._parse_light_coords_str(row.get("Light Source Coordinates", ""))
                    n_lamps = len(light_pos_list)
                    yaws = self._parse_angle_list(row.get("Light Yaw (°)", 0.0), n_lamps, 0.0)
                    tilts = self._parse_angle_list(row.get("Light Tilt (°)", 0.0), n_lamps, 0.0)

                    # Read optional per-row IES column (supports "IES File", "IES Name", "IES", "IES文件", "IES名称")
                    raw_ies_cell = None
                    for col_cand in ("IES File", "IES Name", "IES", "IES Filename", "IES文件", "IES名称"):
                        if col_cand in row and not pd.isna(row[col_cand]) and str(row[col_cand]).strip():
                            raw_ies_cell = str(row[col_cand]).strip()
                            break
                    ies_tokens = [t.strip() for t in re.split(r"[;,|]", raw_ies_cell)] if raw_ies_cell else []

                    # Read optional per-row PPFD factor / color temp column (numeric k or registered light name)
                    raw_k_cell = None
                    for k_col in ("PPFD Factor", "Color Temp", "Light Type", "CCT", "k", "色温", "转换系数"):
                        if k_col in row and not pd.isna(row[k_col]) and str(row[k_col]).strip():
                            raw_k_cell = str(row[k_col]).strip()
                            break
                    k_tokens = [t.strip() for t in re.split(r"[;,|]", raw_k_cell)] if raw_k_cell else []
                    default_k = float(env_params["ppfd_factor"])

                    used_ies_names = []
                    used_k_vals = []
                    for i_lp, lp in enumerate(light_pos_list):
                        lp["yaw"] = yaws[i_lp]
                        lp["tilt"] = tilts[i_lp]
                        tok = ies_tokens[i_lp] if i_lp < len(ies_tokens) else (ies_tokens[-1] if ies_tokens else "")
                        d_ies, ies_label = self._resolve_batch_ies(tok, ies_search_dirs, self.ies_data_batch, ies_cache)
                        lp["ies_data"] = d_ies
                        used_ies_names.append(ies_label)
                        ktok = k_tokens[i_lp] if i_lp < len(k_tokens) else (k_tokens[-1] if k_tokens else "")
                        lamp_k = default_k
                        if ktok:
                            try:
                                lamp_k = float(ktok)
                            except ValueError:
                                lamp_k = float(tl.get_ppfd_factor(ktok))
                        lp["ppfd_factor"] = lamp_k
                        used_k_vals.append(f"{lamp_k:.4f}")

                    batch_physics = tl.calculate_canopy_ppfd(batch_geo, light_pos_list, self.ies_data_batch, env_params)
                    batch_grade = tl.grade_light_environment(batch_physics, species)
                    batch_carbon = tl.calculate_implicit_carbon(batch_physics, species)

                    out_row = row.to_dict()
                    out_row["IES File Used"] = "; ".join(used_ies_names)
                    out_row["PPFD Factor Used"] = "; ".join(used_k_vals)
                    out_row["Cosine Correction"] = env_params["cosine_correction"]
                    out_row["LCP Reference"] = batch_grade["LCP_ref"]
                    out_row["Total Area (m2)"] = round(batch_grade["total_area"], 3)
                    out_row["Max PPFD"] = round(batch_grade["max_ppfd"], 3)
                    out_row["Avg PPFD"] = round(batch_grade["avg_ppfd"], 3)
                    out_row["Annual Carbon Reduction (g)"] = round(batch_carbon["carbon_g"], 3)
                    for k, v in batch_grade.get('grade_stats_area', {}).items():
                        out_row[f"Area {k}"] = round(v, 3)

                    results.append(out_row)

                    if (index + 1) % 10 == 0 or (index + 1) == total:
                        self._log(self.txt_out2, "progress", index + 1, total)
                except Exception as e:
                    self._log(self.txt_out2, "raw", f"⚠️ Skipped row {index + 1}: {e}")

            base_dir = self.output_dir if self.output_dir else os.path.dirname(self.excel_path)
            orig_name = os.path.basename(self.excel_path).split('.')[0]
            out_path = os.path.join(base_dir, f"{orig_name}_Batch_Result.csv")
            pd.DataFrame(results).to_csv(out_path, index=False, encoding='utf-8-sig')

            self._log(self.txt_out2, "batch_complete", time.time() - start_t)
            self._log(self.txt_out2, "result_saved", out_path)

            self.root.after(0, lambda: messagebox.showinfo(self.get_text("success"), self.get_text("batch_finished")))

        Thread(target=batch_task, daemon=True).start()

    def toggle_point_multi_light_panel(self):
        if self.var_multi_light_point.get():
            self.pt_multi_light_frame.grid(row=7, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        else:
            self.pt_multi_light_frame.grid_forget()

    def choose_pending_point_ies(self):
        f = filedialog.askopenfilename(parent=self.root, filetypes=[("IES Files", "*.ies")])
        if f:
            data, msg = tl.parse_ies_full(f)
            if "✅" in msg:
                self.pending_point_ies_path = f
                self.pending_point_ies_data = data
                self.lbl_pt_extra_ies.config(text=f"IES: {os.path.basename(f)}", foreground="green")
            else:
                messagebox.showerror("IES Parse Error", msg, parent=self.root)

    def update_selected_point_ies(self):
        sel = self.lb_pt_extra_lights.curselection()
        if not sel:
            return messagebox.showwarning(self.get_text("warning"), self.get_text("select_extra_first"), parent=self.root)
        f = filedialog.askopenfilename(parent=self.root, filetypes=[("IES Files", "*.ies")])
        if f:
            data, msg = tl.parse_ies_full(f)
            if "✅" in msg:
                idx = sel[0]
                self.extra_lights_point[idx]["ies_path"] = f
                self.extra_lights_point[idx]["ies_data"] = data
                self._refresh_point_extra_lights_listbox()
                self._log(self.txt_out3, "raw", f"Updated Lamp {idx + 2} IES: {os.path.basename(f)}")
            else:
                messagebox.showerror("IES Parse Error", msg, parent=self.root)

    def add_point_extra_light(self):
        try:
            x = float(self.en_pt_ex.get())
            y = float(self.en_pt_ey.get())
            z = float(self.en_pt_ez.get())
            yaw = float(self.en_pt_eyaw.get())
            tilt = float(self.en_pt_etilt.get())
            sel_temp = self.cb_pt_extra_temp.get()
            is_same_k = (not sel_temp) or sel_temp.startswith("Same")
            lamp_light_name = None if is_same_k else sel_temp
            lamp_k = None if is_same_k else float(tl.get_ppfd_factor(sel_temp))
            self.extra_lights_point.append({
                "x": x, "y": y, "z": z, "yaw": yaw, "tilt": tilt,
                "light_name": lamp_light_name, "ppfd_factor": lamp_k,
                "ies_path": self.pending_point_ies_path,
                "ies_data": self.pending_point_ies_data
            })
            self.cb_pt_extra_temp.current(0)
            self.pending_point_ies_path = None
            self.pending_point_ies_data = None
            self.lbl_pt_extra_ies.config(text=self.get_text("extra_ies_same"), foreground="#475569")
            self._refresh_point_extra_lights_listbox()
        except ValueError:
            messagebox.showerror(self.get_text("error"), self.get_text("invalid_number"))

    def remove_point_extra_light(self):
        sel = self.lb_pt_extra_lights.curselection()
        if sel:
            self.extra_lights_point.pop(sel[0])
            self._refresh_point_extra_lights_listbox()

    def clear_point_extra_lights(self):
        self.extra_lights_point.clear()
        self._refresh_point_extra_lights_listbox()

    def _refresh_point_extra_lights_listbox(self):
        self.lb_pt_extra_lights.delete(0, tk.END)
        for i, lp in enumerate(self.extra_lights_point, start=2):
            ies_tag = os.path.basename(lp["ies_path"]) if lp.get("ies_path") else "Primary IES"
            k_tag = lp["light_name"] if lp.get("light_name") else "Primary k"
            self.lb_pt_extra_lights.insert(
                tk.END,
                f"Lamp {i}: ({lp['x']}, {lp['y']}, {lp['z']}) | yaw={lp['yaw']}°, tilt={lp['tilt']}° | {k_tag} | {ies_tag}"
            )

    def _get_point_lights_list(self):
        primary_k = float(tl.get_ppfd_factor(self.cb_temp3.get()))
        primary = {
            "x": 0.0, "y": 0.0, "z": 0.0,
            "yaw": float(self.en_yaw3.get()), "tilt": float(self.en_tilt3.get()),
            "ppfd_factor": primary_k,
            "ies_path": self.ies_path_point, "ies_data": self.ies_data_point
        }
        if self.var_multi_light_point.get() and self.extra_lights_point:
            out = [primary]
            for lp in self.extra_lights_point:
                out.append({
                    "x": lp["x"], "y": lp["y"], "z": lp["z"],
                    "yaw": lp["yaw"], "tilt": lp["tilt"],
                    "ppfd_factor": lp["ppfd_factor"] if lp.get("ppfd_factor") is not None else primary_k,
                    "ies_path": lp.get("ies_path") or self.ies_path_point,
                    "ies_data": lp.get("ies_data") or self.ies_data_point
                })
            return out
        return [primary]

    def run_point_calc(self):
        if not self.ies_data_point:
            return messagebox.showwarning(self.get_text("warning"), self.get_text("no_ies_warning"))

        try:
            dx = float(self.en_pt_dx.get())
            dy = float(self.en_pt_dy.get())
            dz = float(self.en_pt_dz.get())
            mf = float(self.en_mf3.get())
            light_name = self.cb_temp3.get()
            ppfd_factor = tl.get_ppfd_factor(light_name)
            use_cosine = self.var_cosine_point.get()
            lights = self._get_point_lights_list()
        except Exception:
            return messagebox.showerror(self.get_text("error"), self.get_text("invalid_param"))

        total_lux = 0.0
        total_ppfd = 0.0
        per_lamp_details = []

        for idx, lp in enumerate(lights, start=1):
            vx = dx - lp["x"]
            vy = dy - lp["y"]
            vz = dz - lp["z"]
            dist_sq = vx**2 + vy**2 + vz**2
            dist = float(np.sqrt(dist_sq))
            if dist < 1e-6:
                return messagebox.showwarning(self.get_text("warning"), self.get_text("point_zero_dist"))

            ux, uy, uz = vx / dist, vy / dist, vz / dist
            theta_arr, phi_arr = compute_ies_angles(np.array([[ux, uy, uz]]), yaw=lp["yaw"], tilt=lp["tilt"])
            theta, phi = float(theta_arr[0]), float(phi_arr[0])

            intensity = float(get_interpolated_intensity(lp["ies_data"], theta, phi))
            cos_alpha = max(0.0, -uz)
            cos_term = cos_alpha if use_cosine else 1.0

            lamp_k = float(lp["ppfd_factor"]) if lp.get("ppfd_factor") is not None else ppfd_factor
            lux_i = (intensity / dist_sq) * cos_term * mf
            ppfd_i = lux_i * lamp_k
            total_lux += lux_i
            total_ppfd += ppfd_i

            per_lamp_details.append({
                "lamp_id": idx, "x": lp["x"], "y": lp["y"], "z": lp["z"],
                "yaw": lp["yaw"], "tilt": lp["tilt"], "ppfd_factor": lamp_k,
                "ies_file": (lp.get("ies_path") or self.ies_path_point).replace("\\", "/"),
                "dist": dist, "theta": theta, "phi": phi,
                "intensity_cd": intensity, "cos_alpha": cos_alpha,
                "lux": lux_i, "ppfd": ppfd_i
            })

        self.last_point_res = {
            "dx": dx, "dy": dy, "dz": dz,
            "use_cosine": use_cosine, "mf": mf,
            "light_name": light_name, "ppfd_factor": ppfd_factor,
            "lights": per_lamp_details,
            "total_lux": total_lux, "total_ppfd": total_ppfd
        }

        self.txt_out3.delete(1.0, tk.END)
        mode_str = (
            "Horizontal Planar Irradiance (Cosine ON / 开启水平余弦校正)"
            if use_cosine else
            "Omnidirectional Scalar Irradiance (Cosine OFF / 关闭余弦校正，标量辐照度)"
        )
        lines = [
            "=" * 58,
            f"Point Light-Field Analysis ({datetime.now().strftime('%H:%M:%S')})",
            f"Mode / 计算模式: {mode_str}",
            f"Target Point (目标点坐标): ({dx:.2f}, {dy:.2f}, {dz:.2f}) m | Lights: {len(lights)}",
            "-" * 58,
        ]
        for d in per_lamp_details:
            lines.append(
                f"[Lamp {d['lamp_id']}] Pos=({d['x']:.2f}, {d['y']:.2f}, {d['z']:.2f}) | "
                f"Yaw={d['yaw']:.1f}°, Tilt={d['tilt']:.1f}° | k={d['ppfd_factor']:.4f} | IES={os.path.basename(d['ies_file'])}"
            )
            lines.append(
                f"   d={d['dist']:.3f} m | theta={d['theta']:.1f}°, phi={d['phi']:.1f}° | "
                f"I={d['intensity_cd']:.1f} cd | cos(α)={d['cos_alpha']:.4f}"
            )
            lines.append(f"   -> Lux={d['lux']:.3f} lx | PPFD={d['ppfd']:.4f} μmol·m⁻²·s⁻¹")
        lines.extend([
            "-" * 58,
            f"Total Illuminance (总照度):        {total_lux:.3f} lux",
            f"Total PPFD (总光合光子通量密度):   {total_ppfd:.4f} μmol·m⁻²·s⁻¹",
            "=" * 58,
        ])
        for line in lines:
            self._log(self.txt_out3, "raw", line)

    # =====================================================================
    # Reproducible Script Exporters / 可复现脚本导出
    # =====================================================================
    def export_single_script(self):
        if not self.last_physics_res or not self.ies_path_single:
            messagebox.showwarning(self.get_text("warning"), self.get_text("no_calc_warning"))
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"treelight_single_script_{timestamp}.py"
        save_path = filedialog.asksaveasfilename(
            parent=self.root,
            initialfile=default_name,
            defaultextension=".py",
            filetypes=[("Python Script", "*.py"), ("All Files", "*.*")]
        )
        if not save_path:
            return

        ies_path = self.ies_path_single.replace("\\", "/")
        raw_lights = self._get_single_light_pos_list()
        export_lights = [
            {
                "x": lp["x"], "y": lp["y"], "z": lp["z"],
                "yaw": lp["yaw"], "tilt": lp["tilt"],
                "ppfd_factor": lp.get("ppfd_factor"),
                "ies_file": (lp.get("ies_path") or self.ies_path_single).replace("\\", "/")
            }
            for lp in raw_lights
        ]
        use_cosine = self.var_cosine_single.get()

        script_content = f"""# -*- coding: utf-8 -*-
\"\"\"
Reproducible Python Script generated by treelight GUI
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode: Single Tree Analysis
\"\"\"
import warnings
warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use('Agg')

import treelight as tl

def main():
    print(">>> Starting Reproducible Simulation...")

    ies_file = r"{ies_path}"
    ies_data, msg = tl.parse_ies_full(ies_file)
    print("IES Parse Result: " + str(msg))
    if "❌" in msg:
        return

    geo_params = dict(
        canopy_type="{self.cb_shape.get()}",
        tree_height={self.en_height.get()},
        branch_height={self.en_branch.get()},
        crown_width={self.en_crown.get()}
    )

    raw_light_specs = {repr(export_lights)}
    ies_cache = {{ies_file: ies_data}}
    light_pos_list = []
    for spec in raw_light_specs:
        fpath = spec["ies_file"]
        if fpath not in ies_cache:
            d, m = tl.parse_ies_full(fpath)
            if "❌" in m:
                print("Failed to load IES:", fpath, m)
                return
            ies_cache[fpath] = d
        light_pos_list.append({{
            "x": spec["x"], "y": spec["y"], "z": spec["z"],
            "yaw": spec["yaw"], "tilt": spec["tilt"],
            "ppfd_factor": spec.get("ppfd_factor"),
            "ies_data": ies_cache[fpath]
        }})

    env_params = dict(
        precision={self.en_prec1.get()},
        maintenance_factor={self.en_mf1.get()},
        light_output_ratio=0.90,
        ppfd_factor=tl.get_ppfd_factor("{self.cb_temp1.get()}"),
        cosine_correction={use_cosine}
    )
    species = "{self.cb_species.get()}"

    physics_result = tl.calculate_canopy_ppfd(geo_params, light_pos_list, ies_data, env_params)
    grade_stats = tl.grade_light_environment(physics_result, species)
    carbon_stats = tl.calculate_implicit_carbon(physics_result, species)

    print("\\n" + "=" * 50)
    print("--- Simulation Results Report for " + species + " ---")
    print("Light Sources: " + str(len(light_pos_list)) + " | Cosine Correction: " + str({use_cosine}))
    print("Total Surface Area: " + str(round(grade_stats['total_area'], 2)) + " m²")
    print("Max PPFD: " + str(round(grade_stats['max_ppfd'], 2)) + " μmol/m²/s")
    print("Average Effective PPFD: " + str(round(grade_stats['avg_ppfd'], 2)) + " μmol/m²/s")
    print("Annual Carbon Sink: " + str(round(carbon_stats.get('carbon_g', 0), 4)) + " g CO2")
    print("-" * 50)
    for k, v in grade_stats.get('grade_stats_area', dict()).items():
        print("  Interval [" + str(k) + "]: " + str(round(v, 2)) + " m²")
    print("=" * 50)

if __name__ == "__main__":
    main()
"""
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        self._log(self.txt_out1, "script_exported", save_path)
        messagebox.showinfo(self.get_text("success"), "Script exported successfully!")

    def export_batch_script(self):
        if not self.ies_data_batch or not self.excel_path:
            messagebox.showwarning(self.get_text("warning"), self.get_text("no_calc_warning"))
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"treelight_batch_script_{timestamp}.py"
        save_path = filedialog.asksaveasfilename(
            parent=self.root,
            initialfile=default_name,
            defaultextension=".py",
            filetypes=[("Python Script", "*.py"), ("All Files", "*.*")]
        )
        if not save_path:
            return

        ies_path = self.ies_path_batch.replace("\\", "/")
        excel_path = self.excel_path.replace("\\", "/")
        use_cosine = self.var_cosine_batch.get()

        script_content = f"""# -*- coding: utf-8 -*-
\"\"\"
Reproducible Python Script generated by treelight GUI
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode: Batch Tree Analysis
\"\"\"
import os
import re
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import treelight as tl

def parse_lights(light_str):
    coords = re.findall(r"[-+]?\\d*\\.\\d+|\\d+", str(light_str))
    n = len(coords) // 3
    if n >= 1:
        return [dict(x=float(coords[3*i]), y=float(coords[3*i+1]), z=float(coords[3*i+2])) for i in range(n)]
    return [dict(x=1.8, y=2.5, z=9.5)]

def main():
    print(">>> Starting Reproducible Batch Simulation...")

    ies_file = r"{ies_path}"
    ies_dir = r"{(self.ies_dir_batch or os.path.dirname(self.ies_path_batch)).replace(chr(92), chr(47))}"
    data_file = r"{excel_path}"
    ies_cache = {{}}

    ies_data, msg = tl.parse_ies_full(ies_file)
    if "❌" in msg:
        print("Failed to load IES: " + str(msg))
        return

    env_params = dict(
        precision={self.en_prec2.get()},
        maintenance_factor={self.en_mf2.get()},
        light_output_ratio=0.90,
        ppfd_factor=tl.get_ppfd_factor("{self.cb_temp2.get()}"),
        cosine_correction={use_cosine}
    )

    df_input = pd.read_csv(data_file, encoding='utf-8-sig') if data_file.endswith('.csv') else pd.read_excel(data_file)
    results_list = []

    for index, row in df_input.iterrows():
        th_val = row.get("Total Tree Height (m)", 8.0)
        if pd.isna(th_val):
            continue

        batch_geo = dict(
            canopy_type=row.get("Canopy Type", "Half Ellipsoid"),
            tree_height=float(th_val),
            branch_height=float(row.get("Under-branch Height (m)", 2.5)),
            crown_width=float(row.get("Crown Diameter (m)", 4.0))
        )

        raw_species = str(row.get("Tree Species", "default")).strip().lower()
        species = "默认阔叶树 (Default Broadleaf)"
        for available_sp in tl.get_available_species():
            if raw_species in available_sp.lower():
                species = available_sp
                break

        light_pos_list = parse_lights(row.get("Light Source Coordinates", ""))
        n_l = len(light_pos_list)
        def _ang_list(val):
            if pd.isna(val): return [0.0] * n_l
            nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", str(val))]
            return [nums[i] if i < len(nums) else nums[-1] for i in range(n_l)] if nums else [0.0] * n_l
        yaws = _ang_list(row.get("Light Yaw (°)", 0.0))
        tilts = _ang_list(row.get("Light Tilt (°)", 0.0))
        raw_ies = ""
        for c in ("IES File", "IES Name", "IES", "IES Filename", "IES文件", "IES名称"):
            if c in row and not pd.isna(row[c]) and str(row[c]).strip():
                raw_ies = str(row[c]).strip()
                break
        toks = [t.strip() for t in re.split(r"[;,|]", raw_ies)] if raw_ies else []
        raw_k = ""
        for kc in ("PPFD Factor", "Color Temp", "Light Type", "CCT", "k", "色温", "转换系数"):
            if kc in row and not pd.isna(row[kc]) and str(row[kc]).strip():
                raw_k = str(row[kc]).strip()
                break
        ktoks = [t.strip() for t in re.split(r"[;,|]", raw_k)] if raw_k else []
        for idx_l, lp in enumerate(light_pos_list):
            lp["yaw"], lp["tilt"] = yaws[idx_l], tilts[idx_l]
            tok = toks[idx_l] if idx_l < len(toks) else (toks[-1] if toks else "")
            if tok:
                cand = tok if os.path.isabs(tok) else os.path.join(ies_dir, tok if tok.lower().endswith(".ies") else tok + ".ies")
                if os.path.exists(cand):
                    if cand not in ies_cache:
                        d_i, m_i = tl.parse_ies_full(cand)
                        if "✅" in m_i: ies_cache[cand] = d_i
                    lp["ies_data"] = ies_cache.get(cand, ies_data)
            ktok = ktoks[idx_l] if idx_l < len(ktoks) else (ktoks[-1] if ktoks else "")
            if ktok:
                try:
                    lp["ppfd_factor"] = float(ktok)
                except ValueError:
                    lp["ppfd_factor"] = float(tl.get_ppfd_factor(ktok))

        batch_physics = tl.calculate_canopy_ppfd(batch_geo, light_pos_list, ies_data, env_params)
        batch_grade = tl.grade_light_environment(batch_physics, species)
        batch_carbon = tl.calculate_implicit_carbon(batch_physics, species)

        out_row = row.to_dict()
        out_row["Cosine Correction"] = env_params["cosine_correction"]
        out_row["LCP Reference"] = batch_grade["LCP_ref"]
        out_row["Total Area (m2)"] = round(batch_grade["total_area"], 3)
        out_row["Max PPFD"] = round(batch_grade["max_ppfd"], 3)
        out_row["Avg PPFD"] = round(batch_grade["avg_ppfd"], 3)
        out_row["Annual Carbon Reduction (g)"] = round(batch_carbon.get("carbon_g", 0), 3)
        for k, v in batch_grade.get('grade_stats_area', dict()).items():
            out_row["Area " + str(k)] = round(v, 3)

        results_list.append(out_row)

    df_output = pd.DataFrame(results_list)
    out_csv = "Reproducible_Batch_Results.csv"
    df_output.to_csv(out_csv, index=False, encoding='utf-8-sig')
    print(">>> Batch processing completed! Saved to: " + out_csv)

if __name__ == "__main__":
    main()
"""
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        self._log(self.txt_out2, "script_exported", save_path)
        messagebox.showinfo(self.get_text("success"), "Batch script exported successfully!")

    def export_point_script(self):
        if not self.last_point_res or not self.ies_path_point:
            messagebox.showwarning(self.get_text("warning"), self.get_text("no_calc_warning"))
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"treelight_point_script_{timestamp}.py"
        save_path = filedialog.asksaveasfilename(
            parent=self.root,
            initialfile=default_name,
            defaultextension=".py",
            filetypes=[("Python Script", "*.py"), ("All Files", "*.*")]
        )
        if not save_path:
            return

        r = self.last_point_res
        export_lights = [
            {
                "x": d["x"], "y": d["y"], "z": d["z"],
                "yaw": d["yaw"], "tilt": d["tilt"],
                "ppfd_factor": d["ppfd_factor"],
                "ies_file": d["ies_file"]
            }
            for d in r["lights"]
        ]

        script_content = f"""# -*- coding: utf-8 -*-
\"\"\"
Reproducible Python Script generated by treelight GUI
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode: Free-Space Point Analysis (Multi-Light Superposition)
\"\"\"
import numpy as np
import treelight as tl
from treelight.ies_parser import get_interpolated_intensity
from treelight.light_analysis import compute_ies_angles

def main():
    dx, dy, dz = {r['dx']}, {r['dy']}, {r['dz']}
    mf = {r['mf']}
    ppfd_factor = tl.get_ppfd_factor("{r['light_name']}")
    cosine_correction = {r['use_cosine']}
    light_specs = {repr(export_lights)}

    ies_cache = {{}}
    total_lux = 0.0
    total_ppfd = 0.0

    for i, lp in enumerate(light_specs, start=1):
        fpath = lp["ies_file"]
        if fpath not in ies_cache:
            data, msg = tl.parse_ies_full(fpath)
            if "❌" in msg:
                print("IES Parse Error:", fpath, msg)
                return
            ies_cache[fpath] = data

        vx, vy, vz = dx - lp["x"], dy - lp["y"], dz - lp["z"]
        dist_sq = vx**2 + vy**2 + vz**2
        dist = float(np.sqrt(dist_sq))
        ux, uy, uz = vx / dist, vy / dist, vz / dist

        theta_arr, phi_arr = compute_ies_angles(np.array([[ux, uy, uz]]), yaw=lp["yaw"], tilt=lp["tilt"])
        theta, phi = float(theta_arr[0]), float(phi_arr[0])

        intensity = float(get_interpolated_intensity(ies_cache[fpath], theta, phi))
        cos_term = max(0.0, -uz) if cosine_correction else 1.0

        lamp_k = float(lp["ppfd_factor"]) if lp.get("ppfd_factor") is not None else ppfd_factor
        lux_i = (intensity / dist_sq) * cos_term * mf
        ppfd_i = lux_i * lamp_k
        total_lux += lux_i
        total_ppfd += ppfd_i
        print(f"Lamp {{i}}: d={{dist:.3f}} m, I={{intensity:.2f}} cd -> {{lux_i:.3f}} lux | {{ppfd_i:.4f}} PPFD")

    print(f"Total Illuminance: {{total_lux:.3f}} lux | Total PPFD: {{total_ppfd:.4f}} μmol·m⁻²·s⁻¹")

if __name__ == "__main__":
    main()
"""
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        self._log(self.txt_out3, "script_exported", save_path)
        messagebox.showinfo(self.get_text("success"), "Script exported successfully!")


# 程序执行入口 / Program execution entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = TreeLightingGUI(root)
    root.mainloop()
