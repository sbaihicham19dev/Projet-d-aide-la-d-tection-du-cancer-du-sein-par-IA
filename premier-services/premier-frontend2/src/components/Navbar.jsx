import { useEffect, useRef, useState } from 'react'

const PAGE_ORDER = ['dashboard', 'analyze', 'historique', 'rapports']

export default function Navbar({ user, onLogout, analyzeLoading, pageTitle, page, setPage }) {
  const [query, setQuery] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        inputRef.current?.blur()
        setQuery('')
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const currentIndex = PAGE_ORDER.indexOf(page)
  const goPrev = () => {
    if (currentIndex === -1) return
    const prevIndex = (currentIndex - 1 + PAGE_ORDER.length) % PAGE_ORDER.length
    setPage(PAGE_ORDER[prevIndex])
  }
  const goNext = () => {
    if (currentIndex === -1) return
    const nextIndex = (currentIndex + 1) % PAGE_ORDER.length
    setPage(PAGE_ORDER[nextIndex])
  }

  return (
    <header
      className="flex-shrink-0 bg-white flex items-center justify-between px-6"
      style={{ height: 56, borderBottom: '1px solid #EDF2F7' }}
    >
      <style>{`
        @keyframes navFadeIn { from { opacity:0; transform:translateY(-4px) } to { opacity:1; transform:none } }
        .nav-arrow { transition: all .15s; }
        .nav-arrow:hover:not(:disabled) { background:#EEF3FB !important; border-color:#C7D7F8 !important; }
        .nav-arrow:disabled { opacity:0.35; cursor:not-allowed; }
      `}</style>

      {/* LEFT : titre page */}
      <div className="flex items-center gap-3" style={{ animation: 'navFadeIn .3s ease both' }}>
        <div>
          <p className="text-sm font-bold text-gray-800 leading-none">{pageTitle.label}</p>
          <p className="text-[10px] text-gray-400 leading-none mt-0.5">{pageTitle.sub}</p>
        </div>
      </div>

      {/* CENTER : recherche */}
      <div className="flex-1 max-w-sm mx-10" style={{ animation: 'navFadeIn .3s ease .05s both' }}>
        <div className="relative">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Rechercher un patient, une analyse..."
            className="w-full text-xs rounded-xl border bg-gray-50 text-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-300 transition-all duration-150"
            style={{ paddingLeft: 36, paddingRight: 60, paddingTop: 8, paddingBottom: 8, borderColor: '#E2E8F0' }}
          />
          {!query && (
            <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-0.5">
              <kbd className="text-[9px] font-semibold px-1.5 py-0.5 rounded border border-gray-200 text-gray-400 bg-white leading-none">ctrl</kbd>
              <kbd className="text-[9px] font-semibold px-1.5 py-0.5 rounded border border-gray-200 text-gray-400 bg-white leading-none">K</kbd>
            </div>
          )}
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* RIGHT : navigation prev/next + statut + avatar */}
      <div className="flex items-center gap-3" style={{ animation: 'navFadeIn .3s ease .1s both' }}>

        {/* Navigation entre pages */}
        <div className="flex items-center gap-1">
          <button
            className="nav-arrow"
            onClick={goPrev}
            disabled={currentIndex === -1}
            title="Page précédente"
            style={{ width: 28, height: 28, borderRadius: 8, border: '1px solid #E2E8F0', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
          >
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="#64748B" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            className="nav-arrow"
            onClick={goNext}
            disabled={currentIndex === -1}
            title="Page suivante"
            style={{ width: 28, height: 28, borderRadius: 8, border: '1px solid #E2E8F0', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
          >
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="#64748B" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {analyzeLoading && (
          <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg"
            style={{ background: '#EEF3FB', color: '#1B4F9B' }}>
            <div className="w-3 h-3 border-2 rounded-full animate-spin"
              style={{ borderColor: '#1B4F9B22', borderTopColor: '#1B4F9B' }} />
            Analyse en cours...
          </div>
        )}

        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl"
          style={{ background: '#F0FFF4', border: '1px solid #9AE6B4' }}>
          <span className="relative flex w-1.5 h-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60"
              style={{ background: '#38A169' }} />
            <span className="relative inline-flex w-1.5 h-1.5 rounded-full"
              style={{ background: '#38A169' }} />
          </span>
          <span className="text-[10px] font-semibold" style={{ color: '#276749' }}>
            Système opérationnel
          </span>
        </div>

        <div style={{ width: 1, height: 24, background: '#E2E8F0' }} />

        <div className="flex items-center gap-2">
          <div className="relative"
            title={`${user.name} · ${user.role === 'admin' ? 'Administrateur' : 'Médecin'}`}>
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold text-white transition-transform hover:scale-105"
              style={{ background: 'linear-gradient(135deg, #1B4F9B 0%, #153d7a 100%)', boxShadow: '0 2px 6px rgba(27,79,155,0.3)' }}
            >
              {user.name.slice(0, 2).toUpperCase()}
            </div>
            {user.role === 'admin' && (
              <div
                className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-white flex items-center justify-center"
                style={{ boxShadow: '0 0 0 1px #E2E8F0' }}
              >
                <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24"
                  stroke="#F5A623" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
            )}
          </div>

          <button
            onClick={onLogout}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-150 hover:bg-red-50 group"
            title="Déconnexion"
          >
            <svg className="w-4 h-4 text-gray-400 group-hover:text-red-500 transition-colors"
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>

      </div>
    </header>
  )
}