"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; maps from data/site.json and data/paintings.json. Charts and maps only: no paintings."""
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
HALO = [pe.withStroke(linewidth=3.5, foreground=SEA)]
HALOL = [pe.withStroke(linewidth=3.5, foreground=LAND)]
S, P, N, G = pdata()
GC = [GCOL[g] for g in KEEP_GENRES]
PLACES = S["places"]; PAINTERS = S["painters"]


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def gleg(extra=()):
    return [Line2D([], [], ls="", marker="o", ms=9, mfc=c, mec="#fff", label=f"mostly {g}") for g, c in zip(KEEP_GENRES, GC)] + list(extra)


# ---------- world map of painted places ----------
K = 3.2e5 / np.sqrt(N.max())
fig = plt.figure(figsize=(12, 6.6), facecolor=BG); ax = fig.add_axes([0, .05, 1, .87])
outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, ec=BG)
o = np.argsort(-N)
x, y = proj([PLACES[i][2] for i in o], [PLACES[i][1] for i in o])
ax.scatter(x, y, s=[max(3, (K * np.sqrt(N[i]) / 2.2e4) ** 2) for i in o], c=[GC[G[i]] for i in o], alpha=.8, lw=.4, edgecolor="#fff", zorder=3)
LAB = {"Seine": (-2.2e6, 2e5, "right"), "Lofoten": (5e5, 4e5, "left"), "Venice": (9e5, -7e5, "left"), "Rio de Janeiro": (5e5, -4e5, "left"),
       "Hudson River": (6e5, -5e5, "left"), "California": (-6e5, -3e5, "right"), "Atlantic Ocean": (5e5, 0, "left")}
for i in range(60):
    nm = PLACES[i][0]
    if nm in LAB:
        dx, dy, ha = LAB[nm]; xx, yy = proj(PLACES[i][2], PLACES[i][1])
        ax.text(float(xx) + dx, float(yy) + dy, f"{nm}\n{N[i]}", ha=ha, va="center", fontsize=9.5, color=FG, path_effects=HALO, zorder=6)
fig.text(.02, .955, f"{R['source']['n']:,} catalogued landscape, marine and city paintings and the {R['source']['places']:,} places they show; circle area = paintings", fontsize=11, color=FG)
fig.legend(handles=gleg(), loc="lower center", ncol=3, frameon=False, fontsize=10, bbox_to_anchor=(.5, -.005))
both(fig, "map")

# ---------- Europe ----------
fig = plt.figure(figsize=(12, 10.5), facecolor=BG); ax = fig.add_axes([0, .04, 1, .9]); ax.set_facecolor(SEA)
ext = (2.65e6, 5.45e6, 1.45e6, 5.15e6)
europe(ax, ext=(2.55e6, 5.55e6, 1.45e6, 4.95e6), ec=BG)
ax.add_patch(plt.Rectangle((2.55e6, 1.45e6), 3e6, 3.5e6, fc=SEA, ec="none", zorder=0))
K2 = 1.15e5 / np.sqrt(N.max())
xs, ys = LAEA.transform([PLACES[i][2] for i in o], [PLACES[i][1] for i in o])
ax.scatter(xs, ys, s=[max(4, (K2 * np.sqrt(N[i]) / 4.2e3) ** 2) for i in o], c=[GC[G[i]] for i in o], alpha=.78, lw=.4, edgecolor="#fff", zorder=3)
ELAB = {"Seine": (-1.2e5, -1.1e5, "right"), "Paris": (1.0e5, -1.0e5, "left"), "Venice": (1.0e5, -.6e5, "left"), "River Thames": (-.6e5, .9e5, "right"),
        "Dordrecht": (1.1e5, -.4e5, "left"), "Mount Vesuvius": (.9e5, -.6e5, "left"), "Tivoli": (1.0e5, .7e5, "left"), "Étretat": (-.9e5, -.9e5, "right"),
        "Rome": (-1.0e5, -.5e5, "right"), "Black Forest": (1.1e5, .1e5, "left"), "Rhine": (1.1e5, -.8e5, "left"), "Oslofjord": (-1e5, -.4e5, "right")}
