"""r/dataisbeautiful collage for painted-places: 2400 x 3200 px, light background. Charts and maps only, no paintings.
Numbers from data/results.json. Map labels sit on open sea with a halo; a short leader joins a label to its circle when
needed, and no leader may cross another label."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import matplotlib.patheffects as pe
from matplotlib.patches import Patch, Circle
from matplotlib.lines import Line2D
from shapely.geometry import shape as _shape, box as _box, Point as _Pt, LineString as _LS, Polygon as _Poly
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep as _prep

R = jload(f"{DATA}/results.json")
BGc = "#F8F6F1"; SEAc = "#DAE5EC"; LANDc = "#E9E2D1"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
S, P, N, G = pdata(); PLACES = S["places"]; GC = [GCOL[g] for g in KEEP_GENRES]
src, d, PL = R["source"], R["dist"], R["places"]
DC = {x["c"]: x for x in R["dist_cent"]}; CT = {x["c"]: x for x in R["cents"]}

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, .985, "Where the landscape painters painted", fontproperties=DISP, fontsize=42, color=FG, va="top")
fig.text(.045, .943, f"{src['n']:,} landscape, sea and city paintings catalogued in Wikidata, and the {src['places']:,} real places they show.\n"
         f"The most painted place on Earth is a river: the Seine, {PL['Q1471']['n']} paintings by {R['seine']['painters']} painters. Half of all paintings\n"
         f"were made more than {d['median']} km from the painter's birthplace.", fontproperties=SERP, fontsize=13.5, color=FG, va="top", linespacing=1.45)

# ---- Europe map
EXT = (1.75e6, 6.85e6, 1.42e6, 5.32e6)
ax = fig.add_axes([.045, .36, .91, .505]); ax.set_facecolor(SEAc)
europe(ax, ext=EXT, land=LANDc, ec=BGc, lw=.5)
ax.add_patch(plt.Rectangle((EXT[0], EXT[2]), EXT[1] - EXT[0], EXT[3] - EXT[2], fc=SEAc, ec="none", zorder=0)); ax.axis("on")
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_color("#C9CDD0")
K = 1.25e5 / np.sqrt(N.max())
o = np.argsort(-N)
xs, ys = LAEA.transform([PLACES[i][2] for i in o], [PLACES[i][1] for i in o])
rr = [max(4e3, K * np.sqrt(N[i])) for i in o]
inside = [(EXT[0] < x < EXT[1] and EXT[2] < y < EXT[3]) for x, y in zip(xs, ys)]
for x, y, r, i, ok in zip(xs, ys, rr, o, inside):
    if ok: ax.add_patch(Circle((x, y), r, fc=GC[G[i]], ec="#fff", lw=.35 if r < 2e4 else .8, alpha=.85, zorder=3))
# land (buffered) and circles for the label checks
_land = []
for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
    g = _shape(f["geometry"]); gs = g.geoms if g.geom_type == "MultiPolygon" else [g]
    for q in gs:
        q = q.buffer(0).intersection(_box(-45, 25, 75, 84))          # clip in degrees first, then project
        for part in (q.geoms if q.geom_type in ("MultiPolygon", "GeometryCollection") else [q]):
            if part.geom_type != "Polygon" or part.is_empty: continue
            xy = np.array(part.exterior.coords); x, y = LAEA.transform(xy[:, 0], xy[:, 1]); _land.append(_Poly(np.column_stack([x, y])).buffer(0))
LAND = unary_union(_land).buffer(1.2e4); LANDP = _prep(LAND)
BUB = unary_union([_Pt(x, y).buffer(max(r, 9e3)) for x, y, r, ok in zip(xs, ys, rr, inside) if ok and r > 9e3])
fig.canvas.draw(); REN = fig.canvas.get_renderer()
PLACED, LINES = [], []


def tbox(t):
    bb = t.get_window_extent(REN)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0 - 4, bb.y0 - 3], [bb.x1 + 4, bb.y1 + 3]])
    return _box(x0, y0, x1, y1)


def bad(b):
    if not _box(EXT[0] + 2e4, EXT[2] + 2e4, EXT[1] - 2e4, EXT[3] - 2e4).contains(b): return True
    return LANDP.intersects(b) or BUB.intersects(b) or any(b.intersects(o) for _, _, o in PLACED) or any(b.intersects(l) for _, l in LINES)


def place(q, s, pref, ha="center", lead_gap=4e4, maxr=32, step=2.5e4, col=FG, size=10.5, maxlead=7e5):
    i = next(k for k, p in enumerate(PLACES) if p[7] == q); tx, ty = LAEA.transform(PLACES[i][2], PLACES[i][1]); tr = max(4e3, K * np.sqrt(N[i]))
    t = ax.text(0, 0, s, ha=ha, va="center", fontsize=size, color=col, family=MONO, linespacing=1.12, zorder=10, path_effects=HALO, fontweight="medium")
    x0, y0 = LAEA.transform(*pref)
    grid = [(tx + dx * step, ty + dy * step) for dx in range(-maxr, maxr + 1) for dy in range(-maxr, maxr + 1)]
    grid.sort(key=lambda q: np.hypot(q[0] - tx, q[1] - ty) + .35 * np.hypot(q[0] - x0, q[1] - y0))
    cands = [(x0, y0)] + grid
    for x, y in cands:
        t.set_position((x, y)); b = tbox(t)
        if bad(b): continue
        c = _Pt(tx, ty); ln = None
        if b.distance(c) - tr > lead_gap:
            pb, _ = nearest_points(b, c); dd = np.hypot(pb.x - c.x, pb.y - c.y)
            ln = _LS([(pb.x, pb.y), (c.x + (pb.x - c.x) * tr / dd, c.y + (pb.y - c.y) * tr / dd)])
            if ln.length > maxlead or any(ln.intersects(o) for _, _, o in PLACED) or any(ln.intersects(l) for _, l in LINES): continue
        PLACED.append((q, t, b))
        if ln is not None:
            LINES.append((q, ln)); ax.plot(*ln.xy, color=FG, lw=.8, zorder=9)
        return
    t.remove(); print("SKIPPED", s.replace(chr(10), " ")); return
    raise RuntimeError("no clean spot for " + s)


place("Q1471", f"SEINE\n{PL['Q1471']['n']}", (-3.5, 50.6))
place("Q90", f"PARIS\n{PL['Q90']['n']}", (-5.5, 47.3), maxr=34, maxlead=8e5)
place("Q186822", f"LOFOTEN {PL['Q186822']['n']}\nNORDLAND {PL['Q50630']['n']}", (8.5, 68.4))
place("Q641", f"VENICE\n{PL['Q641']['n']}", (13.6, 44.4))
place("Q19686", f"THAMES\n{PL['Q19686']['n']}", (2.6, 52.6))
place("Q26421", f"DORDRECHT\n{PL['Q26421']['n']}", (4.0, 54.2))
place("Q159605", f"TIVOLI\n{PL['Q159605']['n']}", (10.6, 41.4))
place("Q290936", f"ÉTRETAT\n{PL['Q290936']['n']}", (-1.5, 51.0))
place("Q667456", f"OSLOFJORD\n{PL['Q667456']['n']}", (8.4, 57.3))
for q, t, b in PLACED:
    assert not LANDP.intersects(b) and not BUB.intersects(b), q
    assert not any(b.intersects(o) for q2, _, o in PLACED if q2 != q), q
for q, l in LINES:
    assert not any(l.intersects(o) for q2, _, o in PLACED if q2 != q), q
print("labels ok:", len(PLACED), "leaders:", [q for q, _ in LINES])
# size key on open sea, bottom left (Atlantic)
kx, ky = LAEA.transform(-19.0, 42.0)
KEYT = []
for j, n in enumerate((10, 50, 200)):
    r = K * np.sqrt(n); xc = kx + j * 1.25e5 + (2e4 if j == 2 else 0)
    ax.add_patch(Circle((xc, ky + r), r, fc="none", ec=FG, lw=.9, zorder=9))
    KEYT.append(ax.text(xc, ky - 4.5e4, f"{n}", ha="center", fontsize=9, color=FG, family=MONO, zorder=10, path_effects=HALO))
KEYT.append(ax.text(kx - 4e4, ky + 2.55e5, "paintings of a place", ha="left", fontsize=9, color=FG, family=MONO, zorder=10, path_effects=HALO))
fig.canvas.draw()
for kt in KEYT:
    assert not LANDP.intersects(tbox(kt)) and not any(tbox(kt).intersects(o) for _, _, o in PLACED), "size key"
ax.legend(handles=[Line2D([], [], ls="", marker="o", ms=10, mfc=c, mec="#fff", label=f"mostly {g}") for g, c in zip(KEEP_GENRES, GC)],
          loc="upper left", frameon=True, facecolor=BGc, edgecolor="#C9CDD0", fontsize=10, borderpad=.7)
fig.text(.045, .352, f"Western Europe, where {R['continent']['Europe']:.0f}% of the paintings look. Circle area = paintings of each place; colour = the genre most of them belong to.",
         fontsize=9.5, color=MUT, family=MONO)

# ---- chart 1: most painted places
a1 = fig.add_axes([.2, .175, .28, .155]); a1.set_facecolor(BGc)
D = R["top"][:10][::-1]
a1.barh([t["label"].replace("River ", "") for t in D], [t["n"] for t in D], color=[KCOL[t["kind"]] for t in D], height=.72)
for k, t in enumerate(D): a1.text(t["n"] + 3, k, str(t["n"]), va="center", fontsize=9.5, color=FG)
a1.set_xlim(0, 270); a1.set_xticks([]); spines(a1); a1.spines["bottom"].set_visible(False); a1.tick_params(axis="y", length=0, labelsize=10)
fig.text(.045, .338, "The 10 most painted places", fontproperties=DISPB, fontsize=15, color=FG)
a1.legend(handles=[Patch(color=c, label=n.split(",")[0]) for k, n, c in KINDS if k != "mountain"], loc="lower right", frameon=False, fontsize=8.2, handlelength=1, bbox_to_anchor=(1.12, 0))

# ---- chart 2: distance from birthplace by period
a2 = fig.add_axes([.64, .175, .32, .155]); a2.set_facecolor(BGc)
rows = [x for x in R["dist_cent"] if x["n"] >= 300]
C6 = ["#2E5418", "#5E8C3A", "#A9C98A", "#CDB6E0", "#8F66B5", "#4B2A6B"]
for k, r_ in enumerate(rows[::-1]):
    x0 = 0
    for b, v in enumerate(r_["bins"]):
        a2.barh(k, v, left=x0, color=C6[b], height=.7, ec=BGc, lw=.6)
        if v > 9: a2.text(x0 + v / 2, k, f"{v:.0f}%", ha="center", va="center", fontsize=8.5, color="#fff" if b in (0, 1, 4, 5) else FG)
        x0 += v
a2.set_yticks(range(len(rows))); a2.set_yticklabels([f"{r_['name']}\nmedian {r_['median']} km" for r_ in rows[::-1]], fontsize=9)
a2.set_xlim(0, 100); a2.set_xticks([]); spines(a2); a2.spines["bottom"].set_visible(False); a2.spines["left"].set_visible(False); a2.tick_params(axis="y", length=0)
fig.text(.53, .338, "How far from the painter's birthplace", fontproperties=DISPB, fontsize=15, color=FG)
fig.legend(handles=[Patch(color=c, label=b.replace(" km", "")) for c, b in zip(C6, d["bins"])], loc="upper left", bbox_to_anchor=(.53, .172), ncol=3, frameon=False, fontsize=8.5, handlelength=1, columnspacing=1)
fig.text(.53, .128, "km from birthplace to the place painted", fontsize=8.5, color=MUT, family=MONO)

# ---- chart 3: country by period
a3 = fig.add_axes([.12, .045, .84, .055]); a3.set_facecolor(BGc)
KC = ["Netherlands", "Italy", "France", "United Kingdom", "United States", "Norway", "Other"]
CC = ["#E0A11B", "#2E9A8C", "#2F6DA8", "#C8322B", "#7B57A8", "#5E8C3A", "#C9C2B6"]
rows3 = [x for x in R["cents"] if x["c"] in (1600, 1700, 1800, 1900)]
for k, r_ in enumerate(rows3[::-1]):
    x0 = 0
    for kk, c in zip(KC, CC):
        v = r_[kk] if kk != "Other" else 100 - sum(r_[q] for q in KC[:-1])
        a3.barh(k, v, left=x0, color=c, height=.72, ec=BGc, lw=.6)
        if v > 7: a3.text(x0 + v / 2, k, f"{kk.replace('United Kingdom', 'UK').replace('United States', 'US')} {v:.0f}%", ha="center", va="center", fontsize=8, color=FG if kk in ("Other", "Netherlands") else "#fff")
        x0 += v
a3.set_yticks(range(len(rows3))); a3.set_yticklabels([r_["name"] for r_ in rows3[::-1]], fontsize=9)
a3.set_xlim(0, 100); a3.set_xticks([]); spines(a3); a3.spines["bottom"].set_visible(False); a3.spines["left"].set_visible(False); a3.tick_params(axis="y", length=0)
fig.text(.045, .112, "From Dutch towns and Italian views to French rivers: country of the painted place, share of each century's paintings", fontproperties=DISPB, fontsize=13, color=FG)
fig.legend(handles=[Patch(color=c, label=k) for k, c in zip(KC, CC)], loc="lower center", bbox_to_anchor=(.5, .012), ncol=7, frameon=False, fontsize=8.5, handlelength=1, columnspacing=1)
fig.text(.045, .006, f"Data: Wikidata (CC0), {src['query_date']}; Natural Earth. Events, ships and the Moon removed. What is catalogued, not every painting. Tristan Hotham · maps.tristanhotham.com/painted-places",
         fontsize=7.0, color=MUT, family=MONO)
out = os.path.join(ROOT, "reddit", "painted_places.png")
fig.savefig(out, dpi=200, facecolor=BGc)
print("collage", out)
