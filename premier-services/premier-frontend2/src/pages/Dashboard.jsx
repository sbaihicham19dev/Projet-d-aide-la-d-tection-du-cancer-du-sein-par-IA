import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8080'

const COUCHES = [
  {
    num: '01', label: 'Détection', desc: 'Localisation automatique des zones suspectes sur la mammographie',
    color: '#1B4F9B', light: '#EEF3FB', grad: 'linear-gradient(135deg,#1B4F9B,#2563eb)',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  },
  {
    num: '02', label: 'Classification BI-RADS', desc: 'Score BI-RADS 0–6 · Bénin, suspect, malin',
    color: '#B7791F', light: '#FFFBEB', grad: 'linear-gradient(135deg,#B7791F,#d97706)',
    icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
  },
  {
    num: '03', label: 'Rapport narratif', desc: 'Génération automatique du compte-rendu radiologique',
    color: '#276749', light: '#F0FFF4', grad: 'linear-gradient(135deg,#276749,#059669)',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  },
]

const resultBadge = (r) => {
  if (r === 'Cancer')     return { bg: '#FFF1F2', color: '#BE123C', border: '#FECDD3' }
  if (r === 'Non-Cancer') return { bg: '#F0FDF4', color: '#15803D', border: '#BBF7D0' }
  return { bg: '#FEFCE8', color: '#92400E', border: '#FDE68A' }
}

const biradsBadge = (score) => {
  if (!score)      return { bg: '#F8FAFC', color: '#475569', border: '#E2E8F0' }
  if (score <= 2)  return { bg: '#F0FDF4', color: '#15803D', border: '#BBF7D0' }
  if (score === 3) return { bg: '#FEFCE8', color: '#92400E', border: '#FDE68A' }
  return { bg: '#FFF1F2', color: '#BE123C', border: '#FECDD3' }
}

function SkeletonPulse({ w = '100%', h = 20, r = 6 }) {
  return (
    <div style={{ width: w, height: h, borderRadius: r, background: 'linear-gradient(90deg,#e2e8f0 25%,#f1f5f9 50%,#e2e8f0 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.4s infinite' }} />
  )
}

