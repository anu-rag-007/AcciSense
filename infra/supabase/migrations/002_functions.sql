-- ============================================================
-- 002_functions.sql — nearby_agencies, accept_dispatch, abort_dispatch, realtime
-- ============================================================

-- ── nearby_agencies ──────────────────────────────────────────
create or replace function public.nearby_agencies(
  p_incident_id    uuid,
  p_radius_m       int,
  p_required_caps  text[] default null
)
returns table (
  agency_id    uuid,
  ambulance_id uuid,
  distance_m   float,
  unit_type    text
)
language sql stable as $$
  with inc as (
    select location from public.incidents where id = p_incident_id
  )
  select distinct on (a.id)
         a.id   as agency_id,
         amb.id as ambulance_id,
         ST_Distance(amb.location, inc.location) as distance_m,
         amb.unit_type
    from public.agencies a
    join inc on true
    join public.ambulances amb on amb.agency_id = a.id
   where a.is_active = true
     and amb.status = 'available'
     and amb.last_ping > now() - interval '5 minutes'
     and amb.location is not null
     and ST_DWithin(amb.location, inc.location, p_radius_m)
     and (p_required_caps is null or amb.capabilities && p_required_caps)
   order by a.id, ST_Distance(amb.location, inc.location) asc;
$$;

-- ── accept_dispatch (the atomic lock) ────────────────────────
create or replace function public.accept_dispatch(
  p_incident_id  uuid,
  p_offer_id     uuid,
  p_agency_id    uuid,
  p_ambulance_id uuid default null
)
returns table (
  success          boolean,
  reason           text,
  assigned_agency  uuid,
  accepted_at      timestamptz
)
language plpgsql security definer as $$
declare
  v_offer dispatch_offers%rowtype;
  v_rows  int;
  v_now   timestamptz := clock_timestamp();
begin
  select * into v_offer
    from public.dispatch_offers
   where id = p_offer_id
   for update;

  if not found then
    return query select false, 'offer_not_found', null::uuid, null::timestamptz;
    return;
  end if;

  if v_offer.incident_id <> p_incident_id then
    return query select false, 'offer_incident_mismatch', null::uuid, null::timestamptz;
    return;
  end if;

  if v_offer.agency_id <> p_agency_id then
    return query select false, 'offer_agency_mismatch', null::uuid, null::timestamptz;
    return;
  end if;

  if v_offer.status <> 'pending' then
    return query select false, 'offer_already_' || v_offer.status, null::uuid, null::timestamptz;
    return;
  end if;

  if v_offer.expires_at < v_now then
    update public.dispatch_offers
       set status = 'expired', responded_at = v_now
     where id = p_offer_id;
    return query select false, 'offer_expired', null::uuid, null::timestamptz;
    return;
  end if;

  -- ATOMIC GUARD
  update public.incidents
     set dispatch_status        = 'accepted',
         assigned_agency_id     = p_agency_id,
         assigned_ambulance_id  = p_ambulance_id,
         accepted_at            = v_now
   where id                 = p_incident_id
     and dispatch_status    = 'broadcasting'
     and assigned_agency_id is null;

  get diagnostics v_rows = row_count;

  if v_rows = 0 then
    update public.dispatch_offers
       set status = 'revoked', responded_at = v_now
     where id = p_offer_id;
    return query select false, 'already_accepted', null::uuid, null::timestamptz;
    return;
  end if;

  update public.dispatch_offers
     set status = 'accepted', responded_at = v_now
   where id = p_offer_id;

  update public.dispatch_offers
     set status = 'revoked', responded_at = v_now
   where incident_id = p_incident_id
     and id <> p_offer_id
     and status = 'pending';

  if p_ambulance_id is not null then
    update public.ambulances set status = 'dispatched' where id = p_ambulance_id;
  end if;

  insert into public.dispatch_events (incident_id, event, actor_type, actor_id, metadata)
  values (p_incident_id, 'dispatch_accepted', 'agency', p_agency_id,
          jsonb_build_object('offer_id', p_offer_id,
                             'ambulance_id', p_ambulance_id,
                             'wave', v_offer.wave));

  return query select true, 'ok'::text, p_agency_id, v_now;
end $$;

-- ── abort_dispatch ───────────────────────────────────────────
create or replace function public.abort_dispatch(
  p_incident_id uuid,
  p_agency_id   uuid,
  p_reason      text
)
returns boolean language plpgsql as $$
declare v_rows int;
begin
  update public.incidents
     set dispatch_status       = 'broadcasting',
         assigned_agency_id    = null,
         assigned_ambulance_id = null,
         accepted_at           = null
   where id                 = p_incident_id
     and assigned_agency_id = p_agency_id
     and dispatch_status    in ('accepted','en_route');

  get diagnostics v_rows = row_count;
  if v_rows = 0 then return false; end if;

  insert into public.dispatch_events (incident_id, event, actor_type, actor_id, metadata)
  values (p_incident_id, 'dispatch_aborted', 'agency', p_agency_id,
          jsonb_build_object('reason', p_reason));

  return true;
end $$;