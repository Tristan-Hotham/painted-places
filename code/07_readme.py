"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, d, c, F, PL = R["source"], R["dist"], R["coll"], R["fav"], R["places"]
CT = {x["c"]: x for x in R["cents"]}; DC = {x["c"]: x for x in R["dist_cent"]}
N = lambda v: f"{round(v):,}"
readme = f"""# Painted places: where catalogued landscape, marine and city paintings look, and how far painters went from home

A map and analysis of {N(s['n'])} paintings in Wikidata classed as landscapes, marine paintings or cityscapes that depict a real place with coordinates: {N(s['places'])} places in {s['countries']} countries, painted by {N(s['painters'])} named painters. Which places were painted most, which painters returned to which places, how far from their birthplaces they painted, how the geography changed from the 1600s to the 1900s, and how strongly a few collections shape the catalogue.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Places: the Seine is the most painted place ({PL['Q1471']['n']} paintings by {R['seine']['painters']} painters; Monet {R['seine']['monet']}, Sisley {R['seine']['sisley']}, Pissarro {R['seine']['pissarro']}), then Paris ({PL['Q90']['n']}), Lofoten ({PL['Q186822']['n']}), Venice ({PL['Q641']['n']}) and Nordland ({PL['Q50630']['n']}). Of the 100 most painted places, {R['kinds_top']['city']['places']} are cities, towns or villages, {R['kinds_top']['building']['places']} buildings, {R['kinds_top']['river']['places']} rivers, {R['kinds_top']['coast']['places']} coasts and {R['kinds_top']['mountain']['places']} mountains. {R['single']['places_1_pct']:.0f}% of places appear in only one painting.
- Painters: the Seine is {F['monet_seine']['n']} of Monet's {F['monet']['n']} paintings; Turner's {F['turner']['n']} show {F['turner']['places']} places, Venice most; {F['canaletto_london']['n']} of Canaletto's {F['canaletto']['n']} show London, {F['canaletto_venice']['n']} Venice.
- Distance: for {N(d['n'])} paintings with a measurable birthplace and place, the median distance is {N(d['median'])} km; {d['within50_pct']:.0f}% are within 50 km and {d['over1000_pct']:.0f}% beyond 1,000 km. Median {DC[1600]['median']} km in the 1600s, {DC[1800]['median']} km in the 1800s.
- Periods: the Netherlands are {CT[1600]['Netherlands']:.0f}% of 1600s paintings; Italy {CT[1700]['Italy']:.0f}% of the 1700s; France {CT[1800]['France']:.0f}% of the 1800s; Norway {CT[1900]['Norway']:.0f}% after 1900 ({CT[1900]['Norway_wo_boberg']:.0f}% without Anna Boberg).
- Coverage: {N(c['n'])} collections; the largest (Nationalmuseum, Stockholm) holds {c['top1_pct']:.1f}% of paintings, {R['boberg']['nm']} of them by Anna Boberg; the ten largest hold {c['top10_pct']:.0f}%. {R['continent']['Europe']:.0f}% of paintings show places in Europe. Only {s['wiki_pct']:.0f}% have a Wikipedia article.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; results and place and painter data embedded, `data/paintings.json` and `data/world.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/paintings.csv` | All {N(s['n'])} mapped paintings: Wikidata id, title, painter, year, genres, collections, depicted places, distance from the painter's birthplace, Wikipedia article count, Commons image URL. |
| `data/places.csv` | The {N(s['places'])} places: Wikidata id, label, coordinates, country, kind (top 100), broad area flag, paintings, painters, first and last year. |
| `data/painters.csv` | Painters: paintings, places, birthplace coordinates and country, citizenship, median and maximum distance. |
| `data/places_by_period.csv` | Share of each period's paintings by the country of the place shown. |
| `data/collections.csv` | Collections and their mapped paintings. |
| `data/excluded_items.csv` | Depicted items removed as not being places, with the reason and the number of paintings. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/paintings.json`, `data/world.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Query: Wikidata through QLever, {s['query_date'].split()[-1]}: paintings with a genre of landscape art, marine art or cityscape (or religious art, genre painting or animal painting) that depict an item with coordinates. {N(s['rows'])} rows, {N(s['paintings_all'])} paintings. Kept: paintings with at least one of the three landscape genres ({N(s['core'])}).
- Places: depicted items removed if their coordinate is not a point on the Earth ({s['drop_globe']}, chiefly the Moon), if their coordinates are implausible, or if they are events ({s['drop_event']}, mostly sea battles), vessels ({s['drop_vessel']}) or other non-places ({s['drop_other']}); listed by id in `code/common.py`, with a keyword scan that fails the build on anything unlisted. {N(s['no_place'])} paintings left with no place are dropped.
- Distance: great circle from the painter's birthplace to each depicted place, median per painting; countries, regions, seas and oceans left out where a painting names a finer place. Countries are today's (Natural Earth).
- Caveats: a catalogue, not a sample; a few collections and painters dominate; depicts does not prove a visit; birthplace is a crude proxy for home; rivers are single points.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are read from `raw/` (not in the repository; the queries are described in `code/common.py`) and Natural Earth from `/home/claude/newdata/raw/geo/`. Intermediate files go to `/dev/shm/paintedplaces/work` (set `PPTMP` to change).

```
python3 code/01_clean.py        # read Wikidata extracts, keep genuine places, painters and birthplaces
python3 code/02_geo.py          # outlines
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Wikidata, queried through QLever on {s['query_date']}. CC0.
- Images: Wikimedia Commons, linked and shown as thumbnails on the page only; each keeps its own licence and none is included in this repository.
- Natural Earth countries, regions and land (https://www.naturalearthdata.com/). Public domain.
- Base map on the page: hillshade, relief and imagery © Esri; place names © OpenFreeMap, OpenMapTiles and OpenStreetMap contributors.

## Citation

Hotham, T. (2026) Painted places: where catalogued landscape, marine and city paintings look, and how far painters went from home. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/rocket-launches/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The painting, place and painter
data come from Wikidata (CC0). Images of paintings are not included in this
repository: the page shows thumbnails from Wikimedia Commons, where each image
remains under its own licence or in the public domain. Natural Earth is public
domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Where landscape painters painted: {N(s['n'])} paintings mapped from Wikidata. The most painted place on Earth is a river, the Seine ({PL['Q1471']['n']} paintings), and half were painted more than {N(d['median'])} km from the painter's birthplace

## Body

I mapped every painting in Wikidata classed as a landscape, sea painting or cityscape that depicts a real place: {N(s['n'])} paintings by {N(s['painters'])} painters, {N(s['places'])} places. The Seine wins ({PL['Q1471']['n']}, a third of them by Monet, Sisley and Pissarro), then Paris, Lofoten, Venice and Nordland. In the 1600s half the paintings show somewhere within 50 km of the painter's birthplace (Dutch painters painting Dutch towns); by the 1800s the median distance is {DC[1800]['median']} km. The map is also a map of catalogues: Lofoten and Nordland are in the top five because one Swedish museum has catalogued {R['boberg']['nm']} paintings by one painter, Anna Boberg. Caveats: this is what Wikidata has described, not every painting ever made; distance is from birthplace, so emigrants like Bierstadt look like great travellers. Interactive map with thumbnails, filters by century, genre and painter, and painters' journeys: {PAGE}

## Source comment

Source: Wikidata (CC0), queried through QLever on {s['query_date']}: paintings with genre landscape, marine art or cityscape that depict an item with coordinates, plus painters' birthplaces. I removed {s['items_dropped']} depicted items that are not places (the Moon, sea battles, ships). Countries: Natural Earth.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