for i in range(80):
    nm = PLACES[i][0]
    if nm in ELAB:
        dx, dy, ha = ELAB[nm]; xx, yy = LAEA.transform(PLACES[i][2], PLACES[i][1])
        if not (2.55e6 < xx < 5.55e6 and 1.45e6 < yy < 4.95e6): continue
        ax.text(xx + dx, yy + dy, f"{nm} {N[i]}", ha=ha, va="center", fontsize=9.5, color=FG, path_effects=HALOL, zorder=6)
fig.text(.02, .965, "Western Europe: the paintings' places close up (Lofoten and Nordland lie further north); circle area = paintings", fontsize=11, color=FG)
fig.legend(handles=gleg(), loc="lower center", ncol=3, frameon=False, fontsize=10, bbox_to_anchor=(.5, 0))
both(fig, "europe", blog=False)

# ---------- most painted places ----------
D = R["top"][:20][::-1]
fig = plt.figure(figsize=(12, 7.2), facecolor=BG); ax = fig.add_axes([.2, .1, .74, .84]); ax.set_facecolor(BG)
ax.barh([d["label"] for d in D], [d["n"] for d in D], color=[KCOL[d["kind"]] for d in D], height=.7)
for i, d in enumerate(D): ax.text(d["n"] + 2, i, f"{d['n']}  ({d['top_painter'] or 'unknown painter'} {d['top_painter_n']})", va="center", fontsize=9, color=FG)
ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=10.5); ax.set_xlim(0, 330)
fig.legend(handles=[Patch(color=c, label=n) for k, n, c in KINDS], loc="lower center", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(.55, -.005))
fig.text(.02, .965, "The 20 most painted places: paintings, and the painter with the most of them", fontsize=11, color=FG)
both(fig, "top")

# ---------- painters' favourite places ----------
FR = R["fav_rows"]
tones = ["#8E3A17", "#C2582B", "#E3A07F"]
fig = plt.figure(figsize=(12, 7.6), facecolor=BG); ax = fig.add_axes([.21, .04, .77, .88]); ax.set_facecolor(BG)
for i, d in enumerate(FR):
    y = len(FR) - 1 - i; x = 0
    for k, (nm, v) in enumerate(d["top"]):
        w = v / d["n"]; ax.barh(y, w, left=x, color=tones[k], height=.72, ec=BG, lw=.8)
        tx = f"{nm} {v}"
        if w > len(tx) * .0105: ax.text(x + .008, y, tx, va="center", fontsize=8.6, color="#fff" if k < 2 else "#2a1a12")
        x += w
    ax.barh(y, 1 - x, left=x, color=RULE, height=.72)
ax.set_yticks(range(len(FR))); ax.set_yticklabels([f"{d['name']} ({d['n']})" for d in FR][::-1], fontsize=10)
ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0", "25%", "50%", "75%", "100%"], fontsize=9); spines(ax); ax.tick_params(axis="y", length=0)
fig.text(.02, .955, "Share of each painter's catalogued paintings showing their three most painted places (dark to light); grey: everywhere else", fontsize=10.5, color=FG)
both(fig, "painters")

