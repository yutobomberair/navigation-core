-- Progress Navi mock: Supabase schema
-- Run this in the Supabase SQL editor before deploying the app.

create extension if not exists "pgcrypto";

create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    code text unique not null,
    line_user_id text unique,  -- set when identity originated from the LINE bot
    nickname text,
    created_at timestamptz not null default now()
);

create table if not exists persons (
    user_id uuid primary key references users(id) on delete cascade,
    age int,
    personality text,
    strengths text,
    weaknesses text,
    lifestyle text,
    available_time text,
    motivation_type text
);

create table if not exists goals (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    title text not null,
    deadline date,
    background text,
    reason text,
    ideal_state text,
    estimated_arrival text,
    status text not null default 'active',
    created_at timestamptz not null default now()
);

create table if not exists current_states (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    goal_id uuid not null references goals(id) on delete cascade,
    current_ability text,
    issues text,
    missing_elements text,
    distance_to_goal text,
    -- per-parameter score (0-100) from the diagnostic assessment, e.g.
    -- {"Vocabulary": 70, "Listening": 40}; parameter names vary by goal domain
    parameters jsonb,
    updated_at timestamptz not null default now()
);

create table if not exists assessments (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    goal_id uuid not null references goals(id) on delete cascade,
    questions jsonb not null default '[]',
    answers jsonb,
    created_at timestamptz not null default now()
);

create table if not exists milestones (
    id uuid primary key default gen_random_uuid(),
    goal_id uuid not null references goals(id) on delete cascade,
    "order" int not null,
    name text not null,
    kpi text,
    tasks jsonb not null default '[]',
    estimated_effort text,
    buffer text,
    status text not null default 'not_started'
);

create table if not exists daily_tasks (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    -- scoped per goal, not just per user+date — otherwise switching goals
    -- mid-day resurfaces the previous goal's tasks for "today"
    goal_id uuid references goals(id) on delete cascade,
    date date not null,
    tasks jsonb not null default '[]',
    completed jsonb not null default '[]',
    unique (user_id, goal_id, date)
);

create table if not exists conversation_history (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    channel text not null,
    role text not null,
    message text not null,
    timestamp timestamptz not null default now()
);

create table if not exists reflections (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    goal_id uuid references goals(id) on delete cascade,  -- see daily_tasks.goal_id
    date date not null,
    went_well text,
    struggled text,
    unique (user_id, goal_id, date)
);

-- This app is server-side only (Streamlit never exposes the Supabase URL/key to
-- a browser), and identity is handled by our own ?u= code rather than Supabase
-- Auth, so RLS policies based on auth.uid() don't apply here. Make sure RLS is
-- off and grant the anon role direct CRUD access instead.
alter table public.users disable row level security;
alter table public.persons disable row level security;
alter table public.goals disable row level security;
alter table public.current_states disable row level security;
alter table public.assessments disable row level security;
alter table public.milestones disable row level security;
alter table public.daily_tasks disable row level security;
alter table public.conversation_history disable row level security;
alter table public.reflections disable row level security;

grant usage on schema public to anon;
grant select, insert, update, delete on all tables in schema public to anon;

notify pgrst, 'reload schema';
