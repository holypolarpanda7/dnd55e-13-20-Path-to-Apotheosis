"""Shared helpers for the class generators (gen_illrigger.py, ...): stats entries, loca handles, idempotent
patches of Progressions / ActionResourceDefinitions / LevelMapValues / PassiveLists / loca between markers,
creature stats (Character_*.txt) and root templates (RootTemplates/*.lsf, built as LSX and converted with Divine
through the bg3-data CLI)."""
import glob
import os
import re
import subprocess
import tempfile
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = glob.glob(os.path.join(REPO, "Public", "*"))[0]
DATA = os.path.join(PUB, "Stats", "Generated", "Data")
LOCA = glob.glob(os.path.join(REPO, "Mods", "*", "Localization", "English", "dnd55e-Apotheosis.xml"))[0]
# dnd55e as the game loads it: the dependency pak, extracted by the bg3-data MCP (layer `dnd55e`, see
# bg3deps.lock.json). DND55E_ROOT overrides; the git clone is only a fallback (it runs ahead of the release).
DND = (glob.glob(os.path.join(os.environ.get("DND55E_ROOT", os.path.expanduser("~/.cache/bg3-data-mcp/cache/mods/dnd55e")),
                              "Public", "DnD2024*"))
       or glob.glob(os.path.join(REPO, "..", "dnd55e", "Public", "DnD2024*")))[0]
NODE_RE = re.compile(r'[ \t]*<node id="Progression">(?:(?!</node>).)*?</node>\n', re.S)
# A spell with no SpellAnimation (own or inherited) never finishes casting - verified in game 2026-09-30.
SHOUT_ANIM = "9122eb08-93f1-4010-a275-f5ae3ec7c76e,,;,,;9fb11cca-02d4-4d2f-955f-2826c0553b17,,;5103d398-d8de-4aa4-9633-db2e1b7f6254,,;5301d674-b7da-47b6-b4cf-2802ba33a9e9,,;,,;86b3cf93-21fb-4a3d-bed9-97d0a567d084,,;,,;,,"
TARGET_ANIM = "3ff87abf-1ea1-4c32-aadf-c822d74c7dc0,,;,,;ab7b6aac-b3c9-4918-8f17-f777a94dcb5e,,;57211a11-ed0b-46d7-9369-81df25a85df6,,;d8925ce4-d6d9-400c-92f5-ad772ef7f178,,;,,;eadedcce-d01b-4fbb-a1ae-d218f13aa5d6,,;,,;,,"


def icon_of(name, fallback="PassiveFeature_Generic"):
    """The Icon an existing stats entry uses (base / dnd55e / Apotheosis, from the bg3-data MCP index): reuse a
    subclass's own earlier feature icon instead of guessing names that don't exist (29 guesses on 2026-10-03)."""
    import json
    import sqlite3
    db = os.path.expanduser("~/.cache/bg3-data-mcp/cache/index.sqlite")
    try:
        con = sqlite3.connect(db)
        for (data,) in con.execute("SELECT data FROM stats WHERE name=? ORDER BY rank DESC", (name,)):
            icon = json.loads(data).get("Icon")
            if icon:
                return icon
    except sqlite3.Error:
        pass
    return fallback


