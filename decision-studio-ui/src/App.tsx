import { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Login } from './pages/Login'
import { LandingPageAlternate as LandingPage } from './pages/LandingPageAlternate'

// Route-based code splitting (2026-08-29 audit item #3) — every page used to
// be a static top-level import, so the whole app (dashboard, every settings
// screen, every onboarding wizard, every marketing page) shipped as one
// 2.25MB chunk on first load regardless of which single route a visitor
// actually opened. Only the two entry routes ("/" and "/login" — the first
// thing effectively every visitor hits) stay eager, to avoid an extra
// request-waterfall hop on first paint; everything reached by navigating
// somewhere lazy-loads its own chunk instead.
// AdminConsole replaced by Settings (RegistryExplorer at /settings)
const DataProductOnboarding = lazy(() =>
  import('./pages/DataProductOnboarding').then(m => ({ default: m.DataProductOnboarding })))
const DataProductOnboardingNew = lazy(() =>
  import('./pages/DataProductOnboardingNew').then(m => ({ default: m.DataProductOnboardingNew })))
const RegistryExplorer = lazy(() =>
  import('./pages/RegistryExplorer').then(m => ({ default: m.RegistryExplorer })))
const ContextExplorer = lazy(() =>
  import('./pages/ContextExplorer').then(m => ({ default: m.ContextExplorer })))
const ExecutiveBriefing = lazy(() =>
  import('./pages/ExecutiveBriefing').then(m => ({ default: m.ExecutiveBriefing })))
const WhitePaperReport = lazy(() =>
  import('./pages/WhitePaperReport').then(m => ({ default: m.WhitePaperReport })))
const CouncilDebatePage = lazy(() =>
  import('./pages/CouncilDebatePage').then(m => ({ default: m.CouncilDebatePage })))
const Portfolio = lazy(() =>
  import('./pages/Portfolio').then(m => ({ default: m.Portfolio })))
const HowItWorks = lazy(() =>
  import('./pages/HowItWorks').then(m => ({ default: m.HowItWorks })))
const InsightsBIModernization = lazy(() =>
  import('./pages/InsightsBIModernization').then(m => ({ default: m.InsightsBIModernization })))
const DataOnboarding = lazy(() =>
  import('./pages/DataOnboarding').then(m => ({ default: m.DataOnboarding })))
const ActionHandler = lazy(() => import('./pages/ActionHandler'))
const DelegatePage = lazy(() => import('./pages/DelegatePage'))
const CompanyProfile = lazy(() => import('./pages/CompanyProfile'))
const KPIIntelligence = lazy(() =>
  import('./pages/KPIIntelligence').then(m => ({ default: m.KPIIntelligence })))
const BusinessProcessIntelligence = lazy(() =>
  import('./pages/BusinessProcessIntelligence').then(m => ({ default: m.BusinessProcessIntelligence })))
const GovernanceView = lazy(() =>
  import('./pages/GovernanceView').then(m => ({ default: m.GovernanceView })))
const OnboardingDayView = lazy(() =>
  import('./pages/OnboardingDayView').then(m => ({ default: m.OnboardingDayView })))
const OnboardingResume = lazy(() =>
  import('./pages/OnboardingResume').then(m => ({ default: m.OnboardingResume })))
// DecisionStudio is the actual post-login app -- the single highest-traffic
// route after the entry pages, but still not the FIRST thing painted, so it
// stays lazy like the rest rather than joining Login/LandingPage as eager.
const DecisionStudio = lazy(() =>
  import('./pages/DecisionStudio').then(m => ({ default: m.DecisionStudio })))
// PrincipalManagement merged into Settings (RegistryExplorer)

// Hostname routing: decision-studios.com → corporate site, everything else → app
const isCorporateDomain = window.location.hostname.includes('decision-studios.com')

// Admin mode guard — redirect to /settings if system admin tries to access the pipeline
function AdminGuard({ children }: { children: React.ReactNode }) {
  const isAdmin = localStorage.getItem('a9_admin_mode') === 'true'
  if (isAdmin) return <Navigate to="/settings" replace />
  return <>{children}</>
}

