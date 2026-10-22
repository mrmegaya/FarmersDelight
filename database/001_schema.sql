-- =====================================================================
-- Farmer <-> Consumer Marketplace : Database Schema (PostgreSQL + PostGIS)
-- Designed for Supabase. Free, no ads, no commission, no payments stored.
-- Privacy principle: collect only what is needed to run a trade.
-- =====================================================================

create extension if not exists postgis;
create extension if not exists pgcrypto;

-- ---------- ENUMS ----------
create type user_role      as enum ('farmer', 'consumer', 'admin');
create type sale_mode      as enum ('fixed', 'auction', 'negotiation');
create type listing_status as enum ('draft', 'active', 'paused', 'sold_out', 'expired', 'removed');
create type unit_type      as enum ('kg', 'gram', 'bunch', 'piece', 'dozen');
create type bid_status     as enum ('active', 'outbid', 'accepted', 'rejected', 'withdrawn', 'expired', 'countered');
create type fulfilment     as enum ('pickup', 'delivery');
create type order_status   as enum ('pending', 'confirmed', 'ready', 'completed', 'cancelled_by_buyer', 'cancelled_by_farmer', 'expired');
create type report_status  as enum ('open', 'reviewing', 'resolved', 'dismissed');

-- ---------- USERS ----------
-- Phone number lives ONLY in auth.users (Supabase Auth, OTP login). It is
-- never copied into public tables, so it cannot leak through queries.
create table profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  role        user_role not null,
  full_name   text not null check (char_length(full_name) between 2 and 80),
  avatar_url  text,
  language    text not null default 'en' check (language in ('en','ta','te','kn','ml','hi')),
  is_blocked  boolean not null default false,
  created_at  timestamptz not null default now()
);

create table farmer_profiles (
  user_id          uuid primary key references profiles(id) on delete cascade,
  farm_name        text not null,
  -- EXACT location: readable only by the farmer, admin, and buyers with a confirmed order
  exact_location   geography(Point, 4326) not null,
  address_text     text,
  -- PUBLIC location: exact point shifted randomly by ~300-500 m. Used for map/search.
  public_location  geography(Point, 4326) not null,
  verified         boolean not null default false,
  verification_doc_path text,            -- private storage bucket, admin-only
  offers_delivery  boolean not null default false,
  delivery_radius_km numeric(5,1),
  rating_avg       numeric(3,2) not null default 0,
  rating_count     int not null default 0,
  -- Trust level: +1 for every 10 completed sales that had no dispute.
  clean_sales      int not null default 0,
  trust_level      int not null default 0,
  created_at       timestamptz not null default now()
);
create index farmer_public_loc_gix on farmer_profiles using gist (public_location);

-- Consumers: NO location or address is stored on the profile.
-- Search location is sent with the query and discarded.
-- Delivery address is stored only on the order, and only if delivery is chosen.

create table device_tokens (            -- push notifications only
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references profiles(id) on delete cascade,
  token      text not null unique,
  platform   text not null check (platform in ('android','ios')),
  created_at timestamptz not null default now()
);

-- ---------- CATALOGUE ----------
create table categories (
  id      serial primary key,
  name_en text not null,
  name_ta text not null,
  icon    text
);

-- ---------- LISTINGS ----------
create table listings (
  id                 uuid primary key default gen_random_uuid(),
  farmer_id          uuid not null references farmer_profiles(user_id) on delete cascade,
  category_id        int  not null references categories(id),
  title              text not null check (char_length(title) between 2 and 80),
  description        text check (char_length(description) <= 500),
  quantity_total     numeric(10,2) not null check (quantity_total > 0),
  quantity_available numeric(10,2) not null check (quantity_available >= 0),
  unit               unit_type not null,
  harvest_date       date,
  available_until    timestamptz not null,

  sale_mode          sale_mode not null,
  -- fixed: price_per_unit is the price.
  -- auction / negotiation: price_per_unit is the starting/asking price.
  price_per_unit     numeric(10,2) not null check (price_per_unit > 0),
  reserve_price      numeric(10,2),            -- private to farmer (never returned to buyers)
  buy_now_price      numeric(10,2),
  auction_ends_at    timestamptz,              -- required when sale_mode = 'auction'

  -- delivery is the farmer's choice per listing; pickup is always available
  delivery_available boolean not null default false,
  delivery_charge    numeric(10,2) default 0,
  delivery_radius_km numeric(5,1),

  -- copied from farmer's PUBLIC location (never the exact one)
  public_location    geography(Point, 4326) not null,

  status             listing_status not null default 'active',
  created_at         timestamptz not null default now(),

  constraint auction_needs_end check (sale_mode <> 'auction' or auction_ends_at is not null),
  constraint qty_ok check (quantity_available <= quantity_total)
);
create index listings_loc_gix    on listings using gist (public_location);
create index listings_active_idx on listings (status, available_until) where status = 'active';
create index listings_cat_idx    on listings (category_id);