class Gen:
    def __init__(self, key, marker):
        self.key, self.marker = key, marker
        self.P, self.S, self.SP, self.I, self.C, self.T = [], [], [], [], [], []
        self.TI = []  # item root templates (traps)
        self.loca, self.resources, self.lists, self.levelmaps = {}, [], [], []

    def gid(self, k):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"apotheosis-{self.key}:{k}"))

    def h(self, k, text):
        handle = "h" + uuid.uuid5(uuid.NAMESPACE_URL, f"apotheosis-{self.key}-loca:{k}").hex
        self.loca[handle] = text
        return handle

    @staticmethod
    def entry(name, typ, fields, using=None, comment=None):
        out = ([f"// {comment}"] if comment else []) + [f'new entry "{name}"', f'type "{typ}"']
        if using:
            out.append(f'using "{using}"')
        out += [f'data "{k}" "{v}"' for k, v in fields.items() if v is not None]
        return "\n".join(out) + "\n"

    def passive(self, name, title, text, fields=None, icon="PassiveFeature_Generic_Magical", hidden=False, comment=None, using=None):
        base = {"DisplayName": self.h(name + ":n", title), "Description": self.h(name + ":d", text), "Icon": icon,
                "Properties": "IsHidden" if hidden else "Highlighted"}
        self.P.append(self.entry(name, "PassiveData", {**base, **(fields or {})}, using=using, comment=comment))

    def status(self, name, title, text, fields=None, using=None, icon=None, comment=None):
        base = {"DisplayName": self.h(name + ":n", title)}
        if text:
            base["Description"] = self.h(name + ":d", text)
        if icon:
            base["Icon"] = icon
        if not using:
            base["StatusType"] = "BOOST"
        self.S.append(self.entry(name, "StatusData", {**base, **(fields or {})}, using=using, comment=comment))

    def spell(self, name, title, text, fields, using=None, icon=None, comment=None):
        base = {"DisplayName": self.h(name + ":n", title), "Description": self.h(name + ":d", text)}
        if icon:
            base["Icon"] = icon
        f = {**base, **fields}
        if not using and "SpellAnimation" not in f and "ContainerSpells" not in f:
            f["SpellAnimation"] = SHOUT_ANIM if f.get("SpellType") == "Shout" else TARGET_ANIM
        self.SP.append(self.entry(name, "SpellData", f, using=using, comment=comment))

    def interrupt(self, name, title, text, fields, icon=None, comment=None):
        base = {"DisplayName": self.h(name + ":n", title), "Description": self.h(name + ":d", text)}
        if icon:
            base["Icon"] = icon
        self.I.append(self.entry(name, "InterruptData", {**base, **fields}, comment=comment))

    def character(self, name, fields, using=None, comment=None):
        self.C.append(self.entry(name, "Character", fields, using=using, comment=comment))

    def template(self, key, name, parent, stats, title, skills=(), level=None, spellset="CommonPlayerActions", extra=None):
        """A character root template (a new creature): MapKey is stable per generator key. The model and effects come
        from `parent` (a base-game template) - swap it, or add VisualTemplate/CharacterVisualResourceID in `extra`,
        to give the creature a new look. title=None / spellset=None inherit them from the parent. Returns the MapKey."""
        mk = self.gid("template:" + key)
        handle = self.h(f"template:{key}", title) if title is not None else None
        self.T.append(dict(mk=mk, name=name, parent=parent, stats=stats, handle=handle,
                           skills=list(skills), level=level, spellset=spellset, extra=extra or {}))
        return mk

    def item_template(self, key, name, parent, projectile):
        """A trap item root template: it carries one thing, the name of the projectile spell the trap casts (the
        `Projectile` constellation parameter, as the base game's PUZ_Trap_Spell_* items). Returns the MapKey."""
        mk = self.gid("template:" + key)
        self.TI.append(dict(mk=mk, name=name, parent=parent, projectile=projectile))
        return mk

    # ------------------------------------------------------------ writers
    def write_templates(self, fname):
        """Write the templates as Public/<mod>/RootTemplates/<fname>.lsf (binary, what the game loads)."""
        path = os.path.join(PUB, "RootTemplates", fname + ".lsf")
        if not self.T and not self.TI:
            if os.path.exists(path):
                os.remove(path)
            return
        a = lambda i, t, v: f'<attribute id="{i}" type="{t}" value="{v}" />'
        cond = ('<node id="{0}">' + a("MinimumHealthPercentage", "int32", 0) + a("MaximumHealthPercentage", "int32", 100)
                + '<children><node id="Tags" /></children></node>')
        skill = lambda sp: ('<node id="Skill">' + a("Skill", "FixedString", sp) + a("SpellCastingAbility", "uint8", 0)
                            + a("LearningStrategy", "uint8", 0) + a("ScoreModifier", "float", 1) + a("StartRound", "int32", 0)
                            + a("FallbackStartRound", "int32", -1) + a("MinimumImpact", "int32", 0)
                            + a("OnlyCastOnSelf", "bool", "False") + a("AIFlags", "uint16", 0)
                            + "<children>" + cond.format("SourceConditions") + cond.format("TargetConditions")
                            + "</children></node>")
        objs = []
        for t in self.T:
            o = ['<node id="GameObjects">', a("MapKey", "FixedString", t["mk"]), a("Name", "LSString", t["name"]),
                 a("LevelName", "FixedString", ""), a("Type", "FixedString", "character"),
                 a("ParentTemplateId", "FixedString", t["parent"]),
                 *([f'<attribute id="DisplayName" type="TranslatedString" handle="{t["handle"]}" version="1" />']
                   if t["handle"] else []),
                 a("Stats", "FixedString", t["stats"])]  # (same order as before: existing LSX digests stay stable)
            if t["spellset"] is not None:  # "" deliberately clears the parent's spell set
                o.append(a("SpellSet", "FixedString", t["spellset"]))
            if t["level"]:
                o.append(a("LevelOverride", "int32", t["level"]))
            o += [a(k, typ, v) for k, (typ, v) in t["extra"].items()]
            o.append("<children><node id=\"SkillList\"><children>" + "".join(skill(x) for x in t["skills"])
                     + "</children></node></children></node>")
            objs.append("".join(o))
        for t in self.TI:  # the nested Scalar/String nodes are what the base game's trap items use
            s_ = ('<node id="String">' + a("String", "LSString", t["projectile"]) + "</node>")
            for nm in ("Scalar", "Scalar"):
                s_ = f'<node id="{nm}"><children>{s_}</children></node>'
            val = f'<node id="Value"><children>{s_}</children></node>'
            objs.append('<node id="GameObjects">' + a("LevelName", "FixedString", "") + a("MapKey", "FixedString", t["mk"])
                        + a("Name", "LSString", t["name"]) + a("ParentTemplateId", "FixedString", t["parent"])
                        + a("Type", "FixedString", "item")
                        + '<children><node id="ConstellationConfigGlobalParameters"><children><node id="ConstellationConfigParameter">'
                        + a("Name", "LSString", "Projectile") + f"<children>{val}</children></node></children></node></children></node>")
        lsx = ('<?xml version="1.0" encoding="utf-8"?><save><version major="4" minor="8" revision="0" build="500" />'
               '<region id="Templates"><node id="Templates"><children>' + "".join(objs)
               + "</children></node></region></save>")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        import hashlib
        stamp = os.path.join(REPO, "Scripts", "data", f"{fname}.lsx.sha256")  # Divine's LSF bytes differ run to run:
        digest = hashlib.sha256(lsx.encode("utf-8")).hexdigest()        # only convert when the templates changed
        if os.path.exists(path) and os.path.exists(stamp) and open(stamp).read().strip() == digest:
            return
        tmp = os.path.join(tempfile.gettempdir(), f"apotheosis_{fname}.lsx")
        open(tmp, "w", encoding="utf-8").write(lsx)
        mcp = os.path.join(REPO, "..", "bg3-data-mcp")
        env = dict(os.environ, UV_PROJECT_ENVIRONMENT=os.path.expanduser("~/.cache/bg3-data-mcp/venv"))
        subprocess.run(["uv", "run", "--project", mcp, "bg3-data", "convert", tmp, path], check=True, env=env,
                       stdout=subprocess.DEVNULL)
        os.makedirs(os.path.dirname(stamp), exist_ok=True)
        open(stamp, "w").write(digest + "\n")

    def write_stats(self, prefix, script, issue):
        head = (f"// GENERATED by Scripts/{script} ({issue}) - edit the generator, not this file.\n\n")
        for kind, rows in (("Passive", self.P), ("Status", self.S), ("Spell", self.SP), ("Interrupt", self.I),
                           ("Character", self.C)):
            path = os.path.join(DATA, f"{kind}_{prefix}.txt")
            if rows:
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(head + "\n".join(rows))
            elif os.path.exists(path):
                os.remove(path)

    def _between(self, path, rows):
        block = (f"                <!-- {self.marker} BEGIN (generated) -->\n" + "".join(rows)
                 + f"                <!-- {self.marker} END -->\n")
        s = open(path, encoding="utf-8").read()
        start, end = f"                <!-- {self.marker} BEGIN", f"<!-- {self.marker} END -->\n"
        if start in s:
            s = s[:s.index(start)] + block + s[s.index(end) + len(end):]
        else:
            i = s.rindex("            </children>")
            s = s[:i] + block + s[i:]
        open(path, "w", encoding="utf-8", newline="").write(s)

    def resource(self, name, mx, replenish, title, text):
        self.resources.append(f"""                <node id="ActionResourceDefinition">
                    <attribute id="DisplayName" type="TranslatedString" handle="{self.h('res:' + name + ':n', title)}" version="1"/>
                    <attribute id="Description" type="TranslatedString" handle="{self.h('res:' + name + ':d', text)}" version="1"/>
                    <attribute id="IsHidden" type="bool" value="false"/>
                    <attribute id="MaxLevel" type="uint32" value="0"/>
                    <attribute id="MaxValue" type="uint32" value="{mx}"/>
                    <attribute id="Name" type="FixedString" value="{name}"/>
                    <attribute id="ReplenishType" type="FixedString" value="{replenish}"/>
                    <attribute id="ShowOnActionResourcePanel" type="bool" value="true"/>
                    <attribute id="UUID" type="guid" value="{self.gid('res:' + name)}"/>
                </node>
""")

    def passive_list(self, name, passives):
        u = self.gid("list:" + name)
        self.lists.append(f"""                <node id="PassiveList">
                    <attribute id="Name" type="FixedString" value="{name}"/>
                    <attribute id="Passives" type="LSString" value="{','.join(passives)}"/>
                    <attribute id="UUID" type="guid" value="{u}"/>
                </node>
""")
        return u

    def levelmap(self, name, uuid_, levels, preferred_class=None):
        """A LevelMapSeries; with dnd55e's UUID it replaces dnd55e's series."""
        attrs = [(f"Level{lv}", "LSString", v) for lv, v in sorted(levels.items())]
        attrs += [("Name", "FixedString", name)]
        if preferred_class:
            attrs.append(("PreferredClassUUID", "guid", preferred_class))
        attrs.append(("UUID", "guid", uuid_))
        rows = "".join(f'                    <attribute id="{k}" type="{t}" value="{v}"/>\n' for k, t, v in attrs)
        self.levelmaps.append(f'                <node id="LevelMapSeries">\n{rows}                </node>\n')

    def patch_files(self):
        if self.resources:
            self._between(glob.glob(os.path.join(PUB, "ActionResourceDefinitions", "*.lsx"))[0], self.resources)
        if self.lists:
            self._between(os.path.join(PUB, "Lists", "PassiveLists.lsx"), self.lists)
        if self.levelmaps:
            self._between(os.path.join(PUB, "Levelmaps", "LevelMapValues.lsx"), self.levelmaps)

    def patch_loca(self):
        update_loca(self.loca)

