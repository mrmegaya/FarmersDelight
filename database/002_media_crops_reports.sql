-- =====================================================================
-- FarmersDelight · migration 002 (BRD/PRD v2.0, 22 Oct 2026)
-- Crop catalogue, unlisted items (max 5), listing media (1-3 photos +
-- 1 silent video <= 10 s), photo reports with automatic takedown at 5.
-- Run after 001_schema.sql. Seed data for crops is in 003_seed_crops.sql.
-- =====================================================================

-- ---------- units: add quintal and tonne ----------
alter type unit_type add value if not exists 'quintal';
alter type unit_type add value if not exists 'tonne';

-- ---------- crop catalogue (13 groups, 217 crops from the Tamil Nadu list) ----------
create table crop_groups (
  id        text primary key,                 -- g1 .. g13
  name_en   text not null,
  name_ta   text not null,
  icon      text not null,
  sort      smallint not null
);

create table crops (
  id          text primary key,               -- e.g. g5_1, or quick keys such as 'tomato'
  group_id    text not null references crop_groups(id),
  sub_group   text,                           -- vegetables only: "Fruiting vegetables", ...
  name        text not null,                  -- list text, e.g. "Okra / ladies' finger (Vendakkai)"
  name_ta     text,                           -- Tamil name where available
  note        text,                           -- e.g. "limited/specialised"
  icon        text not null,
  quick_sort  smallint                        -- not null = shown in the 4x5 quick grid (1..18)
);
create index crops_group_idx on crops (group_id);

-- ---------- unlisted items: up to 5 visible per farmer ----------
create table farmer_custom_items (
  id         uuid primary key default gen_random_uuid(),
  farmer_id  uuid not null references farmer_profiles(user_id) on delete cascade,
  name       text not null check (char_length(name) between 1 and 40),
  icon       text not null default '🌱',
  hidden     boolean not null default false,  -- removed by farmer; kept for old listings
  created_at timestamptz not null default now()
);
create unique index custom_items_unique_name on farmer_custom_items (farmer_id, lower(name)) where not hidden;

create or replace function check_custom_item_limit() returns trigger language plpgsql as $$
begin
  if not new.hidden and (select count(*) from farmer_custom_items
                         where farmer_id = new.farmer_id and not hidden and id <> new.id) >= 5 then
    raise exception 'A farmer can keep at most 5 unlisted items';
  end if;
  return new;
end $$;
create trigger trg_custom_item_limit before insert or update on farmer_custom_items
  for each row execute function check_custom_item_limit();

-- ---------- listings: what is sold + reported flag ----------
alter table listings
  add column crop_id         text references crops(id),
  add column custom_item_id  uuid references farmer_custom_items(id),
  add column reported        boolean not null default false,   -- live, but last photo was taken down
  add column published_once  boolean not null default false,
  add constraint listing_item_choice check ((crop_id is null) <> (custom_item_id is null));

-- ---------- listing media (replaces listing_images) ----------
create type media_kind   as enum ('photo', 'video');
create type media_status as enum ('live', 'removed');

create table listing_media (
  id            uuid primary key default gen_random_uuid(),
  listing_id    uuid not null references listings(id) on delete cascade,
  kind          media_kind not null,
  path          text not null,              -- storage: listing-media/<listing_id>/<id>.jpg|webm
  thumb_path    text,                       -- video thumbnail (jpg)
  sort          smallint not null default 0,-- photo 0 = cover
  duration_s    numeric(4,1),               -- video only
  width         int, height int, bytes int,
  status        media_status not null default 'live',
  report_count  smallint not null default 0,
  created_at    timestamptz not null default now(),
  check (kind = 'photo' or (duration_s is not null and duration_s <= 10.0))
);
create index listing_media_idx on listing_media (listing_id, status, sort);

-- at most 3 live photos and 1 live video per listing
create or replace function check_media_limits() returns trigger language plpgsql as $$
declare n int;
begin
  if new.status <> 'live' then return new; end if;
  select count(*) into n from listing_media
   where listing_id = new.listing_id and kind = new.kind and status = 'live' and id <> new.id;
  if new.kind = 'photo' and n >= 3 then raise exception 'At most 3 photos per listing'; end if;
  if new.kind = 'video' and n >= 1 then raise exception 'At most 1 video per listing'; end if;
  return new;
end $$;
create trigger trg_media_limits before insert or update on listing_media
  for each row execute function check_media_limits();

