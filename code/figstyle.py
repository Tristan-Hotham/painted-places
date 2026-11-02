"""House style for static figures (as in the rocket-launches study): fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, and Natural Earth outlines in the Equal Earth projection."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#675F55", "axes.labelcolor": "#211E1A",
                     "xtick.color": "#675F55", "ytick.color": "#675F55"})
BG, FG, MUT, LAND, RULE, SEA = "#F7F4EE", "#211E1A", "#675F55", "#E6E0D2", "#DED7CA", "#EEF1F1"
HOT, COOL, GREEN, GOLD, LINE, NAVY = "#C2582B", "#2F6DA8", "#5E8C3A", "#B8862B", "#7A4E9E", "#2A3550"
KCOL = {k: c for k, _, c in KINDS}; KCOL["other"] = "#8C8478"

EE = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in W["features"]:
    for ring in rings(f["geometry"]):
        x, y = EE.transform(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
        SHAPES.append((f["properties"]["iso"], np.column_stack([x, y]), ring))
WORLD_EXT = (-17.0e6, 17.0e6, -8.75e6, 8.7e6)


def world(ax, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1, skip_ata=False):
    for iso, p, _ in SHAPES:
        if skip_ata and iso == "ATA":
            continue
        ax.add_patch(MPoly(p, closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def outline(ax, fc=None, lw=.8, ec=MUT, z=0):
    """Equal Earth globe outline."""
    lat = np.linspace(-90, 90, 181)
    xl, yl = EE.transform(np.full_like(lat, -180), lat); xr, yr = EE.transform(np.full_like(lat, 180), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]), closed=True, fc=fc or "none", ec=ec, lw=lw, zorder=z))


def proj(lon, lat):
    return EE.transform(np.asarray(lon), np.asarray(lat))


def circle_ll(lat0, lon0, r_km, n=180):
    """Points on a small circle of radius r_km around (lat0, lon0)."""
    d = r_km / 6371.0; p0, l0 = np.radians(lat0), np.radians(lon0); b = np.linspace(0, 2 * np.pi, n)
    p = np.arcsin(np.sin(p0) * np.cos(d) + np.cos(p0) * np.sin(d) * np.cos(b))
    l = l0 + np.arctan2(np.sin(b) * np.sin(d) * np.cos(p0), np.cos(d) - np.sin(p0) * np.sin(p))
    return np.degrees(p), (np.degrees(l) + 540) % 360 - 180


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


LAEA = Transformer.from_crs(4326, 3035, always_xy=True)


def europe(ax, ext=(2.45e6, 6.6e6, 1.35e6, 5.45e6), land=LAND, ec="#FFFFFF", lw=.4):
    """Natural Earth outlines in the European LAEA projection (EPSG:3035)."""
    from shapely.geometry import Polygon as _P, box as _b
    for iso, _, ring in SHAPES:
        if ring[:, 0].max() < -45 or ring[:, 0].min() > 75 or ring[:, 1].max() < 25: continue
        g = _P(ring).buffer(0).intersection(_b(-45, 25, 75, 84))      # clip in degrees, then project
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.geom_type != "Polygon" or part.is_empty: continue
            xy = np.array(part.exterior.coords); x, y = LAEA.transform(xy[:, 0], xy[:, 1])
            ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=land, ec=ec, lw=lw, zorder=1))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def pdata():
    """Places with counts and dominant genre, painters, paintings (from data/site.json and data/paintings.json)."""
    S = jload(f"{DATA}/site.json"); P = jload(f"{DATA}/paintings.json")["rows"]
    n = np.zeros(len(S["places"]), int); g = np.zeros((len(S["places"]), 3), int)
    for r in P:
        for pi in r[7]:
            n[pi] += 1
            for b in range(3):
                if r[4] & (1 << b): g[pi, b] += 1
    return S, P, n, g.argmax(1)


def gc_pts(lon1, lat1, lon2, lat2, k=48):
    r = np.pi / 180; l1, p1, l2, p2 = lon1 * r, lat1 * r, lon2 * r, lat2 * r
    d = 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))
    if d < 1e-6: return np.array([lon1, lon2]), np.array([lat1, lat2])
    f = np.linspace(0, 1, k); A = np.sin((1 - f) * d) / np.sin(d); B = np.sin(f * d) / np.sin(d)
    x = A * np.cos(p1) * np.cos(l1) + B * np.cos(p2) * np.cos(l2); y = A * np.cos(p1) * np.sin(l1) + B * np.cos(p2) * np.sin(l2); z = A * np.sin(p1) + B * np.sin(p2)
    return np.degrees(np.arctan2(y, x)), np.degrees(np.arctan2(z, np.sqrt(x * x + y * y)))
