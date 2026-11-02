"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json) is embedded; data/paintings.json and data/world.json are loaded by the
page. Facts stated in words are checked here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted
before </body>. 10.5281/zenodo.23873007 and https://blog.tristanhotham.com/2026/10/31/painted-places/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
PL, F, T, CT, DC = R["places"], R["fav"], R["trav"], {c["c"]: c for c in R["cents"]}, {d["c"]: d for d in R["dist_cent"]}

# facts stated in words (page, blog, paper, collage)
assert R["top"][0]["label"] == "Seine" and R["top"][1]["label"] == "Paris" and [t["label"] for t in R["top"][2:5]] == ["Lofoten", "Venice", "Nordland"]
assert R["top"][0]["kind"] == "river" and R["seine"]["impr_pct"] > 33                                     # "three Impressionists account for a third"
assert F["monet"]["top"] == "Seine" and F["monet"]["top2"] == "English Channel" and F["monet"]["top3"] == "Étretat"
assert F["sisley"]["top"] == "Seine" and F["sisley"]["top2"] == "Loing" and F["pissarro"]["top3"] == "boulevard Montmartre"
assert F["goyen"]["top"] == "Dordrecht" and F["cezanne"]["top"] == "Montagne Sainte-Victoire"
assert F["turner"]["places"] > F["turner"]["n"]                                                           # "a painter of everywhere"
assert F["guardi_venice"]["n"] >= F["guardi_venice"]["of"] - 1                                           # "stayed put"
assert [r["name"] for r in sorted(R["fav_rows"], key=lambda r: -r["n"])[:3]] == ["Anna Boberg", "Albert Bierstadt", "Grandma Moses"]
assert R["painters_top"][0]["name"] == "Anna Boberg"                                                      # "more than anyone"
assert 45 <= DC[1600]["within50_pct"] <= 55                                                                # "half of the paintings from that century"
assert DC[1600]["median"] < DC[1700]["median"] < DC[1800]["median"] and DC[1900]["median"] < DC[1800]["median"]
assert min(R["dist_country"], key=lambda d: d["median"])["country"] == "Netherlands"                      # "stayed closest"
assert R["dist_country_de"]["median"] > R["dist_country_uk"]["median"] > R["dist_country_fr"]["median"]    # "further still"
assert [k for k, _ in R["uk_far"]["top"][:2]] == ["United States", "Italy"]
assert all(t["bcountry"] in ("United Kingdom", "Australia") for t in R["travellers"][:4])                  # antipodes
assert T["utrillo"]["median"] < 5
assert [CT[c]["top"][0][0] for c in (1600, 1700, 1800, 1900)] == ["Netherlands", "Italy", "France", "France"]
assert CT[1700]["top"][1][0] == "United Kingdom" and CT[1800]["top"][1][0] == "United States"
assert CT[1600]["Norway"] < 1.5 and CT[1700]["Norway"] < 1.5                                              # "about 1% before 1800"
assert [p for p, _ in CT[1800]["top_places"][:3]] == ["Seine", "Paris", "English Channel"]
assert R["colls"][0]["name"] == "Nationalmuseum" and R["colls"][0]["top_painter"] == "Anna Boberg"
assert PL["Q41428"]["top_coll_pct"] == 100 and PL["Q41428"]["top_coll"] == "Brasiliana Iconográfica"      # "every one"
assert PL["Q42646"]["top_coll"] == "National Trust" and PL["Q42646"]["top_coll_n"] > PL["Q42646"]["n"] / 2  # "mostly"
assert R["source"]["depcoord_n"] == 2 and R["source"]["oldest_painter"] == "Huang Gongwang"
assert R["source"]["moon"] > 100


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23873007", "https://blog.tristanhotham.com/2026/10/31/painted-places/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