# ---------- distance by period ----------
rows = [{"name": "All periods", "n": R["dist"]["n"], "bins": R["dist"]["all"], "median": R["dist"]["median"]}] + [dict(d, name=d["name"][0].upper() + d["name"][1:]) for d in R["dist_cent"] if d["n"] >= 30]
C6 = ["#2E5418", "#5E8C3A", "#A9C98A", "#CDB6E0", "#8F66B5", "#4B2A6B"]
fig = plt.figure(figsize=(12, 5.2), facecolor=BG); ax = fig.add_axes([.17, .2, .8, .72]); ax.set_facecolor(BG)
for i, d in enumerate(rows):
    y = len(rows) - 1 - i; x = 0
    for k, v in enumerate(d["bins"]):
        ax.barh(y, v, left=x, color=C6[k], height=.7, ec=BG, lw=.8)
        if v > 4.5: ax.text(x + v / 2, y, f"{v:.0f}%", ha="center", va="center", fontsize=9, color="#fff" if k in (0, 1, 4, 5) else FG)
        x += v
ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{d['name']}\nmedian {d['median']:,} km" for d in rows][::-1], fontsize=9.5)
ax.set_xlim(0, 100); ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
fig.legend(handles=[Patch(color=c, label=b) for c, b in zip(C6, R["dist"]["bins"])], loc="lower center", ncol=6, frameon=False, fontsize=9, bbox_to_anchor=(.55, 0))
fig.text(.02, .95, "Distance from the painter's birthplace to the place painted, share of paintings by period", fontsize=11, color=FG)
both(fig, "distance")

# ---------- countries by period ----------
KC = ["Netherlands", "Italy", "France", "United Kingdom", "United States", "Norway", "Germany", "Belgium", "Other"]
CC = ["#E0A11B", "#2E9A8C", "#2F6DA8", "#C8322B", "#7B57A8", "#5E8C3A", "#3B3B3B", "#D46A8C", "#C9C2B6"]
D = [d for d in R["cents"] if d["n"] >= 30]
fig = plt.figure(figsize=(12, 6.4), facecolor=BG); ax = fig.add_axes([.06, .2, .92, .72]); ax.set_facecolor(BG)
for i, d in enumerate(D):
    acc = 0
    for k, c in zip(KC, CC):
        v = max(0, d[k]); ax.bar(i, v, bottom=acc, color=c, width=.72, ec=BG, lw=.8)
        if v > 4.5: ax.text(i, acc + v / 2, f"{v:.0f}%", ha="center", va="center", fontsize=9.5, color=FG if k in ("Other", "Netherlands") else "#fff")
        acc += v
ax.set_xticks(range(len(D))); ax.set_xticklabels([f"{d['name'][0].upper() + d['name'][1:]}\n{d['n']:,} paintings" for d in D], fontsize=10)
ax.set_ylim(0, 100); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0", "25%", "50%", "75%", "100%"]); spines(ax)
fig.legend(handles=[Patch(color=c, label=k) for k, c in zip(KC, CC)], loc="lower center", ncol=9, frameon=False, fontsize=9, bbox_to_anchor=(.52, 0), handlelength=1.2, columnspacing=1.1)
fig.text(.02, .95, "Where the painted places are: share of each period's paintings by country (today's borders)", fontsize=11, color=FG)
both(fig, "periods")

# ---------- journeys: four painters in Europe, two worldwide ----------
JP = [("Claude Monet", "#2F6DA8", 0), ("J. M. W. Turner", "#C2582B", 0), ("Giovanni Antonio Canal", "#B8862B", 0), ("Anna Boberg", "#5E8C3A", 0),
      ("Marianne North", "#7A4E9E", 1), ("Albert Bierstadt", "#C8322B", 1)]
NMS = {"Giovanni Antonio Canal": "Canaletto"}
fig = plt.figure(figsize=(12, 6.6), facecolor=BG)
a0 = fig.add_axes([.0, .1, .42, .8]); a0.set_facecolor(SEA)
europe(a0, ext=(2.75e6, 5.25e6, 1.5e6, 5.4e6), ec=BG); a0.add_patch(plt.Rectangle((2.75e6, 1.5e6), 2.5e6, 3.9e6, fc=SEA, ec="none", zorder=0)); a0.axis("on")
for sp in a0.spines.values(): sp.set_color("#C9CDD0")
a0.set_xticks([]); a0.set_yticks([])
a1 = fig.add_axes([.43, .1, .57, .8]); outline(a1, fc=SEA, ec="#C9CDD0"); world(a1, ec=BG)
JL = {}
for nm, col, w in JP:
    ax = (a0, a1)[w]; T = (lambda lo, la: LAEA.transform(lo, la)) if w == 0 else proj
    j = next(k for k, p in enumerate(PAINTERS) if p[0] == nm); pa = PAINTERS[j]; seen = set()
    for r in P:
        if r[2] != j: continue
        for pi in r[7]:
            if pi in seen or PLACES[pi][6]: continue
            seen.add(pi); lo, la = gc_pts(pa[2], pa[1], PLACES[pi][2], PLACES[pi][1]); xx, yy = T(lo, la)
            ax.plot(xx, yy, color=col, lw=1.1, alpha=.75, zorder=3)
            ex, ey = T(PLACES[pi][2], PLACES[pi][1]); ax.scatter([ex], [ey], s=10, c=col, zorder=4, lw=0)
    bx, by = T(pa[2], pa[1]); ax.scatter([bx], [by], s=70, c=col, ec="#fff", lw=1.5, zorder=6)
    JL[nm] = len(seen)
