import { useState } from 'react'
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'
import Dashboard from './pages/Dashboard'
import AnalyzePage from './pages/AnalyzePage'
import PatientAdmission from './pages/PatientAdmission'
import RapportsPage from './pages/Rapports'
import ViewRapport from './pages/ViewRapport'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import StatistiquesDashboard from './pages/StatistiquesDashboard'
import Historique from './pages/Historique'

function App() {
  const [user, setUser] = useState(null)
  const [authPage, setAuthPage] = useState('login')
  const [page, setPage] = useState('dashboard')
  const [patientData, setPatientData] = useState(null)
  const [editingPatient, setEditingPatient] = useState(false)
  const [selectedRapport, setSelectedRapport] = useState(null)

  const [analyzeState, setAnalyzeState] = useState({
    result: null,
    loading: false,
    error: null,
    preview: null,
    gradcam: null,
    loadingGradcam: false,
    currentFile: null,
  })

  if (!user) {
    if (authPage === 'register') {
      return (
        <RegisterPage
          onRegister={() => setAuthPage('login')}
          onSwitchToLogin={() => setAuthPage('login')}
        />
      )
    }
    return (
      <LoginPage
        onLogin={setUser}
        onSwitchToRegister={() => setAuthPage('register')}
      />
    )
  }

  const handlePatientSubmit = (data) => {
    setPatientData(data)
    setEditingPatient(false)
    setPage('analyze')
  }

  const pageTitle = {
    dashboard:  { label: 'Dashboard',       sub: "Vue d'ensemble · CHU Mohammed VI Oujda" },
    analyze:    { label: 'Nouvelle analyse', sub: 'Analyse mammographique par IA' },
    historique: { label: 'Historique',       sub: 'Toutes les analyses passées' },
    rapports:   { label: 'Rapports',         sub: 'Rapports générés' },
    users:      { label: 'Utilisateurs',     sub: 'Gestion des accès' },
    statistics: { label: 'Statistiques',     sub: 'Tableau de bord analytique' },
  }[page] ?? { label: 'PREMIER', sub: '' }

  return (
    <div className="flex h-screen overflow-hidden"
      style={{ background: '#F0F4FA', fontFamily: "'DM Sans', 'Segoe UI', sans-serif" }}>

      <Sidebar page={page} setPage={setPage} role={user.role} />

      <div className="flex flex-col flex-1 min-w-0">
       <Navbar
  user={user}
  onLogout={() => setUser(null)}
  analyzeLoading={analyzeState.loading}
  pageTitle={pageTitle}
  page={page}
  setPage={setPage}
/>

        <main className="flex-1 overflow-y-auto p-6">
          {page === 'dashboard' && <Dashboard setPage={setPage} user={user} />}

          {/* Admission : pas de patient OU en mode édition */}
          {page === 'analyze' && (!patientData || editingPatient) && (
            <PatientAdmission onSubmit={handlePatientSubmit} initialData={patientData} />
          )}

          {/* Analyse : patient existant et pas en édition */}
          {page === 'analyze' && patientData && !editingPatient && (
            <AnalyzePage
              state={analyzeState}
              setState={setAnalyzeState}
              patient={patientData}
              onReset={() => { setPatientData(null); setEditingPatient(false) }}
              onEditPatient={() => setEditingPatient(true)}
              user={user}
            />
          )}

          {page === 'historique' && <Historique user={user} />}

          {page === 'rapports' && !selectedRapport && (
            <RapportsPage onViewRapport={(r) => setSelectedRapport(r)} user={user} />
          )}
          {page === 'rapports' && selectedRapport && (
            <ViewRapport rapport={selectedRapport} onBack={() => setSelectedRapport(null)} />
          )}

          {page === 'statistics' && <StatistiquesDashboard />}
        </main>
      </div>
    </div>
  )
}

export default App