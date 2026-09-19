-- ============================================================
-- 001_schema.sql — tables, indexes, triggers
-- ============================================================
create extension if not exists postgis;
create extension if not exists pgcrypto;

-- ── profiles (mirrors auth.users) ────────────────────────────
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  full_name   text,
  phone       text,
  role        text not null default 'citizen'
              check (role in ('citizen','admin','responder','supervisor')),
  trust_score int  not null default 50,
  created_at  timestamptz not null default now()
);

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (id, phone)
  values (new.id, new.phone)
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ── agencies ─────────────────────────────────────────────────
create table if not exists public.agencies (
  id                 uuid primary key default gen_random_uuid(),
  name               text not null,
  type               text not null check (type in ('hospital','blinkit','fire','police','ngo')),
  capabilities       text[] not null default '{}',
  contact_phone      text,
  api_endpoint       text,
  api_key            text,
  integration_tier   int not null default 1 check (integration_tier in (1,2,3)),
  coverage           geography(Polygon),
  sla_accept_seconds int not null default 45,
  is_active          boolean not null default true,
  created_at         timestamptz not null default now()
);
create index if not exists idx_agencies_coverage    on public.agencies using gist (coverage);
create index if not exists idx_agencies_active_type on public.agencies (is_active, type);

-- ── agency_users (RLS mapping) ───────────────────────────────
create table if not exists public.agency_users (
  user_id   uuid not null references auth.users(id) on delete cascade,
  agency_id uuid not null references public.agencies(id) on delete cascade,
  role      text not null default 'dispatcher'
            check (role in ('dispatcher','manager')),
  primary key (user_id, agency_id)
);
create index if not exists idx_agency_users_agency on public.agency_users (agency_id);

-- ── ambulances ───────────────────────────────────────────────
create table if not exists public.ambulances (
  id           uuid primary key default gen_random_uuid(),
  agency_id    uuid not null references public.agencies(id) on delete cascade,
  call_sign    text,
  unit_type    text not null check (unit_type in (
                 'ALS','BLS','bike_first_responder','fire_engine','police_unit')),
  capabilities text[] not null default '{}',
  status       text not null default 'available'
               check (status in ('available','dispatched','offline','en_route','on_scene')),
  location     geography(Point),
  last_ping    timestamptz not null default now()
);
create index if not exists idx_ambulances_location      on public.ambulances using gist (location);
create index if not exists idx_ambulances_status_ping   on public.ambulances (status, last_ping);
create index if not exists idx_ambulances_agency_status on public.ambulances (agency_id, status);

-- ── incidents ────────────────────────────────────────────────
create table if not exists public.incidents (
  id                    uuid primary key default gen_random_uuid(),
  reporter_id           uuid references auth.users(id) on delete set null,
  category              text,
  severity              text check (severity in ('LOW','MEDIUM','HIGH','CRITICAL')),
  description           text,
  latitude              float8,
  longitude             float8,
  location              geography(Point),
  address               text,
  dispatch_status       text not null default 'reported'
                        check (dispatch_status in (
                          'reported','verifying','held','broadcasting',
                          'accepted','en_route','on_scene','resolved',
                          'unassigned','cancelled')),
  assigned_agency_id    uuid references public.agencies(id),
  assigned_ambulance_id uuid references public.ambulances(id),
  accepted_at           timestamptz,
  current_wave          int not null default 0,
  trust_score_at_report int,
  ai_confidence         float,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now(),
  resolved_at           timestamptz
);
create index if not exists idx_incidents_location on public.incidents using gist (location);
create index if not exists idx_incidents_dispatch on public.incidents (dispatch_status, severity, created_at desc);
create index if not exists idx_incidents_reporter on public.incidents (reporter_id, created_at desc);

create or replace function public.sync_incident_location()
returns trigger language plpgsql as $$
begin
  if new.latitude is not null and new.longitude is not null then
    new.location := ST_SetSRID(ST_MakePoint(new.longitude, new.latitude), 4326)::geography;
  end if;
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists trg_sync_incident_location on public.incidents;
create trigger trg_sync_incident_location
  before insert or update of latitude, longitude
  on public.incidents
  for each row execute function public.sync_incident_location();

-- ── incident_media ───────────────────────────────────────────
create table if not exists public.incident_media (
  id           uuid primary key default gen_random_uuid(),
  incident_id  uuid not null references public.incidents(id) on delete cascade,
  storage_url  text not null,
  content_hash text,
  captured_at  timestamptz,
  gps_lat      float8,
  gps_lng      float8,
  created_at   timestamptz not null default now()
);
create index if not exists idx_incident_media_incident on public.incident_media (incident_id);

-- ── dispatch_offers ──────────────────────────────────────────
create table if not exists public.dispatch_offers (
  id            uuid primary key default gen_random_uuid(),
  incident_id   uuid not null references public.incidents(id) on delete cascade,
  agency_id     uuid not null references public.agencies(id) on delete cascade,
  ambulance_id  uuid references public.ambulances(id),
  wave          int not null default 1,
  distance_m    float,
  status        text not null default 'pending'
                check (status in ('pending','accepted','declined','expired','revoked')),
  sent_at       timestamptz not null default now(),
  expires_at    timestamptz not null,
  responded_at  timestamptz
);
create index if not exists idx_offers_incident_status on public.dispatch_offers (incident_id, status);
create index if not exists idx_offers_agency_status   on public.dispatch_offers (agency_id, status);
create index if not exists idx_offers_expires_pending on public.dispatch_offers (expires_at) where status = 'pending';

-- ── dispatch_events ──────────────────────────────────────────
create table if not exists public.dispatch_events (
  id          bigserial primary key,
  incident_id uuid not null references public.incidents(id) on delete cascade,
  event       text not null,
  actor_type  text,
  actor_id    uuid,
  metadata    jsonb not null default '{}',
  created_at  timestamptz not null default now()
);
create index if not exists idx_events_incident on public.dispatch_events (incident_id, created_at);