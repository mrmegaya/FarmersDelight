<!-- Generated from docs/source/content.js — edit there and run build.js -->
# FarmersDelight — Business Requirements Document (BRD)

Version 2.0 · 22 October 2026 · Word version: [FarmersDelight_BRD_PRD_v2.0.docx](FarmersDelight_BRD_PRD_v2.0.docx)

| Item | Detail |
| --- | --- |
| Product | FarmersDelight: two Android apps that connect farmers directly with nearby consumers. FD Farmer (for farmers) and FarmersDelight (for buyers). |
| Document version | 2.0 (supersedes 1.0 of 16 October 2026) |
| Date | 22 October 2026 |
| Status | Approved scope for the working prototype; backend build to follow |
| Launch region and languages | Tamil Nadu, India. English and Tamil at launch; Telugu, Kannada, Malayalam and Hindi later |
| Business model | Completely free. No ads. No commission. |
| Target technology | Android first. Production: Flutter + Supabase (PostgreSQL with PostGIS, Auth, Realtime, Storage). Current prototype: offline WebView APKs. |


## Revision history

| Version | Date | Changes |
| --- | --- | --- |
| 1.0 | 16 Oct 2026 | First BRD and PRD: sale modes (fixed, auction, negotiation), optional delivery, 2-hour winner confirmation, trust level per 10 clean sales, privacy model, schema, 8 screen designs. |
| 2.0 | 22 Oct 2026 | Split into two apps (FD Farmer and FarmersDelight). Farmer crop picker: 4×5 grid, Others catalogue of 217 Tamil Nadu crops in 13 groups with search, up to 5 Unlisted items. Photos and video per listing (1 photo required at first publish, max 3 photos, 1 silent video up to 10 s). Camera permission flow. Buyer photo reports with re-upload request and automatic takedown at 5 reports (listing stays live). Prototype status and test results added. |


## 1. Executive summary

FarmersDelight lets farmers in Tamil Nadu sell their harvest directly to consumers who live nearby, without middlemen, fees or ads. A farmer pins the farm on a map, posts produce with photos and a short video, and chooses how to sell: at a fixed price, as a timed auction, or by open negotiation. A consumer finds farms within a chosen distance, buys or bids, and collects the produce from the farm or has it delivered when the farmer offers delivery.

The product is now two separate Android apps: FD Farmer for farmers and FarmersDelight for buyers. Both are working, installable prototypes that run fully on the phone with simulated other users. The next phase connects them to a shared backend (Supabase) so real farmers and buyers can trade.

> **What changed in version 2.0**  
> Separate farmer and consumer apps; a crop picker built on the Tamil Nadu crop list (217 crops in 13 groups) with search and up to 5 unlisted items; photos and a 10-second silent video for every listing with at least 1 photo required; camera permission asked only once by Android; and a buyer report flow that asks the farmer to replace a photo and removes it automatically after 5 reports while the listing stays live.


## 2. Problem statement and opportunity

- Small farmers often sell through middlemen, lose a large share of the final price and have little say in price discovery.
- Consumers want fresher produce at fair prices but have no easy way to find nearby farmers and buy directly.
- Existing marketplace apps are built for large sellers, charge fees, show ads and collect far more personal data than a simple trade needs.
- Most farmers, and many buyers, are more comfortable in Tamil than English and need a simple interface with large touch targets and pictures.
- Buyers cannot judge freshness from text alone; trustworthy photos and a short video of the actual harvest build confidence.

Opportunity: a free, neighbourhood-level, privacy-first marketplace where the farmer controls the price, the sale method and whether to deliver.


## 3. Business objectives and success measures

| ID | Objective | Success measure (first 6 months) |
| --- | --- | --- |
| BO-1 | Give farmers a direct sales channel with better price realisation | Farmers posting at least one listing a week; listing sell-through rate |
| BO-2 | Give consumers easy access to fresh produce nearby | Consumers completing a first order; repeat order rate |
| BO-3 | Build trust between strangers without handling payments | Orders completed without a dispute; average rating; trust-level distribution; photo report rate |
| BO-4 | Stay free, ad-free and privacy-first | Zero ads; only the agreed data collected; no privacy incidents; no broad storage permission requested |
| BO-5 | Serve Tamil speakers first, then other South Indian languages | Share of users on the Tamil interface; effort to add a language |
| BO-6 | Make listings trustworthy with real media | Share of listings with 2 or more photos; share with a video; photos removed after reports |

*Target values for each measure are to be set by the product owner before public launch.*


## 4. Stakeholders and users

| Stakeholder | Needs | Uses |
| --- | --- | --- |
| Farmer (seller) | Post harvest quickly in Tamil or English; choose price and sale method; get fair offers; keep exact location and phone private until an order is confirmed | FD Farmer app |
| Consumer (buyer) | Find fresh produce nearby; see real photos and video; buy, bid or make an offer; pick up or get delivery; rate the farmer; report misleading photos | FarmersDelight app |
| Admin / operations | Approve farmer verification; review reported photos and disputes; restore wrongly removed photos; manage the crop list | Admin web panel (planned) |
| Founder / product owner | Validate the market in Tamil Nadu cheaply; keep running costs low while the app is free | All |


## 5. Scope


### 5.1 In scope for the MVP

- Two Android apps: FD Farmer and FarmersDelight; English and Tamil.
- Mobile number and OTP sign-in; farm profile with an approximate map pin.
- Listings from the Tamil Nadu crop list or up to 5 farmer-defined unlisted items; units kg, bunch, piece, dozen, quintal and tonne.
- Photos (1 to 3, at least 1 at first publish) and 1 silent video up to 10 seconds per listing; camera, gallery and video trimming.
- Sale modes: fixed price, timed auction (with optional buy-now and private reserve), negotiation (offer, counter, accept, reject).
- Orders with pickup or optional delivery; cash payment outside the app; contact revealed after confirmation.
- Ratings, trust level, optional verified badge, photo reports and automatic takedown, disputes.
- In-app notifications; admin web panel for verification, reports and disputes.


