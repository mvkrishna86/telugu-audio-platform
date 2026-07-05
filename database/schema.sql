-- Telugu Audio Platform — Supabase PostgreSQL Schema
-- Run this in: Supabase Dashboard → SQL Editor

-- ── Users ──
CREATE TABLE users (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    supabase_uid    text UNIQUE NOT NULL,
    name            text,
    avatar_url      text,
    email           text,
    phone           text,
    role            text NOT NULL DEFAULT 'listener'
                    CHECK (role IN ('listener','admin','superadmin')),
    preferred_lang  text NOT NULL DEFAULT 'te'
                    CHECK (preferred_lang IN ('te','en')),
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ── Categories ──
CREATE TABLE categories (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name_te         text NOT NULL,
    name_en         text NOT NULL,
    slug            text UNIQUE NOT NULL,
    icon_url        text,
    display_order   int NOT NULL DEFAULT 0
);

INSERT INTO categories (name_te, name_en, slug, display_order) VALUES
    ('సంగీతం',      'Music',     'music',     1),
    ('పాడ్‌క్యాస్ట్', 'Podcast',  'podcast',   2),
    ('ఆడియోబుక్',   'Audiobook', 'audiobook', 3),
    ('కథలు',        'Stories',   'story',     4);

-- ── Content ──
CREATE TABLE content (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title_te        text NOT NULL,
    title_en        text,
    description_te  text,
    description_en  text,
    type            text NOT NULL
                    CHECK (type IN ('music','podcast','audiobook','story')),
    category_id     uuid REFERENCES categories(id) ON DELETE SET NULL,
    thumbnail_url   text,
    artist_author   text,
    release_year    int,
    total_parts     int NOT NULL DEFAULT 1,
    play_count      bigint NOT NULL DEFAULT 0,
    is_published    boolean NOT NULL DEFAULT false,
    uploaded_by     uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_content_type ON content(type);
CREATE INDEX idx_content_published ON content(is_published);
CREATE INDEX idx_content_play_count ON content(play_count DESC);

-- ── Audio Files ──
CREATE TABLE audio_files (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id      uuid NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    part_number     int NOT NULL DEFAULT 1,
    title_te        text,
    title_en        text,
    s3_key          text NOT NULL,
    duration_sec    int,
    file_size_bytes bigint,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (content_id, part_number)
);

-- ── Listen History ──
CREATE TABLE listen_history (
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    audio_file_id   uuid NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
    position_sec    int NOT NULL DEFAULT 0,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, audio_file_id)
);

-- ── Bookmarks ──
CREATE TABLE bookmarks (
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_id      uuid NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, content_id)
);

-- ── Playlists ──
CREATE TABLE playlists (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE playlist_items (
    playlist_id     uuid NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    content_id      uuid NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    position        int NOT NULL DEFAULT 0,
    PRIMARY KEY (playlist_id, content_id)
);

-- ── Row Level Security ──
ALTER TABLE users           ENABLE ROW LEVEL SECURITY;
ALTER TABLE content         ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_files     ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories      ENABLE ROW LEVEL SECURITY;
ALTER TABLE listen_history  ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks       ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlists       ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlist_items  ENABLE ROW LEVEL SECURITY;

-- Public can read published content and categories
CREATE POLICY "public read content"     ON content     FOR SELECT USING (is_published = true);
CREATE POLICY "public read audio_files" ON audio_files FOR SELECT USING (true);
CREATE POLICY "public read categories"  ON categories  FOR SELECT USING (true);

-- Service role (backend) bypasses RLS — all other access goes through the Python backend
-- using the service role key, so no further user-level policies are needed here.
