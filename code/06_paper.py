"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23873007 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Painted_Places"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert R["dist_country_uk"]["median"] > R["dist_country_fr"]["median"] and R["dist_country_de"]["median"] > R["dist_country_uk"]["median"]
assert max(d["median"] for d in R["dist_country"] if d["n"] >= 400) in (R["dist_country_de"]["median"], R["dist_country_se"]["median"])


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


rows = "".join(f"{tex(p['label'])} & {tex(p['country'] or 'at sea')} & {p['n']} & {p['painters']} & {tex(p['top_painter'] or 'unknown')} ({p['top_painter_n']}) & {tex(p['top_coll'] or 'none')} ({p['top_coll_n']})\\\\\n" for p in R["top"][:25])
TP = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{The 25 most painted places: paintings, painters, and the leading painter and collection.}\\label{tab:places}"
      "\\begin{tabular}{p{2.9cm}p{2cm}rrp{3.5cm}p{3.6cm}}\\toprule Place & Country & Paintings & Painters & Leading painter & Leading collection\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(d['country'])} & {d['n']:,} & {d['painters']} & {d['median']:,} & {d['within50_pct']:.0f}\\% & {d['over1000_pct']:.0f}\\%\\\\\n" for d in R["dist_country"])
TC = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Distance from birthplace by the painter's country of birth (today's borders; at least 80 paintings and 20 painters).}\\label{tab:countries}"
      "\\begin{tabular}{lrrrrr}\\toprule Born in & Paintings & Painters & Median km & Within 50 km & Over 1,000 km\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(c['name'])} & {c['n']} & {c['pct']:.1f}\\% & {tex(c['top_painter'])} ({c['top_painter_n']}) & {tex(c['top_place'])} ({c['top_place_n']})\\\\\n" for c in R["colls"][:15])
TL = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{The 15 collections with the most mapped paintings.}\\label{tab:colls}"
      "\\begin{tabular}{p{4.6cm}rrp{4.2cm}l}\\toprule Collection & Paintings & Share & Leading painter & Most painted place\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(a)} & {tex(b)} & {c}\\\\\n" for a, b, c in R["excluded_top"])
TE = ("\\begin{table}[tbp]\\centering\\small\\caption{The depicted items most often removed as not being places (painting and item pairs).}\\label{tab:excluded}"
      "\\begin{tabular}{p{6cm}p{6cm}r}\\toprule Item & Reason & Pairs\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("PLACES", TP), ("COUNTRIES", TC), ("COLLS", TL), ("EXCLUDED", TE)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
