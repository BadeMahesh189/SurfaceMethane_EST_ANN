import os
import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
import numpy as np
from scipy.interpolate import griddata

# === Paths ===
base_path = r"D:\Baylor University-2024\Paper1\Final commensts_Manuscript\09172025\Figure 5"
files = {
    "BR_A": ("BR_A.xlsx", "MethaneMixingRatio"),
    "LM_A": ("BR_B.xlsx", "MethaneMixingRatio"),
    "SCG_A": ("LM_A.xlsx", "MethaneMixingRatio"),
    "BR_B": ("LM_B.xlsx", "MethaneMixingRatio"),
    "LM_B": ("SCG_A.xlsx", "MethaneMixingRatio"),
    "SCG_B": ("SCG_B.xlsx", "MethaneMixingRatio"),
}

# Station data (CSV)
file_path_csv = r"D:\Baylor University-2024\Paper1\ANN1\NOAA_GML_2022\observational_data.csv"
stations_df = pd.read_csv(file_path_csv)

# Convert stations into GeoDataFrame
stations_gdf = geopandas.GeoDataFrame(
    stations_df,
    geometry=geopandas.points_from_xy(stations_df["Longitude"], stations_df["Latitude"]),
    crs="EPSG:4326"
)

# === Load Excel datasets ===
datasets = {}
for key, (fname, colname) in files.items():
    fpath = os.path.join(base_path, fname)
    df = pd.read_excel(fpath, sheet_name="Sheet1")
    geometry = geopandas.points_from_xy(df['Longitude'], df['Latitude'])
    gdf = geopandas.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    datasets[key] = (gdf, colname)

# === Setup figure (3 rows × 2 columns) ===
projection = ccrs.PlateCarree()
fig, axes = plt.subplots(
    3, 2, figsize=(20, 12),
    subplot_kw={"projection": projection}
)
axes_flat = axes.flatten()

# Color scale across all plots
vmin_val, vmax_val = 1900, 2100

plot_order = ["BR_A", "LM_A", "SCG_A", "BR_B", "LM_B", "SCG_B"]
subplot_labels = ["a)", "b)", "c)", "d)", "e)", "f)"]  # subplot annotations

sc_list = []
for i, (ax, key) in enumerate(zip(axes_flat, plot_order)):
    gdf, colname = datasets[key]

    # Background
    ax.set_extent([-125, -60, 25, 50], crs=projection)
    ax.coastlines(linewidth=1)
    ax.add_feature(cfeature.STATES, edgecolor="black", linewidth=0.5)

    # --- Interpolation to grid ---
    lon = gdf["Longitude"].values
    lat = gdf["Latitude"].values
    values = gdf[colname].values

    grid_lon, grid_lat = np.meshgrid(
        np.linspace(lon.min(), lon.max(), 200),
        np.linspace(lat.min(), lat.max(), 200)
    )
    grid_values = griddata(
        (lon, lat), values, (grid_lon, grid_lat), method="linear"
    )

    # Spatial field
    im = ax.pcolormesh(
        grid_lon, grid_lat, grid_values,
        cmap="Reds", vmin=vmin_val, vmax=vmax_val,
        transform=ccrs.PlateCarree()
    )
    sc_list.append(im)

    # --- Overlay NOAA GML station points ---
    ax.scatter(
        stations_gdf["Longitude"], stations_gdf["Latitude"],
        c=stations_gdf["CH4"].values, cmap="Reds", vmin=vmin_val, vmax=vmax_val,
        transform=ccrs.PlateCarree(),
        marker="o", s=120, edgecolor="gray", linewidth=1.2,
        zorder=5,
        label="Observational Sites" if i == len(plot_order)-1 else "_nolegend_"
    )

    # --- Add subplot annotation slightly upward ---
    x_text = -124
    y_text = ax.get_ylim()[1] + 1.0  # slightly above top
    ax.text(x_text, y_text, subplot_labels[i], fontsize=20, fontweight="bold", color="black")

    # Gridlines
    gl = ax.gridlines(crs=projection, draw_labels=True, linewidth=1)
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 20, "weight": "bold"}
    gl.ylabel_style = {"size": 20, "weight": "bold"}

# --- Add row labels ---
row_labels = ["BR", "LM", "SCG"]
for j, label in enumerate(row_labels):
    axes_flat[j*2].text(-140, 37.5, label, fontsize=24, fontweight="bold", rotation=90, va='center')

# --- Titles for columns ---
axes_flat[0].set_title("Set-A", fontsize=24, fontweight="bold")
axes_flat[1].set_title("Set-B", fontsize=24, fontweight="bold")

# --- Shared colorbar ---
cbar_ax = fig.add_axes([0.92, 0.25, 0.02, 0.5])
cbar = fig.colorbar(sc_list[0], cax=cbar_ax, orientation="vertical")
cbar.set_label(r'CH$_4$ (ppb)', fontsize=22, fontweight="bold", labelpad=-120)
cbar.ax.tick_params(labelsize=22)
for label in cbar.ax.yaxis.get_ticklabels():
    label.set_weight("bold")

# --- Legend ---
axes_flat[-1].legend(loc="lower right", fontsize=14, frameon=True).get_texts()[0].set_fontweight("bold")

# --- Layout adjustments: reduced vertical spacing ---
plt.tight_layout(rect=[0, 0, 0.9, 1])
plt.subplots_adjust(hspace=0.0)  # reduce space between rows

# --- Save figure ---
plt.savefig("Spatial_Methane_with_Stations_Annotated.png", dpi=600, bbox_inches="tight")
plt.show()
