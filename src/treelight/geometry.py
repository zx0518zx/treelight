# -*- coding: utf-8 -*-
"""
3D Canopy Geometry Generator
3D 树冠几何网格生成器
"""
import numpy as np
from typing import Tuple, List

def generate_fibonacci_mesh(canopy_type: str, bh: float, ch: float, cw: float, target_area: float = 0.01) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate uniform point clouds and normal vectors based on the Fibonacci lattice method.
    基于斐波那契网格算法，生成均匀分布的树冠表面点云及其法向量。

    Args:
        canopy_type (str): Shape of the canopy (e.g., Half Ellipsoid, Cone, Cylinder) / 树冠形状 (如 半椭球体、圆锥体、圆柱体)
        bh (float): Branch height (under-branch clearance) in meters / 枝下高 (米)
        ch (float): Crown height in meters / 树冠高度 (米)
        cw (float): Crown width (diameter) in meters / 冠幅直径 (米)
        target_area (float): Target area per mesh grid (m²) / 每个网格的预期划分面积 (平方米)

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: 
            - centers: (N, 3) array of grid center coordinates / 网格中心坐标
            - normals: (N, 3) array of normal vectors / 法向量
            - areas: (N,) array of grid areas / 网格表面积
    """
    radius = cw / 2.0
    
    # Error Interception: Prevent zero-division or meaningless calculation due to invalid parameters
    # 异常拦截：防止因参数为0或极小导致除零错误或无意义的几何计算
    if radius <= 0.01 or (ch <= 0.01 and "圆柱" not in str(canopy_type) and "Cylinder" not in str(canopy_type)):
        return np.array([]), np.array([]), np.array([])
        
    centers, normals, areas = [], [], []
    
    # --- Helper Function 1: Fibonacci Sphere Generator / 辅助函数 1：斐波那契球面生成器 ---
    def fib_sphere(n: int, r_scale: float, z_scale: float, z_offset: float, cap_mode: bool = False) -> Tuple[List[List[float]], List[List[float]]]:
        if n <= 0: return [], []
        pts, nms = [], []
        phi = (np.sqrt(5) - 1) / 2 # Golden ratio conjugate / 黄金分割共轭值
        
        for i in range(n):
            y_s = 1 - (i / float(n - 1)) * 2 if n > 1 else 0
            if cap_mode: y_s = 1 - (i / float(n - 1)) if n > 1 else 1
            
            radius_at_y = np.sqrt(max(0, 1 - y_s * y_s))
            theta = 2 * np.pi * i * phi
            
            x = r_scale * radius_at_y * np.cos(theta)
            y = r_scale * radius_at_y * np.sin(theta)
            z = z_scale * y_s + z_offset
            pts.append([x, y, z])
            
            # Normal vector calculation / 法向量计算
            if cap_mode:
                sr, sz = max(1e-6, r_scale), max(1e-6, z_scale)
                nx, ny, nz = x/(sr**2), y/(sr**2), (z-z_offset)/(sz**2)
                l = np.sqrt(nx*nx + ny*ny + nz*nz)
                nms.append([nx/l, ny/l, nz/l] if l > 0 else [0, 0, 1])
            else:
                nms.append([0, 0, 1])
        return pts, nms

    # --- Helper Function 2: Fibonacci Disk Generator / 辅助函数 2：斐波那契圆盘生成器 ---
    def fib_disk(n: int, z_pos: float, normal_dir: List[float]) -> Tuple[List[List[float]], List[List[float]]]:
        if n <= 0: return [], []
        pts, nms = [], []
        phi = (np.sqrt(5) - 1) / 2
        for i in range(n):
            r = radius * np.sqrt(i / (n - 0.5) if n > 0 else 0)
            theta = 2 * np.pi * i * phi
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            pts.append([x, y, z_pos])
            nms.append(normal_dir)
        return pts, nms

    # --- Main Geometry Generation Logic / 核心几何生成逻辑 ---
    if "半椭球" in str(canopy_type) or "Half Ellipsoid" in str(canopy_type):
        p = 1.6075 # Knud Thomsen's formula approximation exponent / 椭球表面积近似公式指数
        area_ellip = 2 * np.pi * ((radius**p * radius**p + 2 * radius**p * ch**p) / 3)**(1/p)
        area_bottom = np.pi * radius**2
        
        # Grid quantity calculation with max(1) protection / 网格数计算 (添加 max(1) 保护防止划分数为0)
        n_side = max(1, int(area_ellip / target_area))
        n_bottom = max(1, int(area_bottom / target_area))
        
        s_pts, s_nms = fib_sphere(n_side, radius, ch, bh, cap_mode=True)
        b_pts, b_nms = fib_disk(n_bottom, bh, [0, 0, -1])
        
        centers, normals = s_pts + b_pts, s_nms + b_nms
        areas = [area_ellip/n_side]*len(s_pts) + [area_bottom/n_bottom]*len(b_pts)

    elif "圆锥" in str(canopy_type) or "Cone" in str(canopy_type):
        slant = np.sqrt(radius**2 + ch**2)
        area_side = np.pi * radius * slant
        area_bottom = np.pi * radius**2
        
        n_side = max(1, int(area_side / target_area))
        n_bottom = max(1, int(area_bottom / target_area))
        
        s_pts, s_nms = [], []
        phi = (np.sqrt(5) - 1) / 2
        sin_alpha = radius / (slant + 1e-9)
        cos_alpha = ch / (slant + 1e-9)
        
        for i in range(n_side):
            ratio = np.sqrt(i / (n_side - 0.5)) if n_side > 1 else 0.5
            cur_r = radius * (1 - ratio)
            cur_z = bh + ch * ratio
            theta = 2 * np.pi * i * phi
            x = cur_r * np.cos(theta)
            y = cur_r * np.sin(theta)
            s_pts.append([x, y, cur_z])
            
            nx, ny, nz = cos_alpha * np.cos(theta), cos_alpha * np.sin(theta), sin_alpha 
            s_nms.append([nx, ny, nz])
            
        b_pts, b_nms = fib_disk(n_bottom, bh, [0, 0, -1])
        centers, normals = s_pts + b_pts, s_nms + b_nms
        areas = [area_side/n_side]*len(s_pts) + [area_bottom/n_bottom]*len(b_pts)

    else: # Default: Cylinder / 默认: 圆柱体
        area_side = 2 * np.pi * radius * ch
        area_cap = np.pi * radius**2
        
        n_side = max(1, int(area_side / target_area))
        n_cap = max(1, int(area_cap / target_area))
        
        s_pts, s_nms = [], []
        phi = (np.sqrt(5) - 1) / 2
        for i in range(n_side):
            z = bh + ch * (i / (n_side - 1)) if n_side > 1 else bh + ch/2
            theta = 2 * np.pi * i * phi
            x = radius * np.cos(theta)
            y = radius * np.sin(theta)
            s_pts.append([x, y, z])
            s_nms.append([np.cos(theta), np.sin(theta), 0])
            
        t_pts, t_nms = fib_disk(n_cap, bh + ch, [0, 0, 1])
        b_pts, b_nms = fib_disk(n_cap, bh, [0, 0, -1])
        
        centers, normals = s_pts + t_pts + b_pts, s_nms + t_nms + b_nms
        areas = [area_side/n_side]*len(s_pts) + [area_cap/n_cap]*len(t_pts) + [area_cap/n_cap]*len(b_pts)

    return np.array(centers), np.array(normals), np.array(areas)
