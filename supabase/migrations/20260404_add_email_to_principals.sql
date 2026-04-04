-- Migration: Add email column to principal_profiles
-- Phase 9 — PIB email delivery requires a contact address per principal.
-- Applies to both local Supabase and production.

ALTER TABLE public.principal_profiles
    ADD COLUMN IF NOT EXISTS email TEXT;

COMMENT ON COLUMN public.principal_profiles.email IS
    'Contact email address used for Principal Intelligence Briefing delivery.';

-- Lubricants business principals (demo / production seed data)
UPDATE public.principal_profiles SET email = 'barrylellis1@gmail.com' WHERE id = 'cfo_001';
UPDATE public.principal_profiles SET email = 'barrylellis1@gmail.com' WHERE id = 'ceo_001';
UPDATE public.principal_profiles SET email = 'barrylellis1@gmail.com' WHERE id = 'coo_001';
UPDATE public.principal_profiles SET email = 'barrylellis1@gmail.com' WHERE id = 'finance_manager_001';
