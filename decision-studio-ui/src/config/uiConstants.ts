import { User } from 'lucide-react';
import { Principal, Council, Persona } from '../api/types';
import { personaDisplayLabel } from '../utils/personaLabels';

// Mock Data for the Ridgeline Scanner (Simulating System Pulse)
export const MOCK_HISTORY = Array.from({ length: 12 }).map((_, i) => ({
  date: `Month ${i + 1}`,
  distributions: [
    { 
      id: "kpi_revenue", 
      label: "Gross Revenue", 
      // Drifts negative significantly in later months (simulating the breach)
      data: Array.from({ length: 50 }).map(() => Math.random() * 0.6 + (i > 8 ? -0.5 : 0.1)) 
    },
    { 
      id: "kpi_payroll", 
      label: "Payroll Cost", 
      // Stable
      data: Array.from({ length: 50 }).map(() => Math.random() * 0.4 + 0.1) 
    },
    { 
      id: "kpi_margin", 
      label: "Operating Margin", 
      // Slight variance
      data: Array.from({ length: 50 }).map(() => Math.random() * 0.5 - 0.1) 
    }
  ]
}));

export const AVAILABLE_PRINCIPALS: Principal[] = [
  { id: "cfo_001", name: "Sarah Chen", title: "Chief Financial Officer", initials: "SC", decision_style: "analytical", color: "bg-blue-500/20 text-blue-400", workflow_role: "decision_maker" },
  { id: "ceo_001", name: "David Torres", title: "Chief Executive Officer", initials: "DT", decision_style: "visionary", color: "bg-purple-500/20 text-purple-400", workflow_role: "decision_maker" },
  { id: "coo_001", name: "Rachel Kim", title: "Chief Operating Officer", initials: "RK", decision_style: "pragmatic", color: "bg-emerald-500/20 text-emerald-400", workflow_role: "decision_maker" },
  { id: "finance_manager_001", name: "Marcus Webb", title: "Finance Manager", initials: "MW", decision_style: "analytical", color: "bg-amber-500/20 text-amber-400", workflow_role: "framer" },
];

// Preset -> persona-id list, mirroring consulting_personas_registry.yaml's
// `council_presets` section exactly.
//
// WHY THIS EXISTS: selecting a preset previously only set `selectedPreset`
// (a label for UI highlighting) without ever populating `selectedPersonas`.
// Every downstream consumer that builds the actual dispatch payload
// (CouncilDebatePage.tsx) falls back to a hardcoded ['mckinsey','bcg','bain']
// whenever `selectedPersonas` is empty — which is EVERY preset selection,
// not just a new one. Because the backend's persona-resolution order checks
// `consulting_personas` before `council_preset`, that hardcoded fallback wins
// and the actual preset choice is never consulted. This is invisible for the
// MBB preset (the fallback happens to equal the right answer) and was
// silently breaking every OTHER preset — Big 4, Tech, Risk — before lenses
// were ever added. Populating `selectedPersonas` at the moment a preset is
// chosen (see DeepFocusView.tsx) fixes the root cause for all five presets,
// not just the new one.
//
// Declared BEFORE AVAILABLE_COUNCILS (moved 2026-10-02, Phase 18 Category C)
// so each preset's description can be DERIVED from this list via
// personaDisplayLabel() rather than hand-typed — a hand-typed description
// is exactly how "McKinsey, BCG, Bain" ended up on screen, and how it could
// silently drift from this array if either were edited without the other.
export const COUNCIL_PRESET_PERSONAS: Record<string, string[]> = {
  mbb_council: ["mckinsey", "bcg", "bain"],
  big4_council: ["deloitte", "ey_parthenon", "kpmg", "pwc_strategy"],
  tech_council: ["deloitte", "accenture", "bcg"],
  risk_council: ["kpmg", "ey_parthenon", "deloitte"],
  lens_council: ["commercial", "operational", "structural"],
};

// Phase 18 Category C (2026-10-02): every label and description below used to
// name real firms directly ("MBB Strategy Council" / "McKinsey, BCG, Bain",
// "Big 4 Advisory Council" / "Deloitte, EY-Parthenon, KPMG, PwC") in the
// council-preset PICKER a user sees before a debate even starts — the most
// exposed surface of all, since it explicitly invites "pick which firm's
// approach you want" rather than describing what the product itself does.
// Descriptions are now derived from COUNCIL_PRESET_PERSONAS via
// personaDisplayLabel(), the same de-branding utility the Executive Briefing
// and CouncilDebatePage already use, so they can't drift from the persona
// list they describe. Labels naming a specific firm or a well-known
// firm-grouping nickname ("MBB", "Big 4") are renamed to describe the
// council's actual composition instead.
const councilDescription = (ids: string[]): string => ids.map(personaDisplayLabel).join(', ');

export const AVAILABLE_COUNCILS: Council[] = [
  { id: "mbb_council", label: "Strategy Council", description: councilDescription(COUNCIL_PRESET_PERSONAS.mbb_council), icon: User, color: "text-purple-400" },
  { id: "big4_council", label: "Enterprise Advisory Council", description: councilDescription(COUNCIL_PRESET_PERSONAS.big4_council), icon: User, color: "text-blue-400" },
  { id: "tech_council", label: "Tech Transformation", description: councilDescription(COUNCIL_PRESET_PERSONAS.tech_council), icon: User, color: "text-emerald-400" },
  { id: "risk_council", label: "Risk & Governance", description: councilDescription(COUNCIL_PRESET_PERSONAS.risk_council), icon: User, color: "text-red-400" },
  // Method-defined alternative to the four firm-branded presets above — see
  // consulting_personas_registry.yaml:350. Offered alongside MBB, not in place
  // of it (2026-08-17 decision); the analytical comparison is still open.
  { id: "lens_council", label: "Analytical Lens Council", description: councilDescription(COUNCIL_PRESET_PERSONAS.lens_council), icon: User, color: "text-teal-400" },
];

export const AVAILABLE_PERSONAS: Persona[] = [
  // Consulting Firms — label resolves through personaDisplayLabel(), not a
  // literal name, for the same reason as AVAILABLE_COUNCILS above.
  { id: "mckinsey", label: personaDisplayLabel("mckinsey"), type: "firm", icon: User, color: "text-purple-400" },
  { id: "bcg", label: personaDisplayLabel("bcg"), type: "firm", icon: User, color: "text-green-400" },
  { id: "bain", label: personaDisplayLabel("bain"), type: "firm", icon: User, color: "text-red-400" },
  { id: "deloitte", label: personaDisplayLabel("deloitte"), type: "firm", icon: User, color: "text-blue-400" },
  { id: "accenture", label: personaDisplayLabel("accenture"), type: "firm", icon: User, color: "text-orange-400" },
  // Legacy Roles (Fallback)
  { id: "CFO", label: "CFO", type: "role", icon: User, color: "text-emerald-400" },
  { id: "Supply Chain Expert", label: "Supply Chain", type: "role", icon: User, color: "text-amber-400" },
];
