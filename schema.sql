-- Enable pgvector
create extension if not exists vector;

-- Writings table
create table if not exists writings (
    id            bigserial primary key,
    created_at    timestamptz default now(),
    discipline    text,
    agent_name    text,
    context       text,
    word_count    int,
    output_text   text,
    tokens_in     int,
    tokens_out    int,
    cost_usd      numeric(10,6)
);

-- Embeddings table
create table if not exists embeddings (
    id          bigserial primary key,
    writing_id  bigint references writings(id) on delete cascade,
    embedding   vector(1536)
);

-- Cost log table
create table if not exists cost_log (
    id          bigserial primary key,
    created_at  timestamptz default now(),
    feature     text,
    model       text,
    tokens_in   int,
    tokens_out  int,
    cost_usd    numeric(10,6)
);