### 5.2 Out of scope for the MVP

- Online payments, wallets or escrow.
- Logistics partners or a delivery fleet; delivery is done by the farmer when offered.
- iOS app (planned after Android).
- Advertising of any kind, or commission on sales.
- Sound in listing videos (decided: videos are silent).


## 6. Business rules

| ID | Rule | Detail |
| --- | --- | --- |
| BR-01 | Free | No commission, no subscription, no ads. |
| BR-02 | Cash only | Buyers pay the farmer in cash at pickup or delivery. The app never handles money. |
| BR-03 | Delivery is optional | Pickup is always available. The farmer may offer delivery per listing with a charge and a maximum distance. |
| BR-04 | Sale method per listing | Fixed price, timed auction or negotiation, chosen by the farmer for each listing. |
| BR-05 | Auction winner window | The winner has 2 hours to confirm. If not, the lot passes to the next highest bidder (above the reserve, if any), who also gets 2 hours. |
| BR-06 | Trust level | Trust level = floor(clean sales ÷ 10). A clean sale is a completed order without a dispute. Like ride-hailing driver ratings, disputes do not count toward the 10. |
| BR-07 | Stars versus level | Stars (1–5) show buyer opinion; trust level shows reliability. They are shown separately and never combined. |
| BR-08 | Verification | Optional. Admin approval adds a Verified badge. |
| BR-09 | Crop list | Farmers choose from 18 quick crops or the Others catalogue (217 crops in 13 groups, from the Tamil Nadu crop list). |
| BR-10 | Unlisted items | A farmer can add up to 5 unlisted items of their own; duplicates are refused; removing one frees a slot. |
| BR-11 | Photos | 1 to 3 photos per listing. At least 1 photo is required the first time a listing is published. The first photo is the cover. |
| BR-12 | Video | At most 1 video per listing, up to 10 seconds, recorded or saved without sound. |
| BR-13 | Photo reports | A buyer can report a photo once. Each report asks the farmer to replace it and shows the count (n of 5). |
| BR-14 | Automatic takedown | At 5 reports from different buyers the photo is removed automatically. The listing is not paused even if no photo is left; it stays live and is marked “Photo removed (reported)” until the farmer adds a new photo. |
| BR-15 | Report reset | Replacing a photo starts its report count again at 0. Existing orders, bids and search position are not affected by reports. |
| BR-16 | Location privacy | Buyers see only an approximate farm area (about 400 m). Exact location and phone are shared only after the farmer confirms an order. |


## 7. Privacy and data principles

- Collect only what a trade needs: name, mobile number, farm name and approximate pin for farmers; delivery address only on an order that needs delivery.
- No access to contacts, SMS, call logs or the phone's storage. The gallery is opened through Android's system picker, which gives the app only the files the user picks.
- Camera permission is requested only when the farmer taps Take a photo or Record a video. Microphone permission is never requested because videos are silent.
- Location data (EXIF/GPS) is removed from photos before upload so the exact farm spot stays private.
- Buyers' location is used only to sort farms by distance and is not stored on their profile.
- Users can delete their account and data from the app.


## 8. Assumptions, constraints and dependencies

- Users have Android 8.0 or later and a mobile data connection; many phones have limited storage and data plans, so media is compressed.
- OTP SMS delivery requires an SMS provider (cost to be budgeted even though the app is free).
- Supabase free and low tiers are expected to cover the pilot; media storage grows with listings (about 1–2.5 MB per listing).
- Crop names follow the Tamil Nadu crop list supplied by the product owner; local names vary and may be refined with farmers.
- Tamil translations in the prototype were written by the team and need review by a native speaker before launch.


## 9. Risks and mitigations

| Risk | Level | Mitigation |
| --- | --- | --- |
| Low trust between strangers | High | Photos and video of the actual harvest, ratings, trust level, verification, reports with automatic takedown, contact revealed only after confirmation. |
| Misleading or inappropriate photos | Medium | Buyer reports, re-upload request, automatic removal at 5 reports, admin review and restore. |
| Running costs while free (SMS, storage) | Medium | Compress media, cap media per listing, monitor usage; funding model is an open question. |
| No-shows on orders and auctions | Medium | 2-hour confirmation window, pass to next bidder, disputes excluded from trust level. |
| Large phone photos fail or are slow | Medium | Photos are decoded at reduced size and saved at 1600 px (about 250–500 KB); HEIF/HEIC gets a clear message. |
| Low digital literacy | Medium | Tamil interface, icons for crops, large buttons, few steps, demo mode for training. |


## 10. Phasing

| Phase | Content | Status (22 Oct 2026) |
| --- | --- | --- |
| 0. Prototype | Two offline Android apps with simulated users, all flows in this document | Done: FD Farmer v1.3, FarmersDelight v1.2 |
| 1. MVP backend | Supabase schema, auth with OTP, storage for media, realtime bids, notifications, admin panel | Next |
| 2. Pilot | One district in Tamil Nadu with a small group of farmers and buyers | Planned |
| 3. Expand | More districts; Telugu, Kannada, Malayalam, Hindi; iOS | Planned |


## 11. Open questions

1. How will running costs (OTP SMS, storage) be funded while the app stays free?
2. Should the star rating become a rolling score (recent orders weigh more), or stay a lifetime average?
3. Who reviews reported photos and disputes during the pilot, and what is the response time?
4. Which district and how many farmers and buyers for the pilot?

