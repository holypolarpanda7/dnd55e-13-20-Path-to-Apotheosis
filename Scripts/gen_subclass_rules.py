"""Subclass features at levels 13-20, from the rules texts, for the level-up checks (2026-10-05).

Writes tests/bg3/rules/local/subclasses.toml (book-derived: local only, like The Oracle keeps it): one [[subclass_feature]]
per feature with its source and how sure we are -
  verified  the feature's "LEVEL N: NAME" line was found in an owned text (PHB 2024, the library excerpts, ...)
  oracle    from The Oracle's ingested data (rules_subclass) only; the owned texts don't show the line (scan gaps)
  reference read from the library excerpts/subclasses (the texts the mod's third-party 13+ features were built from)
  memory    from knowledge of a book we don't have as text (Tasha's, PHB/DMG 2014, SCAG) - review these
  none      the subclass has no source with features past 12 (dnd55e's own design): nothing is expected at 13-20

and tests/bg3/rules/aliases.toml's [subclass] table maps the mod's subclass names to the rules names.
Run after gen_rules_tables.py: python3 Scripts/gen_subclass_rules.py
"""
import ast
import glob
import json
import os
import re
import sqlite3

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORACLE = os.environ.get("ORACLE_ROOT", "/mnt/d/Projects/The Oracle")
LIBRARY = os.environ.get("DND_LIBRARY", "/mnt/d/Library/DnD")   # the shared source library (CATALOG.md there)
BOOKS = os.path.join(LIBRARY, "text")
DB = os.path.join(ORACLE, "oracle-dm-backend", "oracle.db")
REFS = glob.glob(os.path.join(LIBRARY, "excerpts", "subclasses", "*.txt")) + \
    [os.path.join(LIBRARY, "excerpts", "classes", "UA-Arcane Subclasses.txt")]
OUT = os.path.join(REPO, "tests", "bg3", "rules")

# mod subclass (ClassDescription Name) -> (class, rules subclass name). Only where the names differ.
ALIASES = {
    "ChoreographyCollege": ("Bard", "College of Choreography"), "Fractured": ("Barbarian", "Path of the Fractured"),
    "CircleOfTheUnbroken": ("Druid", "Circle of the Unbroken"), "CircleOfDragons": ("Druid", "Circle of Dragons"),
    "AstralDomain": ("Cleric", "Astral Domain"), "BladeOfRadiance": ("Rogue", "Blade of Radiance"),
    "MysticArts": ("Monk", "Warrior of the Mystic Arts"),
    "HighRoller": ("Gunslinger", "High Roller"), "WhiteHat": ("Gunslinger", "White Hat"),
    "ArchitectOfRuin": ("Illrigger", "Architect of Ruin"), "SanguineKnight": ("Illrigger", "Sanguine Knight"),
    "ValorCollege": ("Bard", "College of Valor"),
    "DraconicBloodline": ("Sorcerer", "Draconic Sorcery"),
    "FourElements": ("Monk", "Warrior of the Elements"),
    "Shadow": ("Monk", "Warrior of Shadow"),
    "OpenHand": ("Monk", "Warrior of the Open Hand"),
    "Mercy": ("Monk", "Warrior of Mercy"),
    "ShadowMagic": ("Sorcerer", ["Shadow Magic", "Shadow Sorcery"]),
    "Hexblade": ("Warlock", ["The Hexblade", "Hexblade Patron"]),
    "TotemWarriorPath": ("Barbarian", "Path of the Wild Heart"),
    "DeadThree": ("Rogue", "Scion of the Three"),
    "CircleOfStars": ("Druid", "Circle of the Stars"),
    "WildMagic": ("Sorcerer", "Wild Magic Sorcery"),
    "WildMagicPath": ("Barbarian", "Path of Wild Magic"),
    "AbjurationSchool": ("Wizard", "Abjurer"), "ConjurationSchool": ("Wizard", "Conjurer"),
    "DivinationSchool": ("Wizard", "Diviner"), "EnchantmentSchool": ("Wizard", "Enchanter"),
    "EvocationSchool": ("Wizard", "Evoker"), "IllusionSchool": ("Wizard", "Illusionist"),
    "NecromancySchool": ("Wizard", "Necromancer"), "TransmutationSchool": ("Wizard", "Transmuter"),
    "BladesingingSchool": ("Wizard", "Bladesinger"),
}

