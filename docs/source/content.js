// FarmersDelight BRD + PRD v2.0 — single source of content, rendered to .docx and Markdown.
// Block types: h1 h2 h3 p bullets numbered table callout image pagebreak part landscape portrait
const IMG = require("path").join(__dirname, "../../designs/");
const B = (...a) => a;

const meta = {
  title: "FarmersDelight",
  subtitle: "Farmer to Consumer Marketplace",
  docname: "Business Requirements Document (BRD) and Product Requirements Document (PRD)",
  version: "2.0",
  date: "22 October 2026",
};

const coverTable = {
  type: "table", widths: [2600, 7038], header: ["Item", "Detail"], rows: [
    ["Product", "FarmersDelight: two Android apps that connect farmers directly with nearby consumers. FD Farmer (for farmers) and FarmersDelight (for buyers)."],
    ["Document version", "2.0 (supersedes 1.0 of 16 October 2026)"],
    ["Date", "22 October 2026"],
    ["Status", "Approved scope for the working prototype; backend build to follow"],
    ["Launch region and languages", "Tamil Nadu, India. English and Tamil at launch; Telugu, Kannada, Malayalam and Hindi later"],
    ["Business model", "Completely free. No ads. No commission."],
    ["Target technology", "Android first. Production: Flutter + Supabase (PostgreSQL with PostGIS, Auth, Realtime, Storage). Current prototype: offline WebView APKs."],
  ],
};

const revisions = {
  type: "table", widths: [1100, 1700, 6838], header: ["Version", "Date", "Changes"], rows: [
    ["1.0", "16 Oct 2026", "First BRD and PRD: sale modes (fixed, auction, negotiation), optional delivery, 2-hour winner confirmation, trust level per 10 clean sales, privacy model, schema, 8 screen designs."],
    ["2.0", "22 Oct 2026", "Split into two apps (FD Farmer and FarmersDelight). Farmer crop picker: 4×5 grid, Others catalogue of 217 Tamil Nadu crops in 13 groups with search, up to 5 Unlisted items. Photos and video per listing (1 photo required at first publish, max 3 photos, 1 silent video up to 10 s). Camera permission flow. Buyer photo reports with re-upload request and automatic takedown at 5 reports (listing stays live). Prototype status and test results added."],
  ],
};

