# FarmersDelight

Farmers in Tamil Nadu sell their harvest directly to buyers nearby. No middlemen, no fees, no ads.

There are two Android apps:

| App | For | Package | Latest build |
|---|---|---|---|
| **FD Farmer** | Farmers: post harvest with photos and a short video, sell at a fixed price, by auction or by negotiation | `com.farmersdelight.farmer` | [v1.3](releases/FD-Farmer-v1.3.apk) |
| **FarmersDelight** | Buyers: find farms nearby, buy, bid or make offers, pick up or get delivery | `com.farmersdelight.app` | [v1.2](releases/FarmersDelight-Consumer-v1.2.apk) |

Both builds are **working prototypes**. They store data on the phone and simulate the other side of each trade, so the two apps don't share data yet. The next phase connects them to a Supabase backend (see [docs/PRD.md § 21](docs/PRD.md)).

## Documents

| Document | Format |
|---|---|
| BRD and PRD v2.0 (22 Oct 2026), with screens | [Word](docs/FarmersDelight_BRD_PRD_v2.0.docx) |
| Business Requirements Document | [docs/BRD.md](docs/BRD.md) |
| Product Requirements Document | [docs/PRD.md](docs/PRD.md) |
| Previous version 1.0 (16 Oct 2026) | [docs/archive](docs/archive/FarmersDelight_BRD_PRD_v1.0.docx) |

The Word file and the two Markdown files are generated from one source, `docs/source/content.js`. To update them, edit that file and run `node docs/source/build.js docs`, which needs the `docx` npm package.

## Repository layout

```
docs/          BRD and PRD (Word + Markdown) and their source
releases/      Installable APKs and SHA256SUMS.txt
designs/       Screen designs and built-screen sheets (A4 landscape, 300 dpi)
database/      Supabase / PostgreSQL schema
  001_schema.sql                 users, farms, listings, bids, orders, reviews, RLS, location fuzzing, trust level
  002_media_crops_reports.sql    crop catalogue, unlisted items (max 5), listing media, photo reports, takedown at 5
  003_seed_crops.sql             13 crop groups, 217 crops and the 18 quick-grid crops
prototype/
  app/index.html                 the app (one HTML/JS file); build/mkhtml.py makes the farmer and consumer variants
  data/                          crop list (source text and generated crops.json), district guide
  build/                         APK builder that needs no Android SDK (DEX, manifest, resources, v2 signing) and its checkers
  tests/                         Playwright click-through tests and a test-media generator
```

## Install on an Android phone

1. Download the APK from `releases/` on the phone and open it.
2. Allow installs from that app when Android asks.
3. If Play Protect warns about an unknown developer, tap **More details → Install anyway**.

Each new version installs over the previous one and keeps its data, as long as it is signed with the same key.

Sign-in in the prototype: any name, a 10-digit mobile number starting with 6–9, and OTP **1234**. No SMS is sent.

## What's in v1.3 / v1.2

- **Separate apps** for farmers and buyers, in English and Tamil.
- **Crop picker** (farmer):
  - A 4×5 grid of 18 common crops, with **Others** and **Unlisted** as the last two tiles.
  - **Others** opens 217 crops from the Tamil Nadu list in 13 groups, with search at the top.
  - **Unlisted** holds up to 5 items the farmer adds themselves.
- **Photos and video** (farmer):
  - 1 to 3 photos, with at least 1 required to publish, plus 1 silent video of up to 10 seconds.
  - Photos and video can come from the in-app camera or the gallery; longer videos open a trim screen.
  - Photos are saved at 1600 px, about 250–500 KB, with GPS data removed.
- **Permissions:** the farmer app asks only for Camera, and Android asks only once. There is no storage or microphone permission. The buyer app asks for no permissions.
- **Photo reports:**
  - A buyer can report a photo once, and the farmer is asked to replace it ("n of 5").
  - At 5 reports the photo is removed automatically. The listing stays live, marked "Photo removed (reported)".
- **Selling:** fixed price, auctions (2-hour winner confirmation), negotiation, orders, ratings and trust level (+1 for every 10 sales without a dispute).

## Build the APKs

You need Python 3 with `cryptography` and `Pillow`; the Android SDK isn't needed.

```bash
cd prototype/build
KEY=/secure/path/farmersdelight-signing.pem ./build.sh
```

The signing key is **not** in this repository. Keep it safe, because every future update must be signed with the same key.

## Run the tests

You need Python 3 with Playwright and Chromium, plus `numpy` and `ffmpeg` for the test media.

```bash
cd prototype
python3 build/mkhtml.py          # generates app/farmer.html and app/consumer.html
python3 tests/gen_testmedia.py   # photos with GPS data, 50 MP photos, a 24 s video
python3 tests/test_split_apps_and_crops.py
python3 tests/test_media_and_reports.py
python3 tests/test_large_photos.py
```

The tests run at the Redmi 13 Pro+ screen size (412×915) with a simulated camera. Camera permission and the Android photo picker still have to be checked on a real phone.
