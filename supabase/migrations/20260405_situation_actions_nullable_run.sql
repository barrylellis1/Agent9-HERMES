-- Phase 9C fix: make run_id nullable on situation_actions
-- Delegation and snooze actions can originate outside an assessment run
-- (e.g. from a PIB email token click), so run_id must be optional.

ALTER TABLE situation_actions
    ALTER COLUMN run_id DROP NOT NULL;
