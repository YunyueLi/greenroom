-- Optional stronger keepalive target for the hosted Greenroom Supabase project.
-- Run once in Supabase Dashboard -> SQL Editor.
--
-- The public anon key can call this RPC, but it can only touch one harmless row.
-- It does not expose or modify any user workspace data.

create table if not exists public.gr_keepalive (
  id integer primary key,
  touched_at timestamptz not null default now()
);

insert into public.gr_keepalive (id, touched_at)
values (1, now())
on conflict (id) do nothing;

alter table public.gr_keepalive enable row level security;

drop policy if exists "read keepalive" on public.gr_keepalive;
create policy "read keepalive"
  on public.gr_keepalive
  for select
  using (true);

create or replace function public.gr_touch_keepalive()
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  ts timestamptz := now();
begin
  update public.gr_keepalive
     set touched_at = ts
   where id = 1;

  return jsonb_build_object('ok', true, 'touched_at', ts);
end;
$$;

revoke all on function public.gr_touch_keepalive() from public;
grant execute on function public.gr_touch_keepalive() to anon, authenticated;
