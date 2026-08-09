# -*- coding: utf-8 -*-
import os
import tempfile
import numpy as np
import pytest
import treelight as tl
from treelight.geometry import generate_fibonacci_mesh

def test_config_operations():
    """测试底层数据库命令及持久化"""
    tl.register_species("Test_Species", alpha=0.045, rd=0.8, lcp=25.0)
    params = tl.get_species_params("Test_Species")
    assert params["alpha"] == 0.045
    assert params["Rd"] == 0.8
    
    tl.register_light("Test_LED", factor=0.016)
    assert tl.get_ppfd_factor("Test_LED") == 0.016

    with pytest.raises(ValueError):
        tl.get_species_params("Unknown_Tree")

def test_mesh_generation_and_tolerance():
    """测试 3D 几何网格离散化与 NaN 容错"""
    centers, normals, areas = generate_fibonacci_mesh("半椭球体/Half Ellipsoid", 8.0, 2.5, 4.0, 0.1)
    assert len(centers) > 0
    assert len(centers) == len(normals)

    centers_nan, normals_nan, areas_nan = generate_fibonacci_mesh("圆柱体/Cylinder", np.nan, 2.5, 4.0, 0.1)
    assert len(centers_nan) == 0

def test_ies_parser_robustness():
    """测试 IES 解析器对异常文件的健壮性"""
    data, msg = tl.parse_ies_full("fake_path_non_existent.ies")
    assert "❌" in msg or data is None

def test_physics_and_ecology_engine():
    """测试 3D 空间光场辐射模拟与隐性碳汇量化引擎"""
    dummy_ies_data = {
        'v_angles': np.array([0, 45, 90]),
        'h_angles': np.array([0, 90, 180, 270]),
        'candela_values': np.ones((4, 3)) * 1000
    }
    
    geo_params = {"canopy_type": "半椭球体/Half Ellipsoid", "tree_height": 8.0, "branch_height": 2.5, "crown_width": 4.0}
    light_pos = [{"x": 1.8, "y": 2.5, "z": 9.5}]
    env_params = {"precision": 0.5, "maintenance_factor": 0.85, "light_output_ratio": 0.9, "ppfd_factor": 0.015}

    physics_result = tl.calculate_canopy_ppfd(geo_params, light_pos, dummy_ies_data, env_params)
    assert 'centers' in physics_result
    assert len(physics_result['centers']) > 0

    tl.register_species("Mock_Species", alpha=0.05, rd=1.0, lcp=20.0)
    grade = tl.grade_light_environment(physics_result, "Mock_Species")
    carbon = tl.calculate_implicit_carbon(physics_result, "Mock_Species", hours=4380)

    assert 'total_area' in grade
    assert 'max_ppfd' in grade
    assert 'carbon_g' in carbon