# Books we don't have as text: features at 13-20 from knowledge of the book (confidence "memory" - review).
MEMORY = {
    ("Barbarian", "Path of Wild Magic"): ("Tasha's Cauldron of Everything", {14: ["Controlled Surge"]}),
    ("Barbarian", "Shadow Gnawer"): ("Book of Ebon Tides (Open Design 2022)", {14: ["Corrosive Haze"]}),
    ("Cleric", "Death Domain"): ("Dungeon Master's Guide 2014", {17: ["Improved Reaper"]}),
    ("Cleric", "Nature Domain"): ("Player's Handbook 2014", {17: ["Master of Nature"]}),
    ("Cleric", "Tempest Domain"): ("Player's Handbook 2014", {17: ["Stormborn"]}),
    ("Cleric", "Twilight Domain"): ("Tasha's Cauldron of Everything", {17: ["Twilight Shroud"]}),
    ("Cleric", "Mind Domain"): ("Exploring Eberron", {17: ["Bend Reality"]}),
    ("Cleric", "Shadow Domain"): ("Book of Ebon Tides (Open Design 2022)", {17: ["Army of Shadow"]}),
    ("Druid", "Circle of the Spores"): ("Tasha's Cauldron of Everything", {14: ["Fungal Body"]}),
    ("Fighter", "Rune Knight"): ("Tasha's Cauldron of Everything", {15: ["Master of Runes"], 18: ["Runic Juggernaut"]}),
    ("Paladin", "Oath of the Crown"): ("Sword Coast Adventurer's Guide", {15: ["Unyielding Spirit"], 20: ["Exalted Champion"]}),
    ("Paladin", "Oathbreaker"): ("Dungeon Master's Guide 2014", {15: ["Supernatural Resistance"], 20: ["Dread Lord"]}),
    ("Paladin", "Oath of the Watchers"): ("Tasha's Cauldron of Everything", {15: ["Vigilant Rebuke"], 20: ["Mortal Bulwark"]}),
    ("Ranger", "Swarmkeeper"): ("Tasha's Cauldron of Everything", {15: ["Swarming Dispersal"]}),
    ("Rogue", "Arachnoid Stalker"): ("Valda's Spire of Secrets (2024)", {13: ["Web Walker"], 17: ["Paralytic Venom"]}),
    ("Rogue", "Highway Rider"): ("Grim Hollow Player's Guide", {13: ["True Grit"], 17: ["Desperado"]}),
    ("Sorcerer", "Shadow Magic"): ("Xanathar's Guide to Everything", {14: ["Shadow Walk"], 18: ["Umbral Form"]}),
    ("Warlock", "Undead Patron"): ("Van Richten's Guide to Ravenloft", {14: ["Spirit Projection"]}),
    ("Wizard", "Conjurer"): ("Player's Handbook 2014", {14: ["Durable Summons"]}),
    ("Wizard", "Enchanter"): ("Player's Handbook 2014", {14: ["Alter Memories"]}),
    ("Wizard", "Necromancer"): ("Player's Handbook 2014", {14: ["Command Undead"]}),
    ("Wizard", "Transmuter"): ("Player's Handbook 2014", {14: ["Master Transmuter"]}),
}
# Third-party subclasses read from References/Subclasses (the texts their 13+ features were built from): confidence "reference"
REFERENCE = {
    ("Barbarian", "Path of the Fractured"): ("References/Subclasses/missing_subclass_ref.txt (Grim Hollow)", {14: ["Better Half"]}),
    ("Fighter", "Viking"): ("References/Subclasses/missing_subclass_ref.txt (Kobold Press Northlands)",
                            {15: ["Marauder's Reprisal"], 18: ["Unstoppable Assault"]}),
    ("Cleric", "Astral Domain"): ("References/Subclasses/missing_subclass_ref.txt (Griffon's Saddlebag)", {17: ["Supreme Switching"]}),
    ("Rogue", "Blade of Radiance"): ("References/Subclasses/missing_subclass_ref.txt", {13: ["Saintly Revelations"], 17: ["Final Judgement"]}),
    ("Druid", "Circle of the Unbroken"): ("References/Subclasses/missing_subclass_ref.txt (Griffon's Saddlebag)", {14: ["Nature Armor"]}),
    ("Druid", "Circle of Dragons"): ("References/Subclasses/griffons_saddlebag_circle_of_dragons.txt", {14: ["Heart of a Dragon"]}),
    ("Sorcerer", "Frost Sorcery"): ("\"Frost Magic\", The Griffon's Saddlebag: Book One p.167 (page photographed by the user 2026-10-04)",
                                    {14: ["Flash Freeze"], 18: ["Frozen Soul"]}),
    ("Sorcerer", "Heroic Sorcery"): ("Mage Hand Press \"Reincarnated Hero\" (page photographed by the user 2026-10-04)",
                                     {14: ["Sorcerous Kindling"], 18: ["Heroic Legacy"]}),
    ("Bard", "College of Choreography"): ("Griffon's Saddlebag page photographed by the user 2026-10-04 (docs/SUBCLASS_SOURCING.md)",
                                          {14: ["Fast Movement", "Entrancing Movement", "Endless Dance"]}),
    ("Cleric", "Apocalypse Domain"): ("Cthulhu by Torchlight, pages photographed by the user 2026-10-05 (library "
                                      "excerpts/subclasses/ApocalypseDomain_CthulhuByTorchlight.txt)", {17: ["Life Beyond Death"]}),
    ("Cleric", "Dragon Domain"): ("Valda's Spire of Secrets: Player Pack 2, page photographed by the user 2026-10-05 (library "
                                  "excerpts/subclasses/DragonDomain_ValdasSpire_PlayerPack2.txt)", {17: ["Legendary Aspect"]}),
}
# PHB 2024 features whose page is missing from the text extract and from The Oracle's ingest
MEMORY.update({
    ("Sorcerer", "Draconic Sorcery"): ("Player's Handbook 2024 (page missing from the text)", {18: ["Dragon Companion"]}),
    ("Fighter", "Eldritch Knight"): ("Player's Handbook 2024 (page missing from the text)", {18: ["Improved War Magic"]}),
    # XGE's Arcane Shot improves at 18 (damage dice) - written as its own line in the mod
    ("Fighter", "Arcane Archer"): ("Xanathar's Guide to Everything (Arcane Shot, 18th level)", {18: ["Improved Shots"]}),
})

