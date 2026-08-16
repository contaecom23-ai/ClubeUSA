-- product_tracker_migration.sql
-- Executar no Supabase SQL Editor

CREATE TABLE tracked_products (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id     UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    source_url    TEXT NOT NULL,
    source        VARCHAR(20) NOT NULL CHECK (source IN ('amazon','walmart','target','bestbuy')),
    source_id     VARCHAR(64) NOT NULL,
    title         TEXT,
    image_url     TEXT,
    status        VARCHAR(20) NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'paused', 'cancelled')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tracked_member ON tracked_products (member_id);
CREATE INDEX idx_tracked_active ON tracked_products (status) WHERE status = 'active';

CREATE TABLE tracked_product_offers (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracked_product_id UUID NOT NULL REFERENCES tracked_products(id) ON DELETE CASCADE,
    marketplace        VARCHAR(20) NOT NULL CHECK (marketplace IN ('amazon','walmart','target','bestbuy')),
    price              NUMERIC(10,2),
    url                TEXT NOT NULL,
    last_checked_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tracked_product_id, marketplace)
);

CREATE TABLE tracked_product_coupons (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracked_product_id UUID NOT NULL REFERENCES tracked_products(id) ON DELETE CASCADE,
    marketplace        VARCHAR(20) NOT NULL,
    code               VARCHAR(64) NOT NULL,
    description        TEXT,
    source             VARCHAR(40),
    verified           BOOLEAN,
    last_verified_at   TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tracked_product_id, marketplace, code)
);

CREATE INDEX idx_coupons_product ON tracked_product_coupons (tracked_product_id);

ALTER TABLE tracked_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracked_product_offers ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracked_product_coupons ENABLE ROW LEVEL SECURITY;

CREATE POLICY tracked_products_own_select ON tracked_products
    FOR SELECT USING (member_id = auth.uid());
CREATE POLICY tracked_products_own_insert ON tracked_products
    FOR INSERT WITH CHECK (member_id = auth.uid());
CREATE POLICY tracked_products_own_update ON tracked_products
    FOR UPDATE USING (member_id = auth.uid());

CREATE POLICY offers_via_product ON tracked_product_offers
    FOR SELECT USING (
        tracked_product_id IN (SELECT id FROM tracked_products WHERE member_id = auth.uid())
    );
CREATE POLICY coupons_via_product ON tracked_product_coupons
    FOR SELECT USING (
        tracked_product_id IN (SELECT id FROM tracked_products WHERE member_id = auth.uid())
    );
