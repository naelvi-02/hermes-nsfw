-- ============================================================
-- NAELVI Supabase Migration (W1.1)
-- Idempotent: CREATE TABLE IF NOT EXISTS + CREATE OR REPLACE FUNCTION
-- pg_ref: generic payment reference (Tripay/Midtrans future swap)
-- Credit-first deduction: purchased credits before monthly allocation
-- ============================================================

-- ============================================================
-- TABLE: users — Core user identity and tier
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    telegram_id    BIGINT PRIMARY KEY,
    username       TEXT,
    display_name   TEXT,
    tier           TEXT NOT NULL DEFAULT 'free',
                     -- 'free' | 'pro' | 'ultra'
    tier_expires   TIMESTAMPTZ,
                     -- NULL for free tier = never expires
    persona_id     TEXT,
                     -- active persona UUID if multiple personas exist
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: usage — Daily/monthly usage tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS usage (
    telegram_id    BIGINT NOT NULL REFERENCES users(telegram_id),
    period_start   DATE NOT NULL DEFAULT CURRENT_DATE,
    msg_count      INT NOT NULL DEFAULT 0,
    img_count      INT NOT NULL DEFAULT 0,
    video_count    INT NOT NULL DEFAULT 0,
    PRIMARY KEY (telegram_id, period_start)
);

-- ============================================================
-- TABLE: credits — Purchased credit balance (additive)
-- ============================================================
CREATE TABLE IF NOT EXISTS credits (
    telegram_id    BIGINT PRIMARY KEY REFERENCES users(telegram_id),
    img_credits    INT NOT NULL DEFAULT 0,
    video_credits  INT NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: payments — Transaction log
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    telegram_id    BIGINT NOT NULL REFERENCES users(telegram_id),
    pg_ref         TEXT UNIQUE,
                     -- Generic payment reference (Tripay/Midtrans)
    product_type   TEXT NOT NULL,
                     -- pro_monthly | ultra_monthly | img_pack_s | img_pack_m |
                     -- img_pack_l | video_pack_m | video_pack_l
    amount_idr     INT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending',
                     -- 'pending' | 'paid' | 'expired' | 'failed'
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at        TIMESTAMPTZ,
    raw_callback   JSONB
                     -- Store raw payment callback for audit
);

-- ============================================================
-- TABLE: video_jobs — Modal render job tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS video_jobs (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    telegram_id    BIGINT NOT NULL REFERENCES users(telegram_id),
    type           TEXT NOT NULL,          -- 't2v' | 'i2v'
    prompt         TEXT NOT NULL,
    input_image_url TEXT,
                     -- Only for I2V
    modal_job_id   TEXT,
    status         TEXT NOT NULL DEFAULT 'queued',
                     -- 'queued' | 'rendering' | 'encoding' | 'done' | 'failed'
    output_url     TEXT,
    error_message  TEXT,
    cost_estimate  NUMERIC(6,4),
                     -- Estimated cost in USD
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at   TIMESTAMPTZ
);