def update_loca(rows):
    """Write {handle: text} into the loca file: existing handles are updated in place, new ones appended (stable
    order - regenerating doesn't move other generators' strings around)."""
    s = open(LOCA, encoding="utf-8").read()
    esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    seen = set()

    def update(m):
        if m.group(1) not in rows:
            return m.group(0)
        seen.add(m.group(1))
        return f'  <content contentuid="{m.group(1)}" version="1">{esc(rows[m.group(1)])}</content>\n'
    s = re.sub(r'  <content contentuid="(h[0-9a-z]+)" version="\d+">[^<]*</content>\n', update, s)
    new = "".join(f'  <content contentuid="{k}" version="1">{esc(v)}</content>\n' for k, v in rows.items() if k not in seen)
    i = s.rindex("</contentList>")
    s = s[:i] + new + s[i:]
    assert "<!--" not in s, "loca must not contain XML comments (Toolkit crash)"
    open(LOCA, "w", encoding="utf-8", newline="").write(s)


def drop_entries(fname, names):
    """Remove whole entries by name from a hand-kept stats file (Passive.txt, ...)."""
    path = os.path.join(DATA, fname)
    s = open(path, encoding="utf-8").read()
    for n in names:
        s = re.sub(rf'(?:\r?\n)*new entry "{n}"\r?\n(?:(?!new entry ).)*', "\n\n", s, flags=re.S)
    s = re.sub(r"\n{3,}", "\n\n", s)
    open(path, "w", encoding="utf-8", newline="").write(s)


