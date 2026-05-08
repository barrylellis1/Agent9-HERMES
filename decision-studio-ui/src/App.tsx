import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { DecisionStudio } from './pages/DecisionStudio'
// AdminConsole replaced by Settings (RegistryExplorer at /settings)
import { DataProductOnboarding } from './pages/DataProductOnboarding'
import { DataProductOnboardingNew } from './pages/DataProductOnboardingNew'
import { RegistryExplorer } from './pages/RegistryExplorer'
import { ContextExplorer } from './pages/ContextExplorer'
import { ExecutiveBriefing } from './pages/ExecutiveBriefing'
import { WhitePaperReport } from './pages/WhitePaperReport'
import { CouncilDebatePage } from './pages/CouncilDebatePage'
import { Login } from './pages/Login'
import { Portfolio } from './pages/Portfolio'
import { LandingPageAlternate as LandingPage } from './pages/LandingPageAlternate'
import { HowItWorks } from './pages/HowItWorks'
import { InsightsBIModernization } from './pages/InsightsBIModernization'
import { DataOnboarding } from './pages/DataOnboarding'
import ActionHandler from './pages/ActionHandler'
import DelegatePage from './pages/DelegatePage'
import CompanyProfile from './pages/CompanyProfile'
// PrincipalManagement merged into Settings (RegistryExplorer)

// Hostname routing: decision-studios.com → corporate site, everything else → app
const isCorporateDomain = window.location.hostname.includes('decision-studios.com')

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={isCorporateDomain ? <LandingPage /> : <Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<DecisionStudio />} />
        <Route path="/debate/:situationId" element={<CouncilDebatePage />} />
        <Route path="/briefing/:situationId" element={<ExecutiveBriefing />} />
        <Route path="/report/:situationId" element={<WhitePaperReport />} />
        <Route path="/context" element={<ContextExplorer />} />
        <Route path="/settings" element={<RegistryExplorer />} />
        <Route path="/settings/onboarding" element={<DataProductOnboardingNew />} />
        <Route path="/settings/onboarding-legacy" element={<DataProductOnboarding />} />
        <Route path="/settings/company-profile" element={<CompanyProfile />} />
        <Route path="/portfolio" element={<Portfolio />} />
        {/* Corporate landing page accessible directly on any domain */}
        <Route path="/landing" element={<LandingPage />} />
        {/* Architecture / how it works */}
        <Route path="/how-it-works" element={<HowItWorks />} />
        {/* Insights / content marketing pages */}
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
    </Router>
  )
}

export default App