# a book's names in The Oracle's source tags: a missing-page feature joins that book's version of the subclass
BOOK_TAGS = {"Player's Handbook 2024": ["PHB 2024", "SRD/PHB"], "Xanathar's Guide to Everything": ["Xanathar"],
             "Van Richten's Guide to Ravenloft": ["Van Richten", "Ravenloft"]}

# scan errors in The Oracle's ingested names
NAME_FIX = {"Jllus Ory Reality": "Illusory Reality", "Keeper Ofsouls": "Keeper of Souls"}

# Subclasses with no source past level 12 (docs/SUBCLASS_SOURCING.md: dnd55e's own design, or no text reachable).
NONE = {}


def norm(s):
    s = re.sub(r"\([^)]*\)", "", str(s)).lower().replace("’", "'")
    return re.sub(r"[^a-z0-9]", "", s)


def level_lines(path):
    """Every 'LEVEL N: NAME' line of a text: [(line no, level, normalised name, name)]."""
    out = []
    for i, line in enumerate(open(path, encoding="utf-8", errors="replace")):
        m = re.match(r"\s*LEVEL\s*(\d+)\s*:\s*(.+?)\s*$", line, re.I)
        if m:
            out.append((i, int(m.group(1)), norm(m.group(2)), re.sub(r"\s+", " ", m.group(2)).title()))
    return out


# the UA Arcane Subclasses text is two-column: a feature can sit after the NEXT subclass's header in reading order
REF_MOVE = {("Wizard", "Enchanter", "Splintered Summons"): ("Wizard", "Conjurer")}


def ref_sections():
    """Library excerpts/subclasses texts: 'CLASS: SUBCLASS' headers, then LEVEL lines -> {(class, subclass): {level: [names]}}."""
    out = {}
    for f in REFS:
        cur = None
        for line in open(f, encoding="utf-8", errors="replace"):
            if line.startswith("#"):
                cur = None
                continue
            classes = ("Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock",
                       "Wizard")
            h = re.match(r"\s*([A-Z]+):\s*([A-Z][A-Z' ]+?)\s*$", line)          # "WARLOCK: HEXBLADE PATRON"
            h2 = re.match(r"\s*([A-Z][A-Za-z'’ ]+?)\s*\(([A-Za-z]+)\)\s*$", line)  # "CONJURER (WIZARD)", "Conjurer (Wizard)"
            if h and h.group(1).title() in classes:
                cur = (h.group(1).title(), h.group(2).title().replace("'S", "'s"))
                continue
            if h2 and h2.group(2).title() in classes:
                cur = (h2.group(2).title(), h2.group(1).strip().title().replace("'S", "'s").replace("’S", "’s").replace(" Of ", " of ").replace(" The ", " the "))
                continue
            m = re.match(r"\s*LEVEL\s*(\d+)\s*:\s*(.+?)\s*$", line, re.I)
            if cur and m:
                name = re.sub(r"\s+", " ", m.group(2)).title().replace("’S", "’s").replace("'S", "'s")
                key = REF_MOVE.get((cur[0], cur[1], name), cur)
                out.setdefault(key, {}).setdefault(int(m.group(1)), []).append((name, os.path.basename(f)))
    return out