def append_progressions(adds):
    """adds: existing node uuid -> {attr: ";"-list item(s)}. Appends each item to the node's attribute (creating it) unless
    it is already there - for additions to nodes that other generators rewrite in full (patch_progressions): run after
    them in regen_all.sh and the result is stable."""
    path = os.path.join(PUB, "Progressions", "Progressions.lsx")
    s = open(path, encoding="utf-8").read()
    seen = set()

    def fix(m):
        b = m.group(0)
        u = re.search(r'id="UUID" type="guid" value="([^"]*)"', b).group(1)
        if u not in adds:
            return b
        seen.add(u)
        ind = re.search(r'\n(\s*)<attribute id="Level"', b).group(1)
        for k, items in adds[u].items():
            cur = re.search(rf'<attribute id="{k}" type="LSString" value="([^"]*)"/>', b)
            have = [x for x in (cur.group(1) if cur else "").split(";") if x]
            new = have + [x for x in items.split(";") if x and x not in have]
            if cur:
                b = b.replace(cur.group(0), f'<attribute id="{k}" type="LSString" value="{";".join(new)}"/>')
            else:
                b = re.sub(r'(\n\s*<attribute id="Level")', f'\n{ind}<attribute id="{k}" type="LSString" value="{";".join(new)}"/>' + r"\1", b, count=1)
        return b

    s = NODE_RE.sub(fix, s)
    missing = [u for u in adds if u not in seen]
    assert not missing, f"progression nodes not found: {missing}"
    open(path, "w", encoding="utf-8", newline="").write(s)


