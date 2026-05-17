/**
 * Supabase client singleton — Infra B Authentication.
 *
 * VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are injected at build time
 * from .env.development / .env.production (see those files).
 *
 * All auth state changes are handled by the Supabase client automatically;
 * the session JWT is refreshed in the background and stored in localStorage
 * under the Supabase default key (supabase.auth.token).
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    '[supabase] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is not set. ' +
    'Auth features will be unavailable. Set these env vars in .env.development or .env.production.'
  );
}

export const supabase = createClient(
  supabaseUrl || 'http://127.0.0.1:54321',   // fallback for safety
  supabaseAnonKey || '',
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,   // handles magic link ?access_token= flows
    },
  }
);

/**
 * Infer client_id from email domain.
 * The mapping comes from VITE_TENANT_DOMAIN_MAP (build-time) or falls
 * back to a demo sentinel.
 *
 * Format: "domain1:client_id1,domain2:client_id2"
 * Example: "apex.com:apex_lubricants,hess.com:hess,lubricants.com:lubricants"
 */
export function inferClientIdFromEmail(email: string): string | null {
  const domainMapRaw = (import.meta.env.VITE_TENANT_DOMAIN_MAP as string) || '';
  if (!domainMapRaw.trim()) return null;

  const domain = email.split('@')[1]?.toLowerCase() ?? '';
  const entries = domainMapRaw.split(',').map(e => e.trim().split(':'));

  for (const [d, cid] of entries) {
    if (d && cid && domain === d.toLowerCase()) return cid;
  }
  return null;
}