CLASS_REFS = os.path.join(LIBRARY, "excerpts", "classes")
OTHER_SUBS = {"Gunslinger": ["Deadeye", "Secret Agent", "Trick Shot"]}
CLASS_SUBS = {"Gunslinger": ["High Roller", "Spellslinger", "White Hat"],
              "Illrigger": ["Architect of Ruin", "Hellspeaker", "Painkiller", "Sanguine Knight", "Shadowmaster"]}


def class_ref_subclasses():
    """Subclass features 13-20 from the class files in the library excerpts/classes (Gunslinger: subclass headings + "Level N: Name";
    Illrigger, MCDM's 2014 layout: a title line then "15th-Level Architect of Ruin Feature", and "Name (13th Level)" boons)."""
    out = {}
    for cls, subs in CLASS_SUBS.items():
        path = os.path.join(CLASS_REFS, f"{cls}.txt")
        if not os.path.exists(path):
            continue
        lines = [l.strip() for l in open(path, encoding="utf-8", errors="replace") if l.strip()]
        cur = None
        for i, line in enumerate(lines):
            # a subclass heading - including the file's subclasses the mod doesn't use, which must end the previous one
            if line in subs or line in OTHER_SUBS.get(cls, ()):
                cur = line
                continue
            m = re.match(r"Level\s*(\d+)\s*:\s*(.+?)(?:\s*\[.*\])?$", line, re.I)
            if m and cur in subs and int(m.group(1)) >= 13:
                out.setdefault((cls, cur), {}).setdefault(int(m.group(1)), []).append(m.group(2).strip())
                continue
            m = re.match(r"(\d+)(?:st|nd|rd|th)-Level (.+?) Features?$", line)
            if m and m.group(2) in subs and int(m.group(1)) >= 13:
                title = next((lines[k] for k in range(i - 1, max(0, i - 4), -1) if lines[k]), "")
                out.setdefault((cls, m.group(2)), {}).setdefault(int(m.group(1)), []).append(title)
                continue
            for name, lv in re.findall(r"(?:^|\. )([A-Z][A-Za-z'’ ]{2,40}) \((\d+)(?:st|nd|rd|th) Level", line):
                if cur in subs and int(lv) >= 13:
                    out.setdefault((cls, cur), {}).setdefault(int(lv), []).append(name.strip())
    return out


