import gpxpy
import pandas as pd
import numpy as np
from datetime import datetime
import math
from pathlib import Path


def haversine_meters(lat1, lon1,lat2,lon2):
    #returns distance in meters
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))

def parse_gpx_to_df(gpx_path):
    with open(gpx_path, 'r') as f:
        gpx = gpxpy.parse(f)
        
    rows = []
    for track in gpx.tracks:
        for seg in track.segments:
            prev_point = None
            total_dist = 0.0
            for point in seg.points:
                t = point.time if point.time else None
                lat = point.latitude
                lon = point.longitude
                ele = point.elevation if point.elevation is not None else float('nan')
                
                if prev_point is not None and prev_point.time and t:
                    dt = (t - prev_point.time).total_seconds()
                    dist = haversine_meters(prev_point.latitude, prev_point.longitude, lat, lon)
                    total_dist += dist
                else:
                    dt = 0.0
                    dist = 0.0
                    
                rows.append({
                    "time": t,
                    "lat": lat,
                    "lon": lon,
                    "elevation": ele,
                    "delta_secs":dist,
                    "cum_dist_m": total_dist
                })
                prev_point = point
    df = pd.DataFrame(rows)
    df['cum_km'] = df['cum_dist_m']/1000.0
    df['pace_m_per_s'] = df['delta_m']/df['delta_secs'].replace(0,pd.NA)
    df['speed_kmh'] = df['pace_m_per_s']*3.6
    return df

