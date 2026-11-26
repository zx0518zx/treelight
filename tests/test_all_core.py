import os
import tempfile
import numpy as np
import pytest
import matplotlib

matplotlib.use("Agg")

import treelight as tl
from treelight.geometry import generate_fibonacci_mesh
from treelight.ies_parser import get_interpolated_intensity
from treelight.light_analysis import compute_ies_angles, visualize_ppfd_3d


def test_config_register_delete_and_validation():
    """Verify species/light registration, deletion, built-in protection, and validation."""
    sp_name = "_pytest_tmp_species"
    lt_name = "_pytest_tmp_led"

    try:
        tl.register_species(sp_name, alpha=0.045, rd=0.8, lcp=25.0, lsp=1200.0)
        assert tl.get_species_params(sp_name)["alpha"] == pytest.approx(0.045)
        assert sp_name in tl.get_available_species()

        tl.register_light(lt_name, factor=0.016)
        assert tl.get_ppfd_factor(lt_name) == pytest.approx(0.016)
        assert lt_name in tl.get_available_lights()

        # Built-in entries must be protected from deletion
        with pytest.raises(ValueError):
            tl.delete_species("香樟 (Cinnamomum camphora)")
        with pytest.raises(ValueError):
            tl.delete_light("4000K LED")

        # Invalid queries and negative parameters must raise ValueError
        with pytest.raises(ValueError):
            tl.get_species_params("Unknown_Tree_XYZ")
        with pytest.raises(ValueError):
            tl.get_ppfd_factor("Unknown_Light_XYZ")
        with pytest.raises(ValueError):
            tl.register_species("Bad_Sp", alpha=-0.1, rd=0.5, lcp=10.0)
        with pytest.raises(ValueError):
            tl.register_light("Bad_Light", factor=0.0)

        # Clean deletion of custom entries
        tl.delete_species(sp_name)
        assert sp_name not in tl.get_available_species()
        tl.delete_light(lt_name)
        assert lt_name not in tl.get_available_lights()
    finally:
        if sp_name in tl.get_available_species():
            tl.delete_species(sp_name)
        if lt_name in tl.get_available_lights():
            tl.delete_light(lt_name)


def test_geometry_all_shapes_and_nan():
    """Cover semi-ellipsoid, cone, cylinder canopy primitives and NaN interception."""
    for shape in ("半椭球体/Half Ellipsoid", "圆锥体/Cone", "圆柱体/Cylinder"):
        centers, normals, areas = generate_fibonacci_mesh(shape, 2.5, 5.5, 4.0, 0.5)
        assert len(centers) > 0
        assert centers.shape == normals.shape
        assert len(areas) == len(centers)
        assert np.all(areas > 0)

    c_nan, n_nan, a_nan = generate_fibonacci_mesh("Cylinder", np.nan, 5.0, 4.0, 0.1)
    assert len(c_nan) == 0 and len(n_nan) == 0 and len(a_nan) == 0


