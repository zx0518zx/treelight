Installation (安装指南)
treelight leverages a modern pyproject.toml configuration. To install and use the core development package from source, clone this repository and install it directly via pip:
treelight 采用现代化的 pyproject.toml 进行构建与打包管理。若需要从源码配置核心科学计算库，请克隆本仓库并通过 pip 直接进行本地安装：


# Clone the repository
git clone [https://github.com/zx0518zx/treelight.git](https://github.com/zx0518zx/treelight.git)
cd treelight

# Install the package and its prerequisites locally
pip install .


Quick Start (快速入门 - Python API)
Here is a quick example of how to programmatically execute a single-tree 3D radiative simulation and evaluate its implicit carbon sink:


import numpy as np
import treelight as tl

# 1. Register or update customized tree species parameters
tl.register_species("Platanus × acerifolia", alpha=0.058, Rd=1.08, LCP=25.3)

# 2. Parse the IES photometric file
ies_data, msg = tl.parse_ies_full("example/dummy_test.ies")
print(msg)

# 3. Configure tree morphology parameters
geo_params = {
    "canopy_type": "半椭球体",    # Supports: "半椭球体" (Half Ellipsoid), "圆锥体" (Cone), "圆柱体" (Cylinder)
    "tree_height": 8.4,
    "branch_height": 2.9,
    "crown_width": 5.1
}

# 4. Set relative streetlight spatial positions (Local trunk-base Cartesian coordinate)
light_pos_list = [{"x": 1.7, "y": 3.0, "z": 10.0}]

# 5. Define environmental simulation parameters
env_params = {
    "precision": 0.01,             # Target surface area discretization grid mesh size (m²)
    "maintenance_factor": 0.85,    # Luminaire maintenance factor
    "light_output_ratio": 0.90,    # Light output ratio
    "ppfd_factor": 0.0143          # k factor matching a 3000K LED source
}

# 6. Execute core light field simulation
physics_result = tl.calculate_canopy_ppfd(geo_params, light_pos_list, ies_data, env_params)

# 7. Perform light environmental grading and carbon sink evaluation
grade_stats = tl.grade_light_environment(physics_result, "Platanus × acerifolia")
carbon_stats = tl.calculate_implicit_carbon(physics_result, "Platanus × acerifolia", hours=4380)

# Output evaluation summaries
print(f"Total Canopy Area: {grade_stats['total_area']:.2f} m²")
print(f"Average Effective PPFD: {grade_stats['avg_ppfd']:.2f} μmol/(m²·s)")
print(f"Annual Implicit Carbon Sink: {carbon_stats['carbon_g']:.4f} g CO2")

# 8. Render academic dual-viewport 3D heatmap
tl.visualize_ppfd_3d(physics_result, species_name="Platanus × acerifolia", show=True)


For field ecologists and urban planning practitioners who prefer a no-code standalone workspace:

Standalone Executable (.exe): Go to the Releases tab on the right side of this repository page. Download the pre-compiled, self-contained treelight_GUI.exe package.

Bilingual Switch: Use the drop-down language box in the upper right corner to instantly shift the full-system UI between English and 简体中文.

Batch Processing: Drop your standardized field inventory data spreadsheets (.xlsx, .xls, .csv) directly into the Multi-Tree Operational Panel to run automated high-throughput computations.

针对更倾向于免代码操作的野外生态学调查人员或城市规划管理从业者：

免安装独立程序 (.exe)： 请直接点击本仓库右侧的 Releases 标签页。下载预编译、自包含的 treelight_GUI.exe 压缩包。

双语瞬间切换： 利用软件右上角的语言下拉框，可将包含日志、计算报告、分级图表在内的全系统 UI 在 English 和 简体中文 之间进行无缝切换（解决了常见的中文字体乱码问题）。

高通量处理： 将标准化的野外调查表格（格式参考 example/sample_input.xlsx）拖入多树分析面板，即可一键自动化批量运行大样本模拟并导出详尽的 Excel 计算结果表。



Academic Limitations & Scope
When citing or applying treelight in rigorous biological assessments, please note the following built-in algorithmic assumptions:

Parametric Continuous Boundary Surface: The framework abstracts tree crowns as continuous geometric primitives (semi-ellipsoids, cones, or cylinders) based on standard inventory indicators rather than voxel grids or leaf-level models.

Outer Canopy Focus: The model calculates the direct radiative field incident upon the outer canopy envelope. It does not account for internal micro-climatic light attenuation, intra-foliar scattering, or branch-level self-shading.

Purpose-Driven Abstraction: This lightweight abstraction is intentionally engineered to strike an optimal balance between structural representation and high computational speed, allowing the tool to execute regional scale-up batch assessments seamlessly.

在将 treelight 应用于严谨的生物生态学 dose-response 效应评估或撰写学术论文时，请务必注意并声明系统内置的以下基础算法假设与局限性：

参数化连续边界曲面： 本框架基于常规林业调查指标将树木冠层抽象为连续的理想几何体（半椭球体、圆锥体、圆柱体），而非基于高密度 LiDAR 点云的微观体素网格。

聚焦树冠外部包络面： 计算引擎重点解析投射并入射于树冠外边界上的直射辐射场。它不包含树冠内部微气候的光衰减过程、叶片间的微观多次散射以及枝条叶片级别的内部自遮挡（Self-shading）效应。

科学目标导向的抽象： 这种轻量级几何原始体抽象经过了有意设计，旨在结构代表性与计算效率之间取得最佳平衡，从而确保软件能以极高的吞吐量完成城市路网级别的跨尺度 scale-up 批量扩展计算。

License (开源协议)
This project is licensed under the MIT License
