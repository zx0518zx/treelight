import numpy as np
import os

def parse_ies_full(ies_path):
    """
    全量解析IES文件，返回光强矩阵和角度轴
    """
    if not os.path.exists(ies_path):
        return None, f"❌ IES文件不存在：{ies_path}"
    
    try:
        with open(ies_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [l.strip() for l in f if l.strip()]
        
        # 1. 定位 TILT=NONE
        start_idx = -1
        for i, l in enumerate(lines):
            if l.upper().startswith("TILT=NONE"):
                start_idx = i
                break
        if start_idx == -1: return None, "❌ IES文件未找到TILT=NONE标记"

        # 2. 读取头部参数
        header_vals = []
        curr = start_idx + 1
        while len(header_vals) < 10 and curr < len(lines):
            header_vals.extend(lines[curr].split())
            curr += 1
            
        np_cnt = int(float(header_vals[3])) # 垂直角度数
        nr_cnt = int(float(header_vals[4])) # 水平角度数

        # 3. 读取后续所有浮点数
        all_data = []
        for l in lines[curr:]:
            for x in l.split():
                try: all_data.append(float(x))
                except: pass
        
        total_floats_needed = np_cnt + nr_cnt + (np_cnt * nr_cnt)
        if len(all_data) < total_floats_needed:
            return None, "❌ IES数据不完整"
            
        raw_data = all_data[-total_floats_needed:]
        
        vert_angles = np.array(raw_data[:np_cnt])
        horiz_angles = np.array(raw_data[np_cnt : np_cnt+nr_cnt])
        candela_flat = np.array(raw_data[np_cnt+nr_cnt:])
        
        intensity_grid = candela_flat.reshape(nr_cnt, np_cnt)
        
        return {
            'v_angles': vert_angles, 
            'h_angles': horiz_angles,
            'grid': intensity_grid
        }, "✅ IES全量解析成功"
        
    except Exception as e:
        return None, f"❌ IES解析异常: {str(e)}"

def get_interpolated_intensity(ies_data, theta, phi):
    """双线性插值获取光强"""
    v_angs = ies_data['v_angles']
    h_angs = ies_data['h_angles']
    grid = ies_data['grid']
    
    # 1. 角度归一化与映射
    theta = np.clip(theta, v_angs.min(), v_angs.max())
    phi = phi % 360.0
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

    # 2. 寻找索引
    v_idx = np.searchsorted(v_angs, theta)
    h_idx = np.searchsorted(h_angs, target_phi)
    
    v_idx = np.clip(v_idx, 1, len(v_angs)-1)
    h_idx = np.clip(h_idx, 1, len(h_angs)-1)
    
    # 3. 计算权重
    v0, v1 = v_angs[v_idx-1], v_angs[v_idx]
    h0, h1 = h_angs[h_idx-1], h_angs[h_idx]
    
    v_t = (theta - v0) / (v1 - v0 + 1e-9)
    h_t = (target_phi - h0) / (h1 - h0 + 1e-9)
    
    # 4. 插值
    c00 = grid[h_idx-1, v_idx-1]
    c01 = grid[h_idx-1, v_idx]
    c10 = grid[h_idx, v_idx-1]
    c11 = grid[h_idx, v_idx]
    
    res_h0 = c00 * (1 - v_t) + c01 * v_t
    res_h1 = c10 * (1 - v_t) + c11 * v_t
    
    return res_h0 * (1 - h_t) + res_h1 * h_t
