import os
import re
from pathlib import Path
import numpy as np
import pandas as pd

import treelight as tl
from treelight.ies_parser import get_interpolated_intensity
from treelight.light_analysis import compute_ies_angles

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_IES = BASE_DIR / "Philips_Luma_gen2_BGP704_DM11.ies"
SAMPLE_CSV = BASE_DIR / "sample.csv"


def _parse_light_coords(coord_str):
    """Parse one or more '(x, y, z)' luminaire coordinate tuples separated by ';'."""
    pattern = r"\(\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\)"
    matches = re.findall(pattern, str(coord_str))
    return [{"x": float(x), "y": float(y), "z": float(z)} for x, y, z in matches]


def _parse_float_list(val, n_lamps, default=0.0):
    if pd.isna(val) or not str(val).strip():
        return [default] * n_lamps
    nums = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", str(val))]
    if not nums:
        return [default] * n_lamps
    return [nums[i] if i < len(nums) else nums[-1] for i in range(n_lamps)]


def _match_species(raw_name):
    raw_l = str(raw_name).strip().lower()
    for sp in tl.get_available_species():
        if raw_l and raw_l in sp.lower():
            return sp
    return "默认阔叶树 (Default Broadleaf)"


def run_single_tree_demo(ies_data):
    """Demo 1: Single-tree canopy PPFD (Section 3.2 worked example + dual-lamp superposition)."""
    print("\n" + "=" * 68)
    print("1. SINGLE-TREE CANOPY ANALYSIS (Worked Example & Multi-Lamp)")
    print("=" * 68)

    geo = {
        "canopy_type": "Half Ellipsoid",
        "tree_height": 8.5,
        "branch_height": 3.0,
        "crown_width": 5.0,
    }
    env = {
        "precision": 0.05,
        "maintenance_factor": 0.85,
        "light_output_ratio": 0.90,
        "ppfd_factor": tl.get_ppfd_factor("3000K LED"),
        "cosine_correction": True,
    }
    species = _match_species("Cinnamomum camphora")

    # (a) Single luminaire (Section 3.2)
    single_lamp = [{"x": 1.8, "y": 2.5, "z": 9.5, "yaw": 0.0, "tilt": 0.0}]
    res_1 = tl.calculate_canopy_ppfd(geo, single_lamp, ies_data, env)
    grade_1 = tl.grade_light_environment(res_1, species)
    carbon_1 = tl.calculate_implicit_carbon(res_1, species)

    print(f"[Single Lamp] Grid elements: {len(res_1['centers'])} | Area: {grade_1['total_area']:.2f} m²")
    print(f"              Max PPFD: {grade_1['max_ppfd']:.2f} | Avg PPFD: {grade_1['avg_ppfd']:.2f} μmol·m⁻²·s⁻¹")
    print(f"              Annual Carbon Index: {carbon_1['carbon_g']:.2f} g CO2")

    # (b) Dual luminaires with distinct orientation and spectral conversion factor k
    dual_lamps = [
        {"x": 1.8, "y": 2.5, "z": 9.5, "yaw": 0.0, "tilt": 0.0, "ppfd_factor": tl.get_ppfd_factor("3000K LED")},
        {"x": -3.5, "y": 2.5, "z": 9.5, "yaw": 180.0, "tilt": 10.0, "ppfd_factor": tl.get_ppfd_factor("5000K LED")},
    ]
    res_2 = tl.calculate_canopy_ppfd(geo, dual_lamps, ies_data, env)
    grade_2 = tl.grade_light_environment(res_2, species)
    print(f"[Dual Mixed-k] Max PPFD: {grade_2['max_ppfd']:.2f} | Avg PPFD: {grade_2['avg_ppfd']:.2f} μmol·m⁻²·s⁻¹")

    # Uncomment to display interactive 3D canopy heatmap with ground IES footprint:
    # tl.visualize_ppfd_3d(res_1, species_name="Cinnamomum camphora", show=True)


