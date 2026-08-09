# treelight (v1.0.0)

### 3D Parametric Radiative Simulation Framework for Tree Lighting Analysis & Implicit Carbon Sink Quantification
### 树木光照分析与隐性碳汇量化的3D参数化辐射模拟框架

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Field](https://img.shields.io/badge/Field-Urban%20Ecology%20%7C%20Ecophysiology-green.svg)]()

---

## 🌟 Overview (项目概述)

### [English]
`treelight` is an open-source, automated Python library and 3D parametric modeling framework designed to quantify the artificial light at night (ALAN) received by urban tree canopies. 

In urban ecology, a critical methodological bottleneck exists: the metric mismatch between human-centric engineering illuminance (**Lux**) and plant-relevant Photosynthetic Photon Flux Density (**PPFD**), alongside the logistical difficulty of high-altitude canopy measurements. `treelight` bridges this gap by integrating universally available Illuminating Engineering Society (IES) photometric data with standard forestry inventory metrics (e.g., tree height, crown spread). By coupling the inverse-square law with spectrum-specific radiometric integration, it directly translates engineering light fields into highly resolved 3D PPFD spatial matrices.

* **High Predictive Accuracy:** In situ field validations confirm that the core simulation engine captures 3D light gradients with high congruence (**$R^2 = 0.791$**, **$\text{RMSE} = 0.283\ \mu\text{mol}\cdot\text{m}^{-2}\cdot\text{s}^{-1}$**).
* **High Computational Efficiency:** Features an object-centric coordinate system that isolates individual tree light calculations, completely avoiding computational redundancy caused by global cross-coupling in large-scale urban road networks.

### [中文]
`treelight` 是一个开源、自动化的 Python 科学计算库与 3D 参数化建模框架，专门用于定量评估城市树木冠层接收的夜间人造光（ALAN）辐射剂量。

在城市生态学研究中，长期存在一个核心方法学瓶颈：即以人眼视觉为核心的工程照度（**Lux**）与植物生理学核心指标——光合有效光子通量密度（**PPFD**）之间的单位错配，以及高空树冠实地测量的极高操作难度。`treelight` 通过将照明工程中通用的 IES 配光曲线文件与基础林业调查指标（如树高、冠幅、枝下高）创新性融合，架起了两者之间的桥梁。框架基于光学平方反比定律和光谱能量积分，实现了从工程光场数据到高空间分辨率 3D PPFD 矩阵的自动转化。

* **高精度预测：** 现场实地物理原位验证表明，核心模拟引擎能够高精度捕捉复杂三维空间中的光强分布梯度（**$R^2 = 0.791$**，**$\text{RMSE} = 0.283\ \mu\text{mol}\cdot\text{m}^{-2}\cdot\text{s}^{-1}$**）。
* **高计算效率：** 引入了以单一树木为中心的局部坐标系，将每棵树的光照计算完全独立化，彻底避免了城市尺度大样本批处理中多灯多树全局交叉耦合带来的巨大计算冗余。

---

## 🛠️ Key Features (核心功能)

### [English]
1.  **Photometric Parsing Module (`ies_parser.py`):** Automatically ingests standard `IESNA LM-63` files, extracting the 3D luminous intensity distribution web with standard road lighting orientation adjustments.
2.  **3D Parametric Mesh Generation (`geometry.py`):** Discretizes tree canopies into adaptive, high-density vertex meshes using Fibonacci point clouds based on geometric primitives (Semi-ellipsoid, Cone, Cylinder).
3.  **Light Field Radiative Engine (`light_analysis.py`):** Implements the fundamental optical inverse-square law and executes bilinear interpolation over the photometric grid to calculate localized incident quantum energy.
4.  **Ecological Assessment & Implicit Carbon Sink Module (`ecology.py`):** Quantifies light environment grades (e.g., area distributions above the Light Compensation Point) and integrates the incremental photosynthetic fixations to calculate the annual "implicit carbon sink" brought by artificial lighting.
5.  **Dual Bilingual GUI Workflow:** Features a standalone, cross-platform Graphical User Interface supporting real-time Single-Tree rendering and high-throughput Multi-Tree batch spreadsheet calculation with seamless English/Chinese dropdown switching.

### [中文]
1.  **光度数据解析模块 (`ies_parser.py`)：** 自动解析标准的 `IESNA LM-63` 配光曲线文件，提取三维光强分布矩阵，并针对道路照明常规的 C0/180 与 C90/270 空间平面进行了精确的角度相位修正。
2.  **3D 参数化网格生成模块 (`geometry.py`)：** 根据基础林业数据，将树冠抽象为特定的几何体（半椭球体、圆锥体、圆柱体），并利用均匀的斐波那契点云算法将其离散化为高密度的自适应表面网格顶点。
3.  **光场辐射计算引擎 (`light_analysis.py`)：** 严格执行光学平方反比定律，并对光度矩阵进行双线性插值，高精度计算每个微观顶点接收到的入射量子能量。
4.  **生态评估与隐性碳汇模块 (`ecology.py`)：** 实现了光环境的分级统计（如统计超越光补偿点 LCP 的有效受光面分布），并可根据表观量子效率动态积分计算人造光带来的年度“隐性碳汇额外收益”（不扣除暗呼吸消耗）。
5.  **中英文双语图形界面 (GUI)：** 包含一个完备的、跨平台的桌面端 GUI 应用程序（基于 Tkinter），支持单树三维热力图学术渲染和多树大样本 Excel/CSV 表格的高通量一键批量处理，右上角支持中英文下拉框瞬间无缝切换。

---

## 📂 Repository Structure (仓库结构)

```text
treelight/
├── src/
│   └── treelight/
│       ├── __init__.py          # Package initialization & public API exposure
│       ├── config.py            # Physiological databases & persistent state manager
│       ├── ies_parser.py        # IESNA photometric file reader & interpolator
│       ├── geometry.py          # Parametric Fibonacci canopy mesh generator
│       ├── light_analysis.py    # 3D light field radiative engine & visualization
│       └── ecology.py           # Ecological grading & implicit carbon sink calculator
├── example/
│   ├── sample.csv               # Standard batch-processing tabular input template
│   ├── test.ies                 # Sample batwing light distribution curve file
│   ├── demo_single.py           # Interactive single tree analysis demo script
│   └── demo_batch.py            # Interactive batch tree analysis demo script
├── tests/
│   └── test_all_core.py         # Automated unit tests for core modules (pytest)
├── pyproject.toml               # Package build configuration & metadata (PEP 517/518)
└── README.md                    # Project documentation (this file)
```
---
#⚙️ Installation (安装指南)
---
We use pyproject.toml for build and package management. To install core scientific computing libraries from source, clone this repository or download the archive directly from the web page, then perform local installation via pip：
采用现代化的 pyproject.toml 进行构建与打包管理。若需要从源码配置核心科学计算库，请克隆本仓库或直接从网页下载压缩包并通过 pip 直接进行本地安装：
```text
# Clone the repository
git clone [https://github.com/zx0518zx/treelight.git](https://github.com/zx0518zx/treelight.git)
cd treelight

# Install the package and its prerequisites locally
pip install .
```
---
#🚀 Quick Start (快速入门 - Python API)
---
Here is a quick example of how to programmatically execute a single-tree 3D radiative simulation and evaluate its implicit carbon sink:
以下是如何在 Python 脚本中调用核心库进行单树 3D 光照模拟与隐性碳汇评估的完整示例：
```text
# -*- coding: utf-8 -*-
"""
treelight Framework: Pure API Reference Guide
treelight 框架：纯净版 API 接口调用指南
"""
import treelight as tl

def api_reference():
    # =========================================================
    # 1. 数据库与配置相关 API / Database & Configuration APIs
    # =========================================================
    
    # [API 1] 注册自定义树种 / Register custom species
    tl.register_species(name="My_Tree", alpha=0.06, rd=1.2, lcp=25.0, lsp=1500)
    
    # [API 2] 注册自定义光源 / Register custom light source
    tl.register_light(name="My_LED", factor=0.015)
    
    # [API 3] 获取所有可用树种列表 / Get all available species
    species_list = tl.get_available_species()
    
    # [API 4] 获取所有可用光源列表 / Get all available lights
    light_list = tl.get_available_lights()
    
    # [API 5] 获取指定树种的生理参数 / Get parameters of a specific species
    my_tree_params = tl.get_species_params("My_Tree")
    
    # [API 6] 获取指定光源的转换因子 / Get conversion factor of a specific light
    my_led_factor = tl.get_ppfd_factor("My_LED")


    # =========================================================
    # 2. 物理光场计算相关 API / Physical Light Field APIs
    # =========================================================
    
    # 准备基础参数 (Mock parameters)
    ies_file_path = "example/test.ies"
    geo_params = {"canopy_type": "Half Ellipsoid", "tree_height": 8.5, "branch_height": 3.0, "crown_width": 5.0}
    light_pos = [{"x": 1.8, "y": 2.5, "z": 9.5}]
    env_params = {"precision": 0.1, "maintenance_factor": 0.85, "light_output_ratio": 0.9, "ppfd_factor": my_led_factor}
    
    # [API 7] 解析 IES 配光文件 / Parse IES file
    ies_data, parse_msg = tl.parse_ies_full(ies_file_path)
    
    # [API 8] 计算树冠 3D 表面 PPFD 分布 / Calculate 3D canopy PPFD
    physics_res = tl.calculate_canopy_ppfd(geo_params, light_pos, ies_data, env_params)


    # =========================================================
    # 3. 生态学评估相关 API / Ecological Evaluation APIs
    # =========================================================
    
    # [API 9] 评估光环境分级与受光面积 / Grade light environment and surface areas
    grade_stats = tl.grade_light_environment(physics_res, species_name="My_Tree")
    
    # [API 10] 计算年度隐性碳减排量 / Calculate annual implicit carbon reduction
    carbon_stats = tl.calculate_implicit_carbon(physics_res, species_name="My_Tree")


    # =========================================================
    # 4. 可视化相关 API / Visualization API
    # =========================================================
    
    # [API 11] 渲染 3D 树冠光环境热力图 / Render 3D PPFD heatmap (Optional)
    # tl.visualize_ppfd_3d(physics_res, species_name="My_Tree", show=True)

if __name__ == "__main__":
    api_reference()
```
---
🖥️ Graphical User Interface (图形用户界面)
---
For field ecologists and urban planning practitioners who prefer a no-code standalone workspace:

Standalone Executable (.exe): Go to the Releases tab on the right side of this repository page. Download the pre-compiled, self-contained treelight_GUI.exe package.

针对更倾向于免代码操作的野外生态学调查人员或城市规划管理从业者：

免安装独立程序 (.exe)： 请直接点击本仓库右侧的 Releases 标签页。下载预编译、自包含的 treelight_GUI.exe 压缩包。

---
⚠️ Academic Limitations & Scope (学术局限性与适用范围)
---
When citing or applying treelight in rigorous biological assessments, please note the following built-in algorithmic assumptions:

Parametric Continuous Boundary Surface: The framework abstracts tree crowns as continuous geometric primitives (semi-ellipsoids, cones, or cylinders) based on standard inventory indicators rather than voxel grids or leaf-level models.

Outer Canopy Focus: The model calculates the direct radiative field incident upon the outer canopy envelope. It does not account for internal micro-climatic light attenuation, intra-foliar scattering, or branch-level self-shading.

Purpose-Driven Abstraction: This lightweight abstraction is intentionally engineered to strike an optimal balance between structural representation and high computational speed, allowing the tool to execute regional scale-up batch assessments seamlessly.
在将 treelight 应用于严谨的生物生态学 dose-response 效应评估或撰写学术论文时，请务必注意并声明系统内置的以下基础算法假设与局限性：

参数化连续边界曲面： 本框架基于常规林业调查指标将树木冠层抽象为连续的理想几何体（半椭球体、圆锥体、圆柱体），而非基于高密度 LiDAR 点云的微观体素网格。

聚焦树冠外部包络面： 计算引擎重点解析投射并入射于树冠外边界上的直射辐射场。它不包含树冠内部微气候的光衰减过程、叶片间的微观多次散射以及枝条叶片级别的内部自遮挡（Self-shading）效应。

科学目标导向的抽象： 这种轻量级几何原始体抽象经过了有意设计，旨在结构代表性与计算效率之间取得最佳平衡，从而确保软件能以极高的吞吐量完成城市路网级别的跨尺度 scale-up 批量扩展计算。

---
📄 License (开源协议)
---
This project is licensed under the MIT License
