# Painted places: where catalogued landscape, marine and city paintings look, and how far painters went from home

A map and analysis of 8,533 paintings in Wikidata classed as landscapes, marine paintings or cityscapes that depict a real place with coordinates: 4,740 places in 102 countries, painted by 2,393 named painters. Which places were painted most, which painters returned to which places, how far from their birthplaces they painted, how the geography changed from the 1600s to the 1900s, and how strongly a few collections shape the catalogue.

Interactive page: https://maps.tristanhotham.com/painted-places/
Paper: https://doi.org/10.5281/zenodo.23873007
Blog post: https://blog.tristanhotham.com/2026/10/31/painted-places/

## Headline results

- Places: the Seine is the most painted place (228 paintings by 81 painters; Monet 38, Sisley 27, Pissarro 15), then Paris (120), Lofoten (97), Venice (95) and Nordland (89). Of the 100 most painted places, 30 are cities, towns or villages, 20 buildings, 16 rivers, 13 coasts and 13 mountains. 68% of places appear in only one painting.
- Painters: the Seine is 38 of Monet's 152 paintings; Turner's 52 show 56 places, Venice most; 13 of Canaletto's 32 show London, 15 Venice.
- Distance: for 7,183 paintings with a measurable birthplace and place, the median distance is 231 km; 26% are within 50 km and 26% beyond 1,000 km. Median 48 km in the 1600s, 331 km in the 1800s.
- Periods: the Netherlands are 62% of 1600s paintings; Italy 37% of the 1700s; France 27% of the 1800s; Norway 9% after 1900 (6% without Anna Boberg).
- Coverage: 1,019 collections; the largest (Nationalmuseum, Stockholm) holds 6.6% of paintings, 222 of them by Anna Boberg; the ten largest hold 30%. 80% of paintings show places in Europe. Only 18% have a Wikipedia article.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; results and place and painter data embedded, `data/paintings.json` and `data/world.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/paintings.csv` | All 8,533 mapped paintings: Wikidata id, title, painter, year, genres, collections, depicted places, distance from the painter's birthplace, Wikipedia article count, Commons image URL. |
| `data/places.csv` | The 4,740 places: Wikidata id, label, coordinates, country, kind (top 100), broad area flag, paintings, painters, first and last year. |
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

- Query: Wikidata through QLever, 2026: paintings with a genre of landscape art, marine art or cityscape (or religious art, genre painting or animal painting) that depict an item with coordinates. 18,249 rows, 10,321 paintings. Kept: paintings with at least one of the three landscape genres (8,757).
- Places: depicted items removed if their coordinate is not a point on the Earth (3, chiefly the Moon), if their coordinates are implausible, or if they are events (70, mostly sea battles), vessels (19) or other non-places (2); listed by id in `code/common.py`, with a keyword scan that fails the build on anything unlisted. 224 paintings left with no place are dropped.
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

- Wikidata, queried through QLever on 1 November 2026. CC0.
- Images: Wikimedia Commons, linked and shown as thumbnails on the page only; each keeps its own licence and none is included in this repository.
- Natural Earth countries, regions and land (https://www.naturalearthdata.com/). Public domain.
- Base map on the page: hillshade, relief and imagery © Esri; place names © OpenFreeMap, OpenMapTiles and OpenStreetMap contributors.

## Citation

Hotham, T. (2026) Painted places: where catalogued landscape, marine and city paintings look, and how far painters went from home. Zenodo. https://doi.org/10.5281/zenodo.23873007

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
