# -*- coding: utf-8 -*-
"""
treelight Framework: Interactive Single Street Tree Analysis Demo
treelight 框架：单棵行道树分析交互式演示脚本（含光区面积分布统计）
"""
import os
import warnings
warnings.filterwarnings("ignore") # Suppress version warnings / 屏蔽版本告警
import treelight as tl

def main():
    print(">>> treelight Single Tree Analysis Demo (单棵树分析演示)")
    print("-" * 50)

    # 1. Interactive input for IES file path / 交互式输入 IES 文件路径
    ies_file = input("👉 Please enter the absolute path of the IES file (请输入 IES 文件路径): ").strip('\'"')
    if not os.path.exists(ies_file):
        print(f"❌ Error: File not found (错误：未找到文件) -> {ies_file}")
        return

    # Parse IES file / 解析配光文件
    ies_data, msg = tl.parse_ies_full(ies_file)
    print(f"IES Parse Status (配光文件解析状态): {msg}")
    if "❌" in msg: 
        return

    # 2. Parameter configuration (aligned with GUI) / 参数配置（与 GUI 保持一致）
    species = "香樟 (Cinnamomum camphora)"
    geo_params = {
        "canopy_type": "半椭球体/Half Ellipsoid", 
        "tree_height": 8.5, 
        "branch_height": 3.0, 
        "crown_width": 5.0
    }
    light_pos = [{"x": 1.8, "y": 2.5, "z": 9.5}]
    env_params = {
        "precision": 0.05, 
        "maintenance_factor": 0.85, 
        "light_output_ratio": 0.90,
        "ppfd_factor": tl.get_ppfd_factor("3000K LED")
    }

    # 3. Core calculation / 核心计算
    print(">>> Running 3D light field simulation (正在运行 3D 光场模拟)...")
    physics_res = tl.calculate_canopy_ppfd(geo_params, light_pos, ies_data, env_params)
    
    # Ecological evaluation / 生态学指标评估
    grade = tl.grade_light_environment(physics_res, species)
    carbon = tl.calculate_implicit_carbon(physics_res, species) # Default standard hours used / 使用库内默认标准时长 (4380h)

    # 4. Print output result report / 打印输出结果报告
    print("\n" + "="*50)
    print(f"--- Simulation Results Report for {species} (分析结果报告) ---")
    print(f"Total Surface Area (总表面积): {round(grade['total_area'], 2)} m²")
    print(f"Max PPFD (最大光合有效辐射): {round(grade['max_ppfd'], 2)} μmol/m²/s")
    print(f"Average Effective PPFD (平均有效PPFD): {round(grade['avg_ppfd'], 2)} μmol/m²/s")
    print(f"Annual Carbon Sink (年度隐性碳减排量): {round(carbon.get('carbon_g', 0), 4)} g CO2")
    print("-" * 50)
    
    # Print light area distribution / 打印光环境分级面积统计
    print("【Light Area Distribution Statistics (受光面积分布统计)】")
    for k, v in grade.get('grade_stats_area', {}).items():
        print(f"  Interval (区间) [{k}]: {round(v, 2)} m²")
    print("=" * 50)

if __name__ == "__main__":
    main()
