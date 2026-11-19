import { useEffect, useState } from 'react'
import logoChu from '../assets/logo-chu.png'

const navItems = [
  { id: 'dashboard',  label: 'Dashboard',       icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { id: 'analyze',    label: 'Nouvelle analyse', icon: 'M12 4v16m8-8H4' },
  { id: 'historique', label: 'Historique',       icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  { id: 'rapports',   label: 'Rapports',         icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
]

const adminItems = [
  { id: 'users',      label: 'Utilisateurs', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' },
  { id: 'statistics', label: 'Statistiques', icon: 'M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z' },
]

const SERVICES = [
  { key: 'detection',      label: 'Détection',      port: 8011, path: '/api/v1/health' },
  { key: 'classification', label: 'Classification', port: 8012, path: '/api/v1/health' },
  { key: 'segmentation',   label: 'Segmentation',   port: 8013, path: '/api/v1/health' },
  { key: 'birads',         label: 'BI-RADS',        port: 8014, path: '/api/v1/health' },
  { key: 'visualization',  label: 'Visualisation',  port: 8019, path: '/api/v1/health' },
  { key: 'assembler',      label: 'Assembleur',     port: 8018, path: '/api/v1/health' },
  { key: 'llm_narrative',  label: 'LLM Narrative',  port: 8020, path: '/api/v1/health' },
  { key: 'gateway',        label: 'Gateway',        port: 8080, path: '/actuator/health' },
]

function useServiceHealth() {
  const [statuses, setStatuses] = useState(() =>
    Object.fromEntries(SERVICES.map(s => [s.key, 'checking']))
  )
  useEffect(() => {
    let cancelled = false
    const checkAll = async () => {
      const results = await Promise.allSettled(
        SERVICES.map(async (svc) => {
          const controller = new AbortController()
          const timeout = setTimeout(() => controller.abort(), 3000)
          try {
            const res = await fetch(`http://localhost:${svc.port}${svc.path}`, { signal: controller.signal })
            clearTimeout(timeout)
            if (!res.ok) return { key: svc.key, ok: false }
            const json = await res.json().catch(() => null)
            const up = !json || ['UP', 'ok', 'healthy', 'running'].includes(json?.status)
            return { key: svc.key, ok: up }
          } catch {
            clearTimeout(timeout)
            return { key: svc.key, ok: false }
          }
        })
      )
      if (!cancelled) {
        const next = {}
        results.forEach(r => {
          if (r.status === 'fulfilled') next[r.value.key] = r.value.ok ? 'up' : 'down'
          else next[r.reason?.key ?? ''] = 'down'
        })
        setStatuses(next)
      }
    }
    checkAll()
    const interval = setInterval(checkAll, 30_000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])
  return statuses
}

const StatusDot = ({ status }) => {
  if (status === 'up') return (
    <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 8, height: 8, flexShrink: 0 }}>
      <span className="animate-ping" style={{ position: 'absolute', inset: 0, borderRadius: '9999px', background: '#34d399', opacity: 0.6 }} />
      <span style={{ position: 'relative', width: 8, height: 8, borderRadius: '9999px', background: '#10b981', display: 'block' }} />
    </span>
  )
  if (status === 'down') return (
    <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '9999px', background: '#f43f5e', flexShrink: 0 }} />
  )
  return (
    <span className="animate-pulse" style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '9999px', background: '#d1d5db', flexShrink: 0 }} />
  )
}

function NavButton({ item, active, onClick, delay }) {
  return (
    <button
      onClick={onClick}
      className="sidebar-nav-item"
      style={{
        width: '100%', display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 12px', borderRadius: 12, fontSize: 13.5,
        textAlign: 'left', cursor: 'pointer', border: 'none',
        background: active ? 'linear-gradient(135deg,#EEF3FB,#dbeafe)' : 'transparent',
        color: active ? '#1B4F9B' : '#64748B',
        fontWeight: active ? 700 : 500,
        boxShadow: active ? '0 2px 8px rgba(27,79,155,0.12)' : 'none',
        transition: 'all 0.18s cubic-bezier(0.16,1,0.3,1)',
        animation: `sidebarFadeIn .35s cubic-bezier(0.16,1,0.3,1) ${delay}s both`,
      }}
      onMouseEnter={e => { if (!active) { e.currentTarget.style.background = '#F8FAFC'; e.currentTarget.style.color = '#374151' } }}
      onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#64748B' } }}
    >
      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke={active ? '#1B4F9B' : 'currentColor'} strokeWidth={2} style={{ flexShrink: 0, transition: 'stroke 0.18s' }}>
        <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
      </svg>
      {item.label}
      {active && <div style={{ marginLeft: 'auto', width: 6, height: 6, borderRadius: '50%', background: '#1B4F9B', boxShadow: '0 0 6px rgba(27,79,155,0.5)' }} />}
    </button>
  )
}

