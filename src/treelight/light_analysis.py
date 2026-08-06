# -*- coding: utf-8 -*-
"""
Physical Light Analysis and Visualization Module
物理光照计算与可视化分析模块 / Physical Light Analysis and Visualization Module
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import rcParams
from typing import Dict, List, Any, Optional

from .geometry import generate_fibonacci_mesh
from .ies_parser import get_interpolated_intensity
from .config import get_species_params

# =========================================================================
# 模块一：物理光场辐射计算 / Module 1: Physical Radiation Simulation
# =========================================================================
def calculate_canopy_ppfd(geo_params: Dict[str, Any], light_pos_list: List[Dict[str, float]], ies_data: Dict[str, Any], env_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算树冠表面的 PPFD 原始物理分布。
    Calculate the raw PPFD distribution on the canopy surface.
    """
    prec = env_params.get("precision", 0.05)
    
    # 1. 生成树冠网格 / Generate canopy mesh
    centers, normals, areas = generate_fibonacci_mesh(
        geo_params["canopy_type"], 
        geo_params["branch_height"], 
        geo_params["tree_height"] - geo_params["branch_height"], 
        geo_params["crown_width"],
        target_area=prec
    )
    
    total_ppfd = np.zeros(len(centers))
    mf = env_params["maintenance_factor"]       # 路灯维护系数 / Maintenance factor
    lor = env_params["light_output_ratio"]      # 灯具效率 / Light output ratio
    conv = env_params["ppfd_factor"]            # PPFD 转换因子 / PPFD conversion factor
    
    # 2. 遍历所有光源并积分 / Iterate and integrate over all light sources
    for lp in light_pos_list:
        l_pos = np.array([lp["x"], lp["y"], lp["z"]])
        vec = centers - l_pos 
        dists_sq = np.sum(vec**2, axis=1)       # 距离平方 / Squared distance
        
        # 计算光照方向与入射余弦角 / Calculate light direction and incidence angle
        l_dir = vec / (np.sqrt(dists_sq)[:, np.newaxis] + 1e-9)
        cos_alpha = np.sum(normals * (-l_dir), axis=1)
        lit_mask = cos_alpha > 0                # 面向光源的表面掩码 / Mask for surfaces facing the light
        
        if not np.any(lit_mask): continue
        
        # 计算用于 IES 插值的球面坐标 / Calculate spherical coordinates for IES mapping
        valid_l_dir = l_dir[lit_mask]
        theta = np.degrees(np.arccos(np.clip(-valid_l_dir[:, 2], -1, 1)))
        phi = np.degrees(np.arctan2(valid_l_dir[:, 1], valid_l_dir[:, 0]))
        phi[phi < 0] += 360
        
        # 获取插值光强 / Get interpolated intensities from IES data
        intensities = np.array([get_interpolated_intensity(ies_data, t, p) 
                                for t, p in zip(theta, phi)])
        
        # 逆平方定律与朗伯余弦定律 / Inverse-square law & Lambert's cosine law
        E = (intensities / dists_sq[lit_mask]) * cos_alpha[lit_mask] * mf * lor
        total_ppfd[lit_mask] += E * conv

    return {
        "centers": centers,
        "normals": normals,
        "areas": areas,
        "ppfd_raw": total_ppfd,
        "geo_params": geo_params,
        "light_pos": light_pos_list[0] if light_pos_list else None
    }

# =========================================================================
# 模块二：光环境生态分级 / Module 2: Light Environment Ecological Grading
# =========================================================================
def grade_light_environment(physics_result: Dict[str, Any], species_name: str) -> Dict[str, Any]:
    """
    对光环境进行分级统计与面积占比分析。
    Grade and statistically analyze the light environment distribution.
    """
    ppfd = physics_result["ppfd_raw"]
    areas = physics_result["areas"]
    
    params = get_species_params(species_name)
    LCP = params["LCP"] # 树种的光补偿点 / Light Compensation Point
    
    # 动态定义数据统计区间 / Dynamically define intervals
    bins = [0.01, 0.1, 1.0, LCP, 99999.0]
    labels = ["0.01-0.1", "0.1-1.0", "1.0-LCP", ">LCP"]
    
    stats_area = {}
    
    # 统计各区间内的受光表面积 / Calculate illuminated area for each interval
    for i in range(len(bins)-1):
        mask = (ppfd >= bins[i]) & (ppfd < bins[i+1])
        stats_area[labels[i]] = np.sum(areas[mask])

    # 计算有效平均 PPFD (剔除完全背光的暗区) / Calculate effective Average PPFD (exclude pure dark zones)
    mask_lit = ppfd > 0.01
    avg_val = np.average(ppfd[mask_lit], weights=areas[mask_lit]) if np.any(mask_lit) else 0.0

    return {
        "species": species_name,
        "LCP_ref": LCP,
        "grade_stats_area": stats_area,
        "total_area": np.sum(areas),
        # 【核心容错】防止因空树冠导致的 np.max 崩溃 / Prevent np.max crash on empty arrays
        "max_ppfd": np.max(ppfd) if len(ppfd) > 0 else 0.0, 
        "avg_ppfd": avg_val
    }

