"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json, embedded in the page, and data/paintings.json, loaded by it).

Definitions:
  * mapped painting: a landscape, marine or cityscape painting with at least one genuine depicted place (01_clean.py);
  * a painting counts once for each place it depicts in place totals, and with weight 1/k (k = its number of places)
    in country shares, so that every painting adds up to one;
  * date: the year of the painting's inception (P571), grouped by hundred years (the 1800s = 1800 to 1899);
  * distance from birthplace: great circle distance from the painter's place of birth to each depicted place; a
    painting's distance is the median over its places, leaving out broad areas (countries, first-level regions, seas,
    oceans) when it also names a finer place, and leaving the painting out if it names only broad areas;
  * country: today's country (Natural Earth) containing the depicted place or the birthplace."""
import numpy as np, pandas as pd
from common import *

W = pd.read_pickle(f"{WORK}/paintings.pkl")
LK = pd.read_pickle(f"{WORK}/links.pkl")
PL = pd.read_pickle(f"{WORK}/places.pkl").set_index("q")
PA = pd.read_pickle(f"{WORK}/painters.pkl").set_index("painter")
DI = pd.read_pickle(f"{WORK}/dropped_items.pkl")
DP = pd.read_pickle(f"{WORK}/dropped_pairs.pkl")
CHK = jload(f"{WORK}/checks.json")
pc = lambda a, b: round(100 * a / b, 2) if b else None
R = {}
W["cent"] = (W.year // 100 * 100).astype("Int64")
W.loc[W.cent < 1600, "cent"] = 1500          # "before 1600"
W.loc[W.cent >= 2000, "cent"] = 1900         # the few after 2000 join the 1900s ("1900 and later")
CENTS = [1500, 1600, 1700, 1800, 1900]
CNAME = {1500: "before 1600", 1600: "1600s", 1700: "1700s", 1800: "1800s", 1900: "1900 and later"}
N = len(W)

# ---------- source ----------
gen = W.explode("genres").genres.value_counts()
R["source"] = {"rows": CHK["rows"], "paintings_all": CHK["paintings_all"], "items_all": CHK["items_all"], "query_date": QUERY_DATE,
               "core": CHK["paintings_core"], "set_aside": CHK["set_aside_by_genre"], "set_aside_religious": CHK["set_aside_genres"]["religious art"],
               "set_aside_genre": CHK["set_aside_genres"]["genre painting"], "items_core": CHK["items_core"], "items_dropped": CHK["items_dropped_n"],
               "drop_event": CHK["items_dropped"]["event"], "drop_vessel": CHK["items_dropped"]["vessel"],
               "drop_globe": CHK["items_dropped"]["not a point on the Earth (another globe or an unknown value)"],
               "drop_other": CHK["items_dropped"]["movable work of art"] + CHK["items_dropped"]["organisation"],
               "pairs_dropped": int(sum(CHK["pairs_dropped"].values())), "moon": int((DP.q == "Q405").sum()),
               "event_pairs": CHK["pairs_dropped"]["event"], "vessel_pairs": CHK["pairs_dropped"]["vessel"],
               "no_place": CHK["paintings_no_place"], "n": N, "places": len(PL), "places_broad": int(PL.broad.sum()),
               "pairs": len(LK), "multi": int((LK.groupby("w").size() > 1).sum()),
               "painters": int(W.painter.ne("").groupby(W.painter).size().shape[0] - (1 if (W.painter == "").any() else 0)),
               "anon": int((W.painter == "").sum()), "painters_birth": CHK["painters_birth"],
               "year_known": int(W.year.notna().sum()), "year_pct": pc(W.year.notna().sum(), N), "year_min": int(W.year.min()), "year_max": int(W.year.max()),
               "img": int((W.img != "").sum()), "img_pct": pc((W.img != "").sum(), N), "coll_known": int(W.colls.map(len).gt(0).sum()),
               "coll_pct": pc(W.colls.map(len).gt(0).sum(), N), "wiki": int((W.links > 0).sum()), "wiki_pct": pc((W.links > 0).sum(), N),
               "landscape": int(gen.get("landscape", 0)), "marine": int(gen.get("marine", 0)), "cityscape": int(gen.get("cityscape", 0)),
               "countries": int(PL[PL.country != ""].country.nunique()), "depcoord_n": CHK["depcoord_n"],
               "depcoord_delft_km": max(d["km"] for d in CHK["depcoord"] if d["place"] == "Delft"),
               "depcoord_max_km": max(d["km"] for d in CHK["depcoord"]), "query_year": QUERY_YEAR}
s = R["source"]
assert s["n"] == CHK["paintings_mapped"] and s["core"] - s["no_place"] == s["n"]
assert s["painters"] == CHK["painters"]
assert s["moon"] == 138 and s["drop_globe"] == 3
first = W.sort_values("year").iloc[0]
R["source"]["oldest_title"], R["source"]["oldest_painter"], R["source"]["oldest_year"] = first.title, first.pname, int(first.year)

# ---------- places ----------
X = LK.merge(W[["w", "painter", "pname", "year", "cent", "colls", "genres"]], on="w").join(PL[["plabel", "lat", "lon", "country", "broad", "kind"]], on="q")
X["wt"] = 1 / X.groupby("w").q.transform("size")
cnt = X.groupby("q").size().sort_values(ascending=False)
PL["n"] = cnt.reindex(PL.index).fillna(0).astype(int)
PL["painters"] = X[X.painter != ""].groupby("q").painter.nunique().reindex(PL.index).fillna(0).astype(int)
order = list(cnt.index)


def place_row(q):
    a = X[X.q == q]; p = PL.loc[q]
    tp = a[a.painter != ""].pname.value_counts(); tc = a.colls.explode().dropna().value_counts()
    g = a.genres.explode().value_counts()
    return {"q": q, "label": p.plabel, "n": int(len(a)), "painters": int(p.painters), "country": p.country, "kind": p.kind, "broad": int(p.broad),
            "lat": round(float(p.lat), 4), "lon": round(float(p.lon), 4), "anon": int((a.painter == "").sum()),
            "top_painter": tp.index[0] if len(tp) else "", "top_painter_n": int(tp.iloc[0]) if len(tp) else 0,
            "top_painter_pct": pc(tp.iloc[0], len(a)) if len(tp) else 0,
            "top_coll": tc.index[0] if len(tc) else "", "top_coll_n": int(tc.iloc[0]) if len(tc) else 0, "top_coll_pct": pc(tc.iloc[0], len(a)) if len(tc) else 0,
            "first": int(a.year.min()) if a.year.notna().any() else None, "last": int(a.year.max()) if a.year.notna().any() else None,
            "g": {k: int(g.get(k, 0)) for k in KEEP_GENRES}}


TOP = [place_row(q) for q in order[:100]]
R["top"] = TOP[:40]
R["places"] = {r["q"]: r for r in TOP}
miss = [r["label"] for r in TOP if r["q"] not in KIND]
assert not miss, miss                                    # every one of the 100 most painted places has a hand-assigned kind
kd = pd.DataFrame(TOP)
R["kinds"] = [{"kind": k, "name": nm, "places": int((kd.kind == k).sum()), "pairs": int(kd[kd.kind == k].n.sum())} for k, nm, _ in KINDS]
R["kinds_top"] = {r["kind"]: r for r in R["kinds"]}
R["top100_pairs"] = int(kd.n.sum()); R["top100_pct"] = pc(kd.n.sum(), len(LK))
R["single"] = {"places_1": int((PL.n == 1).sum()), "places_1_pct": pc((PL.n == 1).sum(), len(PL)), "places_10": int((PL.n >= 10).sum())}
top20 = kd.head(20)
R["bias_top"] = {"one_painter_half": int((top20.top_painter_pct >= 50).sum()), "one_coll_half": int((top20.top_coll_pct >= 50).sum())}
PLC = R["places"]
assert TOP[0]["label"] == "Seine" and TOP[0]["top_painter"] == "Claude Monet"
assert PLC["Q186822"]["top_painter"] == "Anna Boberg" and PLC["Q50630"]["top_painter"] == "Anna Boberg"
assert PLC["Q42646"]["top_coll"] == "National Trust" and PLC["Q41428"]["top_coll"] == "Brasiliana Iconográfica"
by_genre = {}
for g in KEEP_GENRES:
    a = X[X.genres.map(lambda s: g in s)]; v = a.groupby(["q"]).size().sort_values(ascending=False).head(10)
    by_genre[g] = [{"q": q, "label": PL.loc[q, "plabel"], "n": int(n)} for q, n in v.items()]
R["by_genre"] = by_genre

# ---------- countries of the depicted places ----------
ctry = X.groupby("country").wt.sum().sort_values(ascending=False)
R["countries"] = [{"country": c or "at sea", "n": round(float(v), 1), "pct": pc(v, N)} for c, v in ctry.head(20).items()]
R["eu_pct"] = None

X = X.join(PL[["continent"]], on="q")
cont = X.groupby("continent").wt.sum()
R["continent"] = {(k or "at sea").replace(" ", "_"): pc(v, N) for k, v in cont.items()}
R["continent"]["rest"] = round(100 - R["continent"]["Europe"] - R["continent"]["North_America"], 2)
assert R["continent"]["Europe"] > 70

# ---------- by hundred years ----------
SHOW = ["Netherlands", "Italy", "France", "United Kingdom", "United States", "Norway", "Germany", "Belgium"]
cents = []
for c in CENTS:
    a = X[X.cent == c]; tot = a.drop_duplicates("w").shape[0]; sh = a.groupby("country").wt.sum()
    row = {"c": c, "name": CNAME[c], "n": int(tot)}
    for k in SHOW:
        row[k] = pc(sh.get(k, 0), tot)
    row["Other"] = round(100 - sum(row[k] for k in SHOW), 2)
    top = sh.sort_values(ascending=False).head(3)
    row["top"] = [[k or "at sea", pc(v, tot)] for k, v in top.items()]
    tp = a.groupby("q").size().sort_values(ascending=False).head(5)
    row["top_places"] = [[PL.loc[q, "plabel"], int(n)] for q, n in tp.items()]
    nb = a[a.pname != "Anna Boberg"]; nbt = nb.drop_duplicates("w").shape[0]
    row["Norway_wo_boberg"] = pc(nb.groupby("country").wt.sum().get("Norway", 0), nbt)
    cents.append(row)
R["cents"] = cents
CT = {r["c"]: r for r in cents}
R["undated"] = int(W.year.isna().sum())
assert CT[1600]["top"][0][0] == "Netherlands" and CT[1700]["top"][0][0] == "Italy" and CT[1800]["top"][0][0] == "France" and CT[1900]["top"][0][0] == "France"
assert CT[1900]["Norway"] > CT[1600]["Norway"] * 5

# ---------- painters ----------
WP = W[W.painter != ""]
pn = WP.groupby("painter").size().sort_values(ascending=False)
R["painters_top10_pct"] = pc(pn.head(10).sum(), N); R["painters_top1"] = PA.loc[pn.index[0], "pname"]; R["painters_1"] = int((pn == 1).sum())
R["painters_1_pct"] = pc((pn == 1).sum(), len(pn))
pr = []
for q in pn.index[:30]:
    a = X[X.painter == q]; tp = a.groupby("q").size().sort_values(ascending=False)
    pr.append({"q": q, "name": PA.loc[q, "pname"], "n": int(pn[q]), "places": int(a.q.nunique()), "bcountry": PA.loc[q, "bcountry"],
               "top": [[PL.loc[k, "plabel"], int(v)] for k, v in tp.head(3).items()], "top_pct": pc(tp.iloc[0], pn[q]),
               "first": int(a.year.min()) if a.year.notna().any() else None, "last": int(a.year.max()) if a.year.notna().any() else None})
R["painters_top"] = pr
PNAME = {r["name"]: r for r in pr}


def near(painter_name, lat, lon, km):
    """Paintings by a painter that depict at least one place within km of a point (a city and its rivers, squares, churches)."""
    a = X[X.pname == painter_name].copy(); a["d"] = gc_km(a.lat.values, a.lon.values, lat, lon)
    return int(a[a.d <= km].w.nunique()), int(a.w.nunique())


fav = {}
for key, nm, la, lo, km in (("monet_seine", "Claude Monet", None, None, None), ("turner_venice", "J. M. W. Turner", 45.4375, 12.3358, 8),
                            ("turner_london", "J. M. W. Turner", 51.5072, -0.1276, 20), ("canaletto_london", "Giovanni Antonio Canal", 51.5072, -0.1276, 20),
                            ("canaletto_venice", "Giovanni Antonio Canal", 45.4375, 12.3358, 8), ("guardi_venice", "Francesco Guardi", 45.4375, 12.3358, 8),
                            ("pissarro_paris", "Camille Pissarro", 48.8566, 2.3522, 12), ("goyen_dordrecht", "Jan van Goyen", 51.8133, 4.6901, 6)):
    if la is None:
        a = X[X.pname == nm]; fav[key] = {"n": int(a[a.q == "Q1471"].w.nunique()), "of": int(a.w.nunique())}
    else:
        n, of = near(nm, la, lo, km); fav[key] = {"n": n, "of": of}
for nm, k in (("Claude Monet", "monet"), ("J. M. W. Turner", "turner"), ("Giovanni Antonio Canal", "canaletto"), ("Alfred Sisley", "sisley"), ("Camille Pissarro", "pissarro"),
              ("Jan van Goyen", "goyen"), ("Albert Bierstadt", "bierstadt"), ("Anna Boberg", "boberg"), ("Paul Cézanne", "cezanne"), ("Grandma Moses", "moses"),
              ("Gerrit Adriaenszoon Berckheyde", "berckheyde"), ("Marianne North", "north"), ("Vincent van Gogh", "vangogh"), ("Thomas Cole", "cole")):
    a = X[X.pname == nm]; tp = a.groupby("plabel").size().sort_values(ascending=False)
    fav[k] = {"n": int(a.w.nunique()), "places": int(a.q.nunique()), "top": tp.index[0], "top_n": int(tp.iloc[0]),
              "top2": tp.index[1], "top2_n": int(tp.iloc[1]), "top3": tp.index[2], "top3_n": int(tp.iloc[2])}
R["fav"] = fav
FAVN = ["Anna Boberg", "Albert Bierstadt", "Grandma Moses", "Claude Monet", "Camille Pissarro", "Jan van Goyen", "Maurice Utrillo", "Gerrit Adriaenszoon Berckheyde",
        "Alfred Sisley", "Vincent van Gogh", "Paul Cézanne", "J. M. W. Turner", "Francesco Guardi", "Giovanni Antonio Canal"]
fr = []
for nm in FAVN:
    a = X[X.pname == nm]; tp = a.groupby("plabel").size().sort_values(ascending=False); n = int(a.w.nunique())
    fr.append({"name": {"Giovanni Antonio Canal": "Canaletto", "Gerrit Adriaenszoon Berckheyde": "Gerrit Berckheyde"}.get(nm, nm), "wd_name": nm, "n": n,
               "places": int(a.q.nunique()), "top": [[k, int(v)] for k, v in tp.head(3).items()]})
R["fav_rows"] = fr
rk = {q: i + 1 for i, q in enumerate(order)}
R["rank"] = {"lofoten": rk["Q186822"], "nordland": rk["Q50630"], "cambridge": rk["Q11151861"], "venice": rk["Q641"]}
assert R["rank"]["lofoten"] == 3 and R["rank"]["nordland"] == 5 and R["rank"]["cambridge"] <= 30
tw = X[(X.pname == "J. M. W. Turner") & (X.q == "Q19686")].w.nunique()
assert fav["turner_venice"]["n"] > tw and abs(fav["canaletto_london"]["n"] - fav["canaletto_venice"]["n"]) <= 3
R["top25_water"] = int(sum(1 for r in TOP[:25] if r["kind"] in ("river", "coast")))
assert fav["monet"]["top"] == "Seine" and fav["canaletto"]["top"] == "London" and fav["turner"]["top"] == "Venice"
assert fav["sisley"]["top"] == "Seine" and fav["cezanne"]["top"] == "Montagne Sainte-Victoire" and fav["pissarro"]["top"] == "Pontoise"
sv = X[X.q == "Q1471"]
R["seine"] = {"painters": int(sv.painter[sv.painter != ""].nunique()), "monet": int((sv.pname == "Claude Monet").sum()), "sisley": int((sv.pname == "Alfred Sisley").sum()),
              "pissarro": int((sv.pname == "Camille Pissarro").sum()), "first": int(sv.year.min()), "n1800": int((sv.cent == 1800).sum()), "n1900": int((sv.cent == 1900).sum())}
R["seine"]["impr"] = R["seine"]["monet"] + R["seine"]["sisley"] + R["seine"]["pissarro"]
R["seine"]["impr_pct"] = pc(R["seine"]["impr"], PLC["Q1471"]["n"])

# ---------- distance from birthplace ----------
F = X.join(PA[["blat", "blon", "bcountry"]], on="painter")
F = F[F.blat.notna()].copy()
fine = F.groupby("w").broad.transform("min") == 0
F = F[(F.broad == 0) | ~fine.reindex(F.index)]          # drop broad places where a finer place exists
F = F[F.groupby("w").broad.transform("min") == 0]       # paintings with only broad areas are left out
F = F[F.broad == 0]
F["km"] = gc_km(F.blat.values, F.blon.values, F.lat.values, F.lon.values)
D = F.groupby("w").agg(km=("km", "median"), painter=("painter", "first"), pname=("pname", "first"), cent=("cent", "first"), bc=("bcountry", "first")).reset_index()
BINS = [(0, 10, "under 10 km"), (10, 50, "10 to 50 km"), (50, 200, "50 to 200 km"), (200, 1000, "200 to 1,000 km"), (1000, 5000, "1,000 to 5,000 km"), (5000, 1e9, "over 5,000 km")]
binof = lambda v: next(i for i, (a, b, _) in enumerate(BINS) if a <= v < b)
D["bin"] = D.km.map(binof)
R["dist"] = {"n": len(D), "pct_of_mapped": pc(len(D), N), "median": round(float(D.km.median())), "within10_pct": pc((D.km < 10).sum(), len(D)),
             "within50_pct": pc((D.km < 50).sum(), len(D)), "over1000_pct": pc((D.km >= 1000).sum(), len(D)), "over5000_pct": pc((D.km >= 5000).sum(), len(D)),
             "bins": [b[2] for b in BINS], "all": [pc((D.bin == i).sum(), len(D)) for i in range(len(BINS))],
             "painters": int(D.painter.nunique()), "broad_only": int(X[X.painter.isin(PA.index[PA.blat.notna()])].groupby("w").broad.min().eq(1).sum())}
dc = []
for c in CENTS:
    a = D[D.cent == c]
    dc.append({"c": c, "name": CNAME[c], "n": len(a), "median": round(float(a.km.median())), "within50_pct": pc((a.km < 50).sum(), len(a)),
               "over1000_pct": pc((a.km >= 1000).sum(), len(a)), "bins": [pc((a.bin == i).sum(), len(a)) for i in range(len(BINS))]})
R["dist_cent"] = dc
DCN = {r["c"]: r for r in dc}
assert DCN[1600]["median"] < 100 and DCN[1800]["median"] > 3 * DCN[1600]["median"]
bcn = []
for c, a in D.groupby("bc"):
    if len(a) < 80 or a.painter.nunique() < 20 or not c: continue
    bcn.append({"country": c, "n": len(a), "painters": int(a.painter.nunique()), "median": round(float(a.km.median())), "within50_pct": pc((a.km < 50).sum(), len(a)),
                "over1000_pct": pc((a.km >= 1000).sum(), len(a))})
bcn.sort(key=lambda r: -r["n"])
R["dist_country"] = bcn
DBC = {r["country"]: r for r in bcn}
# the painters furthest from home: at least 5 paintings with a distance
pt = D.groupby("painter").agg(n=("km", "size"), median=("km", "median"), mx=("km", "max")).reset_index()
pt = pt[pt.n >= 5].sort_values("median", ascending=False)
trav = []
for r in pt.head(15).itertuples():
    a = F[F.painter == r.painter]; tp = a.groupby("plabel").size().sort_values(ascending=False)
    trav.append({"q": r.painter, "name": PA.loc[r.painter, "pname"], "n": int(r.n), "median": round(float(r.median)), "max": round(float(r.mx)),
                 "bcountry": PA.loc[r.painter, "bcountry"], "top": tp.index[0], "places_countries": sorted(set(a.country) - {""})[:6]})
R["travellers"] = trav
for c, k in (("Netherlands", "nl"), ("France", "fr"), ("United Kingdom", "uk"), ("Germany", "de"), ("Sweden", "se"), ("United States", "us"), ("Italy", "it")):
    R["dist_country_" + k] = DBC[c]
uk = D[(D.bc == "United Kingdom") & (D.km >= 1000)].w
ukc = X[X.w.isin(uk)].groupby("country").wt.sum().sort_values(ascending=False)
R["uk_far"] = {"n": len(uk), "top": [[k, round(float(v), 1)] for k, v in ukc.head(6).items()], "it_pct": pc(ukc.get("Italy", 0), len(uk)),
               "ch_pct": pc(ukc.get("Switzerland", 0), len(uk))}
nc = sorted(set(F[F.pname == "Marianne North"].country) - {""})
R["north_countries"] = {"n": len(nc), "list": nc}
assert {"Brazil", "Chile", "India", "Australia"} <= set(nc)
R["travellers_min"] = 5
R["painters_dist5"] = len(pt)
R["homebodies_pct"] = pc((pt["median"] < 50).sum(), len(pt))
T = {t["name"]: t for t in trav}
for nm in ("Marianne North", "Albert Bierstadt", "Camille Pissarro"):
    assert nm in T, nm
R["trav"] = {k: T[nm] for k, nm in (("north", "Marianne North"), ("bierstadt", "Albert Bierstadt"), ("pissarro", "Camille Pissarro"))}
R["trav"]["top"] = trav[0]
for nm, k in (("Claude Monet", "monet"), ("J. M. W. Turner", "turner"), ("Giovanni Antonio Canal", "canaletto"), ("Anna Boberg", "boberg"), ("Jan van Goyen", "goyen"),
              ("Vincent van Gogh", "vangogh"), ("Maurice Utrillo", "utrillo")):
    a = D[D.pname == nm]; R["trav"][k] = {"n": len(a), "median": round(float(a.km.median())), "within50_pct": pc((a.km < 50).sum(), len(a))}
assert R["trav"]["utrillo"]["median"] < 20 and R["trav"]["goyen"]["median"] < 100 and R["trav"]["boberg"]["median"] > 900

# ---------- collections and coverage ----------
CE = W.explode("colls")
cc = CE.colls.dropna().value_counts()
coll = []
for nm, n in cc.head(25).items():
    a = X[X.colls.map(lambda s: nm in s)]; tp = a.groupby("plabel").size().sort_values(ascending=False); tpa = a[a.pname != ""].drop_duplicates("w").pname.value_counts()
    coll.append({"name": nm, "n": int(n), "pct": pc(n, N), "top_place": tp.index[0], "top_place_n": int(tp.iloc[0]), "top_painter": tpa.index[0] if len(tpa) else "",
                 "top_painter_n": int(tpa.iloc[0]) if len(tpa) else 0, "top_painter_pct": pc(tpa.iloc[0], n) if len(tpa) else 0})
R["colls"] = coll
CO = {c["name"]: c for c in coll}
cum = np.cumsum(cc.values)
R["coll"] = {"n": int(len(cc)), "none": int(W.colls.map(len).eq(0).sum()), "none_pct": pc(W.colls.map(len).eq(0).sum(), N),
             "top1_pct": pc(cc.iloc[0], N), "top10_pct": pc(cc.head(10).sum(), N), "top20_pct": pc(cc.head(20).sum(), N),
             "half_k": int(np.searchsorted(cum, 0.5 * cum[-1]) + 1), "one_painting": int((cc == 1).sum()), "one_painting_pct": pc((cc == 1).sum(), len(cc)),
             "with_coll": int(W.colls.map(len).gt(0).sum())}
R["coll"]["half_k_pct"] = pc(R["coll"]["half_k"], R["coll"]["n"])
bob = W[W.pname == "Anna Boberg"]
R["boberg"] = {"n": len(bob), "pct": pc(len(bob), N), "nm": int(bob.colls.map(lambda s: "Nationalmuseum" in s).sum()),
               "lof_nord": int(X[(X.pname == "Anna Boberg") & X.q.isin(["Q186822", "Q50630", "Q145948"])].w.nunique()),
               "nm_share_of_nm": pc(bob.colls.map(lambda s: "Nationalmuseum" in s).sum(), cc["Nationalmuseum"])}
R["windsor"] = {"anon": PLC["Q42646"]["anon"], "nt": PLC["Q42646"]["top_coll_n"], "n": PLC["Q42646"]["n"]}
R["moses"] = {"n": fav["moses"]["n"], "cambridge": PLC["Q11151861"]["n"], "checkered": PLC["Q124798672"]["n"]}
assert R["boberg"]["nm"] / R["boberg"]["n"] > .9 and R["coll"]["top1_pct"] < 10
assert coll[0]["name"] == "Nationalmuseum" and coll[0]["top_painter"] == "Anna Boberg"
# how the map would look without the three biggest single-painter catalogues
R["painter_share"] = {"top10": R["painters_top10_pct"], "top1": pc(pn.iloc[0], N)}

# ---------- excluded items (for the methods note and a table) ----------
dp = DP.groupby(["q", "plabel", "why"]).size().reset_index(name="pairs").sort_values("pairs", ascending=False)
dp.to_csv(f"{DATA}/excluded_items.csv", index=False)
R["excluded_top"] = [[r.plabel, r.why, int(r.pairs)] for r in dp.head(10).itertuples()]
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG}

