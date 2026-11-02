"""Shared paths, groupings and helpers for the painted-places project.

Raw inputs (read in place, never modified), all Wikidata via the QLever SPARQL endpoint, queried 1 November 2026, CC0:
  raw/landscapes.tsv   paintings (instance of painting, Q3305213) with a genre (P136) in the set below AND a "depicts"
                       (P180) value that has coordinates (P625). One row per painting, depicted item and genre, so rows
                       repeat. Columns: w (painting), wLabel, place (depicted item), placeLabel, coord (its P625), genre,
                       painter (P170), painterLabel, inception (P571), img (P18, a Commons Special:FilePath URL),
                       collLabel (P195), links (the painting's number of Wikipedia sitelinks).
  raw/depcoord.tsv     the paintings that carry an explicit "coordinates of depicted place" (P9149).
  raw/painters.tsv     painter, country of citizenship (P27) and the coordinates of the place of birth (P19 / P625).
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_10m_admin_1_states_provinces.geojson,
      ne_50m_admin_0_countries.geojson, ne_50m_land.geojson, ne_10m_populated_places_simple.geojson
      (Natural Earth, public domain)
Images: the page and popups show Wikimedia Commons thumbnails through Special:FilePath; no image is copied into the repo.
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PP_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("PP_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("PP_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("PPTMP", "/dev/shm/paintedplaces"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "painted-places"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23873007"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/painted-places/"          # filled in by the publisher
QUERY_DATE = "1 November 2026"
QUERY_YEAR = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
COMMONS = "https://commons.wikimedia.org/wiki/Special:FilePath/"

# Genres in the query. The study keeps paintings with at least one of the three landscape genres; paintings that reached
# the query only through a related genre (religious, genre or animal painting) are counted and set aside.
GENRES = {"Q191163": "landscape", "Q158607": "marine", "Q1935974": "cityscape",
          "Q2864737": "religious art", "Q1047337": "genre painting", "Q16875712": "animal painting"}
KEEP_GENRES = ["landscape", "marine", "cityscape"]
GCOL = {"landscape": "#5E8C3A", "marine": "#2F6DA8", "cityscape": "#C2582B"}

# ---------- which depicted items are genuine places ----------
# "depicts" (P180) catches anything with coordinates. Rule, applied in this order:
#  1. the coordinate must be a plain point on the Earth (Wikidata's Moon entry carries a lunar coordinate; a few items
#     have an "unknown value" coordinate);
#  2. latitude and longitude must be in range and not exactly 0, 0;
#  3. the item must not be an event, a vessel, a movable work of art or an organisation. These are listed by QID below,
#     found by reading every depicted item with two or more paintings and by a keyword scan (NONPLACE_RE) of all labels;
#     the build fails if the keyword scan finds a label that is in neither list.
NONPLACE = {
    "event": {
        # biblical and religious events located at a site
        "Q51636": "crucifixion of Jesus", "Q51633": "Last Supper", "Q39864": "Pentecost", "Q10289604": "Kiss of Judas",
        "Q51635": "Sanhedrin trial of Jesus", "Q98448964": "Jesus and the Samaritan woman at the well",
        "Q22688659": "Battle of Gibeon", "Q133331": "First Council of Nicaea",
        # battles, sieges and naval actions
        "Q734934": "Four Days' Battle", "Q2064362": "Battle of Texel", "Q1808375": "Battle of Solebay", "Q891806": "Bombardment of Algiers",
        "Q2265686": "Battles of Barfleur and La Hougue", "Q179684": "Spanish Armada", "Q755955": "Battle of Copenhagen",
        "Q171416": "Battle of Trafalgar", "Q243979": "Battle of the Nile", "Q331740": "Raid on the Medway", "Q672218": "Battle of the Slaak",
        "Q1083872": "Glorious First of June", "Q238440": "Battle of Navarino", "Q2330975": "Siege of Breda", "Q431488": "Siege of Breda",
        "Q667179": "Battle of Gibraltar", "Q1275200": "Battle of the Sound", "Q156554": "Battle of Jutland", "Q1754313": "Battle of Bennington",
        "Q158054": "Battle of Lissa", "Q132568": "Battle of the Somme", "Q156681": "Battle of Sedan", "Q160387": "Battle of Actium",
        "Q1620408": "Battle of Chesma", "Q165425": "Battle of Lepanto", "Q16822708": "Battle of Sesimbra Bay", "Q16822746": "Battle of the Narrow Seas",
        "Q1779008": "Battle of Anghiari", "Q1814248": "Battle of Haarlemmermeer", "Q18326240": "Battle of the Bay of Biscay",
        "Q188123": "Battle of Villiers", "Q213074": "Battle of the Hydaspes", "Q233219": "Second Battle of Ypres", "Q2364944": "Battle of Cherbourg",
        "Q2510511": "Second Battle of Abukir", "Q2601178": "Battle of Negapatam", "Q267339": "Battle of Grand Port", "Q2888513": "Battle of Focchies",
        "Q3026815": "Alhucemas landing", "Q3108282": "Siege of Valenciennes", "Q311759": "Battle of Vigo Bay", "Q312212": "Battle of Nördlingen",
        "Q3381142": "Battle of Flers-Courcelette", "Q339321": "Battle of the Milvian Bridge", "Q3485809": "Siege of Amiens",
        "Q3504102": "Battle of Guararapes", "Q369893": "Battle of Angamos", "Q392213": "Siege of Orléans", "Q427958": "Battle of Sinop",
        "Q450318": "Battle of Quiberon Bay", "Q4872056": "Battle of Pirano", "Q517262": "Battle of Veracruz", "Q540121": "Siege of Maastricht",
        "Q577081": "Battle of Camperdown", "Q644960": "Battle of the Boyne", "Q675999": "Battle of the Downs", "Q73194": "Battle of Dogger Bank",
        "Q7443105": "Second Battle of Passchendaele", "Q7868544": "USS Constitution vs HMS Guerriere", "Q844886": "Siege of Jerusalem",
        "Q868027": "Battle of Clontarf", "Q211582": "Zong massacre", "Q163891": "St. Bartholomew's Day massacre",
        # fires, floods, explosions, wrecks, fairs and festivals
        "Q10671627": "Tre Kronor fire 1697", "Q115225738": "Great Fire of Troy", "Q164679": "Great Fire of London", "Q4859409": "Burning of Parliament",
        "Q3005548": "1910 Great Flood of Paris", "Q1807803": "explosion of the powder magazine in Delft", "Q2514684": "Leiden gunpowder disaster",
        "Q2577588": "sinking of the RMS Titanic", "Q1345539": "International Exposition 1867", "Q753646": "Exposition Universelle of 1900",
        "Q957317": "Exposition Universelle of 1889", "Q35191": "Carnival of Venice", "Q4677221": "Action of 10 April 1795",
    },
    "vessel": {
        "Q1032063": "HMS Monmouth", "Q1564478": "HMS Captain", "Q1582476": "French ship Vengeur du Peuple", "Q16890409": "SS City of Chester",
        "Q213958": "HMS Victory", "Q241381": "HMS Prince Royal", "Q5632583": "HMS Gloucester", "Q5634128": "HMS Royal James", "Q609925": "HMS Warrior",
        "Q625319": "SS Austria", "Q744558": "HMS Sirius", "Q746389": "HMS Kelly", "Q849276": "Dutch ship Brederode", "Q920520": "USS Kearsarge",
        "Q938422": "HMS Guerriere", "Q944436": "USS Constitution", "Q25173": "Titanic", "Q187425": "RMS Lusitania", "Q504096": "RMS Carpathia", "Q1810254": "Le Train Bleu", "Q65964689": "HMS Santa Monica",
    },
    "movable work of art": {"Q151952": "Venus de Milo", "Q1728619": "Capitoline Venus", "Q618521": "Venus Callipyge"},
    "organisation": {"Q913972": "Order of Friars Minor", "Q2171193": "Royal Yacht Squadron"},
}
NONPLACE_QID = {q: k for k, d in NONPLACE.items() for q in d}
NONPLACE_RE = (r"\b(?:battles?|siege|bombardment|raid on|action of|massacre|great fire|fire \d{4}|great flood|explosion|gunpowder|exposition|"
               r"carnival of|crucifixion|last supper|pentecost|kiss of judas|trial of jesus|jesus and the|burning of|landing$|armada|"
               r"glorious first|council of|sinking of|HMS|USS|SS|RMS|ship|venus)\b")
# labels the keyword scan flags that are genuine places (kept)
NONPLACE_OK = {"Battle Harbour", "Bennington Battle Monument", "Bolton Landing", "Venus", "Fire Island", "Battle", "Battle Abbey",
               "Manchester Ship Canal", "Shipley", "Battle Creek", "Shiprock", "Shipley Glen", "Battle Monument"}

# Broad areas (countries, first-level regions, seas, oceans, continents): kept on the map, but left out of the travel
# distances when a painting also names a finer place, because a single point cannot stand for them.
BROAD_RE = r"(?:\bOcean\b|\bSea\b|^Sea of|English Channel|Strait of Dover|Bay of Biscay|^Arctic$|^Africa$|^Europe$|^Asia$|^North Africa$|^Sahara$|^Low Countries$|^New England$|^Scandinavia$|^Middle East$|^Orient$|^Levant$|^Holy Land$)"
BROAD_EXTRA = {"Q41428": "Rio de Janeiro (state)", "Q50630": "Nordland", "Q327": "Brittany", "Q12130": "Brittany", "Q15878": "Normandy", "Q18677875": "Normandy",
               "Q101081": "Provence", "Q153809": "Tyrol", "Q102911": "Holland", "Q13917": "Île-de-France", "Q1282": "Lazio", "Q40430": "Bahia",
               "Q15104": "Provence-Alpes-Côte d'Azur", "Q12709": "Pyrénées-Orientales", "Q23111": "Suffolk", "Q209523": "Bohuslän",
               "Q199957": "Småland", "Q2254": "Telemark"}

# What kind of place: assigned by hand for the most painted places (the chart and the text), from their Wikidata labels and
# descriptions. Anything not listed is "other".
KINDS = [("river", "Rivers and canals", "#2F6DA8"), ("city", "Cities, towns and villages", "#C2582B"), ("coast", "Coasts, seas and islands", "#2E9A8C"),
         ("mountain", "Mountains, valleys and forests", "#5E8C3A"), ("building", "Buildings, bridges and squares", "#8A5A9E"),
         ("region", "Regions and countries", "#A79F94")]
KIND = {
    "Q1471": "river", "Q90": "city", "Q186822": "coast", "Q641": "city", "Q50630": "region", "Q1545193": "building", "Q41428": "region",
    "Q34640": "coast", "Q19686": "river", "Q42646": "building", "Q3140": "river", "Q26421": "city", "Q97": "coast", "Q4918": "coast",
    "Q630566": "mountain", "Q524": "mountain", "Q99": "region", "Q159605": "city", "Q290936": "coast", "Q1083850": "building", "Q727": "city",
    "Q220": "city", "Q335277": "building", "Q12994": "city", "Q84": "city", "Q41986": "river", "Q4204": "mountain", "Q11151861": "city",
    "Q584": "river", "Q309243": "river", "Q1996389": "mountain", "Q243": "building", "Q2981": "building", "Q124798672": "building",
    "Q837211": "coast", "Q236736": "city", "Q201352": "city", "Q217527": "building", "Q667456": "coast", "Q1229951": "coast", "Q38": "region",
    "Q186115": "city", "Q1644": "river", "Q200231": "river", "Q17373121": "coast", "Q1286": "mountain", "Q762133": "city", "Q9920": "city",
    "Q34221": "river", "Q181946": "city", "Q1731": "city", "Q839050": "building", "Q365": "city", "Q174645": "mountain", "Q877031": "building",
    "Q1518970": "mountain", "Q1075988": "building", "Q3561": "city", "Q173292": "coast", "Q201385": "coast", "Q2634": "city", "Q1056152": "building",
    "Q165061": "city", "Q212406": "city", "Q1133035": "river", "Q2188006": "river", "Q12892": "city", "Q338137": "river", "Q13712": "river",
    "Q1556007": "mountain", "Q180402": "mountain", "Q10285": "building", "Q555450": "river", "Q5463": "mountain", "Q1495651": "mountain",
    "Q2587792": "building", "Q1754": "city", "Q839537": "city", "Q249062": "river", "Q327": "region", "Q22158811": "coast", "Q189358": "building",
    "Q1616324": "coast", "Q2360422": "mountain", "Q1310": "city", "Q52531": "building", "Q182872": "city", "Q189883": "building", "Q155": "region",
    "Q3921376": "building", "Q41983": "river", "Q20": "region", "Q26777": "mountain", "Q183557": "city", "Q686703": "building", "Q40430": "region",
    "Q231720": "city", "Q42810": "city", "Q2441211": "building", "Q920444": "city",
}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    raise ValueError(f)


def qid(s):
    m = re.search(r"/entity/(Q\d+)>", s or "")
    return m.group(1) if m else ""


def label(s):
    """'"Seine"@en' -> 'Seine'; QLever escapes inner quotes as \\"."""
    s = (s or "").strip()
    m = re.fullmatch(r'"(.*)"(@[\w-]+)?', s, re.S)
    t = m.group(1) if m else s
    return t.replace('\\"', '"').replace("\\\\", "\\").strip()


def point(s):
    """'POINT(lon lat)' -> (lat, lon); anything else (another globe, an unknown value) -> None."""
    m = re.fullmatch(r"POINT\((-?[\d.]+(?:e-?\d+)?) (-?[\d.]+(?:e-?\d+)?)\)", (s or "").strip())
    return (float(m.group(2)), float(m.group(1))) if m else None


def read_tsv(name):
    import pandas as pd
    df = pd.read_csv(f"{RAW}/{name}", sep="\t", dtype=str, keep_default_na=False, quoting=3)
    df.columns = [c.lstrip("?") for c in df.columns]
    return df


def gc_km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))