# =========================================================================
# 模块三：3D 可视化系统 / Module 3: 3D Visualization System
# =========================================================================
def visualize_ppfd_3d(physics_result: Dict[str, Any], species_name: Optional[str] = None, show: bool = True, save_path: Optional[str] = None) -> None:
    """
    生成学术级双视口 3D PPFD 热力图。
    Generate academic-grade dual-viewport 3D heatmaps.
    """
    pts = physics_result["centers"]
    ppfd = physics_result["ppfd_raw"]
    geo = physics_result["geo_params"]
    lp = physics_result["light_pos"]
    
    # 字体配置 (包含中文支持) / Font configuration with Chinese support
    rcParams['font.family'] = ['Times New Roman', 'SimHei', 'Microsoft YaHei']
    rcParams['font.size'] = 10.5
    rcParams['axes.unicode_minus'] = False 

    # 为学术可视化定制红绿渐变色图 / Custom colormap for academic visual representation
    colors = ["#006400", "#32CD32", "#FFFF00", "#FF0000"]
    custom_cmap = mcolors.LinearSegmentedColormap.from_list("GreenRed", colors, N=100)
    
    # --- 【核心修复：动态计算坐标轴边界与比例】 / Dynamic Coordinate Axis Calculation ---
    # 根据用户实际输入的树高和灯高，计算 Z 轴上限 (加 1 米缓冲) / Calculate Z-axis max limit
    tree_h = geo.get("tree_height", 10.0)
    light_z = lp["z"] if lp else 0.0
    max_z = max(tree_h, light_z) + 1.0
    
    # 根据冠幅计算 X/Y 轴范围 (加 1 米缓冲，最少 4 米) / Calculate X/Y axis limits
    crown_w = geo.get("crown_width", 5.0)
    max_xy = max(4.0, crown_w / 2.0 + 1.0)
    # -------------------------------------------------------------------------
    
    # 生成树干几何体用于视觉参照 / Generate trunk geometry for visual context
    bh = geo["branch_height"]
    z_trunk = np.linspace(0, bh, 20)
    theta_trunk = np.linspace(0, 2*np.pi, 30)
    Tg, Zg = np.meshgrid(theta_trunk, z_trunk)
    Rg = 0.2 
    X_trunk = Rg * np.cos(Tg)
    Y_trunk = Rg * np.sin(Tg)
    
    fig = plt.figure(figsize=(12, 6), dpi=100)
    if species_name:
        fig.suptitle(f"Light Analysis: {species_name}", fontsize=14, y=0.95)
    
    # === 左图 (全局视角) / Left Plot (Global View) ===
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    sc1 = ax1.scatter(pts[:,0], pts[:,1], pts[:,2], c=ppfd, cmap=custom_cmap, s=6, vmin=0, vmax=np.max(ppfd) if len(ppfd)>0 else 1)
    ax1.plot_surface(X_trunk, Y_trunk, Zg, color='#5D4037', shade=True, alpha=1.0)
    
    # 绘制光源位置 / Plot light source
    if lp:
        ax1.scatter([lp["x"]], [lp["y"]], [lp["z"]], c='#FFD700', s=200, marker='*', zorder=10)
        ax1.plot([lp["x"], lp["x"]], [lp["y"], lp["y"]], [0, lp["z"]], 'k--', lw=0.8)
    
    # 动态应用自适应坐标轴和严格物理等比例 / Apply dynamic limits and strict aspect ratio
    ax1.set_xlabel('X (m)'); ax1.set_ylabel('Y (m)'); ax1.set_zlabel('Height (m)')
    ax1.set_xlim([-max_xy, max_xy]); ax1.set_ylim([-max_xy, max_xy]); ax1.set_zlim([0, max_z])
    ax1.set_box_aspect((max_xy*2, max_xy*2, max_z)) 
    
    ax1.view_init(elev=25, azim=-45)
    ax1.text2D(0.0, 0.95, "a", transform=ax1.transAxes, fontsize=18, fontweight='bold')
    
    # === 右图 (局部对齐视角) / Right Plot (Focus View) ===
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    sc2 = ax2.scatter(pts[:,0], pts[:,1], pts[:,2], c=ppfd, cmap=custom_cmap, s=10, vmin=0, vmax=np.max(ppfd) if len(ppfd)>0 else 1)
    ax2.plot_surface(X_trunk, Y_trunk, Zg, color='#5D4037', shade=True)
    
    # 自动对齐视角至最大光强点 / Auto-align view to the point with maximum PPFD
    if len(ppfd) > 0:
        idx_max = np.argmax(ppfd)
        p_max = pts[idx_max]
        azim = np.degrees(np.arctan2(p_max[1], p_max[0]))
        elev_angle = np.degrees(np.arctan2(p_max[2], np.sqrt(p_max[0]**2 + p_max[1]**2)))
        ax2.view_init(elev=max(20, elev_angle), azim=azim)
        
    # 与左图保持绝对一致的动态坐标轴与比例 / Maintain identical dynamic limits and aspect ratio with the left plot
    ax2.set_xlabel('X (m)'); ax2.set_ylabel('Y (m)'); ax2.set_zlabel('Height (m)')
    ax2.set_xlim([-max_xy, max_xy]); ax2.set_ylim([-max_xy, max_xy]); ax2.set_zlim([0, max_z])
    ax2.set_box_aspect((max_xy*2, max_xy*2, max_z))
    
    ax2.text2D(0.0, 0.95, "b", transform=ax2.transAxes, fontsize=18, fontweight='bold')
    
    # 颜色条配置 / Colorbar configuration
    cbar = fig.colorbar(sc2, ax=[ax1, ax2], fraction=0.03, pad=0.05, shrink=0.8)
    cbar.set_label('PPFD ($\mu mol \cdot m^{-2} \cdot s^{-1}$)')
    
    plt.subplots_adjust(left=0.05, right=0.9, bottom=0.1, top=0.9, wspace=0.1)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