create table listing_images (
  id         uuid primary key default gen_random_uuid(),
  listing_id uuid not null references listings(id) on delete cascade,
  path       text not null,           -- compressed image in storage; EXIF/GPS stripped on upload
  position   smallint not null default 0,
  unique (listing_id, position),
  check (position between 0 and 4)    -- max 5 photos
);

-- ---------- BIDS / OFFERS ----------
-- auction     : buyers place increasing bids until auction_ends_at.
-- negotiation : buyer offers, farmer accepts / rejects / counters (parent_bid_id links the thread).
create table bids (
  id              uuid primary key default gen_random_uuid(),
  listing_id      uuid not null references listings(id) on delete cascade,
  bidder_id       uuid not null references profiles(id) on delete cascade,
  from_farmer     boolean not null default false,       -- true for a counter-offer
  parent_bid_id   uuid references bids(id),
  quantity        numeric(10,2) not null check (quantity > 0),
  amount_per_unit numeric(10,2) not null check (amount_per_unit > 0),
  status          bid_status not null default 'active',
  confirm_by      timestamptz,                          -- winner must confirm before this time
  created_at      timestamptz not null default now()
);
create index bids_listing_idx on bids (listing_id, amount_per_unit desc);

-- ---------- ORDERS ----------
create table orders (
  id              uuid primary key default gen_random_uuid(),
  listing_id      uuid not null references listings(id),
  buyer_id        uuid not null references profiles(id),
  farmer_id       uuid not null references farmer_profiles(user_id),
  bid_id          uuid references bids(id),             -- null for fixed-price / buy-now
  quantity        numeric(10,2) not null check (quantity > 0),
  unit_price      numeric(10,2) not null,
  delivery_charge numeric(10,2) not null default 0,
  total_amount    numeric(12,2) not null,
  fulfilment      fulfilment not null,
  delivery_address text,                                -- only when fulfilment = 'delivery'
  payment_method  text not null default 'cash' check (payment_method = 'cash'),
  status          order_status not null default 'pending',
  disputed        boolean not null default false,       -- set by admin when a report is upheld
  created_at      timestamptz not null default now(),
  confirmed_at    timestamptz,
  completed_at    timestamptz,
  check (fulfilment = 'pickup' or delivery_address is not null)
);
create index orders_buyer_idx  on orders (buyer_id, created_at desc);
create index orders_farmer_idx on orders (farmer_id, created_at desc);

-- ---------- CHAT (only between the two parties of an order) ----------
create table messages (
  id         uuid primary key default gen_random_uuid(),
  order_id   uuid not null references orders(id) on delete cascade,
  sender_id  uuid not null references profiles(id),
  body       text not null check (char_length(body) <= 1000),
  created_at timestamptz not null default now()
);
create index messages_order_idx on messages (order_id, created_at);

-- ---------- TRUST ----------
create table reviews (
  id          uuid primary key default gen_random_uuid(),
  order_id    uuid not null references orders(id) on delete cascade,
  reviewer_id uuid not null references profiles(id),
  reviewee_id uuid not null references profiles(id),
  rating      smallint not null check (rating between 1 and 5),
  comment     text check (char_length(comment) <= 300),
  created_at  timestamptz not null default now(),
  unique (order_id, reviewer_id)                         -- one review per party per order
);

