# Apotheosis icons

- `src/<IconName>.png`: the icon sources (512 px, transparent). `<IconName>` is the stats `Icon` value.
- `generated/`: the raw ComfyUI outputs they were made from (green background).
- `metadata.lsx`, `*_TextureBank.lsx`: editable copies the build writes; the game reads the .lsf versions in the mod.

Build: bg3-data MCP `bg3_icon_import` (keys out the green) -> `bg3_icon_build(layer="apotheosis")` -> redeploy.

## Generation (2026-10-04)
ComfyUI (D:\ComfyUI) with DreamShaper 7 (SD 1.5) + BG3 Action Icons LoRA (civitai 114265 v123503, strength 0.9),
clip skip 2, dpmpp_2m karras, 30 steps, cfg 7, 512x512; script D:\BG3Modding\Tools\comfy\gen_icons.py.
Negative: text, watermark, signature, letters, frame, border, photo, realistic, blurry, lowres, jpeg artifacts,
multiple objects, cropped, ugly, deformed.

| Icon | Used by | Prompt | Seed / pick |
| --- | --- | --- | --- |
| Apo_Spell_StormOfVengeance | Shout_Apo_StormOfVengeance | bg3 action icon, green background, storm of vengeance, a churning black storm cloud with forked lightning bolts and hail, ominous, magical, centered, painterly | 101, #4 |
| Apo_Passive_HeroicLegacy | HeroicSorcery_18_HeroicLegacy | bg3 action icon, green background, heroic legacy, a ghostly armored hero spirit raising a sword, golden glow, determination, centered, painterly | 202, #1 |
| Apo_Status_FinalJudgement | APO_FINAL_JUDGEMENT | bg3 action icon, green background, final judgement, a holy sword blazing with radiant white and gold light, divine rays, centered, painterly | 303, #1 |
