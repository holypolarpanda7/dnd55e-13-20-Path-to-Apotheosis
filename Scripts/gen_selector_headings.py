"""Level-up screen headings for this mod's passive picks (2026-10-06).

A SelectPassives(<list>,<n>,<SelectorId>) pick takes its heading and text from the ProgressionDescription whose SelectorId
matches (base and dnd55e name FightingStyle, WeaponMasteryList... this way). With none the screen shows the generic
"Class Passives" - level 19 had two such rows until 2026-10-06. bg3_lint_progressions lists UNNAMED picks: add every new
SelectorId here.

Owns (rewritten every run): Progressions/ProgressionDescriptions.lsx. Strings go to the loca file through gen_common.
Run: python3 Scripts/gen_selector_headings.py (regen_all.sh runs it).
"""
import os
import uuid

from gen_common import PUB, update_loca

# (SelectorId, heading, text). The hash seeds below are the ones gen_epic_boons.py first used for the Epic Boon rows - kept
# so their handles and UUIDs don't change.
HEADINGS = [
    ("EpicBoon", "Epic Boon", "Choose an Epic Boon: a feat of great power for reaching level 19."),
    ("EpicBoonAbility", "Epic Boon: Ability Increase",
     "Every Epic Boon raises one ability score by 1, to a maximum of 30. If your boon already names its ability "
     "(for example Boon of Irresistible Offense (+1 Strength)), choose \"increase included in my boon\"."),
    ("PowerOfTheWilds", "Power of the Wilds", "Choose the power of the wilds you gain whenever you enter a Rage."),
]

NS = uuid.NAMESPACE_URL
HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="8" revision="0" build="500"/>
    <region id="ProgressionDescriptions">
        <node id="root">
            <children>
"""
TAIL = """            </children>
        </node>
    </region>
</save>
"""


def handle(key):
    return "h" + uuid.uuid5(NS, "apotheosis-epicboon-loca:" + key).hex


def main():
    loca, rows = {}, []
    for sid, title, text in HEADINGS:
        dn, desc = handle(f"sel:{sid}:n"), handle(f"sel:{sid}:d")
        loca[dn], loca[desc] = title, text
        rows.append(f"""                <node id="ProgressionDescription">
                    <attribute id="Description" type="TranslatedString" handle="{desc}" version="1"/>
                    <attribute id="DisplayName" type="TranslatedString" handle="{dn}" version="1"/>
                    <attribute id="SelectorId" type="FixedString" value="{sid}"/>
                    <attribute id="UUID" type="guid" value="{uuid.uuid5(NS, 'apotheosis-epicboon:progdesc:' + sid)}"/>
                </node>
""")
    with open(os.path.join(PUB, "Progressions", "ProgressionDescriptions.lsx"), "w", encoding="utf-8", newline="\n") as f:
        f.write(HEAD + "".join(rows) + TAIL)
    update_loca(loca)
    print(f"{len(rows)} selector headings: {', '.join(s for s, _, _ in HEADINGS)}")


if __name__ == "__main__":
    main()
