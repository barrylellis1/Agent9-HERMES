import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { DecisionStudio } from './pages/DecisionStudio'
import { AdminConsole } from './pages/AdminConsole'
import { DataProductOnboarding } from './pages/DataProductOnboarding'
import { ExecutiveBriefing } from './pages/ExecutiveBriefing'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<DecisionStudio />} />
        <Route path="/briefing/:situationId" element={<ExecutiveBriefing />} />
        <Route path="/admin" element={<AdminConsole />} />
        <Route path="/admin/onboarding" element={<DataProductOnboarding />} />
      </Routes>
    </Router>
  )
}

export default App
