"""Read the Wikidata extracts, keep the landscape, marine and cityscape paintings, keep only the depicted items that are
genuine places on the Earth (rule in common.py), and attach painters' birthplaces, inception years, collections and
Commons image names. Countries for depicted places and birthplaces come from Natural Earth (today's borders).

Outputs (WORK): paintings.pkl (one row per painting), links.pkl (one row per painting and genuine place),
places.pkl (one row per place), painters.pkl, checks.json."""
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

L0 = read_tsv("landscapes.tsv")
P0 = read_tsv("painters.tsv")
D0 = read_tsv("depcoord.tsv")
chk = {"rows": len(L0), "paintings_all": int(L0.w.nunique()), "items_all": int(L0.place.nunique()), "painter_rows": len(P0)}

L = pd.DataFrame({"w": L0.w.map(qid), "title": L0.wLabel.map(label), "q": L0.place.map(qid), "plabel": L0.placeLabel.map(label),
                  "coord": L0.coord, "genre": L0.genre.map(qid).map(GENRES), "painter": L0.painter.map(qid), "pname": L0.painterLabel.map(label),
                  "inception": L0.inception, "img": L0.img, "coll": L0.collLabel.map(label), "links": pd.to_numeric(L0.links, errors="coerce").fillna(0).astype(int)})
assert L.w.ne("").all() and L.q.ne("").all() and L.genre.notna().all(), L[L.genre.isna()].head()
chk["genre_rows"] = L.genre.value_counts().to_dict()

# ---------- genres: keep paintings with at least one landscape genre ----------
gset = L.groupby("w").genre.agg(lambda s: sorted(set(s)))
core = gset[gset.map(lambda g: any(x in KEEP_GENRES for x in g))].index
other = gset[~gset.index.isin(core)]
chk["paintings_core"] = len(core)
chk["set_aside_by_genre"] = len(other)
chk["set_aside_genres"] = other.map(lambda g: " + ".join(g)).value_counts().to_dict()
C = L[L.w.isin(core)].copy()

# ---------- genuine places ----------
items = C.drop_duplicates("q")[["q", "plabel", "coord"]].copy()
items["pt"] = items.coord.map(point)
why = {}
for r in items.itertuples():
    if r.pt is None:
        why[r.q] = "not a point on the Earth (another globe or an unknown value)"
    elif not (-90 <= r.pt[0] <= 90 and -180 <= r.pt[1] <= 180) or (r.pt[0] == 0 and r.pt[1] == 0):
        why[r.q] = "implausible coordinates"
    elif r.q in NONPLACE_QID:
        why[r.q] = NONPLACE_QID[r.q]
flag = items[items.plabel.str.contains(NONPLACE_RE, case=False, regex=True) & ~items.q.isin(why) & ~items.plabel.isin(NONPLACE_OK)]
assert flag.empty, "keyword scan found unlisted items: " + "; ".join(f"{a} {b}" for a, b in zip(flag.q, flag.plabel))
items["why"] = items.q.map(why)
DR = items[items.why.notna()]
C["why"] = C.q.map(why)
pairs = C.drop_duplicates(["w", "q"])
chk["items_core"] = len(items)
chk["items_dropped"] = DR.why.value_counts().to_dict()
chk["items_dropped_n"] = len(DR)
chk["pairs_dropped"] = pairs[pairs.why.notna()].why.value_counts().to_dict()
dropped_pairs = pairs[pairs.why.notna()]
chk["dropped_top"] = dropped_pairs.groupby(["q", "plabel"]).size().sort_values(ascending=False).head(12).reset_index().values.tolist()
moon = items[items.q == "Q405"]
assert len(moon) == 1 and moon.pt.iloc[0] is None                       # the Moon's coordinate is on the lunar globe
G = C[C.why.isna()].copy()
lost = set(core) - set(G.w)
chk["paintings_no_place"] = len(lost)
chk["paintings_mapped"] = int(G.w.nunique())

# ---------- one row per painting ----------
def year(s):
    m = re.match(r"^(-?\d{4})-", s or "")
    return int(m.group(1)) if m else np.nan


def fname(u):
    m = re.search(r"Special:FilePath/(.+?)>?$", u or "")
    return m.group(1) if m else ""


W = G.groupby("w").agg(title=("title", "first"), painter=("painter", "first"), pname=("pname", "first"),
                       inception=("inception", lambda s: sorted(x for x in s if x)[0] if any(s) else ""),
                       img=("img", lambda s: next((x for x in s if x), "")), links=("links", "max"),
                       genres=("genre", lambda s: sorted(set(x for x in s if x in KEEP_GENRES))),
                       colls=("coll", lambda s: sorted(set(x for x in s if x))),
                       n_painters=("painter", lambda s: len(set(x for x in s if x)))).reset_index()
W["year"] = W.inception.map(year)
W["img"] = W.img.map(fname)
W["title"] = W.title.where(W.title != "", "(untitled in English)")
chk["painters_multi"] = int((W.n_painters > 1).sum())
chk["year_known"] = int(W.year.notna().sum()); chk["year_min"] = int(W.year.min()); chk["year_max"] = int(W.year.max())
chk["img"] = int((W.img != "").sum()); chk["coll_known"] = int(W.colls.map(len).gt(0).sum())
chk["no_painter"] = int((W.painter == "").sum())
W["century"] = (np.floor((W.year - 1) / 100) + 1).astype("Int64")

