# Tunel: state

Updated 2026-10-20. Read this first, then `DECISIONS.md`.

## Owner's words that define the current work

- 2026-10-18: "Tünel fontunu contibute edebilir miyiz? https://github.com/google/fonts/blob/main/CONTRIBUTING.md"
- 2026-10-18: "Evet, bence bunu yapabiliriz. Ben gerekli olan ne varsa yapacağım. Sen de kendi tarafından
  ne gerekiyorsa yap. Bunun paylaşılmasını istiyoruz. Tüm maddelere uyum sağlayalım. Adım adım sen
  kendi yapman gerekenleri yap. Sonra da bana adım adım neler yapmam gerektiğini söyle ve hepsini
  yapalım. Ve süreci nihayete erdirene kadar çalışalım."
- 2026-10-19, on the release: "mevcut sürümü replace"

In English: submit Tunel to Google Fonts, comply with every requirement, and see it through.

## Done, with evidence

| What | Evidence |
| --- | --- |
| Google Fonts checks pass | `fontbakery check-googlefonts`: 0 FAIL, 0 ERROR on `fonts/variable`, `fonts/ttf` and `fonts/otf`, each run separately (17 FAIL before) |
| Glyph rules hold | `test.py`: all 7 checks pass |
| Sources and build in the Google Fonts layout | `sources/` (6 UFO masters, `Tunel.designspace`, `config.yaml`), built by `gftools builder` through `font.py` |
| Work merged | PR iuzn/tunel#1, merge commit `b9764d0` on `main` |
| Release replaced in place | Release `v1.100` "Tunel 1.100" on `b9764d0`, asset `Tunel-1.100.zip`; the old zip is kept in `~/.Trash/tunel-release-v1.000-20261019/` and tag `v1.000` remains |
| Submission filed by the owner | https://github.com/google/fonts/issues/11135 "Add Tunel", labels I New Font and II Submission; no comments as of 2026-10-20 |

## Open

- Google Fonts review of issue 11135. The queue is long and the design team curates, so
  acceptance is not guaranteed.
- Google Contributor License Agreement: owner step, not yet confirmed signed
  (https://cla.developers.google.com).

## Next

1. Watch issue 11135. When a reviewer asks for a change, make it here, rebuild, rerun the checks,
   push. The owner answers in the issue himself.
2. After any font change, replace the release in place (owner ruling 2026-10-19), keeping the old
   asset in the Trash.

## Done when

Tunel is merged into google/fonts and listed on fonts.google.com, or the issue is closed.

## How to build and check

```
python3 -m venv .venv && .venv/bin/pip install "fonttools[woff]" pillow ufoLib2 gftools   # Python 3.10+
.venv/bin/python build.py && .venv/bin/python test.py
PATH=$PWD/.venv/bin:$PATH .venv/bin/python font.py
fontbakery check-googlefonts -l FAIL "fonts/variable/Tunel[ROND,wght].ttf"   # then fonts/ttf/*.ttf, fonts/otf/*.otf
```

Run fontbakery on one folder at a time: mixing the variable and static fonts in one run reports
family-level failures that do not exist.

## Standing rules

- Commits and pull requests are authored iuzn, with no co-author lines.
- No reference typeface is named or credited anywhere: files, metadata, commits, issues.
- Nothing is deleted; it moves to `~/.Trash/<topic>-<date>/`.
