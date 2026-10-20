# Tunel: decisions

Append-only. A wrong record is superseded by a new one that names it, never edited away.

## D-001 (2026-10-18): Prepare Tunel for Google Fonts and comply with every requirement

- **Decision:** Bring the project to the Google Fonts onboarding requirements and the
  `check-googlefonts` profile with no failures, then let the owner file the submission.
- **Owner's words:** "Bunun paylaşılmasını istiyoruz. Tüm maddelere uyum sağlayalım."
- **What it took:**
  - UFO sources plus `gftools builder`, as the guide requires.
  - An ASCII menu name "Tunel", since a diacritic is not allowed in a family name.
  - Copyright "The Tunel Project Authors", with AUTHORS.txt and CONTRIBUTORS.txt.
  - Line spacing of 1.2 em, USE_TYPO_METRICS, installable embedding and smart dropout.
  - GF Latin Core: Ș ș Ț ț and Ẁ ẁ Ẃ ẃ Ẅ ẅ Ỳ ỳ.
  - The soft hyphen removed, and `.notdef` drawn.
  - 80 glyphs redrawn from the face's own parts: the punctuation, symbols and marks, and M W w Z.
    Every spacing and combining mark is now built from the drawn marks.
- **Evidence:**
  - fontbakery went from 17 FAIL to 0 FAIL on the variable, static TTF and OTF fonts.
  - test.py passes.
  - Merged as PR iuzn/tunel#1 (`b9764d0`).
- **Alternatives:**
  - Keep the ROND default at 100 and ask Google for an exception, or ship a wght-only family.
    Both were rejected for full compliance.
- **Authority:** owner axiom, 2026-10-18.
- **Reversibility:** reversible. The 1.000 state is commit `6515112` and tag `v1.000`.
- **Supersedes:** nothing.

## D-002 (2026-10-18): ROND defaults to 0, square dots

- **Decision:** The Roundness axis defaults to 0. The static fonts are therefore square, and
  ROND 100 gives round dots.
- **Why:** The Google Fonts axis registry defines ROND with the default 0 and the single
  fallback name "Default". Any other default fails `fvar_axis_defaults` and `STAT/axisregistry`.
- **Owner's words:** "Tüm maddelere uyum sağlayalım."
- **Reversibility:** reversible in `font.py` (the axis default and the instance locations).
- **Supersedes:** the 1.000 default of 100, round.

## D-003 (2026-10-19): The release is replaced in place

- **Decision:** One release entry, updated in place. It is now "Tunel 1.100" on tag `v1.100`,
  with the asset `Tunel-1.100.zip`.
- **Owner's words:** "mevcut sürümü replace"
- **Evidence:**
  - https://github.com/iuzn/tunel/releases/tag/v1.100
  - The old asset is kept in `~/.Trash/tunel-release-v1.000-20261019/`.
  - Tag `v1.000` is kept.
- **Reversibility:** reversible. The old zip and tag both exist.
- **Supersedes:** nothing.