# ---------- tables ----------
D.set_index("w", inplace=True)
out = W.copy()
out["places"] = out.w.map(LK.groupby("w").q.agg(lambda s: "; ".join(s)))
out["place_labels"] = out.w.map(X.groupby("w").plabel.agg(lambda s: "; ".join(s)))
out["km_from_birthplace"] = out.w.map(D.km).round(1)
out["image_url"] = np.where(out.img != "", COMMONS + out.img, "")
out["genres"] = out.genres.map(lambda g: "; ".join(g)); out["collections"] = out.colls.map(lambda g: "; ".join(g))
out[["w", "title", "painter", "pname", "year", "genres", "collections", "places", "place_labels", "km_from_birthplace", "links", "image_url"]] \
    .rename(columns={"w": "wikidata", "pname": "painter_name", "painter": "painter_wikidata", "links": "wikipedia_articles", "places": "place_wikidata"}) \
    .to_csv(f"{DATA}/paintings.csv", index=False)
PO = PL[PL.n > 0].sort_values("n", ascending=False).copy()
fy = X.groupby("q").year.agg(["min", "max"])
PO["first_year"] = fy["min"].reindex(PO.index); PO["last_year"] = fy["max"].reindex(PO.index)
PO.reset_index()[["q", "plabel", "lat", "lon", "country", "kind", "broad", "n", "painters", "first_year", "last_year"]] \
    .rename(columns={"q": "wikidata", "plabel": "place", "n": "paintings", "broad": "broad_area"}).to_csv(f"{DATA}/places.csv", index=False)