-- ============================================================
-- INDEXES (idempotent via IF NOT EXISTS)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_usage_period ON usage(period_start);
CREATE INDEX IF NOT EXISTS idx_payments_telegram ON payments(telegram_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_video_jobs_telegram ON video_jobs(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier);

-- ============================================================
-- FUNCTION: get_or_create_usage — ensure today's usage row exists
-- ============================================================
CREATE OR REPLACE FUNCTION get_or_create_usage(
    p_telegram_id BIGINT
) RETURNS usage AS $$
DECLARE
    v_row usage;
BEGIN
    INSERT INTO usage (telegram_id, period_start)
    VALUES (p_telegram_id, CURRENT_DATE)
    ON CONFLICT (telegram_id, period_start) DO NOTHING;

    SELECT * INTO v_row FROM usage
    WHERE telegram_id = p_telegram_id
    AND period_start = CURRENT_DATE;

    RETURN v_row;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- FUNCTION: check_user_access — gate before action
-- Action enum: 'msg' | 'img_nsfw' | 'video'
-- Credit-first: purchased credits checked before monthly allocation
-- ============================================================
CREATE OR REPLACE FUNCTION check_user_access(
    p_telegram_id BIGINT,
    p_action TEXT  -- 'msg' | 'img_nsfw' | 'video'
) RETURNS TABLE(allowed BOOLEAN, reason TEXT, remaining INT) AS $$
DECLARE
    v_user users%ROWTYPE;
    v_usage usage%ROWTYPE;
    v_credits credits%ROWTYPE;
    v_msg_limit INT := 30;  -- free tier daily limit
BEGIN
    -- Get user (create if new)
    INSERT INTO users (telegram_id) VALUES (p_telegram_id)
    ON CONFLICT (telegram_id) DO NOTHING;
    SELECT * INTO v_user FROM users WHERE telegram_id = p_telegram_id;

    -- Get today's usage
    SELECT * INTO v_usage FROM get_or_create_usage(p_telegram_id);

    CASE p_action
        WHEN 'msg' THEN
            IF v_user.tier = 'free' AND v_usage.msg_count >= v_msg_limit THEN
                allowed := false;
                reason := 'Daily message limit reached. Upgrade to PRO for unlimited.';
                remaining := 0;
            ELSE
                allowed := true;
                reason := 'ok';
                remaining := CASE WHEN v_user.tier = 'free'
                    THEN v_msg_limit - v_usage.msg_count
                    ELSE 999999 END;
            END IF;

        WHEN 'img_nsfw' THEN
            -- Free tier: no NSFW
            IF v_user.tier = 'free' THEN
                allowed := false;
                reason := 'NSFW image requires PRO subscription.';
                remaining := 0;
                RETURN NEXT;
                RETURN;
            END IF;

            -- Credit-first, then monthly allocation
            SELECT * INTO v_credits FROM credits
            WHERE telegram_id = p_telegram_id;

            IF COALESCE(v_credits.img_credits, 0) > 0 THEN
                allowed := true;
                reason := 'Using credit balance';
                remaining := v_credits.img_credits - 1;
            ELSIF v_user.tier = 'pro' AND v_usage.img_count < 100 THEN
                allowed := true;
                reason := 'Using monthly allocation';
                remaining := 99 - v_usage.img_count;
            ELSIF v_user.tier = 'ultra' AND v_usage.img_count < 300 THEN
                allowed := true;
                reason := 'Using monthly allocation';
                remaining := 299 - v_usage.img_count;
            ELSE
                allowed := false;
                reason := 'Monthly image limit reached. Buy credit pack with /topup';
                remaining := 0;
            END IF;

        WHEN 'video' THEN
            IF NOT (v_user.tier = 'ultra') THEN
                allowed := false;
                reason := 'Video generation requires ULTRA subscription.';
                remaining := 0;
                RETURN NEXT;
                RETURN;
            END IF;

            SELECT * INTO v_credits FROM credits
            WHERE telegram_id = p_telegram_id;

            -- Combined: monthly + purchased credits
            remaining := COALESCE(v_credits.video_credits, 0) +
                CASE WHEN v_usage.video_count < 30
                    THEN 30 - v_usage.video_count ELSE 0 END;

            IF remaining > 0 THEN
                allowed := true;
                reason := CASE WHEN v_credits.video_credits > 0
                    THEN 'Using video credit' ELSE 'Using monthly allocation' END;
                remaining := remaining - 1;
            ELSE
                allowed := false;
                reason := 'Video credits exhausted. Buy more with /topup';
            END IF;
    END CASE;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- FUNCTION: record_action — deduct after success
-- Action enum: 'msg' | 'img' | 'video'
-- Credit-first deduction for img/video
-- ============================================================
CREATE OR REPLACE FUNCTION record_action(
    p_telegram_id BIGINT,
    p_action TEXT  -- 'msg' | 'img' | 'video'
) RETURNS TABLE(ok BOOLEAN, remaining INT) AS $$
DECLARE
    v_credits credits%ROWTYPE;
    v_usage usage%ROWTYPE;
    v_remaining INT;
BEGIN
    SELECT * INTO v_usage FROM get_or_create_usage(p_telegram_id);

    CASE p_action
        WHEN 'msg' THEN
            UPDATE usage SET msg_count = msg_count + 1
            WHERE telegram_id = p_telegram_id AND period_start = CURRENT_DATE;

            -- Return remaining for free tier
            SELECT * INTO v_usage FROM usage
            WHERE telegram_id = p_telegram_id AND period_start = CURRENT_DATE;
            ok := true;
            remaining := 30 - v_usage.msg_count;

        WHEN 'img' THEN
            -- Credit-first deduction
            SELECT * INTO v_credits FROM credits
            WHERE telegram_id = p_telegram_id;

            IF COALESCE(v_credits.img_credits, 0) > 0 THEN
                UPDATE credits SET img_credits = img_credits - 1,
                    updated_at = NOW()
                WHERE telegram_id = p_telegram_id;
                remaining := v_credits.img_credits - 1;
            ELSE
                UPDATE usage SET img_count = img_count + 1
                WHERE telegram_id = p_telegram_id AND period_start = CURRENT_DATE;
                SELECT * INTO v_usage FROM usage
                WHERE telegram_id = p_telegram_id AND period_start = CURRENT_DATE;
                remaining := 99 - v_usage.img_count;  -- pro default
            END IF;
            ok := true;

        WHEN 'video' THEN
            SELECT * INTO v_credits FROM credits
            WHERE telegram_id = p_telegram_id;

            IF COALESCE(v_credits.video_credits, 0) > 0 THEN
                UPDATE credits SET video_credits = video_credits - 1,
                    updated_at = NOW()
                WHERE telegram_id = p_telegram_id;
                remaining := v_credits.video_credits - 1;
            ELSE
                UPDATE usage SET video_count = video_count + 1
                WHERE telegram_id = p_telegram_id AND period_start = CURRENT_DATE;
                SELECT * INTO v_usage FROM usage
                WHERE telegram_id = p_telegram_id AND period_start = CURRENT_DATE;
                remaining := 29 - v_usage.video_count;  -- ultra default
            END IF;
            ok := true;
    END CASE;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
