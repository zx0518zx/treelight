import ast
import os
import re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

from treelight import parse_ies_full, get_ppfd_factor
from treelight.ies_parser import get_interpolated_intensity

# ========================== 1. Relative Path Configuration ==========================
BASE_DIR = Path(__file__).resolve().parent

SITES = [
    {
        'panel_tag': '(a)',
        'short_title': 'Site 1: Single-luminaire roadway',
        'data_path': BASE_DIR / 'site1_single_roadway' / 'site1_validation_data.xlsx',
        'ies_path':  BASE_DIR / 'site1_single_roadway' / 'BGP293 LED240-4S_740 I DM11 STD NA 48_60.ies',
        'data_sheet': 'Data',
        'metadata_sheet': 'Metadata',
        'metadata_col': 1,
        'num_lamps': 1,
        'phi_mode': 'y_forward',
    },
    {
        'panel_tag': '(b)',
        'short_title': 'Site 2: Directional floodlighting',
        'data_path': BASE_DIR / 'site2_directional_floodlight' / 'site2_validation_data.xlsx',
        'ies_path':  BASE_DIR / 'site2_directional_floodlight' / 'Signify-BVP561-LED40-740-20W-WLP-AMB.ies',
        'data_sheet': 'Data',
        'metadata_sheet': 'Metadata',
        'metadata_col': 1,
        'num_lamps': 1,
        'phi_mode': 'y_forward',
    },
    {
        'panel_tag': '(c)',
        'short_title': 'Site 3: Overlapping roadway lighting',
        'data_path': BASE_DIR / 'site3_overlapping_roadway' / 'site3_validation_data.xlsx',
        'ies_path':  BASE_DIR / 'site3_overlapping_roadway' / 'BGP292 LED120-4S_740 II DM11 STDE NA 48_.ies',
        'data_sheet': 'Data',
        'metadata_sheet': 'Metadata',
        'metadata_col': 1,
        'num_lamps': 2,
        'phi_mode': 'x_along',
    },
]

USE_METADATA_TILT = True
PHYSICAL_K = None
SAVE_FIGURE = True
OUTPUT_PNG = BASE_DIR / 'Figure4_combined_validation.png'
# ====================================================================================

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams.update({
    'axes.labelsize': 10.5,
    'xtick.labelsize': 9.5,
    'ytick.labelsize': 9.5,
    'legend.fontsize': 10,
    'axes.linewidth': 0.9,
    'figure.dpi': 150,
})


def _extract_first_float(val, default=None):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    if isinstance(val, (int, float)):
        return float(val)
    match = re.search(r'-?\d+(?:\.\d+)?', str(val))
    return float(match.group(0)) if match else default


def _extract_spacing(val, default=20.0):
    if val is None:
        return default
    text = str(val)
    match = re.search(r'(\d+(?:\.\d+)?)\s*m\s*(?:pole\s*)?spacing', text, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))
    nums = [float(m) for m in re.findall(r'x\s*=\s*(\d+(?:\.\d+)?)', text, flags=re.IGNORECASE)]
    if nums and max(nums) > 0:
        return max(nums)
    return default


def get_treelight_ppfd_factor(luminaire_type_cct):
    cct = _extract_first_float(luminaire_type_cct, default=None)
    if cct is None:
        light_key = 'Universal White LED'
    elif cct <= 3500:
        light_key = '3000K LED'
    elif cct <= 4500:
        light_key = '4000K LED'
    else:
        light_key = '5000K LED'
    return float(get_ppfd_factor(light_key))


def load_site_metadata(excel_path, metadata_sheet='Metadata', metadata_col=1):
    xl = pd.ExcelFile(excel_path)
    sheet_to_read = metadata_sheet if metadata_sheet in xl.sheet_names else xl.sheet_names[1]
    df_meta = pd.read_excel(xl, sheet_name=sheet_to_read, header=None)

    raw_map = {}
    for _, row in df_meta.iterrows():
        key = row.iloc[0] if len(row) > 0 else None
        val = row.iloc[metadata_col] if len(row) > metadata_col else None
        if pd.notna(key):
            k_str = str(key).strip().lower()
            v_clean = None if pd.isna(val) else (val if isinstance(val, (int, float)) else str(val).strip())
            if k_str:
                raw_map[k_str] = v_clean

    def get_field(*candidates, default=None):
        for cand in candidates:
            c_l = cand.lower()
            if c_l in raw_map and raw_map[c_l] is not None:
                return raw_map[c_l]
        for cand in candidates:
            c_l = cand.lower()
            for k, v in raw_map.items():
                if c_l in k and v is not None:
                    return v
        return default

    light_height = _extract_first_float(
        get_field('Luminaire Mounting Height (m)', 'Luminaire Mounting Height', 'Mounting Height')
    )
    if light_height is None:
        raise ValueError(f"Could not read mounting height from '{sheet_to_read}'.")

    span_distance = _extract_spacing(
        get_field('Luminaire Configuration & Spacing', 'Spacing'), default=20.0
    )
    tilt_deg = _extract_first_float(get_field('Luminaire Tilt', 'Tilt'), default=0.0)
    luminaire_type_cct = str(get_field('Luminaire Type & CCT', 'CCT', default='LED, 4000 K'))
    cct_val = _extract_first_float(luminaire_type_cct, default=4000.0)

    return {
        'light_height': float(light_height),
        'span_distance': float(span_distance),
        'tilt_deg': float(tilt_deg),
        'luminaire_type_cct': luminaire_type_cct,
        'cct_k': int(round(cct_val)),
    }