pd_ = D.groupby("painter").km.agg(["size", "median", "max"])
PAO = PA.copy(); PAO["places"] = X.groupby("painter").q.nunique().reindex(PAO.index)
PAO["paintings_with_distance"] = pd_["size"].reindex(PAO.index); PAO["median_km"] = pd_["median"].reindex(PAO.index).round(1); PAO["max_km"] = pd_["max"].reindex(PAO.index).round(1)
PAO.sort_values("n", ascending=False).reset_index()[["painter", "pname", "n", "places", "blat", "blon", "bcountry", "citizenship", "paintings_with_distance", "median_km", "max_km"]] \
    .rename(columns={"painter": "wikidata", "pname": "painter", "n": "paintings", "blat": "birth_lat", "blon": "birth_lon", "bcountry": "birth_country"}).to_csv(f"{DATA}/painters.csv", index=False)
cr = []
for c in CENTS:
    a = X[X.cent == c]; sh = a.groupby("country").wt.sum()
    for k, v in sh.sort_values(ascending=False).items():
        cr.append({"period": CNAME[c], "country": k or "at sea", "paintings": round(float(v), 2), "share_pct": pc(v, a.drop_duplicates("w").shape[0])})
pd.DataFrame(cr).to_csv(f"{DATA}/places_by_period.csv", index=False)
pd.DataFrame([{"collection": k, "paintings": int(v), "share_pct": pc(v, N)} for k, v in cc.items()]).to_csv(f"{DATA}/collections.csv", index=False)

