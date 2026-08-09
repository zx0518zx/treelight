# -*- coding: utf-8 -*-
"""
treelight Framework: Interactive Batch Street Tree Analysis Demo
treelight 框架：行道树批量计算交互式演示脚本
"""
import os
import re
import warnings
warnings.filterwarnings("ignore") # Suppress version warnings / 屏蔽版本告警
import pandas as pd
import treelight as tl

def main():
    print(">>> treelight Batch Tree Analysis Demo (行道树批量分析演示)")
    print("-" * 50)
    
    # 1. Interactive input for IES and batch data file paths / 交互式输入 IES 文件及批量数据文件路径
    ies_file = input("👉 Please enter the absolute path of the IES file (请输入 IES 文件路径): ").strip('\'"')
    if not os.path.exists(ies_file):
        print(f"❌ Error: IES file not found (错误：未找到 IES 文件) -> {ies_file}")
        return

    data_file = input("👉 Please enter the path of the batch Excel/CSV file (请输入待处理的 Excel/CSV 文件路径): ").strip('\'"')
    if not os.path.exists(data_file):
        print(f"❌ Error: Data file not found (错误：未找到数据文件) -> {data_file}")
        return

    # Parse IES file / 解析配光文件
    ies_data, msg = tl.parse_ies_full(ies_file)
    print(f"IES Parse Status (配光文件解析状态): {msg}")
    if "❌" in msg:
        return

    # Global environment parameters / 全局环境参数配置
    env_params = {
        "precision": 0.05, 
        "maintenance_factor": 0.85, 
        "light_output_ratio": 0.90,
        "ppfd_factor": tl.get_ppfd_factor("3000K LED")
    }

    # 2. Read batch data / 读取批量数据
    df_input = pd.read_csv(data_file, encoding='utf-8-sig') if data_file.endswith('.csv') else pd.read_excel(data_file)
    results_list = []

    print(f">>> Total {len(df_input)} entries to process (共有 {len(df_input)} 条数据待处理)...")

    # 3. Iterate row by row for calculation / 循环逐行计算
    for index, row in df_input.iterrows():
        th_val = row.get("Total Tree Height (m)", 8.0)
        if pd.isna(th_val):
            continue
            
        # Extract canopy geometry / 提取树冠几何参数
        batch_geo = {
            "canopy_type": row.get("Canopy Type", "Half Ellipsoid"),
            "tree_height": float(th_val),
            "branch_height": float(row.get("Under-branch Height (m)", 2.5)),
            "crown_width": float(row.get("Crown Diameter (m)", 4.0))
        }
        
        # Fuzzy matching for tree species / 树种模糊匹配
        species = "默认阔叶树 (Default Broadleaf)"
        raw_species = str(row.get("Tree Species", "default")).strip().lower()
        for available_sp in tl.get_available_species():
            if raw_species in available_sp.lower():
                species = available_sp
                break
        
        # Parse light source coordinates / 解析路灯坐标
        light_str = str(row.get("Light Source Coordinates", ""))
        coords = re.findall(r"[-+]?\d*\.\d+|\d+", light_str)
        light_pos_list = [{"x": float(coords[0]), "y": float(coords[1]), "z": float(coords[2])}] if len(coords) >= 3 else [{"x": 1.8, "y": 2.5, "z": 9.5}]

        # Execute single tree calculation / 执行单株物理计算与生态评估
        batch_physics = tl.calculate_canopy_ppfd(batch_geo, light_pos_list, ies_data, env_params)
        batch_grade = tl.grade_light_environment(batch_physics, species)
        batch_carbon = tl.calculate_implicit_carbon(batch_physics, species)
        
        # Compile output dictionary / 汇总输出数据字典
        out_row = row.to_dict()
        out_row["LCP Reference"] = batch_grade["LCP_ref"]
        out_row["Total Area (m2)"] = round(batch_grade["total_area"], 3)
        out_row["Max PPFD"] = round(batch_grade["max_ppfd"], 3)
        out_row["Avg PPFD"] = round(batch_grade["avg_ppfd"], 3)
        out_row["Annual Carbon Reduction (g)"] = round(batch_carbon.get("carbon_g", 0), 3)
        
        # Area distribution / 光区面积分布
        for k, v in batch_grade.get('grade_stats_area', {}).items():
            out_row["Area " + str(k)] = round(v, 3)
            
        results_list.append(out_row)

    # 4. Export batch results / 导出批量结果
    df_output = pd.DataFrame(results_list)
    output_path = "Interactive_Batch_Results.csv"
    df_output.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f">>> Batch processing completed! Results successfully saved to (批量处理完成！结果已成功保存至): {output_path}")

if __name__ == "__main__":
    main()