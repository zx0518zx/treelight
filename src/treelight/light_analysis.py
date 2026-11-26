# -*- coding: utf-8 -*-
"""
Physical Light Analysis and Visualization Module / 物理光照计算与可视化分析模块
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import rcParams
from typing import Dict, List, Any, Optional, Tuple

try:
    from .geometry import generate_fibonacci_mesh
    from .ies_parser import get_interpolated_intensity
    from .config import get_species_params
except ImportError:
    from treelight.geometry import generate_fibonacci_mesh
    from treelight.ies_parser import get_interpolated_intensity
    from treelight.config import get_species_params


def compute_ies_angles(l_dir: np.ndarray, yaw: float = 0.0, tilt: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Transform world ray unit vectors (luminaire -> target) into IES photometric angles (theta, phi).
    将世界坐标系下的光线单位向量（光源指向目标点）转换为 IES 配光角 (theta, phi)。

    Conventions / 角度约定:
        - yaw (deg): Horizontal luminaire orientation around +Z (0°=+X, 90°=+Y, 180°=-X, 270°=-Y).
        - tilt (deg): Upward luminaire elevation angle toward its forward axis (0°=horizontal, >0°=tilted up).
    """
    l_dir = np.atleast_2d(np.asarray(l_dir, dtype=float))
    yaw_rad = np.radians(float(yaw))
    tilt_rad = np.radians(float(tilt))

    cos_y, sin_y = np.cos(yaw_rad), np.sin(yaw_rad)
    cos_t, sin_t = np.cos(tilt_rad), np.sin(tilt_rad)

    # Step 1: Rotate world ray into yaw-aligned frame / 水平旋转至灯具前向坐标系
    u1x = l_dir[:, 0] * cos_y + l_dir[:, 1] * sin_y
    u1y = -l_dir[:, 0] * sin_y + l_dir[:, 1] * cos_y
    u1z = l_dir[:, 2]

    # Step 2: Project onto tilted luminaire local axes / 投影至仰角倾斜后的灯具局部坐标系
    x_loc = u1x * cos_t + u1z * sin_t
    y_loc = u1y
    d_loc = u1x * sin_t - u1z * cos_t  # component along luminaire nadir (theta=0°)

    theta = np.degrees(np.arccos(np.clip(d_loc, -1.0, 1.0)))
    phi = np.degrees(np.arctan2(y_loc, x_loc))
    phi[phi < 0] += 360.0
    return theta, phi


