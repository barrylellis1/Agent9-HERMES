import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { DecisionStudio } from './pages/DecisionStudio'
// AdminConsole replaced by Settings (RegistryExplorer at /settings)
import { DataProductOnboarding } from './pages/DataProductOnboarding'
import { DataProductOnboardingNew } from './pages/DataProductOnboardingNew'
import { RegistryExplorer } from './pages/RegistryExplorer'
import { ContextExplorer } from './pages/ContextExplorer'
import { ExecutiveBriefing } from './pages/ExecutiveBriefing'
import { Login } from './pages/Login'
import { Portfolio } from './pages/Portfolio'
// PrincipalManagement merged into Settings (RegistryExplorer)

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<DecisionStudio />} />
        <Route path="/briefing/:situationId" element={<ExecutiveBriefing />} />
        <Route path="/context" element={<ContextExplorer />} />
        <Route path="/settings" element={<RegistryExplorer />} />
        <Route path="/settings/onboarding" element={<DataProductOnboardingNew />} />
        <Route path="/settings/onboarding-legacy" element={<DataProductOnboarding />} />
        <Route path="/portfolio" element={<Portfolio />} />
        {/* Legacy routes → redirects */}
        <Route path="/admin" element={<Navigate to="/settings" replace />} />
        <Route path="/admin/registry" element={<Navigate to="/settings" replace />} />
        <Route path="/admin/principals" element={<Navigate to="/settings" replace />} />
        <Route path="/admin/onboarding" element={<Navigate to="/settings/onboarding" replace />} />
        {/* Redirect any unknown routes to login */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App