def patch_progressions(nodes, new_nodes, marker):
    """nodes: existing uuid -> {attr: value} (PassivesAdded/PassivesRemoved/Boosts/Selectors; None deletes the node).
    new_nodes: [(uuid, name, level, progression_type, table, {attrs})], kept between markers."""
    path = os.path.join(PUB, "Progressions", "Progressions.lsx")
    s = open(path, encoding="utf-8").read()
    seen = set()

    def fix(m):
        b = m.group(0)
        u = re.search(r'id="UUID" type="guid" value="([^"]*)"', b).group(1)
        if u not in nodes:
            return b
        seen.add(u)
        if nodes[u] is None:
            return ""
        ind = re.search(r'\n(\s*)<attribute id="Level"', b).group(1)
        for k in ("PassivesAdded", "PassivesRemoved", "Boosts", "Selectors"):
            b = re.sub(rf'\s*<attribute id="{k}" type="LSString" value="[^"]*"/>', "", b)
        add = "".join(f'\n{ind}<attribute id="{k}" type="LSString" value="{v}"/>' for k, v in nodes[u].items())
        return re.sub(r'(\n\s*<attribute id="Level")', add + r"\1", b, count=1)

    s = NODE_RE.sub(fix, s)
    missing = [u for u, w in nodes.items() if w is not None and u not in seen]
    assert not missing, f"progression nodes not found: {missing}"
    rows = []
    for u, name, level, ptype, table, attrs in new_nodes:
        a = [(k, "LSString", v) for k, v in attrs.items()]
        a += [("Level", "uint8", level), ("Name", "LSString", name), ("ProgressionType", "uint8", ptype),
              ("TableUUID", "guid", table), ("UUID", "guid", u)]
        body = "".join(f'                    <attribute id="{k}" type="{t}" value="{v}"/>\n' for k, t, v in sorted(a, key=lambda x: x[0]))
        rows.append(f'                <node id="Progression">\n{body}                </node>\n')
    block = (f"                <!-- {marker} BEGIN (generated) -->\n" + "".join(rows) + f"                <!-- {marker} END -->\n")
    start, end = f"                <!-- {marker} BEGIN", f"<!-- {marker} END -->\n"
    if start in s:
        s = s[:s.index(start)] + block + s[s.index(end) + len(end):]
    elif rows:
        i = s.rindex("            </children>")
        s = s[:i] + block + s[i:]
    open(path, "w", encoding="utf-8", newline="").write(s)
