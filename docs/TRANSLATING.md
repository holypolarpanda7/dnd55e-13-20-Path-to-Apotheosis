# Translating Path to Apotheosis

Translations are welcome (#85, 2026-11-19). All of PTA's text is in one file, so you only need to translate that file
and ship it as a small translation mod. You can also send it to us, and we'll include it in PTA itself.

## The file to translate

- Every GitHub release has the English text as a download:
  `dnd55e-13-20-Path-to-Apotheosis_English_v<version>.xml`
  (https://github.com/holypolarpanda7/dnd55e-13-20-Path-to-Apotheosis/releases).
- The same file is in this repository at
  `Mods/dnd55e_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa/Localization/English/dnd55e-Apotheosis.xml`.

Each line looks like this:

```xml
<content contentuid="h7f8a9b0c00000000000000000000001" version="1">Unlock 4th Level Spell Slots</content>
```

Translate only the text between `>` and `</content>`. Keep these as they are:

- `contentuid` and `version`: the game looks the text up by the contentuid.
- Markup inside the text, such as `<LSTag Type="Spell" Tooltip="Projectile_MagicMissile">Magic Missile</LSTag>`
  (translate the visible words between the tags, not the attributes), and placeholders such as `[1]` or `[2]`.
- Escaped characters (`&lt;`, `&gt;`, `&amp;`, `&apos;`).

Don't add XML comments (`<!-- -->`) to the file. Comments in localization files crash the Larian Toolkit.

## Making a translation mod

A translation mod is a pak with two files:

```
Mods/<YourModFolder>/meta.lsx
Mods/<YourModFolder>/Localization/<Language>/dnd55e-Apotheosis.xml
```

- `<Language>` is the game's language name, the same as the game's own localization pak for that language. For example,
  `Russian` (Russian.pak) or `German` (German.pak). The game falls back to English for any string that you haven't
  translated yet.
- Use your own mod folder name and a new UUID in `meta.lsx`. Add Path to Apotheosis as a dependency
  (UUID `1467c26f-e7bb-49d1-d980-6e033aea04fa`, Folder `dnd55e_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa`),
  and load your mod after PTA.
- Pack it with the BG3 Modder's Multitool, LSLib (Divine) or the Larian Toolkit, the same way as any other pak mod. The XML
  can ship as it is, or converted to `.loca`.

## Keeping a translation up to date

- The contentuids don't change between releases. A generated string's ID is computed from a fixed key (for example the
  spell it belongs to), not from its text.
- Every GitHub release also has `dnd55e-13-20-Path-to-Apotheosis_localization-changes_v<version>.txt`. It lists the
  strings added, changed and removed since the previous release, by contentuid and with the English text, so you only
  translate what's new.
- A removed string can stay in your file. The game ignores contentuids that nothing uses.

## Including your translation in PTA

Open a pull request that adds `Localization/<Language>/dnd55e-Apotheosis.xml` next to the English one, or attach the file to
an issue. Shipped translations are credited in the CHANGELOG and on the mod pages.
