# treelight (v1.1.0)

### Quantifying Three-Dimensional Artificial Light at Night (ALAN) Exposure in Urban Tree Canopies
### 城市树木冠层三维夜间人造光（ALAN）暴露量化框架

[[https://img.shields.io/badge/python-3.8%2B-blue.svg]](https://www.python.org/)
[[https://img.shields.io/badge/License-MIT-yellow.svg]](https://opensource.org/licenses/MIT)
[[https://img.shields.io/badge/Field-Urban%20Ecology%20%7C%20Ecophysiology-green.svg]]()

---

## Overview (项目概述)

### English
`treelight` is an open-source Python library and standalone graphical user interface (GUI) for quantifying three-dimensional artificial light at night (ALAN) exposure across urban tree canopies.

By integrating standardized Illuminating Engineering Society (`IESNA LM-63`) photometric files with routinely collected urban forestry metrics (tree height, crown-base height, crown diameter, and relative luminaire coordinates), `treelight` bridges the gap between engineering illuminance (**lux**) and plant-relevant photosynthetic photon flux density (**PPFD**, $\mu\text{mol}\cdot\text{m}^{-2}\cdot\text{s}^{-1}$).

* **Multi-Scenario Field Evaluation (No Empirical Rescaling):** Evaluated across 351 free-space locations spanning three typical urban road lighting scenarios up to 7.0 m in height—conventional single-luminaire roadway lighting ($R^2 = 0.698$, $\text{RMSE} = 0.340$), directional floodlighting ($R^2 = 0.816$, $\text{RMSE} = 2.113$), and overlapping dual-luminaire roadway lighting ($R^2 = 0.849$, $\text{RMSE} = 2.267$).
* **Flexible Multi-Luminaire & Receptor Modelling:** Supports linear superposition of arbitrary numbers of luminaires (with per-lamp horizontal yaw, upward tilt, individual IES files, and independent spectral conversion factors $k$), an optional cosine-correction toggle for non-planar receptors, and free-space point receptor analysis.
* **Scalable & Reproducible:** Uses a tree-centred local coordinate system for rapid city-scale batch processing, and exports standalone executable Python scripts directly from the GUI.

### 中文
`treelight` 是一个开源 Python 计算库与独立图形用户界面（GUI），用于定量评估城市树木冠层接收的三维夜间人造光（ALAN）暴露水平。

通过融合照明工程标准的 `IESNA LM-63` 配光曲线文件与常规城市林业调查指标（树高、枝下高、冠幅及灯具相对坐标），`treelight` 弥合了工程照度（**lux**）与植物生理学光合光量子通量密度（**PPFD**，$\mu\text{mol}\cdot\text{m}^{-2}\cdot\text{s}^{-1}$）之间的指标错配。

* **多场景野外验证（无经验缩放）：** 在覆盖至 7.0 m 冠层高度的三类典型城市照明场景（共 351 个测点）中完成验证——常规单灯道路照明（$R^2 = 0.698$，$\text{RMSE} = 0.340$）、定向投光照明（$R^2 = 0.816$，$\text{RMSE} = 2.113$）与双灯叠加道路照明（$R^2 = 0.849$，$\text{RMSE} = 2.267$）。
* **灵活的多灯叠加与受体建模：** 支持任意数量灯具的线性叠加（每盏灯可独立配置水平偏航角 Yaw、仰角 Tilt、独立 IES 文件及独立光谱换算系数 $k$），提供面向非平面受体的余弦校正开关以及自由空间单点受体分析。
* **高通量且可复现：** 采用以目标树为中心的局部坐标系实现快速批量处理，并支持在 GUI 中一键导出可独立运行的 Python 复现脚本。

---

## Key Features (核心功能)

1. **Photometric Parsing (`src/treelight/ies_parser.py`):** Parses standard `IESNA LM-63` files (automatically applying the candela multiplier) and performs bilinear interpolation over C-plane intensity matrices.
2. **3D Parametric Canopy Mesh (`src/treelight/geometry.py`):** Discretizes semi-ellipsoid, cone, and cylinder crown primitives into area-weighted Fibonacci surface elements.
3. **3D Light Field Engine & Visualization (`src/treelight/light_analysis.py`):** Computes inverse-square attenuation with optional Lambert cosine projection (`cosine_correction=True/False`), multi-luminaire superposition with per-lamp `yaw`, `tilt`, `ies_data`, and `ppfd_factor`, and renders dual-viewport 3D PPFD heatmaps with ground-plane ($z = 0$) IES irradiance footprints.
4. **Ecological Grading & Carbon Metrics (`src/treelight/ecology.py`, `src/treelight/config.py`):** Computes canopy area across exposure intervals relative to species-specific light compensation points (LCP), estimates annual implicit carbon fixation, and supports local persistence for custom species and spectral conversion factors (`register_species`, `delete_species`, `register_light`, `delete_light`).
5. **Bilingual Desktop GUI (`GUI/treelight_GUI.py`):** Three-tab English/Chinese Tkinter interface covering **Single Tree Analysis**, **Multi-Tree Batch Processing** (Excel/CSV with optional per-tree or semicolon-separated multi-lamp `Light Yaw (°)`, `Light Tilt (°)`, `IES File`, and `PPFD Factor` columns), and **Free-Space Point Analysis (Receptor)**, with one-click reproducible `.py` script export.

---

## Repository Structure (仓库结构)

```text
treelight/
├── GUI/
│   └── treelight_GUI.py                                # Standalone bilingual desktop GUI (v1.1)
├── example/
│   ├── demo.py                                         # Consolidated demo (single-tree, batch, free-space point)
│   ├── sample.csv                                      # Table S2 batch inventory (18 C. camphora + 3 multi-lamp demos)
│   ├── Philips_Luma_gen2_BGP704_DM11.ies               # Example DM11 photometric file
│   └── BGP292 LED120-4S_740 II DM11 STDE NA 48_.ies    # Secondary IES file for multi-lamp demo
├── src/
│   └── treelight/
│       ├── __init__.py                                 # Package initialization & public API (v1.1.0)
│       ├── config.py                                   # Species & light-source database with local persistence
│       ├── ies_parser.py                               # IESNA LM-63 parser (with candela multiplier) & interpolator
│       ├── geometry.py                                 # Parametric Fibonacci canopy mesh generator
│       ├── light_analysis.py                           # 3D multi-luminaire light field engine & 3D heatmap plotting
│       └── ecology.py                                  # Ecological grading & implicit carbon metrics
├── tests/
│   └── test_all_core.py                                # Automated pytest suite (93% coverage across core modules)
├── validation/
│   ├── site1_single_roadway/
│   │   ├── site1_validation_data.xlsx                  # Site 1 measurements & metadata (n = 126)
│   │   └── BGP293 LED240-4S_740 I DM11 STD NA 48_60.ies
│   ├── site2_directional_floodlight/
│   │   ├── site2_validation_data.xlsx                  # Site 2 measurements & metadata (n = 78)
│   │   └── Signify-BVP561-LED40-740-20W-WLP-AMB.ies
│   ├── site3_overlapping_roadway/
│   │   ├── site3_validation_data.xlsx                  # Site 3 measurements & metadata (n = 147)
│   │   └── BGP292 LED120-4S_740 II DM11 STDE NA 48_.ies
│   └── Reproduce Validation.py                         # Reproduces Figure 4 & Table S3 validation metrics
├── .gitignore
├── MIT License
├── pyproject.toml
└── README.md
```

---

## Installation (安装指南)

Navigate to the repository root and install locally via `pip` (Python 3.8+ recommended inside a clean `venv` or Conda environment):

```bash
pip install .
```

**Dependencies:** `numpy`, `pandas`, `matplotlib`, `openpyxl` (the GUI uses Python's built-in `tkinter`).

---

## Usage & Reproducibility (使用与复现指南)

### 1. Run Consolidated Examples (运行示例脚本)
Runs the Section 3.2 single-tree worked example, Section 3.3 / Table S2 batch inventory (including dual- and triple-lamp mixed-$k$ cases), and free-space point receptor analysis:

```bash
python example/demo.py
```

### 2. Launch the Desktop GUI (启动图形用户界面)
Launch directly from source (or use the standalone Windows `.exe` package from Releases):

```bash
python GUI/treelight_GUI.py
```

### 3. Reproduce Field Validation & Figure 4 (复现三站点野外验证与图 4)
Automatically loads the three site datasets and proxy IES files via relative paths, prints all validation statistics reported in Table S3, and exports the 600 DPI composite Figure 4:

```bash
python "validation/Reproduce Validation.py"
```

### 4. Run Automated Unit Tests (运行单元测试)
Verified on Python 3.10 with `pytest` (5/5 test suites passing, 93% coverage across `src/treelight/`):

```bash
pytest tests --cov=treelight --cov-report=term-missing
```

---

## Quick Start — Python API (Python 接口快速入门)

```python
import treelight as tl

# 1. Manage custom species and spectral conversion factors (optional)
tl.register_species(name="My_Tree", alpha=0.06, rd=1.2, lcp=25.0, lsp=1500)
tl.register_light(name="My_LED", factor=0.0154)
k_4000k = tl.get_ppfd_factor("4000K LED")

# 2. Parse IES photometric file
ies_data, msg = tl.parse_ies_full("example/Philips_Luma_gen2_BGP704_DM11.ies")

# 3. Configure tree geometry and luminaires (supports arbitrary N lamps with per-lamp yaw, tilt, ies_data, ppfd_factor)
geo_params = {
    "canopy_type": "Half Ellipsoid",
    "tree_height": 8.5,
    "branch_height": 3.0,
    "crown_width": 5.0,
}
light_pos_list = [
    {"x": 1.8, "y": 2.5, "z": 9.5, "yaw": 0.0, "tilt": 0.0, "ppfd_factor": k_4000k},
    # Optional additional luminaires for multi-source superposition:
    # {"x": -3.5, "y": 2.5, "z": 9.5, "yaw": 180.0, "tilt": 10.0, "ppfd_factor": tl.get_ppfd_factor("5000K LED")},
]
env_params = {
    "precision": 0.05,
    "maintenance_factor": 0.85,
    "light_output_ratio": 0.90,
    "ppfd_factor": k_4000k,
    "cosine_correction": True,  # Set False for scalar irradiance on non-planar receptors
}

# 4. Run 3D canopy PPFD simulation, ecological grading, carbon metrics, and 3D visualization
physics_res = tl.calculate_canopy_ppfd(geo_params, light_pos_list, ies_data, env_params)
grade_stats = tl.grade_light_environment(physics_res, species_name="香樟 (Cinnamomum camphora)")
carbon_stats = tl.calculate_implicit_carbon(physics_res, species_name="香樟 (Cinnamomum camphora)")
# tl.visualize_ppfd_3d(physics_res, species_name="Cinnamomum camphora", show=True)
```

---

## Scope & Limitations (适用范围与局限性)

* **Outer-Canopy Surface Representation:** Models direct incident radiation on a parametric outer crown envelope (semi-ellipsoid, cone, or cylinder) without internal foliage attenuation, self-shading, or inter-tree occlusion.
* **Direct-Source Light Field:** Excludes diffuse urban skyglow and secondary reflections from building facades or pavements.
* **Spectral Extensions:** Custom conversion coefficients $k$ can be supplied via `register_light()` for band-limited or action-spectrum-weighted metrics; spectral ratios (e.g., red-to-far-red) should be computed by summing multi-luminaire contributions within each band separately before forming the ratio.

---

## License (开源协议)

This project is licensed under the MIT License (see `MIT License`).