export default function Sidebar({ page, setPage, role }) {
  const [servicesOpen, setServicesOpen] = useState(false)
  const statuses = useServiceHealth()
  const upCount = Object.values(statuses).filter(s => s === 'up').length
  const allUp = upCount === SERVICES.length

  return (
    <aside
      className="w-56 h-screen sticky top-0 bg-white border-r border-gray-100 flex flex-col overflow-y-auto"
      style={{ fontFamily: "'DM Sans', 'Segoe UI', sans-serif" }}
    >
      <style>{`
        @keyframes sidebarFadeIn { from { opacity:0; transform:translateX(-8px) } to { opacity:1; transform:none } }
        @keyframes logoFadeIn { from { opacity:0; transform:scale(0.92) } to { opacity:1; transform:scale(1) } }
        .sidebar-nav-item { animation-fill-mode: both; }
      `}</style>

      {/* Logo CHU */}
      <div className="flex items-center justify-center border-b border-gray-100"
        style={{ minHeight: 92, padding: '16px 20px', background: '#fff', animation: 'logoFadeIn .4s cubic-bezier(0.16,1,0.3,1) both' }}>
        <img
          src={logoChu}
          alt="CHU Mohammed VI"
          style={{ height: 64, width: 'auto', objectFit: 'contain', maxWidth: '100%' }}
        />
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest px-2 mb-2"
          style={{ animation: 'sidebarFadeIn .3s ease both' }}>Navigation</p>
        {navItems.map((item, i) => (
          <NavButton key={item.id} item={item} active={page === item.id} onClick={() => setPage(item.id)} delay={0.04 * (i + 1)} />
        ))}
        {role === 'admin' && (
          <>
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest px-2 pt-4 mb-2"
              style={{ animation: 'sidebarFadeIn .3s ease .2s both' }}>Administration</p>
            {adminItems.map((item, i) => (
              <NavButton key={item.id} item={item} active={page === item.id} onClick={() => setPage(item.id)} delay={0.22 + 0.04 * (i + 1)} />
            ))}
          </>
        )}
      </nav>

      {/* Services health */}
      <div className="border-t border-gray-100 px-3 py-3">
        <button
          onClick={() => setServicesOpen(o => !o)}
          className="w-full flex items-center justify-between px-2 py-2 rounded-xl transition-all duration-150"
          style={{ background: servicesOpen ? '#F8FAFC' : 'transparent' }}
          onMouseEnter={e => e.currentTarget.style.background = '#F8FAFC'}
          onMouseLeave={e => { if (!servicesOpen) e.currentTarget.style.background = 'transparent' }}
        >
          <div className="flex items-center gap-2">
            <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
            </svg>
            <span className="text-xs font-medium text-gray-600">Services</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md transition-colors ${allUp ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
              {upCount}/{SERVICES.length}
            </span>
            <svg className={`w-3 h-3 text-gray-400 transition-transform duration-200 ${servicesOpen ? 'rotate-180' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        {servicesOpen && (
          <div className="mt-1 space-y-0.5 px-1" style={{ animation: 'sidebarFadeIn .25s ease both' }}>
            {SERVICES.map(svc => {
              const s = statuses[svc.key]
              return (
                <div key={svc.key} className="flex items-center justify-between py-1.5 px-2 rounded-lg transition-colors duration-150 hover:bg-gray-50">
                  <span className="text-xs text-gray-600 truncate flex-1 min-w-0">{svc.label}</span>
                  <div className="flex items-center gap-1.5 flex-shrink-0 ml-2" style={{ lineHeight: 1 }}>
                    <span className={`text-[10px] font-medium whitespace-nowrap ${
                      s === 'up'   ? 'text-emerald-600' :
                      s === 'down' ? 'text-rose-500'    : 'text-gray-400'
                    }`}>
                      {s === 'up' ? 'En ligne' : s === 'down' ? 'Hors ligne' : '...'}
                    </span>
                    <StatusDot status={s} />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

    </aside>
  )
}