// ------------------------------------------------------------------ PART A: BRD
const brd = [
  { type: "part", label: "PART A", title: "Business Requirements Document" },

  { type: "h1", text: "1. Executive summary" },
  { type: "p", text: "FarmersDelight lets farmers in Tamil Nadu sell their harvest directly to consumers who live nearby, without middlemen, fees or ads. A farmer pins the farm on a map, posts produce with photos and a short video, and chooses how to sell: at a fixed price, as a timed auction, or by open negotiation. A consumer finds farms within a chosen distance, buys or bids, and collects the produce from the farm or has it delivered when the farmer offers delivery." },
  { type: "p", text: "The product is now two separate Android apps: FD Farmer for farmers and FarmersDelight for buyers. Both are working, installable prototypes that run fully on the phone with simulated other users. The next phase connects them to a shared backend (Supabase) so real farmers and buyers can trade." },
  { type: "callout", title: "What changed in version 2.0", text: "Separate farmer and consumer apps; a crop picker built on the Tamil Nadu crop list (217 crops in 13 groups) with search and up to 5 unlisted items; photos and a 10-second silent video for every listing with at least 1 photo required; camera permission asked only once by Android; and a buyer report flow that asks the farmer to replace a photo and removes it automatically after 5 reports while the listing stays live." },

  { type: "h1", text: "2. Problem statement and opportunity" },
  { type: "bullets", items: [
    "Small farmers often sell through middlemen, lose a large share of the final price and have little say in price discovery.",
    "Consumers want fresher produce at fair prices but have no easy way to find nearby farmers and buy directly.",
    "Existing marketplace apps are built for large sellers, charge fees, show ads and collect far more personal data than a simple trade needs.",
    "Most farmers, and many buyers, are more comfortable in Tamil than English and need a simple interface with large touch targets and pictures.",
    "Buyers cannot judge freshness from text alone; trustworthy photos and a short video of the actual harvest build confidence.",
  ] },
  { type: "p", text: "Opportunity: a free, neighbourhood-level, privacy-first marketplace where the farmer controls the price, the sale method and whether to deliver." },

  { type: "h1", text: "3. Business objectives and success measures" },
  { type: "table", widths: [900, 5038, 3700], header: ["ID", "Objective", "Success measure (first 6 months)"], rows: [
    ["BO-1", "Give farmers a direct sales channel with better price realisation", "Farmers posting at least one listing a week; listing sell-through rate"],
    ["BO-2", "Give consumers easy access to fresh produce nearby", "Consumers completing a first order; repeat order rate"],
    ["BO-3", "Build trust between strangers without handling payments", "Orders completed without a dispute; average rating; trust-level distribution; photo report rate"],
    ["BO-4", "Stay free, ad-free and privacy-first", "Zero ads; only the agreed data collected; no privacy incidents; no broad storage permission requested"],
    ["BO-5", "Serve Tamil speakers first, then other South Indian languages", "Share of users on the Tamil interface; effort to add a language"],
    ["BO-6", "Make listings trustworthy with real media", "Share of listings with 2 or more photos; share with a video; photos removed after reports"],
  ] },
  { type: "p", text: "Target values for each measure are to be set by the product owner before public launch.", italic: true },

  { type: "h1", text: "4. Stakeholders and users" },
  { type: "table", widths: [2200, 3900, 3538], header: ["Stakeholder", "Needs", "Uses"], rows: [
    ["Farmer (seller)", "Post harvest quickly in Tamil or English; choose price and sale method; get fair offers; keep exact location and phone private until an order is confirmed", "FD Farmer app"],
    ["Consumer (buyer)", "Find fresh produce nearby; see real photos and video; buy, bid or make an offer; pick up or get delivery; rate the farmer; report misleading photos", "FarmersDelight app"],
    ["Admin / operations", "Approve farmer verification; review reported photos and disputes; restore wrongly removed photos; manage the crop list", "Admin web panel (planned)"],
    ["Founder / product owner", "Validate the market in Tamil Nadu cheaply; keep running costs low while the app is free", "All"],
  ] },

  { type: "h1", text: "5. Scope" },
  { type: "h2", text: "5.1 In scope for the MVP" },
  { type: "bullets", items: [
    "Two Android apps: FD Farmer and FarmersDelight; English and Tamil.",
    "Mobile number and OTP sign-in; farm profile with an approximate map pin.",
    "Listings from the Tamil Nadu crop list or up to 5 farmer-defined unlisted items; units kg, bunch, piece, dozen, quintal and tonne.",
    "Photos (1 to 3, at least 1 at first publish) and 1 silent video up to 10 seconds per listing; camera, gallery and video trimming.",
    "Sale modes: fixed price, timed auction (with optional buy-now and private reserve), negotiation (offer, counter, accept, reject).",
    "Orders with pickup or optional delivery; cash payment outside the app; contact revealed after confirmation.",
    "Ratings, trust level, optional verified badge, photo reports and automatic takedown, disputes.",
    "In-app notifications; admin web panel for verification, reports and disputes.",
  ] },
  { type: "h2", text: "5.2 Out of scope for the MVP" },
  { type: "bullets", items: [
    "Online payments, wallets or escrow.",
    "Logistics partners or a delivery fleet; delivery is done by the farmer when offered.",
    "iOS app (planned after Android).",
    "Advertising of any kind, or commission on sales.",
    "Sound in listing videos (decided: videos are silent).",
  ] },

  { type: "h1", text: "6. Business rules" },
  { type: "table", widths: [900, 2500, 6238], header: ["ID", "Rule", "Detail"], rows: [
    ["BR-01", "Free", "No commission, no subscription, no ads."],
    ["BR-02", "Cash only", "Buyers pay the farmer in cash at pickup or delivery. The app never handles money."],
    ["BR-03", "Delivery is optional", "Pickup is always available. The farmer may offer delivery per listing with a charge and a maximum distance."],
    ["BR-04", "Sale method per listing", "Fixed price, timed auction or negotiation, chosen by the farmer for each listing."],
    ["BR-05", "Auction winner window", "The winner has 2 hours to confirm. If not, the lot passes to the next highest bidder (above the reserve, if any), who also gets 2 hours."],
    ["BR-06", "Trust level", "Trust level = floor(clean sales ÷ 10). A clean sale is a completed order without a dispute. Like ride-hailing driver ratings, disputes do not count toward the 10."],
    ["BR-07", "Stars versus level", "Stars (1–5) show buyer opinion; trust level shows reliability. They are shown separately and never combined."],
    ["BR-08", "Verification", "Optional. Admin approval adds a Verified badge."],
    ["BR-09", "Crop list", "Farmers choose from 18 quick crops or the Others catalogue (217 crops in 13 groups, from the Tamil Nadu crop list)."],
    ["BR-10", "Unlisted items", "A farmer can add up to 5 unlisted items of their own; duplicates are refused; removing one frees a slot."],
    ["BR-11", "Photos", "1 to 3 photos per listing. At least 1 photo is required the first time a listing is published. The first photo is the cover."],
    ["BR-12", "Video", "At most 1 video per listing, up to 10 seconds, recorded or saved without sound."],
    ["BR-13", "Photo reports", "A buyer can report a photo once. Each report asks the farmer to replace it and shows the count (n of 5)."],
    ["BR-14", "Automatic takedown", "At 5 reports from different buyers the photo is removed automatically. The listing is not paused even if no photo is left; it stays live and is marked “Photo removed (reported)” until the farmer adds a new photo."],
    ["BR-15", "Report reset", "Replacing a photo starts its report count again at 0. Existing orders, bids and search position are not affected by reports."],
    ["BR-16", "Location privacy", "Buyers see only an approximate farm area (about 400 m). Exact location and phone are shared only after the farmer confirms an order."],
  ] },

  { type: "h1", text: "7. Privacy and data principles" },
  { type: "bullets", items: [
    "Collect only what a trade needs: name, mobile number, farm name and approximate pin for farmers; delivery address only on an order that needs delivery.",
    "No access to contacts, SMS, call logs or the phone's storage. The gallery is opened through Android's system picker, which gives the app only the files the user picks.",
    "Camera permission is requested only when the farmer taps Take a photo or Record a video. Microphone permission is never requested because videos are silent.",
    "Location data (EXIF/GPS) is removed from photos before upload so the exact farm spot stays private.",
    "Buyers' location is used only to sort farms by distance and is not stored on their profile.",
    "Users can delete their account and data from the app.",
  ] },

  { type: "h1", text: "8. Assumptions, constraints and dependencies" },
  { type: "bullets", items: [
    "Users have Android 8.0 or later and a mobile data connection; many phones have limited storage and data plans, so media is compressed.",
    "OTP SMS delivery requires an SMS provider (cost to be budgeted even though the app is free).",
    "Supabase free and low tiers are expected to cover the pilot; media storage grows with listings (about 1–2.5 MB per listing).",
    "Crop names follow the Tamil Nadu crop list supplied by the product owner; local names vary and may be refined with farmers.",
    "Tamil translations in the prototype were written by the team and need review by a native speaker before launch.",
  ] },

  { type: "h1", text: "9. Risks and mitigations" },
  { type: "table", widths: [3000, 1300, 5338], header: ["Risk", "Level", "Mitigation"], rows: [
    ["Low trust between strangers", "High", "Photos and video of the actual harvest, ratings, trust level, verification, reports with automatic takedown, contact revealed only after confirmation."],
    ["Misleading or inappropriate photos", "Medium", "Buyer reports, re-upload request, automatic removal at 5 reports, admin review and restore."],
    ["Running costs while free (SMS, storage)", "Medium", "Compress media, cap media per listing, monitor usage; funding model is an open question."],
    ["No-shows on orders and auctions", "Medium", "2-hour confirmation window, pass to next bidder, disputes excluded from trust level."],
    ["Large phone photos fail or are slow", "Medium", "Photos are decoded at reduced size and saved at 1600 px (about 250–500 KB); HEIF/HEIC gets a clear message."],
    ["Low digital literacy", "Medium", "Tamil interface, icons for crops, large buttons, few steps, demo mode for training."],
  ] },

  { type: "h1", text: "10. Phasing" },
  { type: "table", widths: [2000, 3600, 4038], header: ["Phase", "Content", "Status (22 Oct 2026)"], rows: [
    ["0. Prototype", "Two offline Android apps with simulated users, all flows in this document", "Done: FD Farmer v1.3, FarmersDelight v1.2"],
    ["1. MVP backend", "Supabase schema, auth with OTP, storage for media, realtime bids, notifications, admin panel", "Next"],
    ["2. Pilot", "One district in Tamil Nadu with a small group of farmers and buyers", "Planned"],
    ["3. Expand", "More districts; Telugu, Kannada, Malayalam, Hindi; iOS", "Planned"],
  ] },

  { type: "h1", text: "11. Open questions" },
  { type: "numbered", items: [
    "How will running costs (OTP SMS, storage) be funded while the app stays free?",
    "Should the star rating become a rolling score (recent orders weigh more), or stay a lifetime average?",
    "Who reviews reported photos and disputes during the pilot, and what is the response time?",
    "Which district and how many farmers and buyers for the pilot?",
  ] },
];