# ---------- page data ----------
PO = PL[PL.n > 0].copy()
PO = PO.loc[[q for q in order]]
PI = {q: i for i, q in enumerate(PO.index)}
CTRY = sorted(set(PO.country) | set(PA.bcountry)); CI = {c: i for i, c in enumerate(CTRY)}
painters = PA[PA.index.isin(W.painter)].sort_values("n", ascending=False)
PAI = {q: i for i, q in enumerate(painters.index)}
COLL = list(cc.index); COI = {c: i for i, c in enumerate(COLL)}
KI = {k: i for i, (k, _, _) in enumerate(KINDS)}; KI["other"] = len(KINDS)
GB = {"landscape": 1, "marine": 2, "cityscape": 4}
site = {"genres": [[g, GCOL[g]] for g in KEEP_GENRES], "kinds": [[k, nm, c] for k, nm, c in KINDS] + [["other", "Other places", "#8C8478"]],
        "cents": [[c, CNAME[c]] for c in CENTS], "countries": CTRY, "colls": COLL,
        "places": [[PO.loc[q, "plabel"], round(float(PO.loc[q, "lat"]), 4), round(float(PO.loc[q, "lon"]), 4), int(PO.loc[q, "n"]), CI[PO.loc[q, "country"]],
                    KI[PO.loc[q, "kind"]], int(PO.loc[q, "broad"]), q] for q in PO.index],
        "painters": [[painters.loc[q, "pname"], None if np.isnan(painters.loc[q, "blat"]) else round(float(painters.loc[q, "blat"]), 3),
                      None if np.isnan(painters.loc[q, "blon"]) else round(float(painters.loc[q, "blon"]), 3), int(painters.loc[q, "n"]), CI[painters.loc[q, "bcountry"]], q]
                     for q in painters.index],
        "bins": R["dist"]["bins"]}
