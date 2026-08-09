# -*- coding: utf-8 -*-
import os
import tempfile
import numpy as np
import pytest
import matplotlib
# 强制 Matplotlib 在后台静默绘图，绝不弹出窗口卡死测试流水线
# Force Matplotlib to plot silently in the background to prevent blocking the testing pipeline
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

import treelight as tl
from treelight.geometry import generate_fibonacci_mesh
from treelight.light_analysis import visualize_ppfd_3d

def test_config_operations():
    """
    测试底层数据库命令及异常拦截
    Test underlying database commands and exception handling
    """
    # 注册并验证新的树种参数 / Register and verify new species parameters
    tl.register_species("Test_Species", alpha=0.045, rd=0.8, lcp=25.0)
    assert tl.get_species_params("Test_Species")["alpha"] == 0.045
    
    # 注册并验证光源转换因子 / Register and verify light source conversion factor
    tl.register_light("Test_LED", factor=0.016)
    assert tl.get_ppfd_factor("Test_LED") == 0.016
    
    # 验证异常拦截：查询未知树种应抛出 ValueError 
    # Verify exception handling: querying unknown species should raise ValueError
    with pytest.raises(ValueError):
        tl.get_species_params("Unknown_Tree")

def test_geometry_all_shapes():
    """
    全面覆盖 3 种树冠几何体与 NaN 容错
    Comprehensively cover 3 canopy geometries and NaN tolerance
    """
    # 测试三种冠形的正常离散化 / Test normal discretization of three canopy shapes
    c1, _, _ = generate_fibonacci_mesh("半椭球体/Half Ellipsoid", 8.0, 2.5, 4.0, 0.5)
    c2, _, _ = generate_fibonacci_mesh("圆柱体/Cylinder", 8.0, 2.5, 4.0, 0.5)
    c3, _, _ = generate_fibonacci_mesh("圆锥体/Cone", 8.0, 2.5, 4.0, 0.5)
    assert len(c1) > 0 and len(c2) > 0 and len(c3) > 0

    # 测试脏数据 (NaN) 拦截能力 / Test dirty data (NaN) interception capability
    c_nan, _, _ = generate_fibonacci_mesh("圆柱体/Cylinder", np.nan, 2.5, 4.0, 0.1)
    assert len(c_nan) == 0

def test_ies_parser_full():
    """
    构造合法极简 IES 文件，全面覆盖解析逻辑
    Construct a valid minimalist IES file to fully cover the parsing logic
    """
    # 模拟一个真实的最小化 IES 文本结构 / Simulate a real minimized IES text structure
    valid_ies_content = """IESNA:LM-63-2002
[TEST] dummy
TILT=NONE
1 1000 1 3 4 1 2 0.3 0.3 0
1.0 1.0 1.0
0 45 90
0 90 180 270
100 100 100
100 100 100
100 100 100
100 100 100
"""
    # 创建临时文件进行无痕测试 / Create a temporary file for traceless testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ies') as f:
        f.write(valid_ies_content)
        temp_name = f.name
        
    try:
        data, msg = tl.parse_ies_full(temp_name)
        assert data is not None
        assert 'grid' in data
    finally:
        os.remove(temp_name) # 测试后自动清理 / Auto-cleanup after testing
        
    # 测试空文件错误拦截 / Test non-existent file error interception
    data_fail, _ = tl.parse_ies_full("fake_not_exist.ies")
    assert data_fail is None

def test_physics_ecology_and_visualization():
    """
    测试物理引擎、碳汇计算，并在后台静默跑通 3D 绘图代码
    Test the physics engine, carbon sink calculation, and silently execute 3D plotting code
    """
    # 构造含 grid 的完整虚拟配光矩阵 / Construct a complete dummy photometric matrix including 'grid'
    dummy_ies_data = {
        'v_angles': np.array([0, 45, 90]),
        'h_angles': np.array([0, 90, 180, 270]),
        'candela_values': np.ones((4, 3)) * 1000,
        'grid': np.ones((4, 3)) * 1000
    }
    
    geo_params = {"canopy_type": "半椭球体/Half Ellipsoid", "tree_height": 8.0, "branch_height": 2.5, "crown_width": 4.0}
    light_pos = [{"x": 1.8, "y": 2.5, "z": 9.5}]
    env_params = {"precision": 0.5, "maintenance_factor": 0.85, "light_output_ratio": 0.9, "ppfd_factor": 0.015}

    # 测试物理辐射计算 / Test physical radiation computation
    physics_result = tl.calculate_canopy_ppfd(geo_params, light_pos, dummy_ies_data, env_params)
    assert len(physics_result['centers']) > 0

    # 测试生态分级与隐性碳汇 / Test ecological grading and implicit carbon sink
    tl.register_species("Mock_Species", alpha=0.05, rd=1.0, lcp=20.0)
    grade = tl.grade_light_environment(physics_result, "Mock_Species")
    carbon = tl.calculate_implicit_carbon(physics_result, "Mock_Species", hours=4380)
    assert grade['total_area'] > 0

    # 测试 3D 绘图功能 (覆盖绘图代码且不弹窗) / Test 3D plotting (covers plotting code without pop-ups)
    visualize_ppfd_3d(physics_result, geo_params, light_pos, save_path="temp_test_plot.png")
    assert os.path.exists("temp_test_plot.png")
    os.remove("temp_test_plot.png")