export default function Dashboard({ setPage, user }) {
  const [rapports, setRapports] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user?.id) return
    axios.get(`${API_BASE}/api/rapports`, { params: { medecinId: user.id } })
      .then(res => setRapports(res.data))
      .catch(err => console.error('Erreur dashboard:', err))
      .finally(() => setLoading(false))
  }, [user])

  const total      = rapports.length
  const cancers    = rapports.filter(r => r.resultat === 'Cancer').length
  const nonCancers = rapports.filter(r => r.resultat === 'Non-Cancer').length
  const tauxDetection = total > 0 ? Math.round((cancers / total) * 100) : 0
  const tauxBenin     = total > 0 ? Math.round((nonCancers / total) * 100) : 0
  const thisWeek = rapports.filter(r => (new Date() - new Date(r.createdAt)) / 86400000 <= 7).length

  const joursLabels = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
  const activiteParJour = joursLabels.map((jour, i) => ({
    jour,
    val: rapports.filter(r => new Date(r.createdAt).getDay() === (i + 1) % 7).length,
  }))
  const maxVal = Math.max(...activiteParJour.map(d => d.val), 1)

  const derniers = [...rapports]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, 5)

  const STATS = [
    { label: 'Analyses totales', value: total,      accent: '#1B4F9B', bg: '#EEF3FB', trend: 'Enregistrées', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
    { label: 'Cas détectés',     value: cancers,    accent: '#DC2626', bg: '#FFF1F2', trend: `${tauxDetection}% taux`, icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' },
    { label: 'Non suspects',     value: nonCancers, accent: '#15803D', bg: '#F0FDF4', trend: `${tauxBenin}% bénin`, icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
    { label: 'Cette semaine',    value: thisWeek,   accent: '#B7791F', bg: '#FFFBEB', trend: '7 derniers jours', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  ]

  const donutR = 42
  const donutC = 251.3 * (donutR / 40)
  const donutBenin  = total > 0 ? (tauxBenin  / 100) * donutC : 0
  const donutCancer = total > 0 ? (tauxDetection / 100) * donutC : 0

  const initials = (r) => `${r.prenom?.[0] ?? ''}${r.nom?.[0] ?? ''}`.toUpperCase()
  const AVATAR_COLORS = ['#1B4F9B','#276749','#B7791F','#6D28D9','#0891B2','#9F1239']
  const avatarColor = (name) => AVATAR_COLORS[(name?.charCodeAt(0) ?? 0) % AVATAR_COLORS.length]

  return (
    <>
      <style>{`
        @keyframes shimmer { to { background-position: -200% 0 } }
        @keyframes fadeUp  { from { opacity:0; transform:translateY(12px) } to { opacity:1; transform:none } }
        .dash-card { animation: fadeUp .35s ease both }
        .row-animated { animation: fadeUp .3s cubic-bezier(0.16,1,0.3,1) both; }
      `}</style>

      <div style={{ background: '#F7F9FC', minHeight: '100%' }}>
        <div style={{ maxWidth: 1220, margin: '0 auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>

          {/* ── BANNIÈRE ─────────────────────────────────────────── */}
          <div className="hero-gradient-anim" style={{
            background: 'linear-gradient(-45deg, #0f2d5c, #1B4F9B, #153d7a, #1d6bb8)',
            backgroundSize: '300% 300%',
            borderRadius: 20, padding: '28px 36px', position: 'relative', overflow: 'hidden',
          }}>
            <div style={{ position:'absolute', right:-60, top:-60, width:260, height:260, borderRadius:'50%', background:'rgba(255,255,255,0.04)' }} />
            <div style={{ position:'absolute', right:100, bottom:-80, width:200, height:200, borderRadius:'50%', background:'rgba(255,255,255,0.03)' }} />
            <div style={{ position:'absolute', right:40, top:16, width:80, height:80, borderRadius:'50%', background:'rgba(245,166,35,0.10)' }} />
            <svg style={{ position:'absolute', right:36, bottom:20, opacity:0.07 }} width="120" height="120" viewBox="0 0 24 24" fill="white">
              <path d="M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm-7 14h-2v-4H6v-2h4V7h2v4h4v2h-4v4z"/>
            </svg>

            <div style={{ position:'relative', display:'flex', alignItems:'center', justifyContent:'space-between', gap:24 }}>
              <div>
                <span style={{ display:'inline-block', marginBottom:10, background:'rgba(245,166,35,0.18)', color:'#F5A623', border:'1px solid rgba(245,166,35,0.32)', fontSize:10, fontWeight:700, padding:'4px 14px', borderRadius:9999, letterSpacing:'0.1em' }}>
                  ✦ MAMMOGRAPHIE IA · CHU Mohammed VI
                </span>
                <h1 style={{ fontSize:26, fontWeight:800, color:'#fff', margin:'0 0 3px', lineHeight:1.2 }}>
                  Bonjour, {user?.name || 'Docteur'} 👋
                </h1>
                <p style={{ color:'rgba(255,255,255,0.55)', fontSize:12, margin:'0 0 20px' }}>
                  CHU Mohammed VI Oujda · Tableau de bord personnel
                </p>

                <div style={{ display:'flex', alignItems:'center', gap:28 }}>
                  {[
                    { label:'Analyses totales', value: loading ? '—' : total, color:'#fff' },
                    { label:'Taux détection',   value: loading ? '—' : `${tauxDetection}%`, color:'#F5A623' },
                    { label:'Cancers détectés', value: loading ? '—' : cancers, color:'#fca5a5' },
                  ].map((s, i) => (
                    <div key={i} style={{ display:'flex', alignItems:'center', gap:i > 0 ? 0 : 0 }}>
                      {i > 0 && <div style={{ width:1, height:32, background:'rgba(255,255,255,0.18)', marginRight:28 }} />}
                      <div>
                        <div style={{ fontSize:26, fontWeight:800, color:s.color, lineHeight:1 }}>{s.value}</div>
                        <div style={{ fontSize:10, color:'rgba(255,255,255,0.5)', marginTop:2 }}>{s.label}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setPage('analyze')}
                style={{ flexShrink:0, background:'linear-gradient(135deg,#F5A623,#e08d10)', color:'#fff', border:'none', padding:'13px 26px', borderRadius:14, fontSize:14, fontWeight:700, cursor:'pointer', display:'flex', alignItems:'center', gap:8, boxShadow:'0 4px 20px rgba(245,166,35,0.45)', whiteSpace:'nowrap', transition:'transform .15s' }}
                onMouseEnter={e => e.currentTarget.style.transform='translateY(-1px)'}
                onMouseLeave={e => e.currentTarget.style.transform='none'}
              >
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                Nouvelle analyse
              </button>
            </div>
          </div>

          {/* ── STATS CARDS ──────────────────────────────────────── */}
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14 }}>
            {STATS.map((s, i) => (
              <div key={s.label} className={`dash-card card-lift card-shine stat-card stagger-${i+1}`}
                style={{ background:'#fff', borderRadius:16, padding:'18px 20px', border:'1px solid #E2EBF6', boxShadow:'0 1px 6px rgba(0,0,0,0.04)', position:'relative', overflow:'hidden' }}>
                <div style={{ position:'absolute', top:0, left:0, right:0, height:3, background:s.accent, borderRadius:'16px 16px 0 0', opacity:0.85 }} />
                <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:10 }}>
                  <div style={{ width:38, height:38, borderRadius:10, background:s.bg, display:'flex', alignItems:'center', justifyContent:'center', transition:'transform 0.2s ease' }}>
                    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke={s.accent} strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d={s.icon} />
                    </svg>
                  </div>
                </div>
                <div className={`count-up stagger-${i+1}`} style={{ fontSize:32, fontWeight:800, color:'#1A202C', lineHeight:1, marginBottom:3 }}>
                  {loading ? <SkeletonPulse w={48} h={32} r={6} /> : s.value}
                </div>
                <div style={{ fontSize:11, color:'#64748B', marginBottom:8, fontWeight:500 }}>{s.label}</div>
                <div style={{ display:'flex', alignItems:'center', gap:4 }}>
                  <span style={{ fontSize:10, fontWeight:700, color:s.accent, background:s.bg, padding:'2px 8px', borderRadius:9999, border:`1px solid ${s.accent}22` }}>
                    {s.trend}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* ── PIPELINE COUCHES (agrandies) ──────────────────────── */}
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16 }}>
            {COUCHES.map((c, i) => (
              <div key={c.num} className={`dash-card card-lift card-shine stagger-${i+1}`} style={{ animationDelay:`${(i+4)*60}ms`, background:'#fff', borderRadius:20, border:'1px solid #E2EBF6', boxShadow:'0 2px 10px rgba(0,0,0,0.05)', overflow:'hidden' }}>
                <div style={{ background:c.grad, padding:'20px 24px', display:'flex', alignItems:'center', gap:16 }}>
                  <div style={{ width:48, height:48, borderRadius:13, background:'rgba(255,255,255,0.18)', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                    <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="#fff" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d={c.icon} />
                    </svg>
                  </div>
                  <div>
                    <div style={{ fontSize:10, fontWeight:700, color:'rgba(255,255,255,0.7)', letterSpacing:'0.12em' }}>COUCHE {c.num}</div>
                    <div style={{ fontSize:16, fontWeight:700, color:'#fff' }}>{c.label}</div>
                  </div>
                  <div style={{ marginLeft:'auto', background:'rgba(255,255,255,0.2)', color:'#fff', fontSize:10, fontWeight:700, padding:'4px 11px', borderRadius:9999, letterSpacing:'0.06em', flexShrink:0 }}>
                    ACTIF
                  </div>
                </div>
                <div style={{ padding:'20px 24px', minHeight:100 }}>
                  <p style={{ fontSize:13, color:'#64748B', margin:'0 0 16px', lineHeight:1.65 }}>{c.desc}</p>
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <div style={{ flex:1, height:5, borderRadius:9999, background:c.light, overflow:'hidden' }}>
                      <div style={{ width:'100%', height:'100%', borderRadius:9999, background:c.grad }} />
                    </div>
                    <span style={{ fontSize:10, fontWeight:700, color:c.color }}>100%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* ── CHARTS ROW ───────────────────────────────────────── */}
          <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:14 }}>

            {/* Activité */}
            <div style={{ background:'#fff', borderRadius:16, border:'1px solid #E2EBF6', boxShadow:'0 1px 6px rgba(0,0,0,0.04)', padding:'20px 22px' }}>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:18 }}>
                <div>
                  <h3 style={{ fontSize:13, fontWeight:700, color:'#1A202C', margin:0 }}>Mon activité</h3>
                  <p style={{ fontSize:11, color:'#94A3B8', margin:'2px 0 0' }}>Analyses par jour de la semaine</p>
                </div>
                <div style={{ display:'flex', gap:16 }}>
                  <div style={{ textAlign:'right' }}>
                    <div style={{ fontSize:20, fontWeight:800, color:'#1B4F9B', lineHeight:1 }}>{loading ? '—' : total}</div>
                    <div style={{ fontSize:9, color:'#94A3B8', fontWeight:600 }}>RAPPORTS</div>
                  </div>
                  <div style={{ textAlign:'right' }}>
                    <div style={{ fontSize:20, fontWeight:800, color:'#DC2626', lineHeight:1 }}>{loading ? '—' : cancers}</div>
                    <div style={{ fontSize:9, color:'#94A3B8', fontWeight:600 }}>CANCERS</div>
                  </div>
                </div>
              </div>

              <div style={{ display:'flex', alignItems:'flex-end', gap:8, height:110 }}>
                {activiteParJour.map((d, i) => {
                  const h = Math.max((d.val / maxVal) * 90, 6)
                  return (
                    <div key={i} style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', gap:4 }}>
                      {d.val > 0 && (
                        <span style={{ fontSize:9, fontWeight:700, color:'#1B4F9B' }}>{d.val}</span>
                      )}
                      <div style={{ flex:1, width:'100%', display:'flex', alignItems:'flex-end' }}>
                        <div className={d.val > 0 ? 'bar-fill' : ''} style={{
                          width:'100%', borderRadius:'5px 5px 0 0',
                          height: `${h}px`,
                          background: d.val > 0
                            ? 'linear-gradient(180deg,#2563eb,#1B4F9B)'
                            : '#EEF3FB',
                          transition:'height .4s ease',
                        }} />
                      </div>
                      <span style={{ fontSize:9, color:'#94A3B8', fontWeight:600 }}>{d.jour}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Résultats donut */}
            <div style={{ background:'#fff', borderRadius:16, border:'1px solid #E2EBF6', boxShadow:'0 1px 6px rgba(0,0,0,0.04)', padding:'20px 22px' }}>
              <h3 style={{ fontSize:13, fontWeight:700, color:'#1A202C', margin:'0 0 4px' }}>Mes résultats</h3>
              <p style={{ fontSize:11, color:'#94A3B8', margin:'0 0 16px' }}>Distribution des diagnostics</p>

              <div style={{ display:'flex', justifyContent:'center', marginBottom:16 }}>
                <svg width="120" height="120" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r={donutR} fill="none" stroke="#F1F5F9" strokeWidth="13" />
                  <circle cx="60" cy="60" r={donutR} fill="none" stroke="#15803D" strokeWidth="13"
                    strokeDasharray={`${donutBenin} ${donutC}`}
                    strokeLinecap="round" transform="rotate(-90 60 60)" />
                  {donutCancer > 0 && (
                    <circle cx="60" cy="60" r={donutR} fill="none" stroke="#DC2626" strokeWidth="13"
                      strokeDasharray={`${donutCancer} ${donutC}`}
                      strokeDashoffset={-donutBenin}
                      strokeLinecap="round" transform="rotate(-90 60 60)" />
                  )}
                  <text x="60" y="55" textAnchor="middle" fontSize="18" fontWeight="800" fill="#1A202C">{tauxBenin}%</text>
                  <text x="60" y="70" textAnchor="middle" fontSize="9" fontWeight="600" fill="#94A3B8">bénins</text>
                </svg>
              </div>

              <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
                {[
                  { label:'Non-Cancer', val:nonCancers, pct:tauxBenin,     color:'#15803D', bg:'#F0FDF4' },
                  { label:'Cancer',     val:cancers,    pct:tauxDetection, color:'#DC2626', bg:'#FFF1F2' },
                ].map(r => (
                  <div key={r.label}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', fontSize:11, marginBottom:5 }}>
                      <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                        <div style={{ width:8, height:8, borderRadius:'50%', background:r.color }} />
                        <span style={{ color:'#475569', fontWeight:500 }}>{r.label}</span>
                      </div>
                      <div style={{ display:'flex', gap:6, alignItems:'center' }}>
                        <span style={{ fontWeight:700, color:r.color }}>{r.val} cas</span>
                        <span style={{ fontSize:10, color:'#94A3B8' }}>{r.pct}%</span>
                      </div>
                    </div>
                    <div style={{ height:5, borderRadius:9999, background:'#F1F5F9', overflow:'hidden' }}>
                      <div className="bar-fill" style={{ width:`${r.pct}%`, height:'100%', borderRadius:9999, background:r.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ── DERNIÈRES ANALYSES (corrigées) ───────────────────── */}
          <div className="dash-card" style={{ background:'#fff', borderRadius:16, overflow:'hidden', border:'1px solid #E2EBF6', boxShadow:'0 2px 12px rgba(27,79,155,0.06)' }}>
            <div style={{ height: 3, background: 'linear-gradient(90deg,#1B4F9B,#3b82f6)' }} />

            <div style={{ padding:'16px 22px', borderBottom:'1px solid #F1F5F9', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
              <div>
                <h3 style={{ fontSize:13, fontWeight:700, color:'#1A202C', margin:0 }}>Dernières analyses</h3>
                <p style={{ fontSize:11, color:'#94A3B8', margin:'2px 0 0' }}>5 derniers rapports enregistrés</p>
              </div>
              <button
                onClick={() => setPage('historique')}
                style={{ fontSize:11, fontWeight:600, padding:'6px 16px', borderRadius:10, border:'none', background:'#EEF3FB', color:'#1B4F9B', cursor:'pointer', display:'flex', alignItems:'center', gap:4 }}
                onMouseEnter={e => e.currentTarget.style.background='#dbeafe'}
                onMouseLeave={e => e.currentTarget.style.background='#EEF3FB'}
              >
                Voir tout
                <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {loading ? (
              <div style={{ padding:'24px 22px', display:'flex', flexDirection:'column', gap:12 }}>
                {[1,2,3].map(i => <SkeletonPulse key={i} h={32} r={8} />)}
              </div>
            ) : derniers.length === 0 ? (
              <div style={{ padding:40, textAlign:'center' }}>
                <svg width="40" height="40" fill="none" viewBox="0 0 24 24" stroke="#CBD5E1" strokeWidth={1.5} style={{ margin:'0 auto 10px' }}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                </svg>
                <p style={{ color:'#94A3B8', fontSize:13, fontWeight:500, margin:0 }}>Aucune analyse enregistrée</p>
              </div>
            ) : (
     <table style={{ width:'100%', borderCollapse:'collapse', tableLayout:'fixed' }}>
  <colgroup>
    <col style={{ width: '30%' }} />
    <col style={{ width: '15%' }} />
    <col style={{ width: '20%' }} />
    <col style={{ width: '15%' }} />
    <col style={{ width: '20%' }} />
  </colgroup>
  <thead>
    <tr style={{ background:'#F8FAFC' }}>
      {['Patient','CIN','Date','BI-RADS','Résultat'].map(h => (
        <th key={h} style={{ padding:'10px 16px', textAlign:'left', fontSize:10, fontWeight:700, color:'#94A3B8', letterSpacing:'0.08em', textTransform:'uppercase' }}>
          {h}
        </th>
      ))}
    </tr>
  </thead>
  <tbody>
    {derniers.map((r, i) => {
      const rb = resultBadge(r.resultat)
      const bb = biradsBadge(r.biradsScore)
      return (
        <tr key={i} style={{ borderTop:'1px solid #F1F5F9', background: i % 2 === 0 ? '#fff' : '#FAFBFE' }}>
          <td style={{ padding:'11px 16px' }}>
            <div style={{ display:'flex', alignItems:'center', gap:10 }}>
              <div style={{ width:30, height:30, borderRadius:'50%', background:avatarColor(r.prenom), display:'flex', alignItems:'center', justifyContent:'center', fontSize:10, fontWeight:700, color:'#fff', flexShrink:0 }}>
                {initials(r)}
              </div>
              <span style={{ fontSize:13, fontWeight:600, color:'#1A202C', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                {r.prenom} {r.nom}
              </span>
            </div>
          </td>
          <td style={{ padding:'11px 16px', fontSize:12, color:'#64748B', fontFamily:'monospace' }}>
            {r.cin || '—'}
          </td>
          <td style={{ padding:'11px 16px', fontSize:12, color:'#64748B', whiteSpace:'nowrap' }}>
            {new Date(r.createdAt).toLocaleDateString('fr-FR', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' })}
          </td>
          <td style={{ padding:'11px 16px' }}>
            <span style={{ fontSize:11, fontWeight:700, padding:'3px 10px', borderRadius:6, background:bb.bg, color:bb.color, border:`1px solid ${bb.border}`, whiteSpace:'nowrap' }}>
              {r.biradsScore ? `Score ${r.biradsScore}` : '—'}
            </span>
          </td>
          <td style={{ padding:'11px 16px' }}>
            <span style={{ fontSize:11, fontWeight:600, padding:'4px 12px', borderRadius:9999, background:rb.bg, color:rb.color, border:`1px solid ${rb.border}`, whiteSpace:'nowrap' }}>
              {r.resultat || '—'}
            </span>
          </td>
        </tr>
      )
    })}
  </tbody>
</table>
            )}
          </div>

        </div>
      </div>
    </>
  )
}