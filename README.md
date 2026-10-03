# Charis Cat // Child of an Android 2025

## Public route ownership

This repository owns the BabyLLM Vue shell and the snapshot/gallery Flask API.
The public Monzboi/OAuth information routes (`/monzboi`, `/privacy`,
`/privacy-policy`, and `/terms`) and their shared stylesheet have migrated to
`apps/monzboi/public_site` in the ICHARIS2 repository. ICHARIS2 Bopit overlays
those files after this frontend build and is the canonical production deploy
owner. Do not restore local copies here or publish this repository's `dist/`
directly to production.
