import { User } from 'lucide-react';
import { Principal, Council, Persona } from '../api/types';

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
  { id: "cfo_001", name: "Lars Mikkelsen", title: "Chief Financial Officer", initials: "LM", decision_style: "analytical", color: "bg-blue-500/20 text-blue-400" },
  { id: "ceo_001", name: "Alex Morgan", title: "Chief Executive Officer", initials: "AM", decision_style: "visionary", color: "bg-purple-500/20 text-purple-400" },
  { id: "coo_001", name: "Priya Desai", title: "Chief Operating Officer", initials: "PD", decision_style: "pragmatic", color: "bg-emerald-500/20 text-emerald-400" },
  { id: "finance_manager_001", name: "Emily Chen", title: "Finance Manager", initials: "EC", decision_style: "analytical", color: "bg-amber-500/20 text-amber-400" },
];

export const AVAILABLE_COUNCILS: Council[] = [
  { id: "mbb_council", label: "MBB Strategy Council", description: "McKinsey, BCG, Bain", icon: User, color: "text-purple-400" },
  { id: "big4_council", label: "Big 4 Advisory Council", description: "Deloitte, EY-Parthenon, KPMG, PwC", icon: User, color: "text-blue-400" },
  { id: "tech_council", label: "Tech Transformation", description: "Accenture, Deloitte, BCG", icon: User, color: "text-emerald-400" },
  { id: "risk_council", label: "Risk & Governance", description: "KPMG, EY-Parthenon, Deloitte", icon: User, color: "text-red-400" },
];

export const AVAILABLE_PERSONAS: Persona[] = [
  // Consulting Firms
  { id: "mckinsey", label: "McKinsey", type: "firm", icon: User, color: "text-purple-400" },
  { id: "bcg", label: "BCG", type: "firm", icon: User, color: "text-green-400" },
  { id: "bain", label: "Bain", type: "firm", icon: User, color: "text-red-400" },
  { id: "deloitte", label: "Deloitte", type: "firm", icon: User, color: "text-blue-400" },
  { id: "accenture", label: "Accenture", type: "firm", icon: User, color: "text-orange-400" },
  // Legacy Roles (Fallback)
  { id: "CFO", label: "CFO", type: "role", icon: User, color: "text-emerald-400" },
  { id: "Supply Chain Expert", label: "Supply Chain", type: "role", icon: User, color: "text-amber-400" },
];
