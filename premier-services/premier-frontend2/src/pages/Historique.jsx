import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8080'

const badge = (result) => {
  if (result === 'Cancer')     return { background: '#FCEBEB', color: '#791F1F', border: '#F09595' }
  if (result === 'Non-Cancer') return { background: '#EAF3DE', color: '#27500A', border: '#97C459' }
  return { background: '#FAEEDA', color: '#633806', border: '#FAC775' }
}

const biradsBadge = (score) => {
  if (!score)      return { background: '#F1EFE8', color: '#5F5E5A' }
  if (score <= 2)  return { background: '#EAF3DE', color: '#27500A' }
  if (score === 3) return { background: '#FAEEDA', color: '#633806' }
  return { background: '#FCEBEB', color: '#791F1F' }
}

const COLS = [
  { key: 'patient',   label: 'Patient',      width: '22%' },
  { key: 'cin',       label: 'CIN',          width: '14%' },
  { key: 'date',      label: 'Date & heure', width: '16%' },
  { key: 'birads',    label: 'BI-RADS',      width: '13%' },
  { key: 'resultat',  label: 'Résultat',     width: '15%' },
  { key: 'confiance', label: 'Confiance',    width: '20%' },
]

export default function Historique({ user }) {
  const [rapports, setRapports]     = useState([])
  const [loading,  setLoading]      = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [search,   setSearch]       = useState('')
  const [filtre,   setFiltre]       = useState('tous')

  const loadRapports = useCallback((isRefresh = false) => {
    if (!user?.id) return
    if (isRefresh) setRefreshing(true)
    axios.get(`${API_BASE}/api/rapports`, { params: { medecinId: user.id } })
      .then(res => setRapports(res.data.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))))
      .catch(err => console.error(err))
      .finally(() => {
        setLoading(false)
        if (isRefresh) setRefreshing(false)
      })
  }, [user])

  useEffect(() => {
    loadRapports(false)
  }, [loadRapports])

  const filtered = rapports.filter(r => {
    const q = search.toLowerCase()
    const matchSearch = (
      r.cin?.toLowerCase().includes(q) ||
      r.nom?.toLowerCase().includes(q) ||
      r.prenom?.toLowerCase().includes(q)
    )
    const matchFiltre =
      filtre === 'tous' ? true :
      filtre === 'cancer' ? r.resultat === 'Cancer' :
      r.resultat === 'Non-Cancer'
    return matchSearch && matchFiltre
  })

  const total      = rapports.length
  const cancers    = rapports.filter(r => r.resultat === 'Cancer').length
  const nonCancers = rapports.filter(r => r.resultat === 'Non-Cancer').length
  const avgConf    = total > 0 ? Math.round(rapports.reduce((a, r) => a + (r.confidence || 0), 0) / total * 100) : 0

  return (
    <div className="page-enter" style={{ fontFamily: "'DM Sans','Segoe UI',sans-serif", padding: '28px 32px', minHeight: '100vh', background: '#F7F9FC' }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:none } }
        .hist-row { animation: fadeUp .35s cubic-bezier(0.16,1,0.3,1) both; transition: background .15s, transform .15s; }
        .hist-row:hover { background:#FAFBFC !important; transform: translateX(2px); }
        .hist-card { animation: fadeUp .4s cubic-bezier(0.16,1,0.3,1) both; }
        .stat-mini { animation: fadeUp .35s cubic-bezier(0.16,1,0.3,1) both; transition: transform .15s; }
        .stat-mini:hover { transform: translateY(-2px); }
        .filter-btn { transition: all .15s; }
        .filter-btn:hover { transform: translateY(-1px); }
        .bar-fill-anim { transition: width .6s cubic-bezier(0.16,1,0.3,1); }
        .refresh-btn { transition: all .15s; }
        .refresh-btn:hover { background:#F8FAFC !important; border-color:#C7D7F8 !important; }
        .refresh-spin { animation: spin 0.8s linear infinite; }
      `}</style>

      <div style={{ maxWidth: 1180, margin: '0 auto' }}>

        {/* ── Header avec bouton Actualiser ── */}
        <div style={{ display:'flex', alignItems:'center', justifyContent:'flex-end', marginBottom:8 }}>
          <button
            className="refresh-btn"
            onClick={() => loadRapports(true)}
            disabled={refreshing}
            style={{
              display:'flex', alignItems:'center', gap:7,
              background:'#fff', border:'1px solid #E2E8F0', borderRadius:10,
              padding:'8px 16px', fontSize:12, fontWeight:600, color:'#374151',
              cursor: refreshing ? 'wait' : 'pointer',
            }}
          >
            <svg className={refreshing ? 'refresh-spin' : ''} width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#64748B" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Actualiser
          </button>
        </div>

        {/* ── Stat mini-cards ── */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14, marginBottom:20 }}>
          {[
            { label:'Analyses totales', value: total, icon:'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', accent:'#1B4F9B', bg:'#EEF3FB' },
            { label:'Cancers détectés', value: cancers, icon:'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z', accent:'#DC2626', bg:'#FFF1F2' },
            { label:'Non suspects', value: nonCancers, icon:'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', accent:'#15803D', bg:'#F0FDF4' },
            { label:'Confiance moyenne', value: `${avgConf}%`, icon:'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z', accent:'#B7791F', bg:'#FFFBEB' },
          ].map((s, i) => (
            <div key={s.label} className="stat-mini" style={{ animationDelay:`${i*0.06}s`, background:'#fff', borderRadius:14, padding:'16px 18px', border:'1px solid #E2EBF6', boxShadow:'0 1px 6px rgba(0,0,0,0.04)', display:'flex', alignItems:'center', gap:14, position:'relative', overflow:'hidden' }}>
              <div style={{ position:'absolute', top:0, left:0, right:0, height:3, background:s.accent, opacity:0.85 }} />
              <div style={{ width:42, height:42, borderRadius:11, background:s.bg, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke={s.accent} strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={s.icon} />
                </svg>
              </div>
              <div>
                <div style={{ fontSize:24, fontWeight:800, color:'#1A202C', lineHeight:1 }}>{s.value}</div>
                <div style={{ fontSize:11, color:'#64748B', marginTop:3 }}>{s.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* ── Filtres ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 360 }}>
            <svg style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', width: 15, height: 15 }} fill="none" viewBox="0 0 24 24" stroke="#9ca3af" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Rechercher par CIN, nom ou prénom..."
              style={{ width: '100%', boxSizing: 'border-box', border: '1px solid #e5e7eb', borderRadius: 9, padding: '9px 12px 9px 36px', fontSize: 13, outline: 'none', background: '#fff' }}
            />
          </div>

          {['tous', 'cancer', 'non-cancer'].map(f => (
            <button key={f} className="filter-btn" onClick={() => setFiltre(f)}
              style={{
                padding: '8px 16px', borderRadius: 9, cursor: 'pointer', fontSize: 12, fontWeight: 600,
                background: filtre === f ? '#1B4F9B' : '#fff',
                color: filtre === f ? '#fff' : '#6b7280',
                border: `1px solid ${filtre === f ? '#1B4F9B' : '#e5e7eb'}`,
                boxShadow: filtre === f ? '0 4px 12px rgba(27,79,155,0.25)' : 'none',
              }}>
              {f === 'tous' ? 'Tous' : f === 'cancer' ? '🔴 Cancer' : '🟢 Non-Cancer'}
            </button>
          ))}

          <span style={{ marginLeft: 'auto', fontSize: 12, color: '#9ca3af' }}>
            {filtered.length} résultat{filtered.length > 1 ? 's' : ''} sur {rapports.length}
          </span>
        </div>

        {/* ── Contenu ── */}
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '40vh', flexDirection: 'column', gap: 12 }}>
            <div style={{ width: 36, height: 36, border: '3px solid #e5e7eb', borderTop: '3px solid #1B4F9B', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
            <p style={{ color: '#6b7280', fontSize: 13 }}>Chargement...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="hist-card" style={{ textAlign: 'center', padding: '60px 20px', color: '#9ca3af', background:'#fff', borderRadius:16, border:'1px solid #E2EBF6' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>📂</div>
            <p style={{ fontSize: 14, fontWeight: 500 }}>Aucun résultat</p>
          </div>
        ) : (
          <div className="hist-card" style={{ background: '#fff', borderRadius: 16, border: '1px solid #E2EBF6', overflow: 'hidden', boxShadow: '0 4px 20px rgba(27,79,155,0.06)' }}>
            <div style={{ height: 3, background: 'linear-gradient(90deg,#1B4F9B,#3b82f6)' }} />

            <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
              <colgroup>
                {COLS.map(c => <col key={c.key} style={{ width: c.width }} />)}
              </colgroup>
              <thead>
                <tr style={{ background: '#FAFBFC', borderBottom: '1px solid #F1F5F9' }}>
                  {COLS.map(c => (
                    <th key={c.key} style={{ padding: '13px 20px', textAlign: 'left', fontSize: 10, fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '.07em', whiteSpace: 'nowrap' }}>
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => {
                  const confidencePct = Math.round((r.confidence || 0) * 100)
                  const b = badge(r.resultat)
                  return (
                    <tr key={r.id}
                      className="hist-row"
                      style={{ borderTop: i === 0 ? 'none' : '1px solid #F1F5F9', animationDelay: `${i * 0.05}s` }}
                    >
                      <td style={{ padding: '14px 20px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                          <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#EEF3FB', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: '#1B4F9B', flexShrink: 0, border:'1px solid #C7D7F8' }}>
                            {(r.prenom?.[0] || '?')}{(r.nom?.[0] || '')}
                          </div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: '#1a1a2e', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {r.prenom} {r.nom}
                          </div>
                        </div>
                      </td>

                      <td style={{ padding: '14px 20px', fontSize: 12, color: '#6b7280', fontFamily: 'monospace', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {r.cin}
                      </td>

                      <td style={{ padding: '14px 20px', fontSize: 12, color: '#6b7280', whiteSpace: 'nowrap' }}>
                        {new Date(r.createdAt).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })}
                        <span style={{ display: 'block', fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                          {new Date(r.createdAt).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </td>

                      <td style={{ padding: '14px 20px' }}>
                        <span style={{ ...biradsBadge(r.biradsScore), fontSize: 11, fontWeight: 700, padding: '4px 11px', borderRadius: 8, display: 'inline-block', minWidth: 56, textAlign: 'center' }}>
                          {r.biradsScore ? `Score ${r.biradsScore}` : '—'}
                        </span>
                      </td>

                      <td style={{ padding: '14px 20px' }}>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: 6,
                          background: b.background, color: b.color, border: `1.5px solid ${b.border}`,
                          fontSize: 11, fontWeight: 700, padding: '5px 14px', borderRadius: 9999,
                        }}>
                          <span style={{ width: 6, height: 6, borderRadius: '50%', background: b.color, display: 'inline-block' }} />
                          {r.resultat || '—'}
                        </span>
                      </td>

                      <td style={{ padding: '14px 20px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div style={{ flex: '1 1 auto', height: 5, background: '#F1F5F9', borderRadius: 9999, overflow: 'hidden' }}>
                            <div className="bar-fill-anim" style={{
                              height: '100%', borderRadius: 9999,
                              background: r.resultat === 'Cancer' ? 'linear-gradient(90deg,#E24B4A,#F09595)' : 'linear-gradient(90deg,#27B562,#97C459)',
                              width: `${confidencePct}%`,
                            }} />
                          </div>
                          <span style={{ fontSize: 12, fontWeight: 700, color: '#374151', width: 34, flexShrink: 0, textAlign: 'right' }}>
                            {confidencePct}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}