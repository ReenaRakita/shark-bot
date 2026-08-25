-- schema.sql
-- Run once to set up the database
-- Command: psql -U shark_bot -d shark_bot -f schema.sql

-- ── Users ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id         BIGINT PRIMARY KEY,
    shark_dollars   INTEGER  DEFAULT 0,
    total_catches   INTEGER  DEFAULT 0,
    daily_last      BIGINT   DEFAULT 0,
    prestige        SMALLINT DEFAULT 0,
    loan_amount     INTEGER  DEFAULT 0,
    loan_due        BIGINT   DEFAULT 0,
    aquarium_slots  SMALLINT DEFAULT 3,
    hatchery_level  SMALLINT DEFAULT 0
);

-- ── Profiles ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS profiles (
    id                  SERIAL PRIMARY KEY,
    user_id             BIGINT   NOT NULL,
    guild_id            BIGINT   NOT NULL,
    xp                  INTEGER  DEFAULT 0,
    level               INTEGER  DEFAULT 0,
    last_xp_ts          BIGINT   DEFAULT 0,
    catching_zone_level SMALLINT DEFAULT 0,
    UNIQUE (user_id, guild_id)
);

-- ── Collection ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS collection (
    user_id    BIGINT      NOT NULL,
    shark_type VARCHAR(30) NOT NULL,
    count      INTEGER     DEFAULT 0,
    PRIMARY KEY (user_id, shark_type)
);

-- ── Aquarium ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aquarium (
    id         SERIAL      PRIMARY KEY,
    user_id    BIGINT      NOT NULL,
    shark_type VARCHAR(30) NOT NULL,
    stage      VARCHAR(20) DEFAULT 'Baby',
    nickname   VARCHAR(50) DEFAULT NULL,
    last_fed   BIGINT      DEFAULT 0,
    placed_at  BIGINT      DEFAULT 0
);

-- ── Breeding ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS breeding (
    id             SERIAL      PRIMARY KEY,
    user_id        BIGINT      NOT NULL,
    shark_type     VARCHAR(30) NOT NULL,
    start_ts       BIGINT      NOT NULL,
    end_ts         BIGINT      NOT NULL,
    hatchery_level SMALLINT    DEFAULT 0
);

-- ── Channels ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS channels (
    channel_id BIGINT  PRIMARY KEY,
    guild_id   BIGINT  NOT NULL,
    spawn_min  INTEGER DEFAULT 60,
    spawn_max  INTEGER DEFAULT 600,
    last_spawn BIGINT  DEFAULT 0,
    next_spawn BIGINT  DEFAULT 0
);

-- ── Servers ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS servers (
    server_id BIGINT  PRIMARY KEY,
    do_spawns BOOLEAN DEFAULT true
);

-- ── Black Market ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS market (
    id        SERIAL      PRIMARY KEY,
    seller_id BIGINT      NOT NULL,
    shark_type VARCHAR(30) NOT NULL,
    price     INTEGER     NOT NULL,
    listed_at BIGINT      NOT NULL
);

-- ── Expeditions ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expeditions (
    id         SERIAL      PRIMARY KEY,
    user_id    BIGINT      NOT NULL,
    shark_type VARCHAR(30) NOT NULL,
    duration   INTEGER     NOT NULL,
    start_ts   BIGINT      NOT NULL,
    end_ts     BIGINT      NOT NULL
);

-- ── Bounties ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bounties (
    id         SERIAL       PRIMARY KEY,
    user_id    BIGINT       NOT NULL,
    task       VARCHAR(100) NOT NULL,
    target     VARCHAR(30),
    reward_sd  INTEGER      NOT NULL,
    reward_xp  INTEGER      NOT NULL,
    is_weekly  BOOLEAN      DEFAULT false,
    completed  BOOLEAN      DEFAULT false,
    expires_at BIGINT       NOT NULL
);