// ------------------------------------------------------------------ PART B: PRD
const fr = (rows) => ({ type: "table", widths: [1000, 6538, 1000, 1100], header: ["ID", "Requirement", "Priority", "Prototype"], rows });

const prd = [
  { type: "pagebreak" },
  { type: "part", label: "PART B", title: "Product Requirements Document" },

  { type: "h1", text: "12. Product overview" },
  { type: "table", widths: [2300, 3669, 3669], header: ["", "FD Farmer", "FarmersDelight"], rows: [
    ["Who", "Farmers and sellers", "Consumers and buyers"],
    ["Android package", "com.farmersdelight.farmer", "com.farmersdelight.app"],
    ["Current build", "v1.3 (version code 3)", "v1.2 (version code 3)"],
    ["Main tabs", "Home, Add, Offers, Orders, Profile", "Explore, Bids, Orders, Alerts, Profile"],
    ["Permissions", "Camera only (asked on first use)", "None"],
    ["Minimum Android", "8.0 (API 26); targets API 34", "8.0 (API 26); targets API 34"],
  ] },
  { type: "callout", title: "Prototype note", text: "Both prototypes store data only on the phone and simulate the other side of each trade (buyers in the farmer app, farmers in the buyer app). They do not share data yet; that needs the MVP backend. Everything else in this PRD is built and testable unless marked Planned." },

  { type: "h1", text: "13. Personas and key journeys" },
  { type: "h3", text: "Murugan, 46, vegetable farmer near Coimbatore" },
  { type: "p", text: "Uses a mid-range Android phone, prefers Tamil, sells tomatoes and greens. Wants to post a harvest in under two minutes with photos, decide the price, and avoid strangers knowing his exact location until they commit." },
  { type: "h3", text: "Priya, 34, home cook in the city" },
  { type: "p", text: "Buys vegetables twice a week, wants to see what she is buying, compare nearby farms, and pick up on the way home or pay a small delivery charge." },
  { type: "h2", text: "Key journeys" },
  { type: "numbered", items: [
    "Farmer posts a listing: Add → pick crop (grid, Others or Unlisted) → add photos/video → quantity, unit, sale method, price → delivery option → Publish.",
    "Buyer buys at fixed price: Explore → listing (gallery) → quantity and pickup/delivery → Place order → farmer confirms → contact revealed → received → rate.",
    "Auction: buyer bids → may be outbid → wins → confirms within 2 hours → order; otherwise next bidder.",
    "Negotiation: buyer offers → farmer accepts, counters or rejects → order on acceptance.",
    "Photo report: buyer reports → farmer asked to replace (n of 5) → farmer replaces, or at 5 reports the photo is removed and the listing stays live as reported.",
  ] },

  { type: "h1", text: "14. Functional requirements" },
  { type: "p", text: "Priority: M = must for MVP, S = should, C = could. Prototype: Built = working in the current APKs; Sim = built with simulated counterpart; Planned = needs the backend or admin panel." },

  { type: "h2", text: "14.1 Sign-in and onboarding (both apps)" },
  fr([
    ["ON-01", "Choose language (English, Tamil) on the welcome screen; change any time in Profile.", "M", "Built"],
    ["ON-02", "Sign in with name and 10-digit Indian mobile number; verify with a 4-digit OTP.", "M", "Sim (OTP 1234)"],
    ["ON-03", "Each app opens straight into its role; there is no role switch inside an app.", "M", "Built"],
    ["ON-04", "Farmer sets farm name, village and taps the map to pin the farm; buyers see only an approximate 400 m area.", "M", "Built"],
  ]),

  { type: "h2", text: "14.2 Farmer: choosing what to sell" },
  fr([
    ["CR-01", "Add listing shows a crop grid of 4 columns × 5 rows: 18 common crops, then Others (19th) and Unlisted (20th, last).", "M", "Built"],
    ["CR-02", "Others opens a Choose a crop page with Search crops at the top and the 13 crop groups as icons with crop counts.", "M", "Built"],
    ["CR-03", "Tapping a group shows its crops below the groups; Vegetables keeps its sub-groups (fruiting, gourds, beans, greens, roots, brassicas).", "M", "Built"],
    ["CR-04", "Search matches crop names, local names in brackets and group names across all groups; no match offers Add as unlisted item.", "M", "Built"],
    ["CR-05", "Crop names use the Tamil Nadu list text; notes such as “limited/specialised” are shown as a second line.", "S", "Built"],
    ["CR-06", "Unlisted: farmer adds an item name and picks an icon; up to 5 items; duplicates refused; items can be removed; saved items appear under My unlisted items.", "M", "Built"],
    ["CR-07", "Units: kg, bunch, piece, dozen, quintal, tonne.", "M", "Built"],
  ]),

  { type: "h2", text: "14.3 Farmer: photos and video" },
  fr([
    ["MD-01", "Media slots under the crop: Cover photo (Required), Photo 2, Photo 3 and Video (10 sec), with a counter “n/3 photos · n/1 video”.", "M", "Built"],
    ["MD-02", "Tapping a slot opens Add photos or video with: Take a photo, Record a video, Photos from gallery, Video from gallery. Options are disabled when their limit is reached.", "M", "Built"],
    ["MD-03", "Take a photo opens the in-app camera with “Photo n of 3”; it closes automatically after the third photo.", "M", "Built"],
    ["MD-04", "Record a video: a ring shows progress; recording stops automatically at 10 seconds; no sound is recorded.", "M", "Built"],
    ["MD-05", "Photos from gallery uses the Android picker; several photos can be picked at once; extras beyond 3 are skipped with a message.", "M", "Built (v1.3 fix)"],
    ["MD-06", "Video from gallery: videos longer than 10 s open Trim video to choose the best 10 seconds; all gallery videos are re-encoded silent at up to 720p.", "M", "Built"],
    ["MD-07", "Tap a photo to make it the cover or remove it; tap the video to play it; ✕ removes the video.", "S", "Built"],
    ["MD-08", "Publish is refused without at least 1 photo; the cover slot turns red with “Add at least 1 photo to publish. A video alone is not enough.”", "M", "Built"],
    ["MD-09", "Edit photos and video of a published listing from Home (camera button) or from a report card.", "M", "Built"],
    ["MD-10", "Photos and videos survive closing the app (stored on the phone in the prototype; in cloud storage in the MVP).", "M", "Built / Planned"],
    ["MD-11", "Clear messages for unreadable photos and HEIF/HEIC photos.", "S", "Built"],
  ]),

  { type: "h2", text: "14.4 Camera permission" },
  fr([
    ["PM-01", "No explainer screen: tapping Take a photo or Record a video shows the standard Android permission dialog directly.", "M", "Built"],
    ["PM-02", "When the farmer chooses “While using the app”, Android remembers it and the app never asks again.", "M", "Built"],
    ["PM-03", "If permission is refused, show “Camera is turned off for FD Farmer” with the Settings path, Open Settings and Choose from gallery instead.", "M", "Built"],
    ["PM-04", "No storage, files or microphone permission is requested.", "M", "Built"],
  ]),

  { type: "h2", text: "14.5 Selling: sale methods" },
  fr([
    ["SL-01", "Fixed price: buyer chooses quantity and pickup or delivery and places an order.", "M", "Sim"],
    ["SL-02", "Auction: start bid, minimum raise, duration (30 min to 24 h), optional buy-now price and private reserve.", "M", "Sim"],
    ["SL-03", "Auction winner confirms within 2 hours or the lot passes to the next bidder.", "M", "Sim"],
    ["SL-04", "Negotiation: buyer offers price and quantity; farmer accepts, counters or rejects; buyer can accept or decline a counter.", "M", "Sim"],
    ["SL-05", "Farmer can close a listing; sold-out listings close automatically.", "M", "Built"],
  ]),

  { type: "h2", text: "14.6 Orders, ratings and trust" },
  fr([
    ["OR-01", "Order states: Placed → Confirmed → Ready → Completed, or Cancelled.", "M", "Sim"],
    ["OR-02", "Phone and exact location are shown only after the farmer confirms.", "M", "Built"],
    ["OR-03", "Buyer marks received, then rates 1–5 stars with tags and an optional comment.", "M", "Built"],
    ["OR-04", "Report a problem marks the order disputed; disputed orders do not count toward trust level.", "M", "Built"],
    ["OR-05", "Farmer home shows trust level, clean sales and progress to the next level.", "M", "Built"],
    ["OR-06", "Farmer can request the Verified badge; admin approves.", "S", "Sim / Planned"],
  ]),

  { type: "h2", text: "14.7 Buyer app" },
  fr([
    ["BY-01", "Explore with map or list, distance filter (5, 10, 25 km), sale-type and delivery filters, and search.", "M", "Built"],
    ["BY-02", "Listing cards show the cover photo; listings with a removed photo show “Photo removed (reported)”.", "M", "Built"],
    ["BY-03", "Listing detail has a swipeable gallery (photo count, dots), a video tile that plays, and full-screen photo view.", "M", "Built (demo photos)"],
    ["BY-04", "My bids and offers, My orders, Alerts and Profile.", "M", "Built"],
  ]),

  { type: "h2", text: "14.8 Photo reports and takedown" },
  fr([
    ["RP-01", "Report photo on the listing gallery opens Report this photo with reasons: Not the actual produce, Blurry or unclear, Old or misleading, Inappropriate.", "M", "Built"],
    ["RP-02", "One report per buyer per photo; after reporting, the button shows Reported.", "M", "Built"],
    ["RP-03", "Farmer Home shows Please replace a photo with the reason, the photo, “n of 5” and Replace photo / View.", "M", "Built"],
    ["RP-04", "At the 5th report the photo is removed automatically and the farmer is notified.", "M", "Built"],
    ["RP-05", "If no photo is left the listing stays live, labelled Live · reported for the farmer and “Photo removed (reported)” for buyers, until a new photo is added.", "M", "Built"],
    ["RP-06", "Farmer can Ask for a review; admin can restore a wrongly removed photo.", "S", "Planned"],
    ["RP-07", "Demo tools in FD Farmer Profile simulate buyer reports for testing.", "C", "Built"],
  ]),

  { type: "h2", text: "14.9 Notifications, profile and admin" },
  fr([
    ["NT-01", "Alerts for new bids, offers, orders, outbid, auction won, confirmations, reports and takedowns, with unread badges.", "M", "Built (in-app)"],
    ["NT-02", "Push notifications through Firebase Cloud Messaging.", "S", "Planned"],
    ["PF-01", "Profile: language, farm details and pin, verification, privacy summary, sign out, delete account and data.", "M", "Built"],
    ["AD-01", "Admin web panel: verification queue, reported photos, disputes, restore media, crop list management.", "M", "Planned"],
  ]),

  { type: "h1", text: "15. Media specification" },
  { type: "table", widths: [2600, 7038], header: ["Item", "Specification"], rows: [
    ["Photos per listing", "1 to 3 (at least 1 at first publish). First photo is the cover."],
    ["Accepted photo input", "Any photo the phone camera or gallery produces in JPEG, PNG or WebP. HEIF/HEIC is not readable; the farmer is asked to switch the camera to JPEG."],
    ["Saved photo", "JPEG, longest side 1600 px, quality 85%, about 250–500 KB. All metadata including GPS removed. 50 MP (8160×6120) photos are supported and decoded at reduced size."],
    ["Video per listing", "0 or 1, up to 10 seconds, no sound."],
    ["Saved video", "WebM (VP8/VP9), up to 720p, about 1.8 Mbit/s, roughly 0.7–1 MB for 10 s, plus a JPEG thumbnail."],
    ["Gallery video longer than 10 s", "Trim screen: slider chooses a 10-second window; preview; Use this clip re-encodes the window."],
    ["Upload (MVP)", "On Publish, to Supabase Storage bucket listing-media; retry on poor network; buyers get short-lived signed links."],
  ] },

  { type: "h1", text: "16. Permissions" },
  { type: "table", widths: [2300, 1700, 1700, 3938], header: ["Permission", "FD Farmer", "FarmersDelight", "Why / when"], rows: [
    ["Camera", "Yes", "No", "Asked the first time the farmer takes a photo or records a video."],
    ["Microphone", "No", "No", "Videos are silent."],
    ["Storage / files / media", "No", "No", "Android Photo Picker returns only the chosen files."],
    ["Location (GPS)", "No", "No", "Farm is pinned by tapping the map; buyer distance uses an approximate area. GPS may be added later as an optional shortcut."],
    ["Contacts, SMS, call logs", "No", "No", "Never needed."],
  ] },

  { type: "h1", text: "17. Data model" },
  { type: "p", text: "The v1.0 schema (database/001_schema.sql) defines profiles, farmer_profiles, categories, listings, bids, orders, messages, reviews, reports, notifications and device_tokens, with row-level security, PostGIS location fuzzing and server functions for bids and orders. Version 2.0 adds the tables below (database/002_media_crops_reports.sql)." },
  { type: "table", widths: [2500, 7138], header: ["Table", "Purpose and key columns"], rows: [
    ["crop_groups", "13 groups: id, name_en, name_ta, icon, sort order."],
    ["crops", "217 crops: id, group_id, sub_group, name, note (for example “limited”), icon; quick-grid flag and order."],
    ["farmer_custom_items", "Unlisted items: farmer_id, name, icon, hidden; at most 5 visible per farmer (trigger)."],
    ["listing_media", "Replaces listing_images: listing_id, kind (photo/video), storage path, thumb path, sort order, duration (≤ 10 s), status (live/removed), report_count."],
    ["media_reports", "media_id, buyer_id, reason, created_at; unique per buyer and media. Trigger removes media at 5 reports and flags the listing as reported (it stays live)."],
    ["listings (changes)", "crop_id or custom_item_id; unit adds quintal and tonne; reported flag; publish check requires at least 1 live photo on first publish."],
  ] },

  { type: "h1", text: "18. Non-functional requirements" },
  { type: "table", widths: [2300, 7338], header: ["Area", "Requirement"], rows: [
    ["Performance", "App opens in under 3 s on a mid-range phone; photo processing under 3 s per photo; trim conversion runs in real time (10 s)."],
    ["Data usage", "A full listing (3 photos and 1 video) uploads about 1.5–2.5 MB."],
    ["Security", "OTP auth; row-level security on every table; contact data only via server function after confirmation; signed media links; APKs signed with APK Signature Scheme v2."],
    ["Privacy", "Rules in section 7; delete account removes personal data and media."],
    ["Localisation", "All interface text in English and Tamil; crop group names in both; new languages added through the text table."],
    ["Accessibility", "Touch targets at least 44 px; text size fixed at 100% in the prototype to protect layouts (to be revisited); colour plus text for every status."],
    ["Compatibility", "Android 8.0 (API 26) and later; tested layout at 412×915 dp (Redmi 13 Pro+)."],
    ["Reliability", "Media kept if the app is closed; uploads retried; auction timers enforced on the server in the MVP."],
  ] },

  { type: "h1", text: "19. Acceptance criteria (selected)" },
  { type: "table", widths: [1100, 8538], header: ["ID", "Given / When / Then"], rows: [
    ["AC-01", "Given the Add listing screen, the crop grid shows exactly 20 tiles in 4 columns and 5 rows, with Others 19th and Unlisted 20th."],
    ["AC-02", "Given Others, when the farmer types “millet”, then 8 crops are listed across groups; when nothing matches, Add as unlisted item is offered with the search text filled in."],
    ["AC-03", "Given 5 unlisted items, when the farmer opens Unlisted, then the add form is hidden and “You've added 5 items, the maximum” is shown."],
    ["AC-04", "Given no photo, when the farmer taps Publish, then the listing is not published and the cover slot shows the required error."],
    ["AC-05", "Given the video camera, when recording reaches 10 seconds, then it stops automatically and the saved video has no audio track."],
    ["AC-06", "Given 2 photos already added, when the farmer picks 2 photos from the gallery, then 1 is added and “Extra photos were skipped” is shown."],
    ["AC-07", "Given a gallery photo with GPS data, when it is added, then the saved photo has no EXIF/GPS data and its longest side is 1600 px."],
    ["AC-08", "Given camera permission granted with “While using the app”, when the farmer opens the camera again, then no permission dialog appears."],
    ["AC-09", "Given a photo with 4 reports, when a 5th buyer reports it, then it is removed, the farmer is notified, and the listing stays live (marked reported if no photo is left)."],
    ["AC-10", "Given a buyer who reported a photo, when they open Report photo again for that photo, then Send report is replaced by Reported."],
  ] },

  { type: "h1", text: "20. Test status" },
  { type: "p", text: "Automated click-through tests run in Chromium at the Redmi 13 Pro+ screen size (412×915) with a simulated camera. Results for the current builds:" },
  { type: "table", widths: [5000, 4638], header: ["Check", "Result"], rows: [
    ["Onboarding, explore, orders, auctions, offers, reviews (both apps)", "Pass, no script errors"],
    ["Crop grid 4×5, Others catalogue (13 groups, 217 crops), search, unlisted limit 5", "Pass"],
    ["Camera photo, 10-second silent video, auto-stop", "Pass: 10.0 s, about 740 KB, no audio track"],
    ["Gallery multi-pick including two 50 MP photos", "Pass: saved at 1600 px, about 450–480 KB, EXIF/GPS removed"],
    ["Gallery video 24 s trimmed to 10 s", "Pass: about 900 KB, audio removed"],
    ["Publish without photo refused", "Pass"],
    ["Reports: re-upload card, takedown at 5, listing stays live, replace clears flag", "Pass"],
    ["Camera refused path", "Pass (simulated refusal)"],
    ["APK structure, manifest, DEX and v2 signature checks", "Pass for both APKs"],
    ["On a real Android phone", "v1.2 installed and ran on Redmi 13 Pro+ (Android 16). Gallery multi-pick bug found and fixed in v1.3; v1.3 to be confirmed on the device."],
  ] },

  { type: "h1", text: "21. Next steps" },
  { type: "numbered", items: [
    "Confirm FD Farmer v1.3 on the Redmi: gallery multi-pick and camera photos.",
    "Set up the Supabase project; apply schemas 001 and 002; configure OTP SMS and the listing-media bucket.",
    "Build the production apps in Flutter against the backend, reusing the screens and rules in this document.",
    "Build the admin panel for verification, reported photos and disputes.",
    "Have a native speaker review all Tamil text.",
    "Choose the pilot district and recruit pilot farmers and buyers.",
  ] },
];

