"""Parse the Tamil Nadu crop list into grouped catalogue JSON for the farmer app."""
import re, json, sys

SRC = sys.argv[1]
GROUPS = {  # number -> (short English, Tamil, emoji, tile colour)
    1: ("Paddy and cereals", "நெல் மற்றும் தானியங்கள்", "🌾", "#F3EBC9"),
    2: ("Pulses and legumes", "பருப்பு வகைகள்", "🫘", "#EDE3D6"),
    3: ("Oilseeds", "எண்ணெய் வித்துக்கள்", "🥜", "#F1E6D3"),
    4: ("Sugar, fibre, industrial", "கரும்பு, நார், தொழில் பயிர்கள்", "🎋", "#E1EFD6"),
    5: ("Vegetables", "காய்கறிகள்", "🥕", "#FCE5CF"),
    6: ("Fruits", "பழங்கள்", "🥭", "#FCE8C4"),
    7: ("Spices", "மசாலா பயிர்கள்", "🌶️", "#F9DDD7"),
    8: ("Flowers", "பூக்கள்", "🌼", "#FBF0C9"),
    9: ("Plantation crops", "தோட்டப் பயிர்கள்", "☕", "#EDE3D6"),
    10: ("Medicinal and aromatic", "மூலிகை, நறுமணப் பயிர்கள்", "🌿", "#DDEFD9"),
    11: ("Fodder crops", "தீவனப் பயிர்கள்", "🐄", "#E6EED9"),
    12: ("Trees and timber", "மரப் பயிர்கள்", "🌳", "#DDEFD9"),
    13: ("Other farm produce", "பிற பண்ணைப் பொருட்கள்", "🌱", "#E8ECE4"),
}
SUBS_TA = {"A": "காய் வகைகள்", "B": "பூசணி, சுரை வகைகள்", "C": "அவரை, பீன்ஸ் வகைகள்", "D": "கீரை வகைகள்",
           "E": "கிழங்கு, வெங்காய வகைகள்", "F": "முட்டைக்கோஸ் மற்றும் பிற"}
QUAL = re.compile(r"limited|specialis|suitable|localised|also used|check legal|not a field|fibre|wood|food and|for sericulture|very |supported|local", re.I)
EMOJI = [  # first keyword match wins
    ("teak", "🌳"), ("turmeric", "🫚"), ("tomato", "🍅"), ("brinjal", "🍆"), ("okra", "🫛"), ("capsicum", "🫑"), ("chilli", "🌶️"), ("watermelon", "🍉"), ("muskmelon", "🍈"),
    ("cucumber", "🥒"), ("pumpkin", "🎃"), ("gourd", "🥒"), ("sweet potato", "🍠"), ("potato", "🥔"), ("carrot", "🥕"), ("onion", "🧅"), ("shallot", "🧅"),
    ("garlic", "🧄"), ("ginger", "🫚"), ("cabbage", "🥬"), ("cauliflower", "🥦"), ("broccoli", "🥦"), ("knol", "🥬"), ("greens", "🥬"), ("amaranth", "🥬"),
    ("spinach", "🥬"), ("fenugreek leaves", "🥬"), ("leaves", "🌿"), ("mint", "🌿"), ("drumstick", "🌿"), ("raw banana", "🍌"), ("banana", "🍌"),
    ("mango", "🥭"), ("grape", "🍇"), ("pineapple", "🍍"), ("orange", "🍊"), ("lemon", "🍋"), ("lime", "🍋"), ("pomegranate", "🍎"), ("strawberry", "🍓"),
    ("avocado", "🥑"), ("coconut", "🥥"), ("palm", "🌴"), ("palmyra", "🌴"), ("paddy", "🌾"), ("maize", "🌽"), ("fodder maize", "🌽"), ("millet", "🌾"),
    ("sorghum", "🌾"), ("wheat", "🌾"), ("barley", "🌾"), ("oats", "🌾"), ("grass", "🌾"), ("groundnut", "🥜"), ("cashew", "🥜"), ("sunflower", "🌻"),
    ("sugarcane", "🎋"), ("bamboo", "🎋"), ("cotton", "☁️"), ("tea", "🍵"), ("coffee", "☕"), ("cocoa", "🍫"), ("rose", "🌹"), ("lotus", "🪷"),
    ("lily", "🪷"), ("jasmine", "🌼"), ("marigold", "🌼"), ("chrysanthemum", "🌼"), ("orchid", "🌸"), ("gerbera", "🌸"), ("carnation", "🌸"),
    ("gladiolus", "🌸"), ("flower", "🌸"), ("aloe", "🪴"), ("nursery", "🪴"), ("ornamental", "🪴"), ("sapling", "🪴"), ("teak", "🌳"), ("neem", "🌳"),
    ("eucalyptus", "🌳"), ("tree", "🌳"), ("sandal", "🌳"), ("bean", "🫘"), ("gram", "🫘"), ("pea", "🫘"), ("cowpea", "🫘"), ("soybean", "🫘"),
    ("lucerne", "🌿"), ("pepper", "🌶️"), ("tamarind", "🫛"), ("jackfruit", "🍈"), ("papaya", "🍈"), ("guava", "🍐"), ("fig", "🍐"), ("sapota", "🍐"),
    ("apple", "🍎"), ("seed", "🌰"), ("cassava", "🍠"), ("tapioca", "🍠"), ("yam", "🍠"), ("taro", "🍠"), ("beetroot", "🫜"), ("radish", "🥕"),
]