def calculate_lamp_ppfd(x, y, z, light_x, light_y, light_z, ies_data, ppfd_factor, tilt_deg=0.0, phi_mode='y_forward'):
    dx = x - light_x
    dy = y - light_y
    dz = z - light_z
    dist_sq = dx**2 + dy**2 + dz**2
    dist = np.sqrt(dist_sq)
    if dist <= 1e-6:
        return 0.0

    cos_surface = abs(dz) / dist
    tilt_rad = np.radians(float(tilt_deg))
    cos_t, sin_t = np.cos(tilt_rad), np.sin(tilt_rad)
    lx = dx
    ly = dy * cos_t + dz * sin_t
    lz = -dy * sin_t + dz * cos_t

    theta_lamp = np.degrees(np.arccos(np.clip(-lz / dist, -1.0, 1.0)))
    if phi_mode == 'x_along':
        phi_lamp = np.degrees(np.arctan2(ly, lx)) % 360.0
    else:
        phi_lamp = np.degrees(np.arctan2(lx, ly)) % 360.0

    intensity = get_interpolated_intensity(ies_data, theta_lamp, phi_lamp - 90.0)
    return (intensity / dist_sq) * cos_surface * float(ppfd_factor)


def evaluate_site(df_data, ies_data, meta, cfg, ppfd_factor):
    light_h = meta['light_height']
    span = meta['span_distance']
    tilt = meta['tilt_deg'] if USE_METADATA_TILT else 0.0
    num_lamps = int(cfg.get('num_lamps', 1))
    phi_mode = cfg.get('phi_mode', 'y_forward')

    y_meas, y_sim = [], []
    for _, row in df_data.iterrows():
        try:
            coord_str = str(row[df_data.columns[0]]).strip().replace('（', '(').replace('）', ')')
            x, y, z = [float(v) for v in ast.literal_eval(coord_str)]
            meas = float(row[df_data.columns[1]])
        except Exception:
            continue

        sim = calculate_lamp_ppfd(x, y, z, 0.0, 0.0, light_h, ies_data, ppfd_factor, tilt, phi_mode)
        if num_lamps == 2:
            sim += calculate_lamp_ppfd(x, y, z, span, 0.0, light_h, ies_data, ppfd_factor, tilt, phi_mode)

        y_meas.append(meas)
        y_sim.append(sim)

    y_meas = np.asarray(y_meas, dtype=float)
    y_sim = np.asarray(y_sim, dtype=float)
    if len(y_meas) == 0:
        return None

    ss_res = float(np.sum((y_meas - y_sim) ** 2))
    ss_tot = float(np.sum((y_meas - np.mean(y_meas)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    pearson_r = float(np.corrcoef(y_meas, y_sim)[0, 1]) if len(y_meas) > 1 else 0.0
    rmse = float(np.sqrt(np.mean((y_meas - y_sim) ** 2)))
    mae = float(np.mean(np.abs(y_meas - y_sim)))
    bias = float(np.mean(y_sim - y_meas))
    slope, intercept = np.polyfit(y_meas, y_sim, 1)

    return {
        'y_meas': y_meas,
        'y_sim': y_sim,
        'tilt_used': tilt,
        'metrics': {
            'n': int(len(y_meas)),
            'r2': float(r2),
            'pearson_r': pearson_r,
            'rmse': rmse,
            'mae': mae,
            'bias': bias,
            'slope': float(slope),
            'intercept': float(intercept),
        },
    }


def main():
    panel_data = []
    summary_rows = []

    for cfg in SITES:
        data_path = Path(cfg['data_path'])
        ies_path = Path(cfg['ies_path'])
        if not data_path.is_file():
            raise FileNotFoundError(f"Validation Excel not found: {data_path}")
        if not ies_path.is_file():
            raise FileNotFoundError(f"IES file not found: {ies_path}")

        meta = load_site_metadata(str(data_path), cfg['metadata_sheet'], cfg['metadata_col'])
        ppfd_factor = PHYSICAL_K if PHYSICAL_K is not None else get_treelight_ppfd_factor(meta['luminaire_type_cct'])

        xl = pd.ExcelFile(data_path)
        sheet_data = cfg['data_sheet'] if cfg['data_sheet'] in xl.sheet_names else 0
        df_data = pd.read_excel(xl, sheet_name=sheet_data)

        ies_data, msg = parse_ies_full(str(ies_path))
        if not ies_data:
            raise RuntimeError(f"Failed to parse {ies_path}: {msg}")

        res = evaluate_site(df_data, ies_data, meta, cfg, ppfd_factor)
        panel_data.append((cfg, meta, res))
        met = res['metrics']
        summary_rows.append([
            cfg['panel_tag'], cfg['short_title'], meta['light_height'], res['tilt_used'],
            round(ppfd_factor, 4), met['n'], round(met['r2'], 3), round(met['pearson_r'], 3),
            round(met['rmse'], 3), round(met['mae'], 3), round(met['bias'], 3),
            round(met['slope'], 3), round(met['intercept'], 3),
        ])

    cols = ["Panel", "Scenario", "H(m)", "Tilt(°)", "k_phys", "n", "R²", "r", "RMSE", "MAE", "Bias", "Slope", "Intercept"]
    print("\n" + "=" * 124)
    print(f"{'Figure 4 Consolidated Field Validation Summary (All 3 Sites)':^124}")
    print("-" * 124)
    print(pd.DataFrame(summary_rows, columns=cols).to_string(index=False))
    print("=" * 124 + "\n")

    n_panels = len(panel_data)
    fig, axes = plt.subplots(1, n_panels, figsize=(4.65 * n_panels, 5.1), squeeze=False)
    axes_flat = axes[0]

    legend_handles = None
    for i, (cfg, meta, res) in enumerate(panel_data):
        ax = axes_flat[i]
        y_meas, y_sim, met = res['y_meas'], res['y_sim'], res['metrics']

        h_pts = ax.scatter(
            y_meas, y_sim, s=34, c='white', edgecolors='#1f77b4',
            linewidths=1.05, alpha=0.88, label='Observed vs. simulated PPFD', zorder=3
        )
        max_val = max(float(y_meas.max()), float(y_sim.max())) * 1.08

        h_1to1, = ax.plot(
            [0, max_val], [0, max_val], color='#d62728', linestyle='--',
            linewidth=1.25, label='1:1 line', zorder=1
        )
        x_line = np.linspace(0, max_val, 100)
        h_ols, = ax.plot(
            x_line, met['slope'] * x_line + met['intercept'], color='#1f77b4',
            linestyle='-', linewidth=1.35, label='OLS linear fit', zorder=2
        )
        if legend_handles is None:
            legend_handles = [h_pts, h_1to1, h_ols]

        ax.set_title(
            f"{cfg['panel_tag']} {cfg['short_title']} (H = {meta['light_height']:g} m)",
            fontsize=9.8, fontweight='bold', loc='left', pad=8
        )
        ax.set_xlabel(r'Measured PPFD ($\mu\mathrm{mol}\cdot\mathrm{m}^{-2}\cdot\mathrm{s}^{-1}$)', labelpad=6)
        if i == 0:
            ax.set_ylabel(r'Simulated PPFD ($\mu\mathrm{mol}\cdot\mathrm{m}^{-2}\cdot\mathrm{s}^{-1}$)')

        ax.set_xlim(0, max_val)
        ax.set_ylim(0, max_val)
        ax.set_aspect('equal', adjustable='box')

        sign = '+' if met['intercept'] >= 0 else '-'
        stats_box = (
            f"$n = {met['n']}$\n"
            f"$y = {met['slope']:.2f}x {sign} {abs(met['intercept']):.2f}$\n"
            f"$R^2 = {met['r2']:.3f}$ ($r = {met['pearson_r']:.3f}$)\n"
            f"$\\mathrm{{RMSE}} = {met['rmse']:.3f}$"
        )
        ax.text(
            0.05, 0.95, stats_box, transform=ax.transAxes, fontsize=9.0,
            verticalalignment='top',
            bbox=dict(boxstyle='square,pad=0.38', facecolor='white', alpha=0.92,
                      edgecolor='#333333', linewidth=0.75)
        )
        ax.grid(False)
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(which='both', direction='out', top=False, right=False)

    fig.subplots_adjust(left=0.06, right=0.98, top=0.90, bottom=0.22, wspace=0.22)
    fig.legend(
        handles=legend_handles,
        labels=['Observed vs. simulated PPFD', '1:1 line', 'OLS linear fit'],
        loc='lower center',
        ncol=3,
        frameon=True,
        edgecolor='#333333',
        fancybox=False,
        bbox_to_anchor=(0.52, 0.03),
    )

    if SAVE_FIGURE:
        fig.savefig(str(OUTPUT_PNG), dpi=600, bbox_inches='tight')
        print(f"Saved Figure 4 (600 DPI PNG): {OUTPUT_PNG}")

    plt.show()


if __name__ == "__main__":
    main()
