-- ============================================================
-- Clube USA — Migration 001: Initial Schema
-- Apply via Supabase SQL Editor or psql.
-- All tables use UUIDs as PKs to prevent enumeration attacks.
-- ============================================================

-- Extension for UUID generation
create extension if not exists "pgcrypto";

-- ----------------------------------------------------------
-- USERS — auth data only; profile data is separate
-- ----------------------------------------------------------
create table if not exists users (
    id                      uuid primary key default gen_random_uuid(),
    email                   text not null unique,
    password_hash           text not null,
    email_confirmed         boolean not null default false,
    email_confirm_token     text,          -- SHA-256 hex of the raw token
    email_confirm_expires   timestamptz,   -- 24h window
    created_at              timestamptz not null default now(),
    updated_at              timestamptz not null default now()
);

create index if not exists idx_users_email on users(email);
create index if not exists idx_users_email_confirm_token on users(email_confirm_token);

-- ----------------------------------------------------------
-- PROFILES — public/editable user data, isolated by user_id
-- ----------------------------------------------------------
create table if not exists profiles (
    id           uuid primary key default gen_random_uuid(),
    user_id      uuid not null unique references users(id) on delete cascade,
    full_name    text not null,
    phone        text,
    zip_code     text,
    state        text,   -- US state abbreviation, e.g. "FL"
    city         text,
    bio          text,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

create index if not exists idx_profiles_user_id on profiles(user_id);

-- ----------------------------------------------------------
-- REFRESH_TOKENS — stored as SHA-256 hash, never plaintext
-- ----------------------------------------------------------
create table if not exists refresh_tokens (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references users(id) on delete cascade,
    token_hash  text not null unique,   -- SHA-256 hex of the raw token
    expires_at  timestamptz not null,
    created_at  timestamptz not null default now(),
    revoked_at  timestamptz            -- null = active
);

create index if not exists idx_refresh_tokens_user_id on refresh_tokens(user_id);
create index if not exists idx_refresh_tokens_hash on refresh_tokens(token_hash);

-- ----------------------------------------------------------
-- updated_at trigger (keeps updated_at in sync automatically)
-- ----------------------------------------------------------
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger users_updated_at
    before update on users
    for each row execute procedure set_updated_at();

create trigger profiles_updated_at
    before update on profiles
    for each row execute procedure set_updated_at();

-- ----------------------------------------------------------
-- RLS — enabled now, policies restrict future client-side access.
-- The backend uses service_role which bypasses RLS, so these
-- policies guard against any accidental anon/jwt usage.
-- ----------------------------------------------------------
alter table users enable row level security;
alter table profiles enable row level security;
alter table refresh_tokens enable row level security;

-- No public access to any table via anon key
create policy "no_anon_users" on users for all to anon using (false);
create policy "no_anon_profiles" on profiles for all to anon using (false);
create policy "no_anon_refresh_tokens" on refresh_tokens for all to anon using (false);

-- Authenticated users via Supabase JWT: can only see their own row
-- (These policies protect the data if RLS-aware client code is ever added)
create policy "own_user_row" on users
    for select to authenticated using (auth.uid() = id);

create policy "own_profile_row" on profiles
    for all to authenticated using (auth.uid() = user_id);

create policy "own_refresh_tokens" on refresh_tokens
    for all to authenticated using (auth.uid() = user_id);
