# -*- coding: utf-8 -*-
"""
IES Photometric Data Parser
IES 光度学数据解析器
"""
import numpy as np
import os
from typing import Tuple, Optional, Dict, Any

def parse_ies_full(ies_path: str) -> Tuple[Optional[Dict[str, np.ndarray]], str]:
    """
    Fully parse the IES file and return the intensity matrix and angle axes.
    全量解析 IES 文件，返回光强矩阵和角度坐标轴。

    Args:
        ies_path (str): The absolute or relative path to the IES file / IES 文件的绝对或相对路径

    Returns:
        Tuple: A dictionary containing vertical/horizontal angles and intensity grid, and a status message.
               返回一个包含垂直/水平角度和光强网格的字典，以及一条状态信息。
    """
    if not os.path.exists(ies_path):
        return None, f"❌ IES文件未找到 / IES file not found: {ies_path}"
    
    try:
        # Read all non-empty lines / 读取所有非空行
        with open(ies_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [l.strip() for l in f if l.strip()]
        
        # 1. Locate the "TILT=NONE" marker / 定位 TILT=NONE 标记
        start_idx = -1
        for i, l in enumerate(lines):
            if l.upper().startswith("TILT=NONE"):
                start_idx = i
                break
        if start_idx == -1: 
            return None, "❌ IES文件缺少 TILT=NONE 标记 / IES file missing TILT=NONE marker"

        # 2. Read header parameters / 读取头部参数
        header_vals = []
        curr = start_idx + 1
        while len(header_vals) < 10 and curr < len(lines):
            header_vals.extend(lines[curr].split())
            curr += 1
            
        np_cnt = int(float(header_vals[3])) # Number of vertical angles / 垂直角度数
        nr_cnt = int(float(header_vals[4])) # Number of horizontal angles / 水平角度数

        # 3. Read all subsequent floating-point numbers / 读取后续所有浮点数数据
        all_data = []
        for l in lines[curr:]:
            for x in l.split():
                try: all_data.append(float(x))
                except ValueError: pass
        
        # Check data integrity / 校验数据完整性
        total_floats_needed = np_cnt + nr_cnt + (np_cnt * nr_cnt)
        if len(all_data) < total_floats_needed:
            return None, "❌ IES数据不完整 / Incomplete IES photometric data"
            
        raw_data = all_data[-total_floats_needed:]
        
        # Extract matrices / 提取矩阵数据
        vert_angles = np.array(raw_data[:np_cnt])
        horiz_angles = np.array(raw_data[np_cnt : np_cnt+nr_cnt])
        candela_flat = np.array(raw_data[np_cnt+nr_cnt:])
        
        # Reshape to grid / 重塑为二维网格
        intensity_grid = candela_flat.reshape(nr_cnt, np_cnt)
        
        return {
            'v_angles': vert_angles, 
            'h_angles': horiz_angles,
            'grid': intensity_grid
        }, "✅ IES全量解析成功 / IES parsed successfully"
        
    except Exception as e:
        return None, f"❌ IES解析异常 / IES parsing error: {str(e)}"

def get_interpolated_intensity(ies_data: Dict[str, np.ndarray], theta: float, phi: float) -> float:
    """
    Get the light intensity using bilinear interpolation based on given angles.
    利用双线性插值，根据给定的垂直和水平角获取光强值。

    Args:
        ies_data: Parsed IES dictionary / 解析后的 IES 字典
        theta: Vertical angle (degrees) / 垂直角 (度)
        phi: Horizontal angle (degrees) / 水平角 (度)
    """
    v_angs = ies_data['v_angles']
    h_angs = ies_data['h_angles']
    grid = ies_data['grid']
    
    # 1. Angle normalization and mapping / 角度归一化与坐标系映射
    theta = np.clip(theta, v_angs.min(), v_angs.max())
    phi = (phi + 90.0) % 360.0
    max_h = h_angs.max()
    
    target_phi = phi
    if max_h == 0: target_phi = 0
    elif max_h == 90:
        if 0 <= phi <= 90: target_phi = phi
        elif 90 < phi <= 180: target_phi = 180 - phi
        elif 180 < phi <= 270: target_phi = phi - 180
        else: target_phi = 360 - phi
    elif max_h == 180:
        if phi > 180: target_phi = 360 - phi
        else: target_phi = phi
        
    target_phi = np.clip(target_phi, h_angs.min(), h_angs.max())

    # 2. Locate nearest indices / 寻找临近插值索引
    v_idx = np.searchsorted(v_angs, theta)
    h_idx = np.searchsorted(h_angs, target_phi)
    
    v_idx = np.clip(v_idx, 1, len(v_angs)-1)
    h_idx = np.clip(h_idx, 1, len(h_angs)-1)
    
    # 3. Calculate weights / 计算距离权重
    v0, v1 = v_angs[v_idx-1], v_angs[v_idx]
    h0, h1 = h_angs[h_idx-1], h_angs[h_idx]
    
    v_t = (theta - v0) / (v1 - v0 + 1e-9)
    h_t = (target_phi - h0) / (h1 - h0 + 1e-9)
    
    # 4. Bilinear interpolation / 执行双线性插值运算
    c00, c01 = grid[h_idx-1, v_idx-1], grid[h_idx-1, v_idx]
    c10, c11 = grid[h_idx, v_idx-1], grid[h_idx, v_idx]
    
    res_h0 = c00 * (1 - v_t) + c01 * v_t
    res_h1 = c10 * (1 - v_t) + c11 * v_t
    
    return res_h0 * (1 - h_t) + res_h1 * h_t
