import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { DecisionStudio } from './pages/DecisionStudio'
import { AdminConsole } from './pages/AdminConsole'
import { DataProductOnboarding } from './pages/DataProductOnboarding'
import { DataProductOnboardingNew } from './pages/DataProductOnboardingNew'
import { RegistryExplorer } from './pages/RegistryExplorer'
import { ExecutiveBriefing } from './pages/ExecutiveBriefing'
import { Login } from './pages/Login'
import { PrincipalManagement } from './pages/PrincipalManagement'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<DecisionStudio />} />
        <Route path="/briefing/:situationId" element={<ExecutiveBriefing />} />
        <Route path="/admin" element={<AdminConsole />} />
        <Route path="/admin/onboarding" element={<DataProductOnboardingNew />} />
        <Route path="/admin/onboarding-legacy" element={<DataProductOnboarding />} />
        <Route path="/admin/registry" element={<RegistryExplorer />} />
        <Route path="/admin/principals" element={<PrincipalManagement />} />
        {/* Redirect any unknown routes to login */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App
