import { useState, useEffect, useCallback } from 'react'
import { fetchRapports, getPdfUrl } from '../services/api'

export default function RapportsPage({ onViewRapport, user }) {
  const [rapports, setRapports]   = useState([])
  const [search,   setSearch]     = useState('')
  const [loading,  setLoading]    = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [pdfModal, setPdfModal]   = useState(null)

  const loadRapports = useCallback((isRefresh = false) => {
    if (!user?.id) return
    if (isRefresh) setRefreshing(true)
    fetchRapports(user.id)
      .then(data => setRapports(data))
      .catch(err => console.error('Erreur chargement rapports:', err))
      .finally(() => {
        setLoading(false)
        if (isRefresh) setRefreshing(false)
      })
  }, [user])

  useEffect(() => {
    loadRapports(false)
  }, [loadRapports])

  const openModal = (rapportId) => {
    if (pdfModal) return
    setPdfModal(getPdfUrl(rapportId))
  }
  const closeModal = () => setPdfModal(null)

  const handleDownload = (e, r) => {
    e.stopPropagation()
    if (!r.hasPdf) return
    const link = document.createElement('a')
    link.href = getPdfUrl(r.id)
    link.download = `PREMIER_${r.cin}_${r.nom}_${Date.now()}.pdf`
    link.rel = 'noopener'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const filtered = rapports.filter(r => {
    const q = search.toLowerCase()
    return (
      r.cin?.toLowerCase().includes(q) ||
      r.nom?.toLowerCase().includes(q) ||
      r.prenom?.toLowerCase().includes(q)
    )
  })

  const total      = rapports.length
  const cancers    = rapports.filter(r => r.resultat === 'Cancer').length
  const nonCancers = rapports.filter(r => r.resultat === 'Non-Cancer').length

  if (loading) return (
    <div style={{display:'flex',justifyContent:'center',alignItems:'center',height:'60vh',flexDirection:'column',gap:12}}>
      <div style={{width:36,height:36,border:'3px solid #e5e7eb',borderTop:'3px solid #1B4F9B',borderRadius:'50%',animation:'spin 0.8s linear infinite'}}/>
      <p style={{color:'#6b7280',fontSize:13}}>Chargement des rapports...</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )

  return (
    <div className="page-enter" style={{fontFamily:"'DM Sans','Segoe UI',sans-serif",padding:'28px 32px',minHeight:'100vh',background:'#F7F9FC'}}>
      <style>{`
        @keyframes fadeUp { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:none } }
        @keyframes modalIn { from { opacity:0; transform:scale(0.97) } to { opacity:1; transform:scale(1) } }
        @keyframes spin { to { transform: rotate(360deg) } }
        .rpt-row { animation: fadeUp .35s cubic-bezier(0.16,1,0.3,1) both; transition: background .15s, transform .15s; }
        .rpt-row:hover { background:#FAFBFC !important; transform: translateX(2px); }
        .rpt-card { animation: fadeUp .4s cubic-bezier(0.16,1,0.3,1) both; }
        .stat-mini { animation: fadeUp .35s cubic-bezier(0.16,1,0.3,1) both; transition: transform .15s; }
        .stat-mini:hover { transform: translateY(-2px); }
        .dl-btn { transition: all .15s; }
        .dl-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(59,130,246,0.4) !important; }
        .eye-btn { transition: all .15s; }
        .eye-btn:hover { transform: scale(1.08); }
        .pdf-modal-content { animation: modalIn .25s cubic-bezier(0.16,1,0.3,1) both; }
        .refresh-btn { transition: all .15s; }
        .refresh-btn:hover { background:#F8FAFC !important; border-color:#C7D7F8 !important; }
        .refresh-spin { animation: spin 0.8s linear infinite; }
      `}</style>

      {pdfModal && (
        <div onClick={closeModal} style={{position:'fixed',inset:0,background:'rgba(0,0,0,0.65)',zIndex:1000,display:'flex',alignItems:'center',justifyContent:'center',backdropFilter:'blur(3px)'}}>
          <div className="pdf-modal-content" onClick={e=>e.stopPropagation()} style={{background:'#fff',borderRadius:16,width:'82vw',height:'92vh',display:'flex',flexDirection:'column',overflow:'hidden',boxShadow:'0 24px 80px rgba(0,0,0,0.35)'}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'14px 20px',borderBottom:'0.5px solid #E8E7E3',background:'linear-gradient(135deg,#1B4F9B,#153d7a)',flexShrink:0}}>
              <span style={{fontWeight:700,fontSize:14,color:'#fff'}}>Rapport PDF — PREMIER · CHU Mohammed VI</span>
              <button onClick={closeModal} style={{background:'rgba(255,255,255,0.15)',color:'#fff',border:'0.5px solid rgba(255,255,255,0.3)',padding:'7px 14px',borderRadius:8,fontSize:13,fontWeight:600,cursor:'pointer'}}>
                ✕ Fermer
              </button>
            </div>
            <iframe src={pdfModal} title="Rapport PDF" style={{flex:1,border:'none',borderRadius:'0 0 16px 16px'}}/>
          </div>
        </div>
      )}

      <div style={{ maxWidth: 1180, margin: '0 auto' }}>

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

        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:14, marginBottom:20 }}>
          {[
            { label:'Rapports générés', value: total, icon:'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', accent:'#1B4F9B', bg:'#EEF3FB' },
            { label:'Cas Cancer détectés', value: cancers, icon:'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z', accent:'#DC2626', bg:'#FFF1F2' },
            { label:'Non suspects', value: nonCancers, icon:'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', accent:'#15803D', bg:'#F0FDF4' },
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

        <div style={{position:'relative',maxWidth:'360px',marginBottom:'20px'}}>
          <svg style={{position:'absolute',left:'12px',top:'50%',transform:'translateY(-50%)',width:'15px',height:'15px'}} fill="none" viewBox="0 0 24 24" stroke="#9ca3af" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <input
            value={search} onChange={e=>setSearch(e.target.value)}
            placeholder="Rechercher par CIN, nom ou prénom..."
            style={{width:'100%',boxSizing:'border-box',border:'1px solid #e5e7eb',borderRadius:'9px',padding:'9px 12px 9px 36px',fontSize:'13px',outline:'none',background:'#fff'}}
          />
        </div>

        {filtered.length === 0 ? (
          <div className="rpt-card" style={{textAlign:'center',padding:'60px 20px',color:'#9ca3af',background:'#fff',borderRadius:16,border:'1px solid #E2EBF6'}}>
            <div style={{fontSize:'40px',marginBottom:'12px'}}>📂</div>
            <p style={{fontSize:'14px',fontWeight:'500',marginBottom:'4px'}}>
              {rapports.length === 0 ? 'Aucun rapport enregistré' : 'Aucun résultat'}
            </p>
            <p style={{fontSize:'12px'}}>
              {rapports.length === 0 ? 'Cliquez sur "Enregistrer & PDF" après une analyse.' : 'Essayez un autre terme.'}
            </p>
          </div>
        ) : (
          <div className="rpt-card" style={{background:'#fff',borderRadius:16,border:'1px solid #E2EBF6',overflow:'hidden',boxShadow:'0 4px 20px rgba(27,79,155,0.06)'}}>
            <div style={{ height: 3, background: 'linear-gradient(90deg,#1B4F9B,#3b82f6)' }} />

            <div style={{display:'grid',gridTemplateColumns:'1.1fr 0.9fr 0.9fr 130px 160px',padding:'13px 20px',background:'#FAFBFC',borderBottom:'1px solid #F1F5F9'}}>
              {['CIN','Nom','Prénom','Résultat',''].map((h,i) => (
                <span key={i} style={{fontSize:'10px',fontWeight:'700',color:'#94A3B8',textTransform:'uppercase',letterSpacing:'.07em'}}>{h}</span>
              ))}
            </div>

            {filtered.map((r, idx) => {
              const isCanc = r.resultat === 'Cancer'
              return (
                <div key={r.id}
                  className="rpt-row"
                  style={{display:'grid',gridTemplateColumns:'1.1fr 0.9fr 0.9fr 130px 160px',padding:'14px 20px',borderTop:idx===0?'none':'1px solid #F1F5F9',alignItems:'center',animationDelay:`${idx * 0.05}s`}}
                >
                  <span style={{fontSize:'13px',fontWeight:'600',color:'#1a1a2e',fontFamily:'monospace'}}>{r.cin}</span>
                  <span style={{fontSize:'13px',color:'#374151'}}>{r.nom}</span>
                  <span style={{fontSize:'13px',color:'#374151'}}>{r.prenom}</span>
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    fontSize:'11px',fontWeight:'700',borderRadius:'9999px',padding:'5px 12px',width:'fit-content',
                    whiteSpace:'nowrap', flexShrink:0,
                    background:isCanc?'#FCEBEB':'#EAF3DE',color:isCanc?'#791F1F':'#27500A',border:`1.5px solid ${isCanc?'#F09595':'#97C459'}`
                  }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: isCanc?'#791F1F':'#27500A', display: 'inline-block', flexShrink:0 }} />
                    {r.resultat || '—'}
                  </span>

                  <div style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'flex-end' }}>
                    <button
                      className="dl-btn"
                      onClick={(e) => handleDownload(e, r)}
                      disabled={!r.hasPdf}
                      title="Télécharger le PDF"
                      style={{
                        display:'flex', alignItems:'center', gap:6, justifyContent:'center',
                        padding:'7px 14px', borderRadius:'9999px', border:'none',
                        background:'linear-gradient(135deg,#3B82F6,#2563EB)',
                        cursor: r.hasPdf ? 'pointer' : 'not-allowed',
                        opacity: r.hasPdf ? 1 : 0.35, flexShrink:0,
                        boxShadow:'0 2px 8px rgba(59,130,246,0.3)',
                      }}
                    >
                      <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="#fff" strokeWidth={2.4}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                      </svg>
                      <span style={{ fontSize:11, fontWeight:700, color:'#fff', whiteSpace:'nowrap' }}>Télécharger</span>
                    </button>
                    <button
                      className="eye-btn"
                      onClick={() => r.hasPdf ? openModal(r.id) : onViewRapport && onViewRapport(r)}
                      title="Voir le rapport"
                      style={{display:'flex',alignItems:'center',justifyContent:'center',width:'32px',height:'32px',borderRadius:'9px',border:'1px solid #E2E8F0',background:'#F8FAFC',cursor:'pointer',flexShrink:0}}
                      onMouseEnter={e=>{e.currentTarget.style.background='#EFF4FF';e.currentTarget.style.borderColor='#c7d7f8'}}
                      onMouseLeave={e=>{e.currentTarget.style.background='#F8FAFC';e.currentTarget.style.borderColor='#E2E8F0'}}
                    >
                      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#1B4F9B" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                      </svg>
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}