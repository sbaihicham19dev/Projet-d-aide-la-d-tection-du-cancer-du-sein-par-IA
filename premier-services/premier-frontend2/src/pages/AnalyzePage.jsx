import { useState } from 'react'
import { analyzeMammography, analyzeGradcam, saveRapport } from '../services/api'
import { jsPDF } from 'jspdf'
import { PipelineSteps } from './PatientAdmission'

// ─── Icônes outline sobres (remplacent les emojis) ─────────────────────────
const Icon = {
  sparkle: (p) => (
    <svg width={p?.size||11} height={p?.size||11} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" />
    </svg>
  ),
  report: (p) => (
    <svg width={p?.size||16} height={p?.size||16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  microscope: (p) => (
    <svg width={p?.size||16} height={p?.size||16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 17h6M10 17v-4.5a2.5 2.5 0 115 0M5 21h14M8 13l-2.5 4M6 9.5h3M12 4l-1 2M16 5l-1.5 1.5" />
    </svg>
  ),
  scan: (p) => (
    <svg width={p?.size||28} height={p?.size||28} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
  ),
  check: (p) => (
    <svg width={p?.size||16} height={p?.size||16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 13l4 4L19 7" />
    </svg>
  ),
  checkCircle: (p) => (
    <svg width={p?.size||16} height={p?.size||16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  user: (p) => (
    <svg width={p?.size||13} height={p?.size||13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  ),
  target: (p) => (
    <svg width={p?.size||20} height={p?.size||20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="12" cy="12" r="0.6" fill="currentColor" />
    </svg>
  ),
  ruler: (p) => (
    <svg width={p?.size||20} height={p?.size||20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="8" width="18" height="8" rx="1.5" transform="rotate(-8 12 12)" />
      <path d="M6.5 9.5l.6 2M10 9l.6 2M13.5 8.5l.6 2M17 8l.6 2" />
    </svg>
  ),
  alertTriangle: (p) => (
    <svg width={p?.size||13} height={p?.size||13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 9v4M12 17h.01M10.3 3.9L2.7 18a1.5 1.5 0 001.3 2.2h16a1.5 1.5 0 001.3-2.2L13.7 3.9a1.5 1.5 0 00-2.6 0z" />
    </svg>
  ),
  alertCircle: (p) => (
    <svg width={p?.size||16} height={p?.size||16} viewBox="0 0 24 24" fill="currentColor">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
    </svg>
  ),
  x: (p) => (
    <svg width={p?.size||11} height={p?.size||11} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  ),
  arrowLeft: (p) => (
    <svg width={p?.size||15} height={p?.size||15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 19l-7-7m0 0l7-7m-7 7h18" />
    </svg>
  ),
  plus: (p) => (
    <svg width={p?.size||13} height={p?.size||13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 4v16m8-8H4" />
    </svg>
  ),
  eye: (p) => (
    <svg width={p?.size||14} height={p?.size||14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ),
}

const PILL = (v) => {
  const M = {
    red:    ['#FCEBEB','#791F1F','#F09595'],
    amber:  ['#FAEEDA','#633806','#FAC775'],
    green:  ['#EAF3DE','#27500A','#97C459'],
    purple: ['#EEEDFE','#3C3489','#AFA9EC'],
    blue:   ['#E6F1FB','#0C447C','#85B7EB'],
    gray:   ['#F1EFE8','#5F5E5A','#B4B2A9'],
  }
  const [bg,color,bd] = M[v]||M.gray
  return { display:'inline-flex',alignItems:'center',gap:'4px',fontSize:'11px',fontWeight:'600',borderRadius:'7px',padding:'4px 11px',whiteSpace:'nowrap',background:bg,color,border:`0.5px solid ${bd}` }
}

const CARD        = { background:'#fff',border:'0.5px solid #E8E7E3',borderRadius:'16px',overflow:'hidden' }
const CARD_HEAD   = { display:'flex',alignItems:'center',justifyContent:'space-between',padding:'13px 20px',borderBottom:'0.5px solid #E8E7E3',background:'#FAFAF9' }
const LABEL_STYLE = { fontSize:'10px',fontWeight:'700',textTransform:'uppercase',letterSpacing:'.09em',color:'#B4B2A9',display:'flex',alignItems:'center',gap:'8px' }
const CARD_SHADOW = '0 1px 3px rgba(0,0,0,.06)'

const biradsCfg = s => {
  if (s<=2) return { pill:'green', accent:'#27B562', text:'#27500A', bg:'#EAF3DE', ring:'#27B562', dash:'10 100', barW:'8%',  label:'Bénin / probablement bénin' }
  if (s===3) return { pill:'amber', accent:'#F59E0B', text:'#633806', bg:'#FAEEDA', ring:'#F59E0B', dash:'45 100', barW:'45%', label:'Probablement bénin' }
  return         { pill:'red',   accent:'#E24B4A', text:'#791F1F', bg:'#FCEBEB', ring:'#E24B4A', dash:'92 100', barW:'95%', label:'Très suggestif de malignité' }
}

function Bar({ pct, color, height=5 }) {
  return (
    <div style={{height,background:'#EEEDE8',borderRadius:3,overflow:'hidden'}}>
      <div style={{height:'100%',width:`${Math.min(pct,100)}%`,background:color,borderRadius:3,transition:'width .7s ease'}}/>
    </div>
  )
}

function SecLabel({ children }) {
  return (
    <div style={{display:'flex',alignItems:'center',gap:'10px',margin:'20px 0 12px'}}>
      <span style={{fontSize:'10px',fontWeight:'700',textTransform:'uppercase',letterSpacing:'.09em',color:'#B4B2A9',whiteSpace:'nowrap'}}>{children}</span>
      <div style={{flex:1,height:'0.5px',background:'#E8E7E3'}}/>
    </div>
  )
}

function FindRow({ label, value, color, isLast }) {
  return (
    <div style={{display:'flex',gap:'16px',padding:'9px 16px',borderBottom:isLast?'none':'0.5px solid #F0EFE9',fontSize:'13px',lineHeight:'1.45',alignItems:'flex-start'}}>
      <span style={{color:'#888780',width:'34%',flexShrink:0,paddingTop:1}}>{label}</span>
      <span style={{fontWeight:'500',color:color||'#1a1a18',flex:1}}>{value}</span>
    </div>
  )
}

function Reco({ text, variant='green' }) {
  const cfg = variant==='green' ? {ibg:'#27B562'} : {ibg:'#F59E0B'}
  return (
    <div style={{display:'flex',gap:'10px',background:'#FAFAF9',borderRadius:'10px',padding:'10px 14px',fontSize:'13px',color:'#2C2C2A',lineHeight:'1.6',border:'0.5px solid #F0EFE9'}}>
      <div style={{width:20,height:20,borderRadius:'50%',flexShrink:0,marginTop:1,display:'flex',alignItems:'center',justifyContent:'center',background:cfg.ibg,color:'#fff'}}>
        {variant==='green' ? <Icon.check size={11} /> : <Icon.alertTriangle size={11} />}
      </div>
      <span>{text}</span>
    </div>
  )
}

function BiradsImageCard({ birads, preview, filename }) {
  if (!birads) return null
  const bc = biradsCfg(birads.birads_score)
  return (
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'14px'}}>
      {preview && (
        <div className="ap-card" style={{...CARD,boxShadow:CARD_SHADOW}}>
          <div style={CARD_HEAD}>
            <div style={LABEL_STYLE}><div style={{width:3,height:16,background:'#3B82F6',borderRadius:2}}/>Image analysée</div>
          </div>
          <div style={{padding:'16px'}}>
            <div style={{background:'#0D0D0D',borderRadius:'10px',overflow:'hidden',height:200,display:'flex',alignItems:'center',justifyContent:'center'}}>
              <img src={preview} style={{maxHeight:'100%',maxWidth:'100%',objectFit:'contain'}} alt="Mammographie"/>
            </div>
            <p style={{fontSize:'11px',color:'#B4B2A9',marginTop:'10px',textAlign:'center',fontFamily:'monospace',background:'#F9F9F7',padding:'5px 10px',borderRadius:'7px',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{filename}</p>
          </div>
        </div>
      )}
      <div className="ap-card" style={{...CARD,border:`0.5px solid ${bc.accent}40`,boxShadow:CARD_SHADOW}}>
        <div style={{...CARD_HEAD,background:`${bc.bg}99`}}>
          <div style={LABEL_STYLE}><div style={{width:3,height:16,background:bc.accent,borderRadius:2}}/>Score BI-RADS ACR</div>
          <span style={PILL(bc.pill)}>{birads.malignancy_risk}</span>
        </div>
        <div style={{padding:'16px'}}>
          <div style={{display:'flex',gap:'16px',alignItems:'center',background:bc.bg,borderRadius:'12px',padding:'14px 16px',marginBottom:'14px'}}>
            <div>
              <div style={{fontSize:'56px',fontWeight:'800',color:bc.text,lineHeight:1}}>{birads.birads_score}</div>
              <span style={{fontSize:'10px',fontWeight:'600',color:bc.text,opacity:.7,display:'block',marginTop:3}}>Score ACR</span>
            </div>
            <div style={{flex:1}}>
              <p style={{fontSize:'13px',fontWeight:'700',color:bc.text,margin:'0 0 4px',lineHeight:'1.35'}}>{bc.label}</p>
              <p style={{fontSize:'12px',color:bc.text,opacity:.75,margin:0,lineHeight:'1.4'}}>{birads.description}</p>
            </div>
            <svg width="54" height="54" viewBox="0 0 36 36" style={{transform:'rotate(-90deg)',flexShrink:0}}>
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#E8E7E3" strokeWidth="3.2"/>
              <circle cx="18" cy="18" r="15.9" fill="none" stroke={bc.ring} strokeWidth="3.2" strokeDasharray={bc.dash} strokeLinecap="round"/>
            </svg>
          </div>
          <div style={{borderTop:'0.5px solid #E8E7E3',paddingTop:'12px'}}>
            <div style={{display:'flex',justifyContent:'space-between',fontSize:'12px',marginBottom:'6px'}}>
              <span style={{color:'#888780'}}>Risque de malignité</span>
              <span style={{fontWeight:'700',color:bc.text}}>{birads.malignancy_risk}</span>
            </div>
            <Bar pct={parseInt(bc.barW)} color={bc.accent} height={4}/>
            <p style={{fontSize:'12px',color:'#5F5E5A',background:'#F9F9F7',borderRadius:'8px',padding:'9px 12px',margin:'12px 0 0',lineHeight:'1.55',border:'0.5px solid #F0EFE9'}}>{birads.recommendation}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function AIReportCard({ narrative, assembler, birads }) {
  if (!narrative) return null
  const isHigh = birads?.birads_score >= 4
  const stg = assembler?.stage
  const tsz = assembler?.tumorsize
  const loc = assembler?.localization

  return (
    <div className="ap-card" style={{...CARD,boxShadow:CARD_SHADOW}}>
      <div style={CARD_HEAD}>
        <div style={LABEL_STYLE}>
          <div style={{width:3,height:16,background:'#6D28D9',borderRadius:2}}/>
          Rapport d'analyse IA — Mammographie
        </div>
        <span style={PILL('purple')}>Généré par IA · PREMIER</span>
      </div>
      <div style={{padding:'20px'}}>
        <div style={{display:'grid',gridTemplateColumns:'repeat(4,minmax(0,1fr))',gap:'10px',marginBottom:'22px'}}>
          {[
            { label:'Résultat détection',  value:assembler?.detection?.predicted_class||'—',       sub:`Confiance ${Math.round((assembler?.detection?.confidence||0)*100)}%`,       color:assembler?.detection?.predicted_class==='Cancer'?'#791F1F':'#27500A',     bg:assembler?.detection?.predicted_class==='Cancer'?'#FCEBEB':'#EAF3DE',     bd:assembler?.detection?.predicted_class==='Cancer'?'#F09595':'#97C459' },
            { label:'Classification',       value:assembler?.classification?.predicted_class||'—',  sub:`Confiance ${Math.round((assembler?.classification?.confidence||0)*100)}%`,  color:assembler?.classification?.predicted_class==='Malignant'?'#791F1F':'#27500A', bg:assembler?.classification?.predicted_class==='Malignant'?'#FCEBEB':'#EAF3DE', bd:assembler?.classification?.predicted_class==='Malignant'?'#F09595':'#97C459' },
            { label:'Score BI-RADS',        value:birads?.birads_score?`Score ${birads.birads_score}`:'—', sub:birads?.malignancy_risk||'', color:isHigh?'#791F1F':'#27500A', bg:isHigh?'#FCEBEB':'#EAF3DE', bd:isHigh?'#F09595':'#97C459' },
            { label:'Stade TNM estimé',     value:stg?.stage||'—',                                  sub:stg?`${stg.t_stage}${stg.n_stage}${stg.m_stage}`:'',                        color:'#633806', bg:'#FAEEDA', bd:'#FAC775' },
          ].map((m,i) => (
            <div key={i} style={{background:m.bg,border:`0.5px solid ${m.bd}`,borderRadius:'11px',padding:'12px 14px'}}>
              <p style={{fontSize:'10px',fontWeight:'600',textTransform:'uppercase',letterSpacing:'.07em',color:m.color,opacity:.7,margin:'0 0 5px'}}>{m.label}</p>
              <p style={{fontSize:'16px',fontWeight:'800',color:m.color,margin:'0 0 2px',lineHeight:1.2}}>{m.value}</p>
              {m.sub && <p style={{fontSize:'11px',color:m.color,opacity:.75,margin:0}}>{m.sub}</p>}
            </div>
          ))}
        </div>

        {(loc||tsz) && (
          <div style={{display:'grid',gridTemplateColumns:loc&&tsz?'1fr 1fr':'1fr',gap:'10px',marginBottom:'22px'}}>
            {loc && (
              <div style={{background:'#E6F1FB',border:'0.5px solid #85B7EB',borderRadius:'11px',padding:'12px 16px',display:'flex',gap:'14px',alignItems:'center'}}>
                <div style={{color:'#0C447C',flexShrink:0,display:'flex'}}><Icon.target size={26} /></div>
                <div>
                  <p style={{fontSize:'10px',fontWeight:'700',textTransform:'uppercase',letterSpacing:'.08em',color:'#0C447C',margin:'0 0 3px'}}>Localisation tumorale</p>
                  <p style={{fontSize:'15px',fontWeight:'700',color:'#0C447C',margin:'0 0 1px'}}>{loc.quadrant_fr}</p>
                  <p style={{fontSize:'11px',color:'#185FA5',margin:0}}>Confiance {Math.round((loc.confidence||0)*100)}%</p>
                </div>
              </div>
            )}
            {tsz && (
              <div style={{background:'#FAEEDA',border:'0.5px solid #FAC775',borderRadius:'11px',padding:'12px 16px',display:'flex',gap:'14px',alignItems:'center'}}>
                <div style={{color:'#633806',flexShrink:0,display:'flex'}}><Icon.ruler size={26} /></div>
                <div>
                  <p style={{fontSize:'10px',fontWeight:'700',textTransform:'uppercase',letterSpacing:'.08em',color:'#633806',margin:'0 0 3px'}}>Taille tumorale estimée</p>
                  <p style={{fontSize:'15px',fontWeight:'700',color:'#633806',margin:'0 0 1px'}}>{tsz.diameter_cm} cm de diamètre</p>
                  <p style={{fontSize:'11px',color:'#854F0B',margin:0}}>{tsz.tnm_stage} — {tsz.tnm_desc}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {narrative.findings?.length > 0 && (
          <>
            <SecLabel>Constatations détaillées</SecLabel>
            <div style={{background:'#FAFAF9',borderRadius:'11px',overflow:'hidden',border:'0.5px solid #F0EFE9'}}>
              {narrative.findings.map((f,i) => {
                const idx = f.indexOf(':')
                const hasColon = idx>0 && idx<50
                const k = hasColon ? f.slice(0,idx).trim() : null
                const v = hasColon ? f.slice(idx+1).trim() : f
                return <FindRow key={i} label={k||'—'} value={v} isLast={i===narrative.findings.length-1} color={k?undefined:'#2C2C2A'}/>
              })}
            </div>
          </>
        )}

        {assembler?.quality_warnings?.length > 0 && (
          <div style={{marginTop:'16px',background:'#FAEEDA',border:'0.5px solid #FAC775',borderRadius:'10px',padding:'12px 14px',display:'flex',flexDirection:'column',gap:'6px'}}>
            {assembler.quality_warnings.map((w,i) => (
              <div key={i} style={{fontSize:'12px',color:'#633806',display:'flex',gap:'8px',lineHeight:'1.5'}}>
                <span style={{flexShrink:0,marginTop:1,display:'flex'}}><Icon.alertTriangle /></span><span>{w}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function RadiologistReport({ value, onChange }) {
  const today = new Date().toLocaleDateString('fr-FR',{day:'2-digit',month:'long',year:'numeric'})
  return (
    <div className="ap-card" style={{...CARD,boxShadow:CARD_SHADOW}}>
      <div style={{...CARD_HEAD,background:'#EEF3FB'}}>
        <div style={LABEL_STYLE}>
          <div style={{width:3,height:16,background:'#1B4F9B',borderRadius:2}}/>
          Rapport du médecin radiologue
        </div>
        <span style={{...PILL('blue'),fontSize:'10px'}}>{today}</span>
      </div>
      <div style={{padding:'20px'}}>
        <div style={{background:'#EEF3FB',borderRadius:'10px',padding:'12px 16px',marginBottom:'16px',border:'0.5px solid #C7D7F8'}}>
          <p style={{fontSize:'12px',color:'#0C447C',margin:0,lineHeight:'1.6'}}>
            <strong>Section réservée au radiologue</strong> — Saisissez votre interprétation clinique, vos observations supplémentaires, ou votre décision de prise en charge.
          </p>
        </div>
        <label style={{display:'block',fontSize:'11px',fontWeight:'600',color:'#5F5E5A',textTransform:'uppercase',letterSpacing:'.07em',marginBottom:'6px'}}>
          Observations &amp; notes complémentaires
        </label>
        <textarea
          value={value}
          onChange={e=>onChange(e.target.value)}
          rows={5}
          placeholder="Ex : Corrélation clinique recommandée. Antécédents familiaux à prendre en compte..."
          style={{width:'100%',boxSizing:'border-box',border:'1px solid #C7D7F8',borderRadius:'9px',padding:'12px 14px',fontSize:'13px',fontFamily:'inherit',color:'#1a1a18',background:'#FAFCFF',resize:'vertical',lineHeight:'1.6',outline:'none',minHeight:'110px'}}
        />
      </div>
    </div>
  )
}

// ─── PDF ──────────────────────────────────────────────────────────────────────
async function generatePDF(patient, result, remarque, gradcamHtml, previewBase64) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const W = 210, M = 20
  let y = 0

  const today = new Date().toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' })
  const asm = result?.assembler_report
  const bir = result?.birads

  const checkPage = (need = 20) => {
    if (y + need > 268) { doc.addPage(); y = 30 }
  }

  const drawPageHeader = async () => {
    doc.setDrawColor(200, 200, 200); doc.setLineWidth(0.3); doc.line(M, 8, W - M, 8)
    try {
      const logoUrl  = new URL('../assets/logo-chu.png', import.meta.url).href
      const response = await fetch(logoUrl)
      const blob     = await response.blob()
      const b64      = await new Promise(r => { const rd = new FileReader(); rd.onload = () => r(rd.result); rd.readAsDataURL(blob) })
      doc.addImage(b64, 'PNG', M, 10, 28, 12, undefined, 'FAST')
    } catch {
      doc.setFont('helvetica', 'bold'); doc.setFontSize(10); doc.setTextColor(27, 79, 155); doc.text('CHU', M, 18)
    }
    doc.setFont('helvetica', 'bold'); doc.setFontSize(9); doc.setTextColor(60, 60, 60)
    doc.text('COMPTE-RENDU DE MAMMOGRAPHIE', W / 2, 14, { align: 'center' })
    doc.setFont('helvetica', 'normal'); doc.setFontSize(7.5); doc.setTextColor(120, 120, 120)
    doc.text('Centre Hospitalier Universitaire Mohammed VI · Oujda', W / 2, 19, { align: 'center' })
    doc.text(today, W - M, 14, { align: 'right' })
    doc.setDrawColor(200, 200, 200); doc.setLineWidth(0.3); doc.line(M, 24, W - M, 24)
    y = 32
  }

  const drawFooter = (pageNum, total) => {
    doc.setDrawColor(200, 200, 200); doc.setLineWidth(0.3); doc.line(M, 280, W - M, 280)
    doc.setFont('helvetica', 'normal'); doc.setFontSize(7); doc.setTextColor(150, 150, 150)
    doc.text('Plateforme IA Mammographie · CHU Mohammed VI Oujda', M, 285)
    doc.text(`Page ${pageNum} / ${total}`, W - M, 285, { align: 'right' })
    doc.text(`Réf. RPT-${patient?.cin || 'XXX'}-${Date.now().toString().slice(-5)}`, W / 2, 290, { align: 'center' })
  }

  const sectionTitle = (title) => {
    checkPage(14)
    doc.setFont('helvetica', 'bold'); doc.setFontSize(8.5); doc.setTextColor(40, 40, 40)
    doc.text(title, M, y)
    doc.setDrawColor(180, 180, 180); doc.setLineWidth(0.3); doc.line(M, y + 1.5, W - M, y + 1.5)
    y += 8
  }

  await drawPageHeader()

  sectionTitle('IDENTITÉ DE LA PATIENTE')
  const patientRows = [
    ['CIN',               patient?.cin || '—'],
    ['Nom et prénom',     `${patient?.prenom || ''} ${patient?.nom || ''}`],
    ['Date de naissance', patient?.dateNaissance || '—'],
    ['Téléphone',         patient?.telephone || '—'],
    ['Date d\'examen',    today],
    ['Côté examiné',      patient?.cote || '—'],
  ]
  patientRows.forEach(([k, v], i) => {
    checkPage(7)
    if (i % 2 === 0) { doc.setFillColor(248, 248, 248); doc.rect(M, y - 4, W - M * 2, 7, 'F') }
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5); doc.setTextColor(100, 100, 100); doc.text(k, M + 2, y)
    doc.setFont('helvetica', 'bold'); doc.setTextColor(30, 30, 30); doc.text(String(v), M + 55, y)
    y += 7
  })
  y += 8

  checkPage(40)
  sectionTitle('MÉTRIQUES D\'ANALYSE')
  const metrics = []
  if (result?.predicted_class) metrics.push(['Diagnostic IA',   result.predicted_class,                              `Confiance ${Math.round((result.confidence || 0) * 100)}%`])
  if (bir?.birads_score)        metrics.push(['Score BI-RADS',   `Score ${bir.birads_score}`,                         bir.malignancy_risk || ''])
  if (asm?.stage?.stage)        metrics.push(['Stade TNM',       asm.stage.stage,                                     `${asm.stage.t_stage || ''}${asm.stage.n_stage || ''}${asm.stage.m_stage || ''}`])
  if (asm?.localization)        metrics.push(['Localisation',    asm.localization.quadrant_fr || '—',                 `Confiance ${Math.round((asm.localization.confidence || 0) * 100)}%`])
  if (asm?.tumorsize)           metrics.push(['Taille estimée',  `${asm.tumorsize.diameter_cm} cm`,                  asm.tumorsize.tnm_stage || ''])
  if (bir?.recommendation)      metrics.push(['Recommandation',  bir.recommendation,                                  ''])

  doc.setFillColor(235, 235, 235); doc.rect(M, y, W - M * 2, 7, 'F')
  doc.setFont('helvetica', 'bold'); doc.setFontSize(7.5); doc.setTextColor(60, 60, 60)
  doc.text('Paramètre', M + 3, y + 5); doc.text('Valeur', M + 55, y + 5); doc.text('Détail', M + 120, y + 5)
  y += 7

  metrics.forEach(([param, val, detail], i) => {
    checkPage(9)
    const valLines    = doc.splitTextToSize(val    || '', 58)
    const detailLines = doc.splitTextToSize(detail || '', 48)
    const rowH        = Math.max(valLines.length, detailLines.length) * 5 + 4
    if (i % 2 === 0) { doc.setFillColor(250, 250, 250); doc.rect(M, y, W - M * 2, rowH, 'F') }
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5); doc.setTextColor(90, 90, 90); doc.text(param, M + 3, y + 5)
    doc.setFont('helvetica', 'bold'); doc.setTextColor(30, 30, 30); doc.text(valLines, M + 55, y + 5)
    doc.setFont('helvetica', 'normal'); doc.setFontSize(7.5); doc.setTextColor(120, 120, 120)
    if (detail) doc.text(detailLines, M + 120, y + 5)
    y += rowH
  })
  y += 8

  checkPage(75)
  sectionTitle('VISUALISATION — IMAGE MAMMOGRAPHIQUE')

  try {
    const iW = W - M * 2
    const iH = 60

    doc.setFillColor(252, 252, 252)
    doc.setDrawColor(210, 210, 210)
    doc.setLineWidth(0.3)
    doc.roundedRect(M, y - 2, iW, iH + 14, 2, 2, 'FD')

    if (gradcamHtml) {
      const gDoc = new DOMParser().parseFromString(gradcamHtml, 'text/html')
      const imgs = gDoc.querySelectorAll('img')
      const lbls = ['Image originale', 'Mammographie + Grad-CAM', 'Carte thermique', 'Zone suspecte']
      const n    = Math.min(imgs.length, 4)
      const imgW = (iW - (n - 1) * 4 - 4) / n
      let xi = M + 2

      for (let i = 0; i < n; i++) {
        const src = imgs[i]?.src || imgs[i]?.getAttribute('src') || ''
        if (src.startsWith('data:')) {
          try { doc.addImage(src, src.includes('png') ? 'PNG' : 'JPEG', xi, y + 2, imgW, iH, undefined, 'FAST') } catch {}
        }
        doc.setFont('helvetica', 'normal'); doc.setFontSize(6.5); doc.setTextColor(100, 100, 100)
        doc.text(lbls[i] || '', xi + imgW / 2, y + iH + 10, { align: 'center' })
        xi += imgW + 4
      }
    } else if (previewBase64) {
      const imgW = 80
      const imgX = M + (iW - imgW) / 2
      try {
        doc.addImage(previewBase64, 'JPEG', imgX, y + 2, imgW, iH - 4, undefined, 'FAST')
      } catch {
        try { doc.addImage(previewBase64, 'PNG', imgX, y + 2, imgW, iH - 4, undefined, 'FAST') } catch {}
      }
      doc.setFont('helvetica', 'normal'); doc.setFontSize(6.5); doc.setTextColor(100, 100, 100)
      doc.text('Image mammographique originale', W / 2, y + iH + 10, { align: 'center' })
    }

    y += iH + 22
  } catch {}

  checkPage(55)
  sectionTitle('RAPPORT DU MÉDECIN RADIOLOGUE')

  const rTxt   = remarque?.trim() || '— Aucune observation saisie —'
  const rLines = doc.splitTextToSize(rTxt, W - M * 2 - 8)
  const rH     = Math.max(rLines.length * 5.5 + 14, 40)
  doc.setFillColor(252, 252, 252); doc.setDrawColor(180, 180, 180); doc.setLineWidth(0.4)
  doc.roundedRect(M, y, W - M * 2, rH, 2, 2, 'FD')
  doc.setFont('helvetica', 'normal'); doc.setFontSize(9); doc.setTextColor(30, 30, 30)
  doc.text(rLines, M + 5, y + 8)
  y += rH + 16

  checkPage(24)
  const sigX = W - M - 70
  doc.setDrawColor(120, 120, 120); doc.setLineWidth(0.4); doc.line(sigX, y, W - M, y)
  doc.setFont('helvetica', 'normal'); doc.setFontSize(7.5); doc.setTextColor(100, 100, 100)
  doc.text('Signature', sigX, y + 5)
  y += 20

  const totalPages = doc.internal.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) { doc.setPage(i); drawFooter(i, totalPages) }

  return doc.output('datauristring')
}

// ─── Page principale ──────────────────────────────────────────────────────────
export default function AnalyzePage({ state, setState, patient, onReset, onEditPatient, user }) {
  // ✅ FIX : `saved` et `remarque` viennent maintenant du state PARTAGÉ (parent),
  // donc ils survivent à la navigation entre pages (Dashboard / Rapports / Historique).
  // Avant, ils étaient en useState local et se réinitialisaient à chaque remount
  // du composant, ce qui réaffichait "Rapport enregistré" -> redonnait l'impression
  // que tout se regénérait, et permettait un double-enregistrement.
  const {
    result, loading, error, preview, gradcam, loadingGradcam, currentFile,
    saved = false,
    remarque = '',
  } = state
  const set = p => setState(prev=>({...prev,...p}))

  const [dragging,    setDragging] = useState(false)
  const [loadingStep, setLS]       = useState(0)
  const [saving,      setSaving]   = useState(false) // transitoire : ok de rester local
  const [toast,       setToast]    = useState(null)

  // setters qui écrivent dans le state partagé au lieu d'un state local
  const setSaved    = v => set({ saved: v })
  const setRemarque = v => set({ remarque: v })

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const AI_STEPS   = ['Détection','Classification','BI-RADS','Narrative']
  const globalStep = saved ? 5 : result ? 4 : loading ? 3 : 2

  const handleFile = async file => {
    if (!file||!file.type.startsWith('image/')) return
    // ✅ saved et remarque réinitialisés ICI dans le state partagé,
    // uniquement quand une VRAIE nouvelle analyse démarre.
    set({loading:true,error:null,result:null,gradcam:null,preview:URL.createObjectURL(file),currentFile:file,saved:false,remarque:''})
    setLS(0)
    const iv = setInterval(()=>setLS(s=>s<AI_STEPS.length-1?s+1:s),1400)
    try   { set({result:await analyzeMammography(file)}) }
    catch { set({error:'Erreur connexion Spring Boot :8080'}) }
    finally { clearInterval(iv); set({loading:false}); setLS(0) }
  }

  const handleGradcam = async () => {
    if (!currentFile) return
    set({loadingGradcam:true,error:null})
    try   { set({gradcam:await analyzeGradcam(currentFile)}) }
    catch { set({error:'Erreur Grad-CAM — vérifiez le service :8011'}) }
    finally { set({loadingGradcam:false}) }
  }

  const handleSave = async () => {
    // ✅ Garde-fou : si déjà sauvegardé (même après un retour de navigation),
    // on bloque tout nouvel enregistrement -> plus de doublon en base.
    if (saved || saving) return
    setSaving(true)
    try {
      let b64 = null
      if (currentFile) b64 = await new Promise((r, j) => {
        const rd = new FileReader()
        rd.onload  = () => r(rd.result)
        rd.onerror = () => j(new Error('Lecture fichier échouée'))
        rd.readAsDataURL(currentFile)
      })
      const pdfDataUri = await generatePDF(patient, result, remarque, gradcam, b64)
      await saveRapport(patient, result, remarque, pdfDataUri, user?.id)
      setSaved(true) // écrit maintenant dans le state PARTAGÉ -> survit à la navigation
      showToast('Rapport enregistré avec succès', 'success')
    } catch (e) {
      showToast('Erreur lors de l\'enregistrement : ' + e.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const reset = () => {
    set({result:null,preview:null,error:null,gradcam:null,currentFile:null,saved:false,remarque:''})
    if (onReset) onReset()
  }

  const isCanc = result?.predicted_class==='Cancer'
  const birads = result?.birads
  const asm    = result?.assembler_report
  const nar    = result?.narrative

  return (
    <div style={{fontFamily:"'DM Sans','Segoe UI',sans-serif",minHeight:'100vh',background:'#F7F9FC'}}>
      <style>{`
        @keyframes spin    { to { transform: rotate(360deg); } }
        @keyframes shimmer { 0%{transform:translateX(-100%)} 100%{transform:translateX(100%)} }
        @keyframes fadeUp  { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
        @keyframes toastIn { from { opacity:0; transform:translate(12px,-6px); } to { opacity:1; transform:translate(0,0); } }
        .ap-fade   { animation: fadeUp 0.4s ease both; }
        .ap-card   { transition: box-shadow 0.2s ease, border-color 0.2s ease; }
        .ap-card:hover { box-shadow: 0 4px 16px rgba(15,30,60,0.06); }
        .ap-dropzone { transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease; }
        .ap-dropzone:hover { box-shadow: 0 4px 16px rgba(15,30,60,0.07); }
        .ap-btn { transition: box-shadow 0.2s ease, transform 0.12s ease, background 0.2s ease, opacity 0.2s ease; }
        .ap-btn:hover:not(:disabled) { transform: translateY(-1px); }
        .ap-btn:active:not(:disabled) { transform: translateY(0) scale(0.98); }
        .ap-btn-primary:hover:not(:disabled) { box-shadow: 0 6px 18px rgba(27,79,155,0.38); }
        .ap-btn-purple:hover:not(:disabled) { box-shadow: 0 5px 16px rgba(109,40,217,0.4); }
        .ap-btn-save:hover:not(:disabled) { box-shadow: 0 6px 20px rgba(245,166,35,0.5); }
        .ap-btn-close { transition: background 0.15s ease, border-color 0.15s ease; }
        .ap-btn-close:hover { background: #F1EFE8; border-color: #D3D1C7; }
        .ap-toast { animation: toastIn 0.25s ease both; }
      `}</style>

      {/* Toast */}
      {toast && (
        <div className="ap-toast" style={{position:'fixed',top:20,right:20,zIndex:9999,display:'flex',alignItems:'center',gap:8,background:toast.type==='success'?'#16A34A':toast.type==='error'?'#DC2626':'#1B4F9B',color:'#fff',padding:'12px 20px',borderRadius:10,fontSize:13,fontWeight:600,boxShadow:'0 4px 20px rgba(0,0,0,0.2)'}}>
          {toast.type==='success' && <Icon.check size={15} />}
          {toast.type==='error' && <Icon.alertTriangle size={15} />}
          {toast.msg}
        </div>
      )}

      {/* HERO BANNER */}
      <div className="ap-fade" style={{background:'linear-gradient(135deg,#1B4F9B 0%,#153d7a 55%,#0f2d5c 100%)',borderRadius:16,padding:'24px 32px',marginBottom:24,position:'relative',overflow:'hidden'}}>
        <div style={{position:'absolute',right:-40,top:-40,width:180,height:180,borderRadius:'50%',background:'rgba(255,255,255,0.04)'}}/>
        <div style={{position:'relative',display:'flex',alignItems:'center',justifyContent:'space-between',gap:16}}>
          <div style={{flex:1}}>
            <div style={{marginBottom:8}}>
              <span style={{display:'inline-flex',alignItems:'center',gap:6,background:'rgba(245,166,35,0.2)',color:'#F5A623',border:'1px solid rgba(245,166,35,0.3)',fontSize:10,fontWeight:700,padding:'4px 12px',borderRadius:9999,letterSpacing:'0.08em'}}>
                <Icon.sparkle /> ANALYSE MAMMOGRAPHIQUE · CHU MOHAMMED VI
              </span>
            </div>
            <h1 style={{display:'flex',alignItems:'center',gap:9,fontSize:20,fontWeight:700,color:'#fff',margin:'0 0 4px'}}>
              {saved
                ? (<><Icon.checkCircle size={19} />Rapport enregistré</>)
                : result
                  ? (<><Icon.report size={19} />Résultats de l'analyse IA</>)
                  : loading
                    ? (<><Icon.microscope size={19} />Analyse en cours…</>)
                    : (<><Icon.scan size={19} />Chargement mammographie</>)
              }
            </h1>
            <p style={{color:'rgba(255,255,255,0.6)',fontSize:13,margin:0}}>
              Pipeline IA — Détection · Classification · BI-RADS · Rapport
            </p>
            {patient && (
              <div style={{display:'inline-flex',alignItems:'center',gap:16,marginTop:12,background:'rgba(255,255,255,0.12)',borderRadius:10,padding:'8px 16px',border:'1px solid rgba(255,255,255,0.15)'}}>
                <span style={{display:'flex',alignItems:'center',gap:6,fontSize:12,color:'#fff',fontWeight:700}}><Icon.user />{patient.prenom} {patient.nom}</span>
                <span style={{fontSize:11,color:'rgba(255,255,255,0.6)'}}>CIN : {patient.cin}</span>
                <span style={{fontSize:11,color:'rgba(255,255,255,0.6)'}}>Née : {patient.dateNaissance}</span>
                {patient.cote && <span style={{fontSize:11,color:'rgba(255,255,255,0.6)'}}>Côté : {patient.cote}</span>}
              </div>
            )}
          </div>
          <PipelineSteps currentStep={globalStep} />
        </div>
      </div>

      {/* ZONE UPLOAD */}
      {!result && (
        <>
          <div
            className="ap-dropzone"
            onDragOver={e=>{e.preventDefault();setDragging(true)}}
            onDragLeave={()=>setDragging(false)}
            onDrop={e=>{e.preventDefault();setDragging(false);handleFile(e.dataTransfer.files[0])}}
            onClick={()=>!loading&&document.getElementById('fileInput').click()}
            style={{border:`2px dashed ${dragging?'#1B4F9B':'#D1D9E6'}`,borderRadius:16,padding:'64px 40px',textAlign:'center',cursor:loading?'default':'pointer',background:dragging?'#EEF3FB':'#fff',boxShadow:'0 1px 3px rgba(0,0,0,0.06)', marginBottom: 16}}
          >
            <input id="fileInput" type="file" accept="image/*" style={{display:'none'}} onChange={e=>handleFile(e.target.files[0])}/>
            {loading ? (
              <div>
                {preview && <img src={preview} style={{width:80,height:80,objectFit:'contain',borderRadius:14,opacity:.4,margin:'0 auto 16px',display:'block'}}/>}
                <div style={{position:'relative',width:44,height:44,margin:'0 auto 16px'}}>
                  <div style={{position:'absolute',inset:0,borderRadius:'50%',border:'3px solid #EEF3FB'}}/>
                  <div style={{position:'absolute',inset:0,borderRadius:'50%',border:'3px solid transparent',borderTopColor:'#1B4F9B',animation:'spin 1s linear infinite'}}/>
                </div>
                <p style={{color:'#1B4F9B',fontWeight:700,marginBottom:16,fontSize:15}}>Analyse en cours…</p>
                <div style={{display:'flex',justifyContent:'center',gap:8,flexWrap:'wrap'}}>
                  {AI_STEPS.map((s,i)=>(
                    <div key={i} style={{display:'flex',alignItems:'center',gap:6,fontSize:12,padding:'6px 14px',borderRadius:20,background:i<=loadingStep?'#1B4F9B':'#F8FAFC',color:i<=loadingStep?'#fff':'#94A3B8',border:`1px solid ${i<=loadingStep?'#1B4F9B':'#E2E8F0'}`,transition:'all .4s',fontWeight:600}}>
                      {i<loadingStep && <Icon.check size={10} />}
                      {s}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div>
                <div style={{width:64,height:64,borderRadius:18,background:'linear-gradient(135deg,#1B4F9B,#153d7a)',display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 20px',boxShadow:'0 8px 24px rgba(27,79,155,0.3)',color:'#fff'}}>
                  <Icon.scan size={28} />
                </div>
                <p style={{color:'#1a1a2e',fontWeight:700,fontSize:16,marginBottom:6}}>Glisser une mammographie ici</p>
                <p style={{fontSize:13,color:'#94A3B8',marginBottom:16}}>ou cliquer pour sélectionner un fichier</p>
                <div style={{display:'inline-flex',alignItems:'center',gap:8}}>
                  {['JPG','PNG','DICOM'].map(f=>(
                    <span key={f} style={{fontSize:11,color:'#94A3B8',background:'#F8FAFC',border:'1px solid #E2E8F0',borderRadius:6,padding:'4px 10px',fontWeight:600}}>{f}</span>
                  ))}
                  <span style={{fontSize:11,color:'#94A3B8'}}>max 50 MB</span>
                </div>
              </div>
            )}
          </div>

          {!loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="ap-btn ap-btn-primary"
                onClick={onEditPatient}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  background: 'linear-gradient(135deg,#1B4F9B,#153d7a)', color: '#fff',
                  border: 'none',
                  padding: '11px 24px', borderRadius: 10, fontSize: 13, fontWeight: 700,
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(27,79,155,0.3)',
                }}
              >
                <Icon.arrowLeft />
                Modifier les informations patient
              </button>
            </div>
          )}
        </>
      )}

      {error && (
        <div style={{marginTop:12,display:'flex',alignItems:'center',gap:10,background:'#FCEBEB',border:'0.5px solid #F09595',color:'#791F1F',fontSize:13,padding:'10px 14px',borderRadius:10}}>
          <Icon.alertCircle />
          {error}
        </div>
      )}

      {result && (
        <div style={{display:'flex',flexDirection:'column',gap:18}}>
          <div className="ap-card" style={{display:'flex',alignItems:'center',gap:10,flexWrap:'wrap',background:'#fff',borderRadius:14,border:'0.5px solid #E8E7E3',padding:'14px 18px',boxShadow:CARD_SHADOW}}>
            <div style={{display:'flex',alignItems:'center',gap:8,padding:'9px 18px',borderRadius:10,background:isCanc?'#FCEBEB':'#EAF3DE',fontWeight:800,fontSize:14,color:isCanc?'#791F1F':'#27500A'}}>
              <span style={{width:8,height:8,borderRadius:'50%',background:isCanc?'#E24B4A':'#27B562',display:'inline-block'}}/>
              {result.predicted_class}
            </div>
            <div style={{display:'flex',alignItems:'center',gap:6,background:'#F8FAFC',padding:'9px 14px',borderRadius:10,fontSize:13,color:'#5F5E5A',border:'0.5px solid #E2E8F0'}}>
              Confiance : <strong style={{color:'#1B4F9B',marginLeft:3}}>{(result.confidence*100).toFixed(1)}%</strong>
            </div>
            {birads && (
              <div style={{display:'flex',alignItems:'center',gap:6,background:'#F8FAFC',padding:'9px 14px',borderRadius:10,fontSize:13,color:'#5F5E5A',border:'0.5px solid #E2E8F0'}}>
                BI-RADS : <strong style={{color:'#1B4F9B',marginLeft:3}}>Score {birads.birads_score}</strong>
              </div>
            )}
            {result?.predicted_class !== 'Non-Cancer' && (
              <button className="ap-btn ap-btn-purple" onClick={handleGradcam} disabled={loadingGradcam}
                style={{display:'flex',alignItems:'center',gap:7,background:'#6D28D9',color:'#fff',border:'none',padding:'9px 18px',borderRadius:10,fontSize:13,fontWeight:600,cursor:loadingGradcam?'wait':'pointer',opacity:loadingGradcam?.7:1,boxShadow:'0 3px 10px rgba(109,40,217,.3)'}}>
                {loadingGradcam
                  ?<><span style={{width:13,height:13,border:'2px solid rgba(255,255,255,.3)',borderTopColor:'#fff',borderRadius:'50%',display:'inline-block',animation:'spin 1s linear infinite'}}/>Génération…</>
                  :<><Icon.eye />Grad-CAM</>}
              </button>
            )}
            <button className="ap-btn ap-btn-primary" onClick={reset}
              style={{marginLeft:'auto',display:'flex',alignItems:'center',gap:7,background:'linear-gradient(135deg,#1B4F9B,#153d7a)',color:'#fff',border:'none',padding:'9px 18px',borderRadius:10,fontSize:13,fontWeight:600,cursor:'pointer',boxShadow:'0 3px 10px rgba(27,79,155,.3)'}}>
              <Icon.plus />
              Nouvelle analyse
            </button>
          </div>

          <BiradsImageCard birads={birads} preview={preview} filename={result.filename}/>

          {gradcam && (
            <div className="ap-card" style={{...CARD,border:'0.5px solid #DDD8FC',boxShadow:CARD_SHADOW}}>
              <div style={{...CARD_HEAD,background:'#EEEDFE'}}>
                <div style={{...LABEL_STYLE,color:'#3C3489'}}><div style={{width:3,height:16,background:'#6D28D9',borderRadius:2}}/>Visualisation Grad-CAM — zones suspectes</div>
                <button className="ap-btn-close" onClick={()=>set({gradcam:null})} style={{display:'flex',alignItems:'center',gap:5,fontSize:12,color:'#888780',background:'none',border:'0.5px solid #E8E7E3',padding:'5px 11px',borderRadius:7,cursor:'pointer'}}>
                  Fermer <Icon.x />
                </button>
              </div>
              <div style={{padding:16}}>
                <iframe srcDoc={gradcam} style={{width:'100%',height:500,border:'none',borderRadius:10}} title="Grad-CAM" sandbox="allow-scripts"/>
              </div>
            </div>
          )}

          <AIReportCard narrative={nar} assembler={asm} birads={birads}/>
          <RadiologistReport value={remarque} onChange={setRemarque}/>

          <div style={{background:'linear-gradient(135deg,#1B4F9B,#153d7a)',borderRadius:16,padding:'20px 28px',display:'flex',alignItems:'center',justifyContent:'space-between',gap:16,boxShadow:'0 8px 32px rgba(27,79,155,0.25)'}}>
            <div>
              <p style={{display:'flex',alignItems:'center',gap:7,fontSize:15,fontWeight:700,color:'#fff',margin:'0 0 3px'}}>
                {saved ? (<><Icon.checkCircle size={16} />Rapport enregistré avec succès</>) : 'Enregistrer & générer le PDF'}
              </p>
              <p style={{fontSize:12,color:'rgba(255,255,255,0.6)',margin:0}}>
                {saved ? 'Consultez le rapport dans la section "Rapports".' : 'Le rapport complet sera sauvegardé et accessible dans Rapports.'}
              </p>
            </div>
            <button className="ap-btn ap-btn-save" onClick={handleSave} disabled={saving || saved}
              style={{display:'flex',alignItems:'center',gap:9,background:saved?'#16A34A':'#F5A623',color:'#fff',border:'none',padding:'13px 32px',borderRadius:12,fontSize:14,fontWeight:700,cursor:(saving||saved)?'default':'pointer',boxShadow:saved?'0 4px 16px rgba(22,163,74,.4)':'0 4px 16px rgba(245,166,35,.4)',whiteSpace:'nowrap',flexShrink:0}}>
              {saving
                ?<><span style={{width:15,height:15,border:'2px solid rgba(255,255,255,.35)',borderTopColor:'#fff',borderRadius:'50%',display:'inline-block',animation:'spin 1s linear infinite'}}/>Enregistrement…</>
                :saved
                  ?<><Icon.check />Enregistré — voir dans Rapports</>
                  :<><Icon.checkCircle />Enregistrer &amp; PDF</>}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
