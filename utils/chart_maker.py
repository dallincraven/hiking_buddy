import os
import uuid
import matplotlib.pyplot as plt
import seaborn as sns 
from pathlib import Path
sns.set(style='whitegrid', rc={"figure.figsize":(9,4)})

def make_elevation_chart(df, charts_dir, job_id):
    path = charts_dir / f"elev_{job_id}.png"
    if 'cum_km' not in df.columns or 'elevation' not in df.columns:
        return None
    plt.figure()
    plt.plot(df['cum_km'], df['elevation'], linewidth=1.5)
    plt.fill_between(df['cum_km'], df['elevation'], alpha=0.1)
    plt.xlabel("Distance (km)")
    plt.ylabel("elevation (m)")
    plt.title("Elevation profile")
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight',dpi=150)
    plt.close()
    return path

def make_pace_chart(df, charts_dir, job_id):
    path = charts_dir / f"pace_{job_id}.png"
    if 'cum_km' not in df.columns or 'speed_kmh' not in df.columns:
        return None
    plt.figure()
    if 'speed_kmh' in df:
        y=df['speed_kmh'].rolling(window=5, min_periods=1).mean()
    else:
        y=df['pace_m_per_s'].rolling(window=5, min_periods=1).mean()
    
    plt.plot(df['cum_km'], y, linewidth=1.2)
    plt.xlabel("Distance (km)")
    plt.ylabel("Speed (km/h)")
    plt.title("Speed over route (smoothed)")
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight',dpi=150)
    plt.close()
    return path