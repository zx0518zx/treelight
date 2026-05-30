import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import rcParams

from .geometry import generate_fibonacci_mesh
from .ies_parser import get_interpolated_intensity
from .config import get_species_params

# =========================================================================
# 模块一：物理计算 (保持不变)
# =========================================================================
def calculate_canopy_ppfd(geo_params, light_pos_list, ies_data, env_params):
    """
    计算树冠表面的 PPFD 原始分布
    """
    prec = env_params.get("precision", 0.05)
    centers, normals, areas = generate_fibonacci_mesh(
        geo_params["canopy_type"], 
        geo_params["branch_height"], 
        geo_params["tree_height"] - geo_params["branch_height"], 
        geo_params["crown_width"],
        target_area=prec
    )
    
    total_ppfd = np.zeros(len(centers))
    mf = env_params["maintenance_factor"]
    lor = env_params["light_output_ratio"]
    conv = env_params["ppfd_factor"]
    
    for lp in light_pos_list:
        l_pos = np.array([lp["x"], lp["y"], lp["z"]])
        vec = centers - l_pos 
        dists_sq = np.sum(vec**2, axis=1)
        l_dir = vec / (np.sqrt(dists_sq)[:, np.newaxis] + 1e-9)
        cos_alpha = np.sum(normals * (-l_dir), axis=1)
        lit_mask = cos_alpha > 0 
        
        if not np.any(lit_mask): continue
        
        valid_l_dir = l_dir[lit_mask]
        theta = np.degrees(np.arccos(np.clip(-valid_l_dir[:, 2], -1, 1)))
        phi = np.degrees(np.arctan2(valid_l_dir[:, 1], valid_l_dir[:, 0]))
        phi[phi < 0] += 360
        
        intensities = np.array([get_interpolated_intensity(ies_data, t, p) 
                                for t, p in zip(theta, phi)])
        
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
# 模块二：光环境分级 (【核心修改】与 v4.5 脚本对齐)
# =========================================================================
def grade_light_environment(physics_result, species_name):
    """
    对光环境进行分级统计
    区间：0.01-0.1, 0.1-1.0, 1.0-LCP, >LCP
    平均值：仅计算 PPFD > 0.01 的区域
    """
    ppfd = physics_result["ppfd_raw"]
    areas = physics_result["areas"]
    
    params = get_species_params(species_name)
    LCP = params["LCP"]
    
    # 1. 动态定义区间 (与 v4.5 一致)
    bins = [0.01, 0.1, 1.0, LCP, 99999.0]
    labels = [
        "0.01-0.1", 
        "0.1-1.0", 
        "1.0-LCP", 
        ">LCP"
    ]
    
    stats_area = {}
    
    # 2. 统计各区间面积
    for i in range(len(bins)-1):
        mask = (ppfd >= bins[i]) & (ppfd < bins[i+1])
        stats_area[labels[i]] = np.sum(areas[mask])

    # 3. 计算平均 PPFD (修正逻辑：仅计算受光面 > 0.01)
    # 这样可以避免背光面的 0 值拉低平均数
    mask_lit = ppfd > 0.01
    if np.any(mask_lit):
        avg_val = np.average(ppfd[mask_lit], weights=areas[mask_lit])
    else:
        avg_val = 0.0

    return {
        "species": species_name,
        "LCP_ref": LCP,
        "grade_stats_area": stats_area, # 返回面积字典
        "total_area": np.sum(areas),    # 树冠总面积
        "max_ppfd": np.max(ppfd),
        "avg_ppfd": avg_val             # 修正后的平均值
    }

# =========================================================================
# 模块三：3D 可视化 (保持不变)
# =========================================================================
def visualize_ppfd_3d(physics_result, species_name=None, show=True, save_path=None):
    """
    生成学术级双视口 3D 热力图
    """
    pts = physics_result["centers"]
    ppfd = physics_result["ppfd_raw"]
    geo = physics_result["geo_params"]
    lp = physics_result["light_pos"]
    
    rcParams['font.family'] = ['Times New Roman', 'SimHei', 'Microsoft YaHei']
    rcParams['font.size'] = 10.5
    rcParams['axes.unicode_minus'] = False 

    colors = ["#006400", "#32CD32", "#FFFF00", "#FF0000"]
    custom_cmap = mcolors.LinearSegmentedColormap.from_list("GreenRed", colors, N=100)
    
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
    
    # --- 左图 ---
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    sc1 = ax1.scatter(pts[:,0], pts[:,1], pts[:,2], c=ppfd, cmap=custom_cmap, s=6, vmin=0, vmax=np.max(ppfd))
    ax1.plot_surface(X_trunk, Y_trunk, Zg, color='#5D4037', shade=True, alpha=1.0)
    if lp:
        ax1.scatter([lp["x"]], [lp["y"]], [lp["z"]], c='#FFD700', s=200, marker='*', zorder=10)
        ax1.plot([lp["x"], lp["x"]], [lp["y"], lp["y"]], [0, lp["z"]], 'k--', lw=0.8)
    
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_zlabel('Height (m)')
    ax1.set_xlim([-4, 4]); ax1.set_ylim([-4, 4]); ax1.set_zlim([0, 10])
    ax1.set_box_aspect((10, 10, 10))
    ax1.view_init(elev=25, azim=-45)
    ax1.text2D(0.0, 0.95, "a", transform=ax1.transAxes, fontsize=18, fontweight='bold')
    
    # --- 右图 ---
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    sc2 = ax2.scatter(pts[:,0], pts[:,1], pts[:,2], c=ppfd, cmap=custom_cmap, s=10, vmin=0, vmax=np.max(ppfd))
    ax2.plot_surface(X_trunk, Y_trunk, Zg, color='#5D4037', shade=True)
    
    if len(ppfd) > 0:
        idx_max = np.argmax(ppfd)
        p_max = pts[idx_max]
        azim = np.degrees(np.arctan2(p_max[1], p_max[0]))
        elev_angle = np.degrees(np.arctan2(p_max[2], np.sqrt(p_max[0]**2 + p_max[1]**2)))
        ax2.view_init(elev=max(20, elev_angle), azim=azim)
        
    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Y (m)')
    ax2.set_zlabel('Height (m)')
    ax2.set_xlim([-4, 4]); ax2.set_ylim([-4, 4]); ax2.set_zlim([0, 6])
    ax2.set_box_aspect((10, 10, 10))
    ax2.text2D(0.0, 0.95, "b", transform=ax2.transAxes, fontsize=18, fontweight='bold')
    
    cbar = fig.colorbar(sc2, ax=[ax1, ax2], fraction=0.03, pad=0.05, shrink=0.8)
    cbar.set_label('PPFD ($\mu mol \cdot m^{-2} \cdot s^{-1}$)')
    
    plt.subplots_adjust(left=0.05, right=0.9, bottom=0.1, top=0.9, wspace=0.1)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()