a0.set_xlim(2.75e6, 5.25e6); a0.set_ylim(1.5e6, 5.4e6)
fig.legend(handles=[Line2D([], [], color=c, lw=2.2, marker="o", mfc=c, mec="#fff", ms=8, label=f"{NMS.get(n, n)}: {JL[n]} places") for n, c, _ in JP], loc="lower center", ncol=3, frameon=False, fontsize=10, bbox_to_anchor=(.5, -.005))
fig.text(.02, .955, "Painters' journeys: lines from the birthplace (large dot) to every place painted. Left: Europe; right: the world", fontsize=11, color=FG)
both(fig, "journeys")

# ---------- collections ----------
D = R["colls"][:12][::-1]
nm = lambda s: s.replace("National Library of Wales Framed works of art collection", "National Library of Wales, framed works").replace("National Museum of Art, Architecture and Design", "National Museum, Oslo").replace("Department of Paintings of the Louvre", "Louvre, Department of Paintings")
fig = plt.figure(figsize=(12, 6.4), facecolor=BG); ax = fig.add_axes([.3, .1, .66, .82]); ax.set_facecolor(BG)
ax.barh([nm(d["name"]) for d in D], [d["n"] for d in D], color=GOLD, alpha=.45, height=.7)
ax.barh([nm(d["name"]) for d in D], [d["top_painter_n"] for d in D], color=GOLD, height=.7)
for i, d in enumerate(D): ax.text(d["n"] + 6, i, f"{d['n']}  (top painter: {d['top_painter']} {d['top_painter_n']})", va="center", fontsize=9, color=FG)
ax.set_xlim(0, 900); ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=10)
fig.text(.02, .955, f"The 12 collections with the most mapped paintings (of {R['coll']['n']:,}); dark: paintings by the collection's leading painter", fontsize=11, color=FG)
both(fig, "collections")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.40, .12, .6, .82]); ax.set_facecolor(BG)
europe(ax, ext=(2.55e6, 5.4e6, 1.45e6, 5.6e6), ec=BG, lw=.3)
ax.add_patch(plt.Rectangle((2.55e6, 1.45e6), 2.85e6, 4.15e6, fc=SEA, ec="none", zorder=0))
ax.scatter(xs, ys, s=[max(2, (K2 * np.sqrt(N[i]) / 4.6e3) ** 2) for i in o], c=[GC[G[i]] for i in o], alpha=.8, lw=.3, edgecolor="#fff", zorder=3)
fig.text(.04, .84, "Painted", fontproperties=DISP, fontsize=64, color=HOT, va="top")
fig.text(.04, .64, "places", fontproperties=DISP, fontsize=64, color=COOL, va="top")
fig.text(.04, .43, f"{R['source']['n']:,} landscape, marine and city\npaintings and the {R['source']['places']:,} places\nthey show. The Seine leads with {R['places']['Q1471']['n']}.", fontproperties=SERP, fontsize=15, color=FG, va="top", linespacing=1.35)
fig.text(.04, .06, "maps.tristanhotham.com/painted-places", fontsize=11, color=MUT)
fig.legend(handles=gleg(), loc="lower right", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(.99, .0))
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
