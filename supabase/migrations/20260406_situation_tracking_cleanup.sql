-- Phase 11A: Situation tracking tech debt cleanup
--
-- 1. Drop principal_id from situations — ownership is via accountability registry, not stored on row
-- 2. Relax card_type CHECK constraint — problem/opportunity binary is wrong; direction is DA's job
-- 3. Add DISMISSED and SNOOZED removal from status CHECK (snooze removed from product)
-- 4. Drop run_id foreign key from situation_actions (keep column nullable for audit but remove FK)

-- Drop principal_id index first, then column
DROP INDEX IF EXISTS idx_situations_principal_id;
ALTER TABLE situations DROP COLUMN IF EXISTS principal_id;

-- Relax card_type constraint (drop and re-add without CHECK, or widen it)
ALTER TABLE situations DROP CONSTRAINT IF EXISTS situations_card_type_check;

-- Remove SNOOZED from situations status CHECK — snooze feature removed
ALTER TABLE situations DROP CONSTRAINT IF EXISTS situations_status_check;
ALTER TABLE situations ADD CONSTRAINT situations_status_check
    CHECK (status IN ('OPEN','ANALYZING','SOLUTION_APPROVED','RESOLVED','DISMISSED','DELEGATED'));

-- Drop the FK constraint on situation_actions.run_id (column stays nullable for legacy rows)
ALTER TABLE situation_actions DROP CONSTRAINT IF EXISTS situation_actions_run_id_fkey;