// Minimal, theme-matched fallback for the gap between "clicked a link" and
// "that route's chunk arrived" -- a bare spinner, not a full skeleton, since
// every lazy route already renders its own loading state once its own code
// is running; this only covers the code-fetch itself; a blank flash on a
// dark app reads as broken, not as fast.
function RouteFallback() {
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-slate-700 border-t-slate-400 rounded-full animate-spin" />
    </div>
  )
}

function App() {
  return (
    <Router>
      <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={isCorporateDomain ? <LandingPage /> : <Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<AdminGuard><DecisionStudio /></AdminGuard>} />
        <Route path="/debate/:situationId" element={<CouncilDebatePage />} />
        <Route path="/briefing/:situationId" element={<ExecutiveBriefing />} />
        <Route path="/report/:situationId" element={<WhitePaperReport />} />
        <Route path="/context" element={<ContextExplorer />} />
        {/* Settings — main registry explorer (section via ?section= param) */}
        <Route path="/settings" element={<RegistryExplorer />} />
        <Route path="/settings/registry/:section" element={<RegistryExplorer />} />
        <Route path="/settings/accountability" element={<RegistryExplorer />} />
        <Route path="/settings/ownership-interview" element={<RegistryExplorer />} />
        <Route path="/settings/connection-health" element={<RegistryExplorer />} />
        <Route path="/settings/slice-validity" element={<RegistryExplorer />} />

        {/* Settings — standalone pages wrapped in SettingsLayout */}
        <Route path="/settings/company-profile" element={<CompanyProfile />} />
        <Route path="/settings/kpi-intelligence" element={<KPIIntelligence />} />
        <Route path="/settings/business-process-intelligence" element={<BusinessProcessIntelligence />} />
        <Route path="/settings/data-onboarding" element={<DataProductOnboardingNew />} />
        <Route path="/settings/onboarding-legacy" element={<DataProductOnboarding />} />

        {/* Settings — Admin onboarding wizard (Mode 1) */}
        <Route path="/settings/onboarding" element={<OnboardingResume />} />
        {/* React Router 7.10.1 fails to match a hyphen-prefixed dynamic segment
            (path="day-:day") on this route shape — confirmed via isolated repro,
            unrelated to any app code. Capture the whole segment via :day instead;
            OnboardingDayView already strips the "day-" prefix itself, so no
            component change is needed, only the route pattern. */}
        <Route path="/settings/onboarding/:day" element={<OnboardingDayView />} />

        {/* Settings — Executive governance pages (Mode 3) */}
        <Route path="/settings/governance/:subsection" element={<GovernanceView />} />
        <Route path="/settings/governance" element={<GovernanceView />} />
        <Route path="/portfolio" element={<Portfolio />} />
        {/* Corporate landing page accessible directly on any domain */}
        <Route path="/landing" element={<LandingPage />} />
        {/* Architecture / how it works */}
        <Route path="/how-it-works" element={<HowItWorks />} />
        {/* Insights / content marketing pages */}
        <Route path="/insights" element={<Navigate to="/insights/bi-modernization" replace />} />
        <Route path="/insights/bi-modernization" element={<InsightsBIModernization />} />
        {/* Data onboarding capability page */}
        <Route path="/data-onboarding" element={<DataOnboarding />} />
        {/* PIB email token action handler — no auth, token is the credential */}
        <Route path="/action" element={<ActionHandler />} />
        <Route path="/delegate" element={<DelegatePage />} />
        {/* Legacy routes → redirects */}
        <Route path="/admin" element={<Navigate to="/settings" replace />} />
        <Route path="/admin/registry" element={<Navigate to="/settings" replace />} />
        <Route path="/admin/principals" element={<Navigate to="/settings" replace />} />
        <Route path="/admin/onboarding" element={<Navigate to="/settings/onboarding" replace />} />
        {/* Redirect any unknown routes to landing page */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </Suspense>
    </Router>
  )
}

export default App
