# -*- coding: utf-8 -*-
"""
树木光照模型 - 学术验证绘图工具 / Tree Lighting Model - Academic Validation & Plotting Tool
功能：全量数据回归分析 (固定90°朝向)、1:1散点图绘制、可靠性统计对比
Features: Full data regression (Fixed 90° orientation), 1:1 scatter plot, reliability stats
"""
import numpy as np
import pandas as pd
import os
import ast
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from matplotlib.ticker import AutoMinorLocator

# ========================== 0. 引入 Treelight 数据库 / Import Treelight Database ==========================
# 接入 treelight 的光度学数据解析器 / Import photometric data parser from treelight
from treelight.ies_parser import parse_ies_full, get_interpolated_intensity

# ========================== 1. 学术配置区域 / Academic Configuration Area ==========================

LIGHT_HEIGHT = 10.0 # 灯具安装高度 (米) / Light installation height (meters)

# === 学术论文标准字体设置 / Academic Paper Standard Font Settings ===
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题 / Fix negative sign display issue
plt.rcParams['mathtext.fontset'] = 'stix'   # 数学公式字体 / Font for mathematical formulas

plt.rcParams.update({
    'axes.labelsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.dpi': 600  # 高清输出 / High-resolution output
})

# ===================================================================

def process_full_data(df, ies_data):
    """ 
    计算全量数据的回归结果 (统一采用 90° 朝向)
    Calculate full regression results (Uniformly using 90° orientation)
    """
    results = []
    for _, row in df.iterrows():
        try:
            # 解析坐标和实测值 / Parse coordinates and measured values
            coord = ast.literal_eval(str(row[df.columns[0]]).replace('（','(').replace('）',')'))
            meas = float(row[df.columns[1]])
            x, y, z = coord
            
            # 计算几何参数 (相对灯具的相对坐标) / Calculate geometric parameters (relative to light coordinates)
            dx, dy, dz = x, y, z - LIGHT_HEIGHT
            d2 = dx**2 + dy**2 + dz**2
            dist = np.sqrt(d2)
            cos_t = abs(dz)/dist # 入射角余弦值 / Cosine of the incidence angle
            theta = np.degrees(np.arccos(cos_t)) # 垂直角 / Vertical angle
            
            # 统一模式: 90度 (灯具旋转90度) / Mode: 90 degrees (light rotated 90 degrees)
            phi90 = np.degrees(np.arctan2(dx, dy)) % 360
            
            # 利用双线性插值获取光强值 / Get light intensity using bilinear interpolation
            # 注意：为保持与原算法完全一致，抵消 treelight 内部自带的 (phi + 90.0) 偏移
            # Note: Offset the default (phi + 90.0) shift in treelight to keep algorithm consistent
            val_s90 = get_interpolated_intensity(ies_data, theta, phi90 - 90.0)

            # 初始照度值 (未乘系数) / Raw illuminance (without scaling factor)
            results.append({
                'meas': meas,
                'raw_s90': (val_s90 / d2) * cos_t
            })
        except Exception: 
            continue
        
    res_df = pd.DataFrame(results)
    if res_df.empty:
        return None
        
    m = res_df['meas'].values # 实测值 / Measured values
    
    # 自动计算缩放系数k，包含PPFD转换系数和灯具折损等
    # Auto-calculate scaling factor k, including PPFD conversion & flux depreciation
    def get_best_k(sim_raw):
        if np.dot(sim_raw, sim_raw) == 0:
            return 0, 0, sim_raw
        k = np.dot(m, sim_raw) / np.dot(sim_raw, sim_raw) 
        sim = sim_raw * k 
        return r2_score(m, sim), k, sim

    r2_90, k90, sim90 = get_best_k(res_df['raw_s90'])
    
    return m, sim90, r2_90, k90, "90°"

def main():
    # 1. 动态获取控制台输入 (Excel 及 IES) / Dynamically get console input (Excel & IES)
    excel_path = input("Enter measured data Excel file path (Press Enter to exit): ").strip(" '\"")
    if not excel_path:
        return
        
    ies_path = input("Enter IES file path (Press Enter to exit): ").strip(" '\"")
    if not ies_path:
        return
        
    print("\n>>> Processing academic validation data...")
    try:
        df_all = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Failed to read Excel file: {e}")
        return

    ies_filename = os.path.basename(ies_path)
    
    # 2. 调用 treelight 库全量解析 IES 文件 / Parse full IES file using treelight library
    ies_data, msg = parse_ies_full(ies_path)
    if not ies_data: 
        print(msg)  
        return
        
    # 得到全量拟合结果 (仅90°) / Get full fitting results (90° only)
    res = process_full_data(df_all, ies_data)
    if not res:
        print("Data processing failed, please check the coordinate format in the Excel file.")
        return
        
    y_meas, y_sim, best_r2, best_k, best_rot = res
    rmse = np.sqrt(mean_squared_error(y_meas, y_sim))
    mae = mean_absolute_error(y_meas, y_sim)
    
    # --- 学术级绘图 / Academic Plotting ---
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    
    # 绘制散点 (空心圆点) / Draw scatter points (hollow circles)
    ax.scatter(y_meas, y_sim, s=45, c='white', edgecolors='#1f77b4', linewidths=1.2, alpha=0.85, label='Experimental Points')
    
    # 绘制1:1参考线 / Draw 1:1 reference line
    max_val = max(y_meas.max(), y_sim.max()) * 1.05
    ax.plot([0, max_val], [0, max_val], color='red', linestyle='--', linewidth=1.5, label='1:1 Line', zorder=1)
    
    # 设置坐标轴标签 / Set axis labels
    ax.set_xlabel(r'Measured PPFD ($\mu mol \cdot m^{-2} \cdot s^{-1}$)')
    ax.set_ylabel(r'Simulated PPFD ($\mu mol \cdot m^{-2} \cdot s^{-1}$)')
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    ax.set_aspect('equal')
    
    # 添加统计框 / Add statistics box
    stats_box = f"$R^2 = {best_r2:.3f}$\n$RMSE = {rmse:.3f}$"
    ax.text(0.05, 0.95, stats_box, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', 
            bbox=dict(boxstyle='square,pad=0.5', facecolor='white', alpha=0.9, edgecolor='black', linewidth=0.8))
    
    # 取消网格并设置刻度 / Disable grid and set minor ticks
    ax.grid(False)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.legend(loc='lower right', frameon=True, edgecolor='black', fancybox=False)
    
    plt.tight_layout()
    plt.show()

    # --- 输出汇总统计表 / Output Summary Table ---
    summary_table = [[ies_filename, best_r2, rmse, mae, best_k, best_rot]]
    cols = ["IES Filename", "R-squared (R²)", "RMSE", "MAE", "Scaling Factor (k)", "Calculated Angle"]
    df_res = pd.DataFrame(summary_table, columns=cols)
    print("\n" + "="*95)
    print(f"{'Final Results of Model Reliability Validation':^90}")
    print("-" * 95)
    print(df_res.to_string(index=False))
    print("="*95)

if __name__ == "__main__":
    main()