def test_ies_parser_multiplier_errors_and_symmetry():
    """Verify IES LM-63 candela multiplier, error handling, and C-plane symmetry interpolation."""
    valid_ies = """IESNA:LM-63-2002
[TEST] dummy multiplier 2.5
TILT=NONE
1 1000 2.5 3 4 1 2 0.3 0.3 0
1.0 1.0 1.0
0 45 90
0 90 180 270
100 80 20
100 80 20
100 80 20
100 80 20
"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ies", encoding="utf-8") as f:
        f.write(valid_ies)
        ies_path = f.name

    try:
        data, msg = tl.parse_ies_full(ies_path)
        assert data is not None and "✅" in msg
        assert data["multiplier"] == pytest.approx(2.5)
        assert data["grid"][0, 0] == pytest.approx(250.0)
        assert get_interpolated_intensity(data, 0.0, 0.0) == pytest.approx(250.0)
    finally:
        os.remove(ies_path)

    # Test 0/90/180 symmetry branches in get_interpolated_intensity
    for h_angs in (np.array([0.0]), np.array([0.0, 45.0, 90.0]), np.array([0.0, 90.0, 180.0])):
        sym_ies = {
            "v_angles": np.array([0.0, 45.0, 90.0]),
            "h_angles": h_angs,
            "grid": np.full((len(h_angs), 3), 500.0),
        }
        for phi in (0.0, 45.0, 135.0, 225.0, 315.0):
            if len(h_angs) > 1:
                assert get_interpolated_intensity(sym_ies, 30.0, phi) == pytest.approx(500.0)

    # Error handling: non-existent file and missing TILT=NONE
    assert tl.parse_ies_full("non_existent_dummy.ies")[0] is None
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ies", encoding="utf-8") as f:
        f.write("IESNA:LM-63-2002\nINVALID_HEADER\n")
        bad_path = f.name
    try:
        assert tl.parse_ies_full(bad_path)[0] is None
    finally:
        os.remove(bad_path)


def test_multi_lamp_mixed_k_yaw_tilt_and_cosine():
    """Verify exact linear superposition across 3 lamps with distinct yaw, tilt, IES, and k, plus cosine toggle."""
    ies_a = {
        "v_angles": np.array([0.0, 45.0, 90.0]),
        "h_angles": np.array([0.0, 90.0, 180.0, 270.0, 360.0]),
        "grid": np.full((5, 3), 1000.0),
    }
    ies_b = {
        "v_angles": np.array([0.0, 45.0, 90.0]),
        "h_angles": np.array([0.0, 90.0, 180.0, 270.0, 360.0]),
        "grid": np.full((5, 3), 600.0),
    }
    geo = {"canopy_type": "Half Ellipsoid", "tree_height": 8.0, "branch_height": 2.5, "crown_width": 4.0}
    env = {
        "precision": 0.5,
        "maintenance_factor": 0.9,
        "light_output_ratio": 0.9,
        "ppfd_factor": 0.0154,
        "cosine_correction": True,
    }

    l1 = {"x": 2.0, "y": 2.0, "z": 9.0, "yaw": 0.0, "tilt": 0.0, "ies_data": ies_a, "ppfd_factor": 0.0143}
    l2 = {"x": -2.5, "y": 2.0, "z": 9.5, "yaw": 90.0, "tilt": 15.0, "ies_data": ies_b, "ppfd_factor": 0.0170}
    l3 = {"x": 0.0, "y": -3.0, "z": 8.5, "yaw": 180.0, "tilt": 10.0}  # falls back to default ies_a and global k

    r1 = tl.calculate_canopy_ppfd(geo, [l1], ies_a, env)["ppfd_raw"]
    r2 = tl.calculate_canopy_ppfd(geo, [l2], ies_a, env)["ppfd_raw"]
    r3 = tl.calculate_canopy_ppfd(geo, [l3], ies_a, env)["ppfd_raw"]
    r123 = tl.calculate_canopy_ppfd(geo, [l1, l2, l3], ies_a, env)["ppfd_raw"]

    assert np.allclose(r123, r1 + r2 + r3, atol=1e-12)

    # Cosine OFF (scalar irradiance) must be >= Cosine ON on every canopy element
    env_scalar = dict(env, cosine_correction=False)
    r_scalar = tl.calculate_canopy_ppfd(geo, [l1], ies_a, env_scalar)["ppfd_raw"]
    assert np.all(r_scalar + 1e-12 >= r1)
    assert np.max(r_scalar) > np.max(r1)

    # Direct check on compute_ies_angles nadir vector
    th, ph = compute_ies_angles(np.array([[0.0, 0.0, -1.0]]), yaw=0.0, tilt=0.0)
    assert th[0] == pytest.approx(0.0, abs=1e-6)


def test_ecology_and_3d_visualization():
    """Verify ecological grading, implicit carbon (lit & dark), and silent 3D heatmap rendering."""
    dummy_ies = {
        "v_angles": np.array([0.0, 45.0, 90.0]),
        "h_angles": np.array([0.0, 90.0, 180.0, 270.0, 360.0]),
        "grid": np.full((5, 3), 1000.0),
    }
    geo = {"canopy_type": "Half Ellipsoid", "tree_height": 8.0, "branch_height": 2.5, "crown_width": 4.0}
    light_pos = [{"x": 1.8, "y": 2.5, "z": 9.5, "yaw": 0.0, "tilt": 0.0}]
    env = {"precision": 0.5, "maintenance_factor": 0.85, "light_output_ratio": 0.9, "ppfd_factor": 0.0154}
    species = "香樟 (Cinnamomum camphora)"

    phys = tl.calculate_canopy_ppfd(geo, light_pos, dummy_ies, env)
    grade = tl.grade_light_environment(phys, species)
    carbon = tl.calculate_implicit_carbon(phys, species, hours=4380)
    assert grade["total_area"] > 0
    assert carbon["carbon_g"] > 0 and 0 < carbon["valid_area_ratio"] <= 1.0

    # Zero-light edge case
    dark_phys = dict(phys, ppfd_raw=np.zeros_like(phys["ppfd_raw"]))
    dark_carbon = tl.calculate_implicit_carbon(dark_phys, species)
    assert dark_carbon["carbon_g"] == 0.0 and dark_carbon["valid_area_ratio"] == 0.0

    # Silent 3D visualization with ground IES footprint
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
        plot_path = f.name
    try:
        visualize_ppfd_3d(phys, species_name="Cinnamomum camphora", show=False, save_path=plot_path)
        assert os.path.exists(plot_path) and os.path.getsize(plot_path) > 0
    finally:
        if os.path.exists(plot_path):
            os.remove(plot_path)
