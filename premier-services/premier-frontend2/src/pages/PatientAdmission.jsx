import { useState } from "react";

// ─── Pipeline steps ───────────────────────────────────────────────────────────
const PIPELINE = [
  { id: 1, label: 'Admission',    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
  { id: 2, label: 'Mammographie', icon: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12' },
  { id: 3, label: 'Analyse IA',   icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
  { id: 4, label: 'Rapport',      icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
]

export function PipelineSteps({ currentStep }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
      {PIPELINE.map((step, i) => {
        const done   = step.id < currentStep
        const active = step.id === currentStep
        return (
          <div key={step.id} style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{ position: 'relative' }}>
                {active && (
                  <div style={{
                    position: 'absolute', inset: -4, borderRadius: '50%',
                    background: 'rgba(245,166,35,0.3)',
                    animation: 'pulse 1.5s ease-in-out infinite',
                  }} />
                )}
                <div style={{
                  width: 36, height: 36, borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 13, fontWeight: 800,
                  background: done ? 'rgba(39,181,98,0.9)' : active ? '#F5A623' : 'rgba(255,255,255,0.15)',
                  color: (done || active) ? '#fff' : 'rgba(255,255,255,0.4)',
                  border: `2px solid ${done ? 'rgba(39,181,98,0.5)' : active ? 'rgba(245,166,35,0.5)' : 'rgba(255,255,255,0.2)'}`,
                  transition: 'all 0.5s ease',
                  boxShadow: active ? '0 0 16px rgba(245,166,35,0.5)' : 'none',
                  position: 'relative', zIndex: 1,
                }}>
                  {done
                    ? <svg width="16" height="16" fill="none" stroke="#fff" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                    : <span style={{ fontSize: 12 }}>0{step.id}</span>
                  }
                </div>
              </div>
              <span style={{
                fontSize: 9, fontWeight: 700, whiteSpace: 'nowrap',
                color: done ? '#27B562' : active ? '#F5A623' : 'rgba(255,255,255,0.35)',
                transition: 'color 0.5s ease', letterSpacing: '0.04em',
              }}>
                {step.label}
              </span>
            </div>
            {i < PIPELINE.length - 1 && (
              <div style={{
                width: 48, height: 2, margin: '0 4px', marginBottom: 20, 
                background: done ? '#27B562' : 'rgba(255,255,255,0.15)',
                borderRadius: 2, overflow: 'hidden', position: 'relative', transition: 'background 0.5s ease',
              }}>
                {active && step.id < 3 && (
                  <div style={{
                    position: 'absolute', inset: 0,
                    background: 'linear-gradient(90deg, #F5A623, rgba(245,166,35,0.3))',
                    animation: 'shimmer 1.5s ease-in-out infinite',
                  }} />
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ─── Icon SVG helper ──────────────────────────────────────────────────────────
function Icon({ d, size = 14, color = '#94A3B8', strokeWidth = 2 }) {
  return (
    <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke={color} strokeWidth={strokeWidth}>
      <path strokeLinecap="round" strokeLinejoin="round" d={d} />
    </svg>
  )
}

// ─── Input with leading icon ──────────────────────────────────────────────────
function IconInput({ icon, field, errors, ...props }) {
  const hasError = !!errors[field]
  return (
    <div style={{ position: 'relative' }}>
      <div style={{
        position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', zIndex: 1,
      }}>
        <Icon d={icon} size={14} color={hasError ? '#E24B4A' : '#94A3B8'} />
      </div>
      <input
        {...props}
        style={{
          width: '100%', boxSizing: 'border-box',
          padding: '10px 14px 10px 36px',
          fontSize: 13, borderRadius: 10,
          border: `1.5px solid ${hasError ? '#FCA5A5' : '#E2E8F0'}`,
          background: hasError ? '#FFF5F5' : '#F8FAFC',
          color: '#1a1a2e', fontFamily: 'inherit',
          outline: 'none', transition: 'border-color 0.18s, box-shadow 0.18s',
        }}
      />
    </div>
  )
}

// ─── Section header with colored accent bar ────────────────────────────────────
function SectionHeader({ icon, title, subtitle, color, bg }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
      <div style={{
        width: 36, height: 36, borderRadius: 10, background: bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Icon d={icon} size={16} color={color} strokeWidth={2} />
      </div>
      <div>
        <p style={{ fontSize: 13, fontWeight: 700, color, margin: 0 }}>{title}</p>
        <p style={{ fontSize: 10, color: '#94A3B8', margin: 0 }}>{subtitle}</p>
      </div>
      <div style={{ marginLeft: 'auto', height: 3, width: 40, borderRadius: 9999, background: color, opacity: 0.25 }} />
    </div>
  )
}

// ─── Field wrapper ─────────────────────────────────────────────────────────────
function Field({ label, required, error, children }) {
  return (
    <div>
      <label style={{
        display: 'block', fontSize: 10, fontWeight: 700,
        color: error ? '#E24B4A' : '#64748B',
        textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6,
        transition: 'color 0.15s',
      }}>
        {label} {required && <span style={{ color: '#E24B4A' }}>*</span>}
      </label>
      {children}
      {error && (
        <p style={{
          color: '#E24B4A', fontSize: 10, marginTop: 4, fontWeight: 600,
          display: 'flex', alignItems: 'center', gap: 4,
          animation: 'shakeX 0.35s ease',
        }}>
          <svg width="10" height="10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          {error}
        </p>
      )}
    </div>
  )
}

// ─── Côté card button ──────────────────────────────────────────────────────────
function CoteCard({ value, label, iconPath, selected, onClick }) {
  return (
    <button onClick={onClick} style={{
      flex: 1, padding: '12px 8px', borderRadius: 12, cursor: 'pointer',
      border: `2px solid ${selected ? '#1B4F9B' : '#E2E8F0'}`,
      background: selected
        ? 'linear-gradient(135deg, #EEF3FB, #dbeafe)'
        : '#F8FAFC',
      color: selected ? '#1B4F9B' : '#94A3B8',
      transition: 'all 0.2s cubic-bezier(0.16,1,0.3,1)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
      boxShadow: selected ? '0 4px 14px rgba(27,79,155,0.18)' : 'none',
      transform: selected ? 'translateY(-1px)' : 'none',
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: 8,
        background: selected ? '#1B4F9B' : '#E2E8F0',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all 0.2s',
      }}>
        <Icon d={iconPath} size={15} color={selected ? '#fff' : '#94A3B8'} />
      </div>
      <span style={{ fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap', letterSpacing: '0.04em' }}>{label}</span>
    </button>
  )
}

// ─── Animated pulse dot ────────────────────────────────────────────────────────
function PulseDot({ color = '#34D399', delay = 0 }) {
  return (
    <div style={{ position: 'relative', width: 8, height: 8, flexShrink: 0 }}>
      <div style={{
        position: 'absolute', inset: 0, borderRadius: '50%',
        background: color, opacity: 0.35,
        animation: `ping 2s cubic-bezier(0,0,0.2,1) infinite`,
        animationDelay: `${delay}s`,
      }} />
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, position: 'relative', zIndex: 1 }} />
    </div>
  )
}

// ─── Main component ────────────────────────────────────────────────────────────
const PatientAdmission = ({ onSubmit, initialData }) => {
  const [errors, setErrors] = useState({})
  const [form, setForm] = useState(initialData || {
    cin: '', nom: '', prenom: '', dateNaissance: '',
    telephone: '', dateExamen: new Date().toISOString().split('T')[0], cote: 'bilateral',
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: '' }))
  }

  const validate = () => {
    const e = {}
    if (!form.cin.trim())       e.cin           = 'Obligatoire'
    if (!form.nom.trim())       e.nom           = 'Obligatoire'
    if (!form.prenom.trim())    e.prenom        = 'Obligatoire'
    if (!form.dateNaissance)    e.dateNaissance = 'Obligatoire'
    if (!form.telephone.trim()) e.telephone     = 'Obligatoire'
    return e
  }

  const handleSubmit = () => {
    const e = validate()
    if (Object.keys(e).length > 0) { setErrors(e); return }
    onSubmit(form)
  }

  const today = new Date().toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'long', year: 'numeric',
  })

  const COTES = [
    { value: 'bilateral', label: 'Bilatéral',   iconPath: 'M4 8h16M4 12h16M4 16h16' },
    { value: 'gauche',    label: 'Sein gauche',  iconPath: 'M11 19l-7-7 7-7m8 14l-7-7 7-7' },
    { value: 'droit',     label: 'Sein droit',   iconPath: 'M13 5l7 7-7 7M5 5l7 7-7 7' },
  ]

  const PIPELINE_SERVICES = [
    { label: 'Détection',        color: '#60A5FA', delay: 0 },
    { label: 'Classification',   color: '#34D399', delay: 0.3 },
    { label: 'Segmentation',     color: '#F5A623', delay: 0.6 },
    { label: 'Rapport narratif', color: '#A78BFA', delay: 0.9 },
  ]

  const GUIDE_STEPS = [
    { num: '01', title: 'CIN',              desc: "Carte d'identité nationale du patient", color: '#1B4F9B', bg: '#EEF3FB' },
    { num: '02', title: 'Date de naissance', desc: 'Format JJ/MM/AAAA — obligatoire', color: '#B7791F', bg: '#FFFBEB' },
    { num: '03', title: 'Côté examiné',     desc: 'Gauche, droit ou bilatéral', color: '#276749', bg: '#F0FFF4' },
  ]

  return (
    <div className="page-enter" style={{ minHeight: '100vh', background: '#F7F9FC', padding: '24px 28px' }}>
      <style>{`
        @keyframes pulse   { 0%,100%{transform:scale(1);opacity:.6} 50%{transform:scale(1.4);opacity:.2} }
        @keyframes shimmer { 0%{transform:translateX(-100%)} 100%{transform:translateX(100%)} }
        @keyframes shakeX  { 0%,100%{transform:translateX(0)} 20%,60%{transform:translateX(-4px)} 40%,80%{transform:translateX(4px)} }
        @keyframes floatY  { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
        @keyframes ping    { 75%,100%{transform:scale(2.2);opacity:0} }
        @keyframes countUp { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:none} }
        input:focus,select:focus { border-color:#1B4F9B!important; box-shadow:0 0 0 3px rgba(27,79,155,0.12)!important; background:#fff!important; }
        .admit-input-wrap input:focus { outline:none; }
        .cote-btn:hover { transform:translateY(-2px)!important; box-shadow:0 6px 18px rgba(27,79,155,0.12)!important; }
        .sidebar-card { animation: fadeInUp .45s cubic-bezier(0.16,1,0.3,1) both; }
        @keyframes fadeInUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:none} }
      `}</style>

      {/* ── Edit mode banner ── */}
      {initialData && (
        <div className="slide-in-left" style={{
          display: 'flex', alignItems: 'center', gap: 10,
          background: 'linear-gradient(135deg, #FFFBEB, #FEF3C7)',
          border: '1.5px solid #FDE68A', borderRadius: 12,
          padding: '11px 18px', marginBottom: 18,
          boxShadow: '0 2px 12px rgba(183,121,31,0.1)',
        }}>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: '#FDE68A', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Icon d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" size={14} color="#B7791F" />
          </div>
          <div>
            <p style={{ fontSize: 12, fontWeight: 700, color: '#92400E', margin: 0 }}>Mode édition</p>
            <p style={{ fontSize: 10, color: '#B45309', margin: 0 }}>Corrigez les informations puis cliquez sur "Continuer l'analyse"</p>
          </div>
        </div>
      )}

      {/* ── Hero Banner ── */}
      <div className="hero-gradient-anim" style={{
        background: 'linear-gradient(-45deg, #0f2d5c, #1B4F9B, #153d7a, #1d6bb8)',
        backgroundSize: '300% 300%',
        borderRadius: 20, padding: '26px 36px', marginBottom: 22,
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Décors */}
        <div style={{ position:'absolute', right:-50, top:-50, width:220, height:220, borderRadius:'50%', background:'rgba(255,255,255,0.04)' }} />
        <div style={{ position:'absolute', right:110, bottom:-60, width:160, height:160, borderRadius:'50%', background:'rgba(245,166,35,0.08)' }} />
        <div style={{ position:'absolute', right:40, top:18, width:70, height:70, borderRadius:'50%', background:'rgba(245,166,35,0.1)' }} />
        {/* Croix médicale flottante */}
        <svg style={{ position:'absolute', right:36, bottom:16, opacity:0.06, animation:'floatY 4s ease-in-out infinite' }} width="110" height="110" viewBox="0 0 24 24" fill="white">
          <path d="M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm-7 14h-2v-4H6v-2h4V7h2v4h4v2h-4v4z" />
        </svg>

        <div style={{ position:'relative', display:'flex', alignItems:'center', justifyContent:'space-between', gap:24 }}>
          <div>
            <span style={{
              display:'inline-block', marginBottom:10,
              background:'rgba(245,166,35,0.18)', color:'#F5A623',
              border:'1px solid rgba(245,166,35,0.32)',
              fontSize:10, fontWeight:700, padding:'4px 14px', borderRadius:9999, letterSpacing:'0.1em',
            }}>
              ✦ {initialData ? 'MODIFICATION DOSSIER' : 'NOUVELLE ANALYSE'} · CHU Mohammed VI
            </span>
            <h1 style={{ fontSize:24, fontWeight:800, color:'#fff', margin:'0 0 4px', lineHeight:1.2 }}>
              {initialData ? 'Modifier les informations 📝' : 'Admission patiente'}
            </h1>
            <p style={{ color:'rgba(255,255,255,0.55)', fontSize:12, margin:0 }}>
              {initialData
                ? "Corrigez les données puis poursuivez l'analyse"
                : 'Identifiez la patiente avant de charger la mammographie'}
            </p>
          </div>
          <PipelineSteps currentStep={1} />
        </div>
      </div>

      {/* ── Grid: Formulaire + Sidebar ── */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 290px', gap:18 }}>

        {/* ════ FORMULAIRE ════ */}
        <div className="slide-in-up card-shine" style={{
          background:'#fff', borderRadius:18,
          border:'1px solid #E2EBF6',
          boxShadow:'0 2px 16px rgba(0,0,0,0.05)',
          overflow:'hidden',
          animation:'fadeInUp .4s cubic-bezier(0.16,1,0.3,1) both',
        }}>

          {/* Section 1: Identité patiente */}
          <div style={{ padding:'22px 26px', borderBottom:'1px solid #F1F5F9' }}>
            {/* Accent top bar */}
            <div style={{ position:'relative', marginBottom:20 }}>
              <div style={{ position:'absolute', top:-22, left:-26, right:-26, height:3, background:'linear-gradient(90deg,#1B4F9B,#3b82f6)', opacity:0.7 }} />
              <SectionHeader
                icon="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                title="Informations de la patiente"
                subtitle="Données d'identité requises"
                color="#1B4F9B"
                bg="#EEF3FB"
              />
            </div>

            <div className="admit-input-wrap" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
              <Field label="CIN" required error={errors.cin}>
                <IconInput
                  icon="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c0 1.306.835 2.417 2 2.83M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2"
                  field="cin" errors={errors}
                  name="cin" value={form.cin} onChange={handleChange}
                  placeholder="Ex : AB123456"
                />
              </Field>

              <Field label="Téléphone" required error={errors.telephone}>
                <IconInput
                  icon="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                  field="telephone" errors={errors}
                  name="telephone" value={form.telephone} onChange={handleChange}
                  placeholder="06XXXXXXXX"
                />
              </Field>

              <Field label="Nom" required error={errors.nom}>
                <IconInput
                  icon="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  field="nom" errors={errors}
                  name="nom" value={form.nom} onChange={handleChange}
                  placeholder="Nom de famille"
                />
              </Field>

              <Field label="Prénom" required error={errors.prenom}>
                <IconInput
                  icon="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  field="prenom" errors={errors}
                  name="prenom" value={form.prenom} onChange={handleChange}
                  placeholder="Prénom"
                />
              </Field>

              <div style={{ gridColumn:'1 / -1' }}>
                <Field label="Date de naissance" required error={errors.dateNaissance}>
                  <div style={{ position:'relative', maxWidth:240 }}>
                    <div style={{ position:'absolute', left:12, top:'50%', transform:'translateY(-50%)', pointerEvents:'none', zIndex:1 }}>
                      <Icon d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" size={14} color={errors.dateNaissance ? '#E24B4A' : '#94A3B8'} />
                    </div>
                    <input
                      type="date" name="dateNaissance" value={form.dateNaissance} onChange={handleChange}
                      style={{
                        width:'100%', boxSizing:'border-box',
                        padding:'10px 14px 10px 36px', fontSize:13, borderRadius:10,
                        border:`1.5px solid ${errors.dateNaissance ? '#FCA5A5' : '#E2E8F0'}`,
                        background: errors.dateNaissance ? '#FFF5F5' : '#F8FAFC',
                        color:'#1a1a2e', fontFamily:'inherit', outline:'none',
                        transition:'border-color .18s, box-shadow .18s',
                      }}
                    />
                  </div>
                </Field>
              </div>
            </div>
          </div>

          {/* Section 2: Examen */}
          <div style={{ padding:'22px 26px' }}>
            <SectionHeader
              icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              title="Paramètres de l'examen"
              subtitle="Date et côté mammographié"
              color="#B7791F"
              bg="#FFFBEB"
            />

            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
              {/* Date examen */}
              <div>
                <label style={{ display:'block', fontSize:10, fontWeight:700, color:'#64748B', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:6 }}>
                  Date de l'examen
                </label>
                <div style={{
                  display:'flex', alignItems:'center', gap:10,
                  padding:'10px 14px', borderRadius:10,
                  border:'1.5px solid #E2E8F0', background:'#F8FAFC',
                  fontSize:13, color:'#374151',
                }}>
                  <Icon d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" size={14} color="#94A3B8" />
                  <span style={{ flex:1 }}>{today}</span>
                  <span style={{ fontSize:9, fontWeight:700, color:'#B7791F', background:'#FFFBEB', border:'1px solid #FDE68A', padding:'2px 8px', borderRadius:6 }}>AUTO</span>
                </div>
              </div>

              {/* Côté examiné */}
              <div>
                <label style={{ display:'block', fontSize:10, fontWeight:700, color:'#64748B', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:6 }}>
                  Côté examiné
                </label>
                <div style={{ display:'flex', gap:8 }}>
                  {COTES.map(c => (
                    <CoteCard
                      key={c.value}
                      className="cote-btn"
                      value={c.value}
                      label={c.label}
                      iconPath={c.iconPath}
                      selected={form.cote === c.value}
                      onClick={() => setForm(p => ({ ...p, cote: c.value }))}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div style={{
            padding:'16px 26px', borderTop:'1px solid #F1F5F9',
            display:'flex', alignItems:'center', justifyContent:'space-between',
            background:'linear-gradient(135deg, #FAFBFC, #F7F9FC)',
          }}>
            <p style={{ fontSize:10, color:'#CBD5E0', margin:0 }}>
              <span style={{ color:'#E24B4A' }}>*</span> Champs obligatoires · CHU Mohammed VI Oujda
            </p>
            <button
              onClick={handleSubmit}
              className="btn-primary"
              style={{
                background:'linear-gradient(135deg, #1B4F9B, #153d7a)',
                color:'#fff', border:'none', borderRadius:12,
                padding:'12px 28px', fontSize:13, fontWeight:700,
                cursor:'pointer', display:'flex', alignItems:'center', gap:8,
                boxShadow:'0 4px 16px rgba(27,79,155,0.35)',
                letterSpacing:'0.02em',
              }}
            >
              <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              {initialData ? "Continuer l'analyse" : 'Charger la mammographie'}
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
          </div>
        </div>

        {/* ════ SIDEBAR ════ */}
        <div style={{ display:'flex', flexDirection:'column', gap:14 }}>

          {/* Pipeline IA card */}
          <div className="sidebar-card card-lift" style={{
            background:'linear-gradient(160deg, #0f2d5c 0%, #1B4F9B 60%, #153d7a 100%)',
            borderRadius:18, padding:'20px',
            border:'1px solid rgba(255,255,255,0.08)',
            boxShadow:'0 8px 32px rgba(27,79,155,0.25)',
            animationDelay:'0.08s',
            position:'relative', overflow:'hidden',
          }}>
            {/* Décor cercles */}
            <div style={{ position:'absolute', right:-30, top:-30, width:120, height:120, borderRadius:'50%', background:'rgba(255,255,255,0.04)' }} />
            <div style={{ position:'absolute', right:20, bottom:-40, width:90, height:90, borderRadius:'50%', background:'rgba(245,166,35,0.08)' }} />

            <div style={{ position:'relative' }}>
              <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:14 }}>
                <div style={{ width:28, height:28, borderRadius:8, background:'rgba(245,166,35,0.2)', display:'flex', alignItems:'center', justifyContent:'center' }}>
                  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#F5A623" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <p style={{ fontSize:12, fontWeight:800, color:'#F5A623', margin:0, letterSpacing:'0.04em' }}>Pipeline IA activé</p>
                <div style={{ marginLeft:'auto', width:8, height:8, borderRadius:'50%', background:'#34D399', boxShadow:'0 0 8px rgba(52,211,153,0.6)' }} />
              </div>

              <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
                {PIPELINE_SERVICES.map((s, i) => (
                  <div key={i} style={{
                    display:'flex', alignItems:'center', gap:10,
                    background:'rgba(255,255,255,0.06)', borderRadius:10,
                    padding:'8px 12px', border:'1px solid rgba(255,255,255,0.07)',
                    animation:`fadeInUp .4s cubic-bezier(0.16,1,0.3,1) ${0.1+i*0.07}s both`,
                  }}>
                    <PulseDot color={s.color} delay={s.delay} />
                    <span style={{ fontSize:11, color:'rgba(255,255,255,0.85)', flex:1, fontWeight:500 }}>{s.label}</span>
                    <span style={{
                      fontSize:9, fontWeight:700, color:s.color,
                      background:'rgba(255,255,255,0.08)', padding:'2px 8px', borderRadius:6,
                      border:`1px solid ${s.color}33`,
                    }}>Prêt</span>
                  </div>
                ))}
              </div>

              <div style={{ marginTop:14, paddingTop:12, borderTop:'1px solid rgba(255,255,255,0.1)', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <p style={{ fontSize:10, color:'rgba(255,255,255,0.4)', margin:0 }}>Temps estimé</p>
                <span style={{ fontSize:12, color:'#F5A623', fontWeight:800 }}>~ 4 min</span>
              </div>
            </div>
          </div>

          {/* Guide card */}
          <div className="sidebar-card card-lift card-shine" style={{
            background:'#fff', borderRadius:18,
            border:'1px solid #E2EBF6',
            boxShadow:'0 2px 12px rgba(0,0,0,0.04)',
            padding:'18px 18px',
            animationDelay:'0.16s',
          }}>
            <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:14 }}>
              <div style={{ width:28, height:28, borderRadius:8, background:'#EEF3FB', display:'flex', alignItems:'center', justifyContent:'center' }}>
                <Icon d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" size={14} color="#1B4F9B" />
              </div>
              <p style={{ fontSize:12, fontWeight:700, color:'#1B4F9B', margin:0 }}>Guide de saisie</p>
            </div>
            <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
              {GUIDE_STEPS.map((g, i) => (
                <div key={i} style={{
                  display:'flex', gap:10, alignItems:'flex-start',
                  padding:'10px 12px', borderRadius:10, background:g.bg,
                  border:`1px solid ${g.color}22`,
                  animation:`fadeInUp .4s cubic-bezier(0.16,1,0.3,1) ${0.18+i*0.08}s both`,
                }}>
                  <div style={{
                    width:22, height:22, borderRadius:6, background:g.color,
                    display:'flex', alignItems:'center', justifyContent:'center',
                    flexShrink:0, fontSize:9, fontWeight:800, color:'#fff',
                  }}>
                    {g.num}
                  </div>
                  <div>
                    <p style={{ fontSize:11, fontWeight:700, color:'#374151', margin:'0 0 1px' }}>{g.title}</p>
                    <p style={{ fontSize:10, color:'#94A3B8', margin:0, lineHeight:1.4 }}>{g.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sécurité card */}
          <div className="sidebar-card card-lift" style={{
            background:'linear-gradient(135deg, #F0FFF4, #DCFCE7)',
            border:'1.5px solid #BBF7D0', borderRadius:18,
            padding:'16px 18px',
            animationDelay:'0.24s',
          }}>
            <div style={{ display:'flex', gap:10, alignItems:'center' }}>
              <div style={{
                width:38, height:38, borderRadius:10,
                background:'rgba(39,103,73,0.12)',
                display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0,
              }}>
                <Icon d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" size={18} color="#276749" strokeWidth={2} />
              </div>
              <div>
                <p style={{ fontSize:12, fontWeight:700, color:'#276749', margin:'0 0 2px' }}>Données sécurisées</p>
                <p style={{ fontSize:10, color:'#16A34A', margin:0 }}>RGPD · Chiffrement E2E · CHU Oujda</p>
              </div>
            </div>
            <div style={{ marginTop:10, display:'flex', gap:6 }}>
              {['RGPD', 'E2E', 'ISO 27001'].map(tag => (
                <span key={tag} style={{
                  fontSize:9, fontWeight:700, color:'#276749',
                  background:'rgba(39,103,73,0.1)', padding:'3px 8px', borderRadius:6,
                  border:'1px solid rgba(39,103,73,0.2)',
                }}>
                  {tag}
                </span>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

export default PatientAdmission