// ------------------------------------------------------------------ Appendix (landscape, A4 sheets)
const appendix = [
  { type: "landscape" },
  { type: "part", label: "APPENDIX", title: "Screens (A4 landscape sheets)" },
  { type: "p", text: "All sheets are also in the designs folder of the repository at full resolution (3508×2480, 300 dpi)." },
  { type: "image", file: "FarmersDelight_v1.2_Media_Screens_A4_page1.png", caption: "A1. v1.2 built screens: photos, video, reports and buyer gallery" },
  { type: "image", file: "FD_Farmer_App_Screens_A4_page1.png", caption: "A2. FD Farmer: 4×5 crop grid, Others catalogue and Unlisted items" },
  { type: "image", file: "FD_Farmer_Photos_Video_Design_v3_A4_page1.png", caption: "A3. Approved design v3: photos and video per listing" },
  { type: "image", file: "FD_Farmer_Photos_Video_Design_v3_A4_page2.png", caption: "A4. Approved design v3: rules and behaviour" },
  { type: "image", file: "FarmersDelight_APK_Screens_A4_page1.png", caption: "A5. v1.0 prototype screens (buyer and farmer)" },
  { type: "image", file: "FarmersDelight_Consumer_A4_page1.png", caption: "A6. Consumer app design (14 screens)" },
  { type: "portrait" },
  { type: "h1", text: "Appendix B. Crop catalogue summary" },
  { type: "table", widths: [3600, 4238, 1800], header: ["Group", "Tamil", "Crops"], rows: [
    ["Paddy and cereals", "நெல் மற்றும் தானியங்கள்", "12"], ["Pulses and legumes", "பருப்பு வகைகள்", "12"], ["Oilseeds", "எண்ணெய் வித்துக்கள்", "10"],
    ["Sugar, fibre, industrial", "கரும்பு, நார், தொழில் பயிர்கள்", "8"], ["Vegetables (6 sub-groups)", "காய்கறிகள்", "45"], ["Fruits", "பழங்கள்", "27"],
    ["Spices", "மசாலா பயிர்கள்", "20"], ["Flowers", "பூக்கள்", "18"], ["Plantation crops", "தோட்டப் பயிர்கள்", "16"],
    ["Medicinal and aromatic", "மூலிகை, நறுமணப் பயிர்கள்", "18"], ["Fodder crops", "தீவனப் பயிர்கள்", "12"], ["Trees and timber", "மரப் பயிர்கள்", "13"],
    ["Other farm produce", "பிற பண்ணைப் பொருட்கள்", "6"], ["Total", "", "217"],
  ] },
  { type: "p", text: "Quick grid (18): Tomato, Brinjal, Okra, Small onion, Carrot, Potato, Green chilli, Keerai (greens), Cucumber, Drumstick, Beans, Sweet corn, Banana, Mango, Coconut, Garlic, Paddy/rice, Groundnut; then Others and Unlisted." },
  { type: "h1", text: "Appendix C. Glossary" },
  { type: "table", widths: [2600, 7038], header: ["Term", "Meaning"], rows: [
    ["Clean sale", "A completed order with no dispute."],
    ["Trust level", "floor(clean sales ÷ 10); shows reliability."],
    ["Cover photo", "The first photo of a listing, shown on cards and as the first gallery image."],
    ["Unlisted item", "A product a farmer adds that is not in the crop list; up to 5 per farmer."],
    ["Takedown", "Automatic removal of a photo after 5 buyer reports."],
    ["Live · reported", "Listing state after its last photo was taken down: still visible and orderable, marked for buyers until a new photo is added."],
    ["Android Photo Picker", "System screen that lets the user choose photos or videos and gives the app only those files, without storage permission."],
  ] },
];

module.exports = { meta, coverTable, revisions, blocks: [...brd, ...prd, ...appendix], IMG };
