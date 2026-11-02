"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23873007, https://doi.org/10.5281/zenodo.23873007 and https://blog.tristanhotham.com/2026/10/31/painted-places/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Painted_Places"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
T = {t["label"]: t["n"] for t in R["top"][:20]}
assert [T[k] for k in ("Seine", "Paris", "Lofoten", "Venice", "Nordland", "Grote Kerk", "Rio de Janeiro", "English Channel", "River Thames", "Hudson River", "Windsor Castle")] == [228, 120, 97, 95, 89, 67, 64, 59, 58, 56, 56]
assert (R["places"]["Q3140"]["n"], R["places"]["Q99"]["n"], R["places"]["Q97"]["n"]) == (56, 43, 55)
FR = {f["name"]: f for f in R["fav_rows"]}
assert FR["Anna Boberg"]["top"][:2] == [["Lofoten", 93], ["Nordland", 88]] and FR["Gerrit Berckheyde"]["top"][:2] == [["Grote Kerk", 28], ["Grote Markt", 23]]
assert FR["Canaletto"]["top"][:2] == [["London", 11], ["River Thames", 7]] and FR["Francesco Guardi"]["top"][0][0] == "Venice"
D = {d["c"]: d for d in R["dist_cent"]}
assert D[1600]["median"] == 48 and D[1800]["median"] == 331 and round(D[1800]["bins"][5]) == 18 and 45 <= D[1600]["within50_pct"] <= 55
assert 22 <= R["dist"]["within50_pct"] <= 28 and 22 <= R["dist"]["over1000_pct"] <= 28                    # "a quarter", "another quarter"
C = {c["c"]: c for c in R["cents"]}
assert (round(C[1600]["Netherlands"]), round(C[1700]["Italy"]), round(C[1700]["United Kingdom"]), round(C[1800]["France"]), round(C[1900]["France"]), round(C[1800]["United States"]), round(C[1900]["United States"])) == (62, 37, 23, 27, 32, 14, 13)
assert [c["n"] for c in R["colls"][:3]] == [566, 429, 355] and R["colls"][0]["top_painter_n"] == 222
assert R["rank"]["cambridge"] <= 30 and R["seine"]["impr_pct"] > 33.3

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23873007"}
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s = R["source"]
meta = {"title": "Painted places: where landscape painters painted, and how far from home they went",
        "slug": "painted-places",
        "excerpt": f"I mapped {s['n']:,} landscape, marine and city paintings from Wikidata and the {s['places']:,} places they show. The most painted place is a river, the Seine, and half the paintings were made more than {R['dist']['median']} km from the painter's birthplace.",
        "seo_description": f"A map of {s['n']:,} landscape paintings and the places they show: the Seine, Venice and Lofoten, painters' home grounds, and how far they travelled.",
        "tags": ["art", "landscape painting", "maps", "data visualisation", "Wikidata", "Monet", "Turner", "Canaletto", "museums"],
        "header_alt": f"Title card reading 'Painted places' in orange and blue on pale paper, beside a map of Europe covered in green, blue and orange dots for painted places, with big circles at the mouth of the Seine, Paris, Venice and Lofoten in northern Norway. Text: {s['n']:,} landscape, marine and city paintings and the {s['places']:,} places they show; the Seine leads with {R['places']['Q1471']['n']}."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/painted-places_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"painted-places/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"painted-places/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "painted-places/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("``", '"').replace("''", '"')
zmeta = {"title": "Painted Places: Where Catalogued Landscape, Marine and City Paintings Look, and How Far Painters Went from Home",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Painting, place and painter data: Wikidata (CC0). Images of paintings are not included.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["landscape painting", "marine painting", "cityscape", "Wikidata", "art geography", "painters", "museum collections", "cultural heritage data", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
