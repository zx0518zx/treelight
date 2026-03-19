import numpy as np

def generate_fibonacci_mesh(canopy_type, bh, ch, cw, target_area=0.01):
    """
    生成均匀的斐波那契点云及其法向量
    """
    radius = cw / 2.0
    centers = []
    normals = []
    areas = []
    
    # 辅助函数
    def fib_sphere(n, r_scale, z_scale, z_offset, cap_mode=False):
        pts = []
        nms = []
        phi = (np.sqrt(5) - 1) / 2
        for i in range(n):
            y_s = 1 - (i / float(n - 1)) * 2
            if cap_mode: y_s = 1 - (i / float(n - 1))
            
            radius_at_y = np.sqrt(1 - y_s * y_s)
            theta = 2 * np.pi * i * phi
            
            x = r_scale * radius_at_y * np.cos(theta)
            y = r_scale * radius_at_y * np.sin(theta)
            z = z_scale * y_s + z_offset
            pts.append([x, y, z])
            
            if cap_mode:
                nx, ny, nz = x/(r_scale**2), y/(r_scale**2), (z-z_offset)/(z_scale**2)
                l = np.sqrt(nx*nx + ny*ny + nz*nz)
                nms.append([nx/l, ny/l, nz/l])
            else:
                nms.append([0,0,1])
        return pts, nms

    def fib_disk(n, z_pos, normal_dir):
        pts = []
        nms = []
        phi = (np.sqrt(5) - 1) / 2
        for i in range(n):
            r = radius * np.sqrt(i / (n - 0.5))
            theta = 2 * np.pi * i * phi
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            pts.append([x, y, z_pos])
            nms.append(normal_dir)
        return pts, nms

    # 几何生成逻辑
    if canopy_type == "半椭球体":
        p = 1.6075
        area_ellip = 2 * np.pi * ((radius**p * radius**p + 2 * radius**p * ch**p) / 3)**(1/p)
        area_bottom = np.pi * radius**2
        
        n_side = int(area_ellip / target_area)
        n_bottom = int(area_bottom / target_area)
        
        s_pts, s_nms = fib_sphere(n_side, radius, ch, bh, cap_mode=True)
        b_pts, b_nms = fib_disk(n_bottom, bh, [0, 0, -1])
        
        centers = s_pts + b_pts
        normals = s_nms + b_nms
        areas = [area_ellip/n_side]*len(s_pts) + [area_bottom/n_bottom]*len(b_pts)

    elif canopy_type == "圆锥体":
        slant = np.sqrt(radius**2 + ch**2)
        area_side = np.pi * radius * slant
        area_bottom = np.pi * radius**2
        
        n_side = int(area_side / target_area)
        n_bottom = int(area_bottom / target_area)
        
        s_pts = []
        s_nms = []
        phi = (np.sqrt(5) - 1) / 2
        sin_alpha = radius / slant
        cos_alpha = ch / slant
        
        for i in range(n_side):
            ratio = np.sqrt(i / (n_side - 0.5))
            cur_r = radius * (1 - ratio)
            cur_z = bh + ch * ratio
            theta = 2 * np.pi * i * phi
            x = cur_r * np.cos(theta)
            y = cur_r * np.sin(theta)
            s_pts.append([x, y, cur_z])
            
            nx = cos_alpha * np.cos(theta)
            ny = cos_alpha * np.sin(theta)
            nz = sin_alpha 
            s_nms.append([nx, ny, nz])
            
        b_pts, b_nms = fib_disk(n_bottom, bh, [0, 0, -1])
        centers = s_pts + b_pts
        normals = s_nms + b_nms
        areas = [area_side/n_side]*len(s_pts) + [area_bottom/n_bottom]*len(b_pts)

    elif canopy_type == "圆柱体":
        area_side = 2 * np.pi * radius * ch
        area_cap = np.pi * radius**2
        
        n_side = int(area_side / target_area)
        n_cap = int(area_cap / target_area)
        
        s_pts = []
        s_nms = []
        phi = (np.sqrt(5) - 1) / 2
        for i in range(n_side):
            z = bh + ch * (i / (n_side - 1))
            theta = 2 * np.pi * i * phi
            x = radius * np.cos(theta)
            y = radius * np.sin(theta)
            s_pts.append([x, y, z])
            s_nms.append([np.cos(theta), np.sin(theta), 0])
            
        t_pts, t_nms = fib_disk(n_cap, bh + ch, [0, 0, 1])
        b_pts, b_nms = fib_disk(n_cap, bh, [0, 0, -1])
        
        centers = s_pts + t_pts + b_pts
        normals = s_nms + t_nms + b_nms
        areas = [area_side/n_side]*len(s_pts) + [area_cap/n_cap]*len(t_pts) + [area_cap/n_cap]*len(b_pts)

    return np.array(centers), np.array(normals), np.array(areas)