# =========================================================================
# 模块一：物理光场辐射计算 / Module 1: Physical Radiation Simulation
# =========================================================================
def calculate_canopy_ppfd(
    geo_params: Dict[str, Any],
    light_pos_list: List[Dict[str, Any]],
    ies_data: Dict[str, Any],
    env_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate the raw PPFD distribution on the canopy surface. / 计算树冠表面的 PPFD 原始物理分布。

    Supports linear superposition of multiple luminaires via `light_pos_list`, optional per-lamp
    `yaw` (horizontal orientation, deg), `tilt` (upward elevation, deg), and `ies_data` (individual
    parsed IES dict overriding the default `ies_data`), plus `cosine_correction` in `env_params`.
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
    mf = env_params["maintenance_factor"]                 # 路灯维护系数 / Maintenance factor
    lor = env_params["light_output_ratio"]                # 灯具效率 / Light output ratio
    conv = env_params["ppfd_factor"]                      # PPFD 转换因子 / PPFD conversion factor
    use_cosine = env_params.get("cosine_correction", True) # 余弦校正开关（默认开启）/ Cosine correction toggle

    # 2. 遍历所有光源并线性叠加积分 / Iterate and linearly superimpose all light sources
    for lp in light_pos_list:
        l_pos = np.array([lp["x"], lp["y"], lp["z"]], dtype=float)
        yaw = float(lp.get("yaw", 0.0))
        tilt = float(lp.get("tilt", 0.0))
        lamp_ies = lp.get("ies_data") or ies_data         # 支持每个光源使用独立 IES 数据 / Per-lamp IES support

        vec = centers - l_pos
        dists_sq = np.sum(vec**2, axis=1)                 # 距离平方 / Squared distance

        # 计算光照方向与入射余弦角 / Calculate light direction and incidence angle
        l_dir = vec / (np.sqrt(dists_sq)[:, np.newaxis] + 1e-9)
        cos_alpha = np.sum(normals * (-l_dir), axis=1)
        lit_mask = cos_alpha > 0                          # 面向光源的表面掩码 / Mask for surfaces facing the light

        if not np.any(lit_mask):
            continue

        # 计算考虑水平朝向角 (yaw) 与仰角 (tilt) 的 IES 配光球面角 / Compute IES spherical angles with yaw & tilt
        theta, phi = compute_ies_angles(l_dir[lit_mask], yaw=yaw, tilt=tilt)

        # 获取插值光强 / Get interpolated intensities from IES data
        intensities = np.array([
            get_interpolated_intensity(lamp_ies, t, p)
            for t, p in zip(theta, phi)
        ])

        # 逆平方定律与可选朗伯余弦定律 / Inverse-square law & optional Lambert's cosine law
        cos_term = cos_alpha[lit_mask] if use_cosine else 1.0
        E = (intensities / dists_sq[lit_mask]) * cos_term * mf * lor
        total_ppfd[lit_mask] += E * conv

    return {
        "centers": centers,
        "normals": normals,
        "areas": areas,
        "ppfd_raw": total_ppfd,
        "geo_params": geo_params,
        "light_pos": light_pos_list[0] if light_pos_list else None,
        "light_pos_list": list(light_pos_list),
        "ies_data": ies_data,
        "env_params": dict(env_params)
    }


# =========================================================================
# 模块二：光环境生态分级 / Module 2: Light Environment Ecological Grading
# =========================================================================
def grade_light_environment(physics_result: Dict[str, Any], species_name: str) -> Dict[str, Any]:
    """
    Grade the light environment and analyze its area distribution. / 对光环境进行分级统计与面积占比分析。
    """
    ppfd = physics_result["ppfd_raw"]
    areas = physics_result["areas"]

    params = get_species_params(species_name)
    LCP = params["LCP"]  # 树种的光补偿点 / Light Compensation Point

    bins = [0.01, 0.1, 1.0, LCP, 99999.0]
    labels = ["0.01-0.1", "0.1-1.0", "1.0-LCP", ">LCP"]

    stats_area = {}
    for i in range(len(bins) - 1):
        mask = (ppfd >= bins[i]) & (ppfd < bins[i + 1])
        stats_area[labels[i]] = np.sum(areas[mask])

    mask_lit = ppfd > 0.01
    avg_val = np.average(ppfd[mask_lit], weights=areas[mask_lit]) if np.any(mask_lit) else 0.0

    return {
        "species": species_name,
        "LCP_ref": LCP,
        "grade_stats_area": stats_area,
        "total_area": np.sum(areas),
        "max_ppfd": np.max(ppfd) if len(ppfd) > 0 else 0.0,
        "avg_ppfd": avg_val
    }


def _plot_ground_ies_footprint(
    ax,
    light_list: List[Dict[str, Any]],
    default_ies: Optional[Dict[str, Any]],
    env_params: Dict[str, Any],
    max_xy: float
) -> None:
    """
    Compute and render the true physical ground-plane (z=0) irradiance footprint from actual IES data,
    plus a subtle dashed ray from each luminaire to its real ground peak illumination point.
    基于真实 IES 配光数据计算并在地面 (z=0) 绘制实际光照覆盖等值面，同时用细虚线连接每盏灯与其地面最亮中心。
    """
    if not light_list:
        return

    n_grid = 45
    xs = np.linspace(-max_xy, max_xy, n_grid)
    ys = np.linspace(-max_xy, max_xy, n_grid)
    Xg, Yg = np.meshgrid(xs, ys)
    pts_g = np.column_stack([Xg.ravel(), Yg.ravel(), np.zeros(Xg.size)])

    mf = float(env_params.get("maintenance_factor", 1.0))
    lor = float(env_params.get("light_output_ratio", 1.0))
    conv = float(env_params.get("ppfd_factor", 0.0154))

    total_ground_ppfd = np.zeros(pts_g.shape[0])
    peak_points = []
    has_any_ies = False

    for lp in light_list:
        lamp_ies = lp.get("ies_data") or default_ies
        if lamp_ies is None:
            continue
        has_any_ies = True

        l_pos = np.array([lp["x"], lp["y"], lp["z"]], dtype=float)
        yaw = float(lp.get("yaw", 0.0))
        tilt = float(lp.get("tilt", 0.0))

        vec = pts_g - l_pos
        dists_sq = np.sum(vec**2, axis=1) + 1e-9
        l_dir = vec / np.sqrt(dists_sq)[:, None]
        cos_g = np.clip(-l_dir[:, 2], 0.0, 1.0)

        theta, phi = compute_ies_angles(l_dir, yaw=yaw, tilt=tilt)
        intensities = np.array([get_interpolated_intensity(lamp_ies, t, p) for t, p in zip(theta, phi)])
        ppfd_i = (intensities / dists_sq) * cos_g * mf * lor * conv
        total_ground_ppfd += ppfd_i

        # Record real peak illumination point on the ground for this lamp / 记录该灯在地面上的真实最亮点
        idx_p = int(np.argmax(ppfd_i))
        if ppfd_i[idx_p] > 0:
            peak_points.append((l_pos, pts_g[idx_p]))

    if not has_any_ies or np.max(total_ground_ppfd) <= 0:
        return

    Zg_ppfd = total_ground_ppfd.reshape(Xg.shape)
    gmax = float(np.max(Zg_ppfd))

    # Subtle warm translucent ground-footprint colormap (transparent at low values -> warm gold/amber at peak)
    ground_cmap = mcolors.LinearSegmentedColormap.from_list(
        "GroundLight",
        [(1.0, 0.99, 0.90, 0.0), (1.0, 0.95, 0.60, 0.25), (1.0, 0.80, 0.22, 0.48), (0.95, 0.55, 0.10, 0.65)],
        N=64
    )
    levels = np.linspace(gmax * 0.08, gmax, 9)
    ax.contourf(Xg, Yg, Zg_ppfd, levels=levels, zdir='z', offset=0.0, cmap=ground_cmap, zorder=0)
    ax.contour(Xg, Yg, Zg_ppfd, levels=levels[::2], zdir='z', offset=0.0, colors='#D97706', linewidths=0.75, alpha=0.55, zorder=1)

    # Draw subtle dashed aiming ray from each lamp to its actual brightest ground spot / 连接灯具与地面最亮点的细虚线
    for l_pos, p_peak in peak_points:
        ax.plot(
            [l_pos[0], p_peak[0]], [l_pos[1], p_peak[1]], [l_pos[2], 0.0],
            color='#D97706', linestyle='--', linewidth=1.2, alpha=0.70, zorder=4
        )
        ax.scatter([p_peak[0]], [p_peak[1]], [0.0], color='#D97706', marker='x', s=32, linewidths=1.3, alpha=0.85, zorder=5)


# =========================================================================
# 模块三：3D 可视化系统 / Module 3: 3D Visualization System
# =========================================================================
def visualize_ppfd_3d(
    physics_result: Dict[str, Any],
    species_name: Optional[str] = None,
    show: bool = True,
    save_path: Optional[str] = None
) -> None:
    """
    Generate academic-grade dual-viewport 3D PPFD heatmaps. / 生成学术级双视口 3D PPFD 热力图。
    """
    pts = physics_result["centers"]
    ppfd = physics_result["ppfd_raw"]
    geo = physics_result["geo_params"]

    light_list = physics_result.get("light_pos_list")
    if not light_list and physics_result.get("light_pos"):
        light_list = [physics_result["light_pos"]]
    light_list = light_list or []

    rcParams['font.family'] = ['Times New Roman', 'SimHei', 'Microsoft YaHei']
    rcParams['font.size'] = 10.5
    rcParams['axes.unicode_minus'] = False

    colors = ["#006400", "#32CD32", "#FFFF00", "#FF0000"]
    custom_cmap = mcolors.LinearSegmentedColormap.from_list("GreenRed", colors, N=100)

    tree_h = geo.get("tree_height", 10.0)
    light_z = max((l["z"] for l in light_list), default=0.0)
    max_z = max(tree_h, light_z) + 1.0

    crown_w = geo.get("crown_width", 5.0)
    light_xy = max((max(abs(l["x"]), abs(l["y"])) for l in light_list), default=0.0)
    max_xy = max(4.0, crown_w / 2.0 + 1.0, light_xy + 1.0)

    bh = geo["branch_height"]
    z_trunk = np.linspace(0, bh, 20)
    theta_trunk = np.linspace(0, 2 * np.pi, 30)
    Tg, Zg = np.meshgrid(theta_trunk, z_trunk)
    Rg = 0.2
    X_trunk = Rg * np.cos(Tg)
    Y_trunk = Rg * np.sin(Tg)

    fig = plt.figure(figsize=(12, 6), dpi=100)
    if species_name:
        fig.suptitle(f"Light Analysis: {species_name}", fontsize=14, y=0.95)

    vmax_val = np.max(ppfd) if len(ppfd) > 0 and np.max(ppfd) > 0 else 1.0

    # === 左图 (全局视角) / Left Plot (Global View) ===
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')

    # 在地面 (z=0) 绘制基于真实 IES 配光的实际照射范围等值面 / Render true physical IES ground footprint at z=0
    _plot_ground_ies_footprint(
        ax1, light_list,
        physics_result.get("ies_data"),
        physics_result.get("env_params", {}),
        max_xy
    )

    sc1 = ax1.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=ppfd, cmap=custom_cmap, s=6, vmin=0, vmax=vmax_val, zorder=3)
    ax1.plot_surface(X_trunk, Y_trunk, Zg, color='#5D4037', shade=True, alpha=1.0, zorder=2)

    for lp in light_list:
        lx, ly, lz = lp["x"], lp["y"], lp["z"]
        ax1.scatter([lx], [ly], [lz], c='#FFD700', edgecolors='#B45309', linewidths=0.8, s=200, marker='*', zorder=10)
        ax1.plot([lx, lx], [ly, ly], [0, lz], 'k--', lw=0.8)

    ax1.set_xlabel('X (m)'); ax1.set_ylabel('Y (m)'); ax1.set_zlabel('Height (m)')
    ax1.set_xlim([-max_xy, max_xy]); ax1.set_ylim([-max_xy, max_xy]); ax1.set_zlim([0, max_z])
    ax1.set_box_aspect((max_xy * 2, max_xy * 2, max_z))

    ax1.view_init(elev=25, azim=-45)
    ax1.text2D(0.0, 0.95, "a", transform=ax1.transAxes, fontsize=18, fontweight='bold')

    # === 右图 (局部对齐视角) / Right Plot (Focus View) ===
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    sc2 = ax2.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=ppfd, cmap=custom_cmap, s=10, vmin=0, vmax=vmax_val)
    ax2.plot_surface(X_trunk, Y_trunk, Zg, color='#5D4037', shade=True)

    if len(ppfd) > 0:
        idx_max = np.argmax(ppfd)
        p_max = pts[idx_max]
        azim = np.degrees(np.arctan2(p_max[1], p_max[0]))
        elev_angle = np.degrees(np.arctan2(p_max[2], np.sqrt(p_max[0]**2 + p_max[1]**2)))
        ax2.view_init(elev=max(20, elev_angle), azim=azim)

    ax2.set_xlabel('X (m)'); ax2.set_ylabel('Y (m)'); ax2.set_zlabel('Height (m)')
    ax2.set_xlim([-max_xy, max_xy]); ax2.set_ylim([-max_xy, max_xy]); ax2.set_zlim([0, max_z])
    ax2.set_box_aspect((max_xy * 2, max_xy * 2, max_z))

    ax2.text2D(0.0, 0.95, "b", transform=ax2.transAxes, fontsize=18, fontweight='bold')

    cbar = fig.colorbar(sc2, ax=[ax1, ax2], fraction=0.03, pad=0.05, shrink=0.8)
    cbar.set_label(r'PPFD ($\mu\mathrm{mol}\cdot\mathrm{m}^{-2}\cdot\mathrm{s}^{-1}$)')

    plt.subplots_adjust(left=0.05, right=0.9, bottom=0.1, top=0.9, wspace=0.1)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