create table reports (
  id          uuid primary key default gen_random_uuid(),
  reporter_id uuid not null references profiles(id),
  target_user uuid references profiles(id),
  target_listing uuid references listings(id),
  reason      text not null,
  status      report_status not null default 'open',
  created_at  timestamptz not null default now(),
  check (target_user is not null or target_listing is not null)
);

create table notifications (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references profiles(id) on delete cascade,
  type       text not null,       -- new_nearby, outbid, bid_won, order_update, expiry
  ref_id     uuid,
  is_read    boolean not null default false,
  created_at timestamptz not null default now()
);

-- =====================================================================
-- FUNCTIONS
-- =====================================================================

-- Random shift of 300-500 m so the public map never shows the real farm gate.
create or replace function fuzz_point(p geography) returns geography
language sql immutable as $$
  select ST_Project(
           p,
           300 + random() * 200,          -- distance in metres
           radians(random() * 360)        -- bearing
         )::geography;
$$;

-- Nearby search. The caller's coordinates are parameters only, never stored.
create or replace function nearby_listings(
  lat double precision, lng double precision, radius_km numeric default 10,
  p_category int default null, p_mode sale_mode default null
) returns table (
  id uuid, title text, price_per_unit numeric, unit unit_type, sale_mode sale_mode,
  delivery_available boolean, distance_km numeric, available_until timestamptz
) language sql stable security invoker as $$
  select l.id, l.title, l.price_per_unit, l.unit, l.sale_mode, l.delivery_available,
         round((ST_Distance(l.public_location, ST_MakePoint(lng, lat)::geography) / 1000)::numeric, 1),
         l.available_until
  from listings l
  where l.status = 'active'
    and l.available_until > now()
    and ST_DWithin(l.public_location, ST_MakePoint(lng, lat)::geography, radius_km * 1000)
    and (p_category is null or l.category_id = p_category)
    and (p_mode is null or l.sale_mode = p_mode)
  order by l.public_location <-> ST_MakePoint(lng, lat)::geography
  limit 50;
$$;

-- Contact + exact location are revealed ONLY to the two parties of a confirmed order.
create or replace function get_order_contact(p_order uuid)
returns table (other_name text, other_phone text, farm_exact_lat double precision, farm_exact_lng double precision)
language plpgsql security definer set search_path = public as $$
declare o orders%rowtype;
begin
  select * into o from orders where id = p_order;
  if o.id is null or auth.uid() not in (o.buyer_id, o.farmer_id)
     or o.status not in ('confirmed','ready','completed') then
    raise exception 'not allowed';
  end if;
  return query
    select p.full_name,
           u.phone,
           case when auth.uid() = o.buyer_id and o.fulfilment = 'pickup'
                then ST_Y(f.exact_location::geometry) end,
           case when auth.uid() = o.buyer_id and o.fulfilment = 'pickup'
                then ST_X(f.exact_location::geometry) end
    from profiles p
    join auth.users u on u.id = p.id
    join farmer_profiles f on f.user_id = o.farmer_id
    where p.id = case when auth.uid() = o.buyer_id then o.farmer_id else o.buyer_id end;
end $$;

-- Place an auction bid atomically (prevents race conditions).
create or replace function place_bid(p_listing uuid, p_qty numeric, p_amount numeric)
returns uuid language plpgsql security definer set search_path = public as $$
declare l listings%rowtype; top numeric; new_id uuid;
begin
  select * into l from listings where id = p_listing for update;
  if l.status <> 'active' or l.sale_mode <> 'auction' or now() >= l.auction_ends_at then
    raise exception 'auction closed';
  end if;
  if l.farmer_id = auth.uid() then raise exception 'cannot bid on own listing'; end if;
  select max(amount_per_unit) into top from bids where listing_id = p_listing and status = 'active';
  if p_amount < l.price_per_unit or (top is not null and p_amount <= top) then
    raise exception 'bid too low';
  end if;
  update bids set status = 'outbid' where listing_id = p_listing and status = 'active';
  insert into bids (listing_id, bidder_id, quantity, amount_per_unit)
  values (p_listing, auth.uid(), p_qty, p_amount) returning id into new_id;
  return new_id;