-- first publish needs at least one live photo; later takedowns do not unpublish
create or replace function check_first_publish() returns trigger language plpgsql as $$
begin
  if new.status = 'active' and not old.published_once then
    if not exists (select 1 from listing_media where listing_id = new.id and kind = 'photo' and status = 'live') then
      raise exception 'Add at least 1 photo to publish';
    end if;
    new.published_once := true;
  end if;
  return new;
end $$;
create trigger trg_first_publish before update of status on listings
  for each row execute function check_first_publish();
-- Apps create listings as 'draft', upload media, then set status = 'active'.
alter table listings alter column status set default 'draft';

-- a new live photo clears the "reported" flag
create or replace function clear_reported_flag() returns trigger language plpgsql as $$
begin
  if new.kind = 'photo' and new.status = 'live' then
    update listings set reported = false where id = new.listing_id and reported;
  end if;
  return new;
end $$;
create trigger trg_clear_reported after insert on listing_media
  for each row execute function clear_reported_flag();

-- ---------- photo reports ----------
create type media_report_reason as enum ('not_actual_produce', 'blurry', 'old_or_misleading', 'inappropriate');

create table media_reports (
  id         uuid primary key default gen_random_uuid(),
  media_id   uuid not null references listing_media(id) on delete cascade,
  buyer_id   uuid not null references profiles(id) on delete cascade,
  reason     media_report_reason not null,
  created_at timestamptz not null default now(),
  unique (media_id, buyer_id)                 -- one report per buyer per photo
);

-- each report: count it, ask the farmer to replace; at 5: take the photo down,
-- notify, and flag the listing as reported if no live photo is left (it stays live)
create or replace function on_media_report() returns trigger language plpgsql security definer as $$
declare m listing_media; l listings; n int;
begin
  update listing_media set report_count = report_count + 1 where id = new.media_id returning * into m;
  select * into l from listings where id = m.listing_id;
  n := m.report_count;
  if n >= 5 and m.status = 'live' then
    update listing_media set status = 'removed' where id = m.id;
    if not exists (select 1 from listing_media where listing_id = l.id and kind = 'photo' and status = 'live') then
      update listings set reported = true where id = l.id;
    end if;
    insert into notifications (user_id, type, ref_id) values (l.farmer_id, 'media_removed', m.id);
  else
    insert into notifications (user_id, type, ref_id) values (l.farmer_id, 'media_reported', m.id);
  end if;
  return new;
end $$;
create trigger trg_media_report after insert on media_reports
  for each row execute function on_media_report();

-- ---------- move old images into listing_media ----------
insert into listing_media (listing_id, kind, path, sort)
select listing_id, 'photo', path, position from listing_images;
-- drop table listing_images;   -- after the apps no longer read it

-- ---------- row-level security ----------
alter table crop_groups         enable row level security;
alter table crops               enable row level security;
alter table farmer_custom_items enable row level security;
alter table listing_media       enable row level security;
alter table media_reports       enable row level security;

create policy crop_groups_read on crop_groups for select using (true);
create policy crops_read       on crops       for select using (true);

create policy custom_items_own on farmer_custom_items for all
  using (farmer_id = auth.uid()) with check (farmer_id = auth.uid());
create policy custom_items_read on farmer_custom_items for select using (true);   -- names shown on listings

create policy media_read on listing_media for select using (
  status = 'live' or exists (select 1 from listings l where l.id = listing_id and l.farmer_id = auth.uid()));
create policy media_write on listing_media for all using (
  exists (select 1 from listings l where l.id = listing_id and l.farmer_id = auth.uid()))
  with check (exists (select 1 from listings l where l.id = listing_id and l.farmer_id = auth.uid()));

-- buyers can file reports (not on their own listings) and see their own; farmers see reports on their media
create policy reports_insert on media_reports for insert with check (
  buyer_id = auth.uid() and not exists (
    select 1 from listing_media m join listings l on l.id = m.listing_id where m.id = media_id and l.farmer_id = auth.uid()));
create policy reports_read on media_reports for select using (
  buyer_id = auth.uid() or exists (
    select 1 from listing_media m join listings l on l.id = m.listing_id where m.id = media_id and l.farmer_id = auth.uid()));

-- ---------- storage ----------
-- Create a private bucket "listing-media". Farmers upload to listing-media/<listing_id>/...;
-- buyers receive short-lived signed URLs for live media only.