def run_batch_inventory_demo(csv_path, default_ies):
    """Demo 2: Multi-tree batch processing from Table S2 CSV (single, dual, and triple lamps)."""
    print("\n" + "=" * 68)
    print("2. MULTI-TREE BATCH INVENTORY ANALYSIS (sample.csv)")
    print("=" * 68)

    df = pd.read_csv(csv_path)
    default_k = tl.get_ppfd_factor("3000K LED")
    env = {
        "precision": 0.05,
        "maintenance_factor": 0.85,
        "light_output_ratio": 0.90,
        "ppfd_factor": default_k,
        "cosine_correction": True,
    }
    ies_cache = {"": default_ies}
    summary_rows = []

    for _, row in df.iterrows():
        geo = {
            "canopy_type": row["Canopy Type"],
            "tree_height": float(row["Total Tree Height (m)"]),
            "branch_height": float(row["Under-branch Height (m)"]),
            "crown_width": float(row["Crown Diameter (m)"]),
        }
        species = _match_species(row["Tree Species"])
        lights = _parse_light_coords(row["Light Source Coordinates"])
        n_l = len(lights)
        yaws = _parse_float_list(row.get("Light Yaw (°)"), n_l, 0.0)
        tilts = _parse_float_list(row.get("Light Tilt (°)"), n_l, 0.0)

        raw_ies = "" if pd.isna(row.get("IES File")) else str(row.get("IES File")).strip()
        ies_toks = [t.strip() for t in re.split(r"[;,|]", raw_ies)] if raw_ies else []
        raw_k = "" if pd.isna(row.get("PPFD Factor")) else str(row.get("PPFD Factor")).strip()
        k_toks = [t.strip() for t in re.split(r"[;,|]", raw_k)] if raw_k else []

        for i, lp in enumerate(lights):
            lp["yaw"], lp["tilt"] = yaws[i], tilts[i]
            itok = ies_toks[i] if i < len(ies_toks) else (ies_toks[-1] if ies_toks else "")
            if itok:
                fpath = str(BASE_DIR / itok) if not os.path.isabs(itok) else itok
                if fpath not in ies_cache and os.path.isfile(fpath):
                    parsed, msg = tl.parse_ies_full(fpath)
                    if "✅" in msg:
                        ies_cache[fpath] = parsed
                lp["ies_data"] = ies_cache.get(fpath, default_ies)
            ktok = k_toks[i] if i < len(k_toks) else (k_toks[-1] if k_toks else "")
            if ktok:
                try:
                    lp["ppfd_factor"] = float(ktok)
                except ValueError:
                    lp["ppfd_factor"] = float(tl.get_ppfd_factor(ktok))

        phys = tl.calculate_canopy_ppfd(geo, lights, default_ies, env)
        grade = tl.grade_light_environment(phys, species)
        summary_rows.append({
            "Tree ID": row["Tree ID"],
            "Canopy": row["Canopy Type"],
            "Lamps": n_l,
            "Area (m²)": round(grade["total_area"], 2),
            "Max PPFD": round(grade["max_ppfd"], 2),
            "Avg PPFD": round(grade["avg_ppfd"], 2),
        })

    out_df = pd.DataFrame(summary_rows)
    print(f"Processed {len(out_df)} trees successfully. Preview (first 3 + last 3 showcase rows):")
    preview = pd.concat([out_df.head(3), out_df.tail(3)], ignore_index=True)
    print(preview.to_string(index=False))


def run_free_space_point_demo(ies_data):
    """Demo 3: Free-space point receptor analysis (scalar vs. cosine-corrected horizontal PPFD)."""
    print("\n" + "=" * 68)
    print("3. FREE-SPACE POINT RECEPTOR ANALYSIS (Non-Planar vs. Horizontal)")
    print("=" * 68)

    # Target point 2.0 m forward and 4.5 m below Lamp 1 at origin (0, 0, 0)
    target = np.array([2.0, 0.0, -4.5])
    lights = [
        {"x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0, "tilt": 10.0, "k": tl.get_ppfd_factor("4000K LED")},
        {"x": 20.0, "y": 0.0, "z": 0.0, "yaw": 0.0, "tilt": 10.0, "k": tl.get_ppfd_factor("4000K LED")},
    ]

    for use_cosine, label in [(False, "Scalar irradiance (Cosine OFF, e.g., buds / animal eyes)"),
                              (True, "Horizontal planar irradiance (Cosine ON, e.g., flat PPFD sensor)")]:
        total_ppfd = 0.0
        for lp in lights:
            vec = target - np.array([lp["x"], lp["y"], lp["z"]])
            dist_sq = float(np.sum(vec**2))
            u = vec / np.sqrt(dist_sq)
            theta, phi = compute_ies_angles(u, yaw=lp["yaw"], tilt=lp["tilt"])
            intensity = float(get_interpolated_intensity(ies_data, float(theta[0]), float(phi[0])))
            cos_term = max(0.0, -float(u[2])) if use_cosine else 1.0
            total_ppfd += (intensity / dist_sq) * cos_term * lp["k"]
        print(f"  {label}:\n    -> Total PPFD = {total_ppfd:.4f} μmol·m⁻²·s⁻¹")


def main():
    ies_data, msg = tl.parse_ies_full(str(DEFAULT_IES))
    if not ies_data:
        raise FileNotFoundError(f"Could not load {DEFAULT_IES}: {msg}")

    run_single_tree_demo(ies_data)
    run_batch_inventory_demo(SAMPLE_CSV, ies_data)
    run_free_space_point_demo(ies_data)


if __name__ == "__main__":
    main()