def emoji_for(name, gnum):
    low = name.lower()
    for k, e in EMOJI:
        if re.search(r"\b" + re.escape(k) + r"(s|es)?\b", low):
            return e
    return GROUPS[gnum][2]


def clean(line):
    m = re.match(r"^(.*?)\s*\((.*)\)\s*$", line)
    if not m:
        return line.strip(), ""
    base, inner = m.group(1).strip(), m.group(2).strip()
    keep, qual = [], []
    for part in [p.strip() for p in inner.split(";")]:
        (qual if QUAL.search(part) else keep).append(part)
    name = base + (" (" + "; ".join(keep) + ")" if keep else "")
    return name, "; ".join(qual)


lines = open(SRC, encoding="utf8").read().splitlines()
groups, cur, sub = [], None, None
for raw in lines:
    s = raw.strip()
    if s.startswith("WHERE DIFFERENT GROUPS"):
        break
    m = re.match(r"^(\d+)\.\s+[A-Z][A-Z ,\-/]+$", s)
    if m:
        n = int(m.group(1))
        g = GROUPS[n]
        cur = {"id": "g%d" % n, "en": g[0], "ta": g[1], "e": g[2], "bg": g[3], "subs": []}
        sub = {"en": "", "ta": "", "items": []}
        cur["subs"].append(sub)
        groups.append(cur)
        continue
    if cur is None or not s or s.startswith("Note:"):
        continue
    m = re.match(r"^([A-F])\.\s+(.*):$", s)
    if m:
        if not sub["items"]:
            cur["subs"].remove(sub)
        sub = {"en": m.group(2), "ta": SUBS_TA[m.group(1)], "items": []}
        cur["subs"].append(sub)
        continue
    name, q = clean(s)
    gn = int(cur["id"][1:])
    sub["items"].append({"id": "%s_%d" % (cur["id"], sum(len(x["items"]) for x in cur["subs"]) + 1), "n": name, "q": q, "e": emoji_for(name, gn)})

total = sum(len(i["items"]) for g in groups for i in g["subs"])
json.dump(groups, open(sys.argv[2], "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
print(len(groups), "groups,", total, "crops")
for g in groups:
    print(" ", g["e"], g["en"], [len(s["items"]) for s in g["subs"]], "|", ", ".join(i["e"] + i["n"] + ("[" + i["q"] + "]" if i["q"] else "") for s in g["subs"] for i in s["items"])[:260])