jsave(site, f"{DATA}/site.json")
WW = W.copy(); WW["pl"] = WW.w.map(LK.groupby("w").q.agg(list))
rows = [[r.w, r.title, PAI.get(r.painter, -1), int(r.year) if not np.isnan(r.year) else 0, sum(GB[g] for g in r.genres), [COI[c] for c in r.colls], r.img,
         [PI[q] for q in r.pl], round(float(D.km[r.w])) if r.w in D.index else -1] for r in WW.itertuples()]
rows.sort(key=lambda r: (r[3] or 9999))
jsave({"cols": ["q", "title", "painter", "year", "genre", "colls", "img", "places", "km"], "rows": rows}, f"{DATA}/paintings.json")
jsave(R, f"{DATA}/results.json", indent=1)
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("site.json", "paintings.json", "results.json")})
print(R["source"]); print([(r["label"], r["n"], r["kind"]) for r in R["top"][:25]]); print(R["kinds"])
print(R["fav"]); print(R["seine"]); print(R["dist"]); print(R["dist_cent"]); print(R["dist_country"]); print([(t["name"], t["n"], t["median"], t["bcountry"], t["top"]) for t in trav])
print([(c["name"], c["n"], c["top"], c["Norway"], c["Norway_wo_boberg"]) for c in cents]); print(R["coll"]); print(coll[:12]); print(R["boberg"], R["bias_top"], R["single"], R["painters_top10_pct"])
print(R["countries"][:10]); print(R["excluded_top"]); print(R["trav"])