def main():
    texts = {os.path.basename(p): level_lines(p) for p in glob.glob(os.path.join(BOOKS, "*.txt")) + REFS}
    refs = ref_sections()
    for k, v in class_ref_subclasses().items():
        for lv, names in v.items():
            refs.setdefault(k, {}).setdefault(lv, []).extend((n, f"excerpts/classes/{k[0]}.txt") for n in names)
    con = sqlite3.connect(DB)
    oracle = {}
    for name, cls, feats, src in con.execute("SELECT name, class_name, features, source FROM rules_subclass"):
        try:
            fl = json.loads(feats) if feats else []
        except json.JSONDecodeError:
            fl = ast.literal_eval(feats)
        oracle[(cls, name)] = (src, fl)

    import difflib
    raw = {os.path.basename(p): [l.rstrip("\n") for l in open(p, encoding="utf-8", errors="replace")]
           for p in glob.glob(os.path.join(BOOKS, "*.txt"))}
    ordinal = lambda n: f"{n}th" if n in (13, 14, 15, 16, 17, 18, 19, 20) else str(n)

    def verify(level, name):
        n = norm(name)
        for fn, lines in texts.items():   # 2024 layout: "LEVEL 14: NAME" (scan-garbled names compared loosely)
            for _, lv, nn, real in lines:
                if lv == level and nn == n:
                    return fn, real
                if lv == level and ((len(n) > 6 and (n in nn or nn in n)) or difflib.SequenceMatcher(None, n, nn).ratio() >= 0.85):
                    return fn, name           # a scan-garbled line: keep the clean name
        for fn, lines in raw.items():     # 2014 layout: a "Name" heading line, "At 14th level" / "Starting at 14th level" below it
            for i, line in enumerate(lines):
                if norm(line) == n and len(n) > 4:
                    near = re.sub(r"\s+", "", " ".join(lines[i + 1:i + 6]).lower())   # the XGE text runs words together
                    if f"{ordinal(level)}level" in near:
                        return fn, name
        return None, None

    rows, report = [], {"verified": 0, "oracle": 0, "reference": 0, "memory": 0, "none": 0}
    keys = set(oracle) | set(MEMORY) | set(refs) | set(NONE) | set(REFERENCE)
    for key in sorted(keys):
        cls, sub = key
        if key in NONE:
            rows.append({"class": cls, "subclass": sub, "level": 0, "name": "", "confidence": "none", "source": NONE[key]})
            report["none"] += 1
            continue
        feats = {}
        # every version of the subclass is kept, tagged with its group (one book / text): the check picks the version the
        # mod follows (Conjurer: PHB 2014 Durable Summons vs UA Arcane Subclasses Splintered Summons)
        if key in oracle:
            src = oracle[key][0].split(" — ")[0].split(" (local")[0]
            for f in oracle[key][1]:
                nm = NAME_FIX.get(f.get("name", ""), f.get("name", ""))
                feats.setdefault(int(f.get("level", 0)), []).append((nm, "oracle", oracle[key][0], f"oracle: {src}"))
        for lv, names in refs.get(key, {}).items():
            for n, fname in names:
                feats.setdefault(lv, []).append((n, "verified", fname, f"text: {fname}"))
        if key in REFERENCE:
            book, m = REFERENCE[key]
            for lv, names in m.items():
                for n in names:
                    feats.setdefault(lv, []).append((n, "reference", book, f"reference: {book.split(' (')[0]}"))
        if key in MEMORY:
            book, m = MEMORY[key]
            groups = {x[3] for v in feats.values() for x in v}
            for lv, names in m.items():
                have = {norm(x[0]) for x in feats.get(lv, [])}
                for n in names:
                    if norm(n) not in have:
                        # a missing page of a book another group already covers joins that group; else its own version
                        tags = BOOK_TAGS.get(book.split(" (")[0], [book.split(" (")[0]])
                        grp = next((g for g in groups if any(tg.lower() in g.lower() for tg in tags)), f"memory: {book.split(' (')[0]}")
                        feats.setdefault(lv, []).append((n, "memory", book, grp))
        for lv in sorted(feats):
            if lv < 13:
                continue
            seen = set()
            for name, conf, src, grp in feats[lv]:
                fn, real = verify(lv, name)
                if fn:
                    name, conf, src = (real if conf != "verified" else name), "verified", fn
                if (grp, norm(name)) in seen:
                    continue
                seen.add((grp, norm(name)))
                rows.append({"class": cls, "subclass": sub, "level": lv, "name": name, "confidence": conf, "source": src,
                             "group": grp})
                report[conf] += 1
    # a level line in an owned text the sources above lack is reported, not added (its subclass isn't known from the text)
    out = ["# GENERATED by Scripts/gen_subclass_rules.py - subclass features at levels 13-20 from the rules texts.",
           "# Book-derived: LOCAL ONLY. confidence: verified (line found in an owned text) / oracle / memory / none.", ""]
    for r in rows:
        out += ["[[subclass_feature]]"] + [f"{k} = {json.dumps(v, ensure_ascii=False)}" for k, v in r.items()] + [""]
    os.makedirs(os.path.join(OUT, "local"), exist_ok=True)
    open(os.path.join(OUT, "local", "subclasses.toml"), "w", encoding="utf-8", newline="\n").write("\n".join(out))
    al = ["# Mod subclass (ClassDescription Name) -> the rules subclass name, where they differ. Scripts/gen_subclass_rules.py", "",
          "[subclass]"] + [f"{k} = {json.dumps(v[1])}" for k, v in sorted(ALIASES.items())]
    open(os.path.join(OUT, "aliases.toml"), "w", encoding="utf-8", newline="\n").write("\n".join(al) + "\n")
    print(f"{len(rows)} subclass features 13-20: {report}")


if __name__ == "__main__":
    main()