# ---------- places ----------
PL = G.drop_duplicates("q")[["q", "plabel", "coord"]].copy()
PL["lat"] = PL.coord.map(lambda c: point(c)[0]); PL["lon"] = PL.coord.map(lambda c: point(c)[1])
PL["plabel"] = PL.plabel.where(PL.plabel != "", PL.q.map(lambda q: f"{q} (no English label)"))
# countries (today's borders) from Natural Earth 1:10m; a point just offshore takes the nearest country within 30 km
A0 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
A1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]
PP = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
geoms = [shape(f["geometry"]) for f in A0]
FIXN = {"People's Republic of China": "China", "United States Virgin Islands": "US Virgin Islands", "United States of America": "United States",
        "Dhekelia Cantonment": "Cyprus", "Akrotiri Sovereign Base Area": "Cyprus", "Turkish Republic of Northern Cyprus": "Cyprus",
        "United Nations Buffer Zone in Cyprus": "Cyprus", "Republic of the Congo": "Congo"}
cname = [FIXN.get(f["properties"]["NAME_EN"], f["properties"]["NAME_EN"]) for f in A0]
tree = STRtree(geoms)


cont = [f["properties"]["CONTINENT"] for f in A0]


def country(lat, lon, k=None):
    p = Point(lon, lat)
    for i in tree.query(p, predicate="intersects"):
        return (k or cname)[i]
    i = tree.nearest(p)
    d = geoms[i].distance(p) * 111.0 * max(.2, np.cos(np.radians(lat)))
    return (k or cname)[i] if d <= 30 else ""


PL["country"] = [country(a, b) for a, b in zip(PL.lat, PL.lon)]
PL["continent"] = [country(a, b, cont) for a, b in zip(PL.lat, PL.lon)]
a0q = {f["properties"].get("WIKIDATAID") for f in A0}
ppn = {norm(f["properties"]["name"]) for f in PP}
a1q = {f["properties"].get("wikidataid") for f in A1 if norm(f["properties"]["name"]) not in ppn}
PL["broad"] = (PL.q.isin(a0q) | PL.q.isin(a1q) | PL.q.isin(BROAD_EXTRA) | PL.plabel.str.contains(BROAD_RE, regex=True)).astype(int)
PL["kind"] = PL.q.map(KIND).fillna("other")
chk["places"] = len(PL); chk["places_broad"] = int(PL.broad.sum()); chk["places_sea"] = int((PL.country == "").sum())

# ---------- painters ----------
P = pd.DataFrame({"painter": P0.painter.map(qid), "nat": P0.natLabel.map(label), "pt": P0.bcoord.map(point)})
P = P[P.painter != ""]
bp = P[P.pt.notna()].sort_values("painter").groupby("painter").pt.first()
nat = P[P.nat != ""].groupby("painter").nat.agg(lambda s: "; ".join(sorted(set(s))))
PA = W[W.painter != ""].groupby("painter").agg(pname=("pname", "first"), n=("w", "size")).reset_index()
PA["blat"] = PA.painter.map(lambda q: bp[q][0] if q in bp.index else np.nan)
PA["blon"] = PA.painter.map(lambda q: bp[q][1] if q in bp.index else np.nan)
PA["citizenship"] = PA.painter.map(nat).fillna("")
PA["bcountry"] = [country(a, b) if not np.isnan(a) else "" for a, b in zip(PA.blat, PA.blon)]
PA["pname"] = PA.pname.where(PA.pname != "", PA.painter)
chk["painters"] = len(PA); chk["painters_birth"] = int(PA.blat.notna().sum())
chk["painters_birth_paintings"] = int(PA[PA.blat.notna()].n.sum())

# ---------- explicit coordinates of the depicted place (P9149), as a check ----------
DC = pd.DataFrame({"w": D0.w.map(qid), "title": D0.wLabel.map(label), "pt": D0.coord.map(point), "pname": D0.painterLabel.map(label)})
dchk = []
for r in DC.itertuples():
    sub = G[G.w == r.w].drop_duplicates("q")
    for s in sub.itertuples():
        la, lo = point(s.coord)
        dchk.append({"title": r.title, "painter": r.pname, "place": s.plabel, "km": round(float(gc_km(r.pt[0], r.pt[1], la, lo)), 1)})
chk["depcoord"] = dchk
chk["depcoord_n"] = len(DC)

LK = G.drop_duplicates(["w", "q"])[["w", "q"]].reset_index(drop=True)
W.to_pickle(f"{WORK}/paintings.pkl"); LK.to_pickle(f"{WORK}/links.pkl"); PL.drop(columns=["coord"]).to_pickle(f"{WORK}/places.pkl"); PA.to_pickle(f"{WORK}/painters.pkl")
DR[["q", "plabel", "coord", "why"]].to_pickle(f"{WORK}/dropped_items.pkl")
dropped_pairs[["w", "q", "plabel", "why"]].to_pickle(f"{WORK}/dropped_pairs.pkl")
jsave(chk, f"{WORK}/checks.json", indent=1)
print(json.dumps({k: v for k, v in chk.items() if k not in ("dropped_top",)}, ensure_ascii=False, indent=0)[:3000])
print(chk["dropped_top"])