end $$;

-- Keep farmer rating up to date.
create or replace function refresh_rating() returns trigger language plpgsql as $$
begin
  update farmer_profiles f
     set rating_avg = (select round(avg(rating)::numeric, 2) from reviews where reviewee_id = new.reviewee_id),
         rating_count = (select count(*) from reviews where reviewee_id = new.reviewee_id)
   where f.user_id = new.reviewee_id;
  return new;
end $$;
create trigger trg_refresh_rating after insert on reviews
  for each row execute function refresh_rating();

-- Trust level: recomputed whenever an order is completed or its dispute flag changes.
-- trust_level = floor(clean_sales / 10), where clean_sales = completed orders with no dispute.
create or replace function refresh_trust_level() returns trigger language plpgsql
security definer set search_path = public as $$
begin
  update farmer_profiles f
     set clean_sales = c.n,
         trust_level = c.n / 10
    from (select count(*)::int as n
            from orders
           where farmer_id = new.farmer_id and status = 'completed' and not disputed) c
   where f.user_id = new.farmer_id;
  return new;
end $$;
create trigger trg_refresh_trust
  after insert or update of status, disputed on orders
  for each row execute function refresh_trust_level();

-- Scheduled (pg_cron, every minute): close ended auctions, expire unconfirmed
-- winners and pass the offer to the next bidder, expire old listings.

-- =====================================================================
-- ROW LEVEL SECURITY  (deny by default)
-- =====================================================================
alter table profiles        enable row level security;
alter table farmer_profiles enable row level security;
alter table listings        enable row level security;
alter table listing_images  enable row level security;
alter table bids            enable row level security;
alter table orders          enable row level security;
alter table messages        enable row level security;
alter table reviews         enable row level security;
alter table reports         enable row level security;
alter table notifications   enable row level security;
alter table device_tokens   enable row level security;

-- Profiles: own row full access; others see name/avatar only via a limited view.
create policy profile_self on profiles for all using (id = auth.uid()) with check (id = auth.uid());

create view public_farmers as
  select user_id, farm_name, public_location, verified, offers_delivery, rating_avg, rating_count,
         clean_sales, trust_level
  from farmer_profiles;               -- exact_location, address, documents NOT exposed

-- farmer_profiles base table: owner only (buyers use the view above).
create policy farmer_self on farmer_profiles for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Listings: anyone signed in sees active ones; only the owner writes.
-- NOTE: reserve_price must be excluded for buyers -> expose via a view (listings_public) without that column.
create policy listing_read  on listings for select using (status = 'active' or farmer_id = auth.uid());
create policy listing_write on listings for all    using (farmer_id = auth.uid()) with check (farmer_id = auth.uid());
create policy images_read   on listing_images for select using (true);
create policy images_write  on listing_images for all using (
  exists (select 1 from listings l where l.id = listing_id and l.farmer_id = auth.uid()));

-- Bids: bidder sees own; farmer sees bids on own listings. Inserts go through place_bid().
create policy bids_read on bids for select using (
  bidder_id = auth.uid()
  or exists (select 1 from listings l where l.id = listing_id and l.farmer_id = auth.uid()));

-- Orders / messages: only the two parties.
create policy orders_parties on orders for select using (auth.uid() in (buyer_id, farmer_id));
create policy msgs_parties   on messages for all using (
  exists (select 1 from orders o where o.id = order_id and auth.uid() in (o.buyer_id, o.farmer_id)))
  with check (sender_id = auth.uid());

-- Reviews: public read; write only for a completed order you took part in.
create policy reviews_read  on reviews for select using (true);
create policy reviews_write on reviews for insert with check (
  reviewer_id = auth.uid() and exists (
    select 1 from orders o where o.id = order_id and o.status = 'completed'
      and auth.uid() in (o.buyer_id, o.farmer_id)));

create policy reports_own on reports for all using (reporter_id = auth.uid()) with check (reporter_id = auth.uid());
create policy notif_own   on notifications for all using (user_id = auth.uid());
create policy tokens_own  on device_tokens for all using (user_id = auth.uid());

-- Admin access: via service role in a separate admin panel, never from the mobile app.
