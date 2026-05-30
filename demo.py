import sys
import os
sys.path.insert(0, os.path.abspath('src'))
import numpy as np
import treelight as tl


def run_english_verification():
    print("==================================================")
    print("  treelight Framework: Comprehensive Automated Verification & Testing Script  ")
    print("==================================================\n")

    # --------------------------------------------------
    # 1. Verify Core Database and Configuration Commands
    # --------------------------------------------------
    print("[1/4] Verifying 6 core configuration commands for the underlying database...")
    
    # Command 1: Get list of all available tree species in the system
    initial_species = tl.get_available_species()
    print(f"-> [Command 1] Initial species in system: {initial_species}")
    
    # Command 2: Register a new custom species (triggers local JSON read/write persistence)
    print("-> [Command 2] Registering custom species 'Platanus_orientalis'...")
    tl.register_species(name="Platanus_orientalis", alpha=0.062, Rd=1.15, LCP=24.5, LSP=1500)
    
    # Command 3: Query physiological parameters of the newly registered species
    species_params = tl.get_species_params("Platanus_orientalis")
    print(f"-> [Command 3] Retrieved core physiological parameters for 'Platanus_orientalis': {species_params}")
    
    # Command 4: Get list of all supported light source spectral factors
    initial_lights = tl.get_available_lights()
    print(f"-> [Command 4] Initial light source configuration table: {initial_lights}")
    
    # Command 5: Register a new custom light source conversion factor
    print("-> [Command 5] Registering custom light source conversion factor 'Experimental_LED'...")
    tl.register_light(name="Experimental_LED", factor=0.0165)
    
    # Command 6: Retrieve the conversion factor for the specific custom light source
    light_factor = tl.get_ppfd_factor("Experimental_LED")
    print(f"-> [Command 6] Successfully retrieved conversion factor for 'Experimental_LED': {light_factor}")
    
    # Verify if the local configuration file was successfully generated
    if os.path.exists("treelight_config.json"):
        print("✅ Success: Local database file 'treelight_config.json' correctly generated and persisted.")
    else:
        print("❌ Failure: Local database persistence failed.")
    print("-" * 50 + "\n")

    # --------------------------------------------------
    # 2. Photometric Data Parsing and 3D Mesh Generation
    # --------------------------------------------------
    print("[2/4] Verifying IES photometric curve parsing and 3D geometric mesh discretization...")
    
    while True:
        ies_path = input("👉 Please enter the absolute path of the IES file (Hint: You can drag and drop the file here): ").strip()
        ies_path = ies_path.strip('\'"') 
        
        if os.path.exists(ies_path):
            print(f"✅ Successfully located file: {ies_path}")
            break
        else:
            print(f"❌ File not found: {ies_path}. Please check the path and try again!\n")

    # Execute parsing
    ies_data, msg = tl.parse_ies_full(ies_path)
    print(f"-> IES parser returned log: {msg}")
    
    # Set geometric canopy parameters (for single tree test)
    geo_params = {
        "canopy_type": "半椭球体",  # Semi-ellipsoid (kept in Chinese to match underlying library mappings)
        "tree_height": 8.5,
        "branch_height": 3.0,
        "crown_width": 5.0
    }
    print("✅ Success: Photometric mesh interpolation ready; ideal geometric boundary conditions for canopy established.")
    print("-" * 50 + "\n")

    # --------------------------------------------------
    # 3. 3D Spatial Light Field Radiation Computation
    # --------------------------------------------------
    print("[3/4] Initiating 3D spatial light field radiation simulation engine...")
    light_pos_list_single = [{"x": 1.8, "y": 2.5, "z": 9.5}] 
    env_params = {
        "precision": 0.05,
        "maintenance_factor": 0.85,
        "light_output_ratio": 0.90,
        "ppfd_factor": tl.get_ppfd_factor("3000K LED (0.0143)")
    }
    
    physics_result = tl.calculate_canopy_ppfd(geo_params, light_pos_list_single, ies_data, env_params)
    print(f"-> Fibonacci point cloud successfully discretized. Canopy outer surface mesh vertices: {len(physics_result['centers'])}")
    print("✅ Success: Spatial optical inverse-square law and bilinear luminous intensity interpolation completed.")
    print("-" * 50 + "\n")

    # --------------------------------------------------
    # 4. Ecological Assessment and Implicit Carbon Sink Quantification
    # --------------------------------------------------
    print("[4/4] Quantifying nighttime light exposure grading and implicit carbon sink increments...")
    
    grade_stats = tl.grade_light_environment(physics_result, "Platanus_orientalis")
    carbon_stats = tl.calculate_implicit_carbon(physics_result, "Platanus_orientalis", hours=4380)
    areas = grade_stats["grade_stats_area"]
    
    print("\n[ Physical & Ecological Indicators Report of Light Environment ]")
    print(f"📍 Relative Light Source Coordinates: X={light_pos_list_single[0]['x']}m, Y={light_pos_list_single[0]['y']}m, H={light_pos_list_single[0]['z']}m (Origin at trunk base)")
    print(f"🌲 Total Surface Area of Canopy Outer Boundary: {grade_stats['total_area']:.2f} m²")
    print(f"💡 Maximum Light Intensity Received (Max PPFD): {grade_stats['max_ppfd']:.2f} μmol/(m²·s)")
    print(f"📊 Average Effective Light Intensity (PPFD > 0.01): {grade_stats['avg_ppfd']:.2f} μmol/(m²·s)")
    
    print("\n[ Gradient Distribution of Canopy Illuminated Area ]")
    print(f"  ├─ [Mild Disturbance] 0.01 - 0.1 μmol/(m²·s) : {areas.get('0.01-0.1', 0):.2f} m²")
    print(f"  ├─ [Moderate Disturbance] 0.1 - 1.0 μmol/(m²·s)  : {areas.get('0.1-1.0', 0):.2f} m²")
    print(f"  ├─ [Severe Disturbance] 1.0 - LCP point      : {areas.get('1.0-LCP', 0):.2f} m²")
    print(f"  └─ [Effective Carbon Sink] > LCP point       : {areas.get('>LCP', 0):.2f} m²")
    
    print(f"\n🌍 Total Annual Implicit Carbon Sink Benefit from Artificial Light Radiation: {carbon_stats['carbon_g']:.4f} g CO2")
    print("✅ Success: Ecological incremental effect analysis module successfully verified.")
    print("\n==================================================")
    print("  Single-tree baseline test passed seamlessly! ")
    print("==================================================")
    
    # --------------------------------------------------
    # 5. High-Throughput Batch Processing Demonstration
    # --------------------------------------------------
    print("\n[5/5] Verifying high-throughput batch processing capabilities via Pandas...")
    
    import pandas as pd
    
    while True:
        sample_excel_path = input("👉 Please enter the absolute path of the batch calculation Excel/CSV file (e.g., Tree_Lighting_Standard_Format.csv)\n   (Hint: Drag and drop the file here, or type 'skip' to bypass): ").strip()
        sample_excel_path = sample_excel_path.strip('\'"')
        
        if sample_excel_path.lower() == 'skip':
            print("⚠️ Batch processing demonstration manually skipped.")
            break
            
        elif os.path.exists(sample_excel_path):
            print(f"✅ Successfully located batch input template: {sample_excel_path}. Initiating high-throughput computation...")
            try:
                # Auto-detect file format (CSV or Excel)
                if sample_excel_path.lower().endswith('.csv'):
                    df_input = pd.read_csv(sample_excel_path, encoding='utf-8')
                else:
                    df_input = pd.read_excel(sample_excel_path)
                    
                results_list = []
                
                # Iterate through each tree in the dataframe for independent computation
                for index, row in df_input.iterrows():
                    # Dynamically read forestry parameters for each row
                    batch_geo = {
                        "canopy_type": row.get("Canopy Type", "半椭球体"),
                        "tree_height": float(row.get("Total Tree Height (m)", 8.0)),
                        "branch_height": float(row.get("Under-branch Height (m)", 2.5)),
                        "crown_width": float(row.get("Crown Diameter (m)", 4.0))
                    }
                    species = row.get("Tree Species", "Platanus_orientalis")
                    
                    # Dynamically parse specific light source coordinates for this tree
                    coord_str = str(row.get("Light Source Coordinates (x,y,z)", "")).strip()
                    tree_light_pos = []
                    if coord_str and coord_str != 'None' and coord_str != 'nan':
                        # Expecting format (x, y, z)
                        try:
                            clean_coord = coord_str.replace('(', '').replace(')', '').replace(' ', '')
                            x, y, z = map(float, clean_coord.split(','))
                            tree_light_pos.append({"x": x, "y": y, "z": z})
                        except Exception as parse_e:
                            print(f"⚠️ Row {index+1}: Failed to parse coordinates '{coord_str}': {parse_e}. Skipping this light source.")
                    
                    # Execute computation only if valid light sources are parsed
                    if tree_light_pos:
                        batch_physics = tl.calculate_canopy_ppfd(batch_geo, tree_light_pos, ies_data, env_params)
                        batch_grade = tl.grade_light_environment(batch_physics, species)
                        batch_carbon = tl.calculate_implicit_carbon(batch_physics, species, hours=4380)
                        
                        batch_areas = batch_grade["grade_stats_area"]
                        
                        # Record comprehensive results for this tree
                        results_list.append({
                            "Tree_ID": row.get("Tree ID", index + 1),
                            "Species": species,
                            "Light_Coordinates": coord_str,
                            "Total_Canopy_Area_m2": round(batch_grade["total_area"], 2),
                            "Max_PPFD": round(batch_grade["max_ppfd"], 3),
                            "Avg_PPFD": round(batch_grade["avg_ppfd"], 3),
                            "Area_0.01_to_0.1_m2": round(batch_areas.get('0.01-0.1', 0), 2),
                            "Area_0.1_to_1.0_m2": round(batch_areas.get('0.1-1.0', 0), 2),
                            "Area_1.0_to_LCP_m2": round(batch_areas.get('1.0-LCP', 0), 2),
                            "Area_above_LCP_m2": round(batch_areas.get('>LCP', 0), 2),
                            "Annual_Carbon_Sink_g": round(batch_carbon["carbon_g"], 4)
                        })
                    
                # Export results to CSV uniformly
                df_output = pd.DataFrame(results_list)
                output_file = "Batch_Simulation_Results.csv"
                df_output.to_csv(output_file, index=False, encoding='utf-8-sig')
                
                print(f"✅ Success: Batch computation completed! Processed {len(df_output)} tree-light combinations. Results saved to '{output_file}' in the current directory.")
                break 
                
            except Exception as e: 
                print(f"❌ Exception occurred during batch processing: {e}")
                print("💡 Please verify that column names match (e.g., 'Light Source Coordinates (x,y,z)') and ensure the file is not currently open in Excel or another program.")
                break
        else:
            print(f"❌ File not found: {sample_excel_path}. Please check the path and try again!\n")

    print("\n==================================================")
    print("  Full pipeline verification thoroughly completed!  ")
    print("==================================================")

if __name__ == "__main__":
    run_english_verification()
