import { jsPDF } from 'jspdf'
import { useState, useEffect } from 'react'

async function buildPDF(rapport) {
  const { patient, result, remarque, preview, date, gradcamHtml } = rapport
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const W = 210, margin = 18
  let y = 0
  const today = new Date(date).toLocaleDateString('fr-FR', { day:'2-digit', month:'long', year:'numeric' })
  const assembler = result?.assembler_report
  const birads    = result?.birads
  const narrative = result?.narrative
  const isCanc    = result?.predicted_class === 'Cancer'

  // ── Header ──
  doc.setFillColor(27,79,155); doc.rect(0,0,W,22,'F')
  doc.setFontSize(14); doc.setFont('helvetica','bold'); doc.setTextColor(255,255,255)
  doc.text('PREMIER — Plateforme IA Mammographie', margin, 10)
  doc.setFontSize(8); doc.setFont('helvetica','normal')
  doc.text('CHU Mohammed VI Oujda', margin, 16)
  doc.text(`Rapport généré le ${today}`, W-margin, 16, { align:'right' })
  y = 30

  // ── Patiente ──
  doc.setFillColor(240,244,250); doc.roundedRect(margin,y,W-margin*2,32,3,3,'F')
  doc.setFontSize(9); doc.setFont('helvetica','bold'); doc.setTextColor(27,79,155)
  doc.text('INFORMATIONS DE LA PATIENTE', margin+4, y+7)
  doc.setFont('helvetica','normal'); doc.setTextColor(30,30,30)
  const c2 = W/2+4
  doc.text(`CIN : ${patient?.cin||'—'}`, margin+4, y+15)
  doc.text(`Nom : ${patient?.prenom||''} ${patient?.nom||''}`, margin+4, y+22)
  doc.text(`Date de naissance : ${patient?.dateNaissance||'—'}`, margin+4, y+29)
  doc.text(`Téléphone : ${patient?.telephone||'—'}`, c2, y+15)
  doc.text(`Côté : ${patient?.cote||'—'}`, c2, y+22)
  doc.text(`Date examen : ${today}`, c2, y+29)
  y += 40

  // ── Image mammographie ──
  if (preview) {
    try {
      doc.setFont('helvetica','bold'); doc.setFontSize(10); doc.setTextColor(27,79,155)
      doc.text('IMAGE MAMMOGRAPHIE', margin, y)
      doc.setDrawColor(27,79,155); doc.line(margin, y+1.5, W-margin, y+1.5); y+=6
      doc.addImage(preview,'JPEG',margin,y,W-margin*2,60,undefined,'FAST'); y+=68
    } catch(e) { console.warn('image:', e) }
  }

  // ── Résultat ──
  doc.setFillColor(isCanc?252:234,isCanc?235:243,isCanc?235:222)
  doc.roundedRect(margin,y,W-margin*2,24,3,3,'F')
  doc.setFont('helvetica','bold'); doc.setFontSize(11)
  doc.setTextColor(isCanc?121:39,isCanc?31:80,isCanc?31:10)
  doc.text(`Résultat IA : ${result?.predicted_class||'—'}`, margin+4, y+9)
  doc.setFont('helvetica','normal'); doc.setFontSize(9)
  doc.text(`Confiance : ${Math.round((result?.confidence||0)*100)}%   |   BI-RADS : ${birads?.birads_score||'—'}   |   Risque : ${birads?.malignancy_risk||'—'}`, margin+4, y+18)
  y += 30

  // ── BI-RADS ──
  if (birads) {
    doc.setFont('helvetica','bold'); doc.setFontSize(10); doc.setTextColor(27,79,155)
    doc.text('SCORE BI-RADS', margin, y)
    doc.setDrawColor(27,79,155); doc.line(margin,y+1.5,W-margin,y+1.5); y+=7
    doc.setFont('helvetica','normal'); doc.setFontSize(9); doc.setTextColor(50,50,50)
    doc.text(`Score ACR : ${birads.birads_score}  —  ${birads.description}`, margin, y); y+=6
    doc.text(`Recommandation : ${birads.recommendation}`, margin, y); y+=10
  }

  // ── Résumé clinique ──
  if (assembler) {
    if(y>210){doc.addPage();y=20}
    doc.setFont('helvetica','bold'); doc.setFontSize(10); doc.setTextColor(27,79,155)
    doc.text('RÉSUMÉ CLINIQUE', margin, y)
    doc.setDrawColor(27,79,155); doc.line(margin,y+1.5,W-margin,y+1.5); y+=8
    const rows=[
      ['Détection', `${assembler.detection?.predicted_class||'—'} (${Math.round((assembler.detection?.confidence||0)*100)}%)`],
      ['Classification', `${assembler.classification?.predicted_class||'—'} (${Math.round((assembler.classification?.confidence||0)*100)}%)`],
      ['Localisation', assembler.localization?.quadrant_fr||'—'],
      ['Taille tumorale', assembler.tumorsize?`${assembler.tumorsize.diameter_cm} cm (${assembler.tumorsize.tnm_stage})`:'—'],
      ['Stade TNM', assembler.stage?`${assembler.stage.stage} — ${assembler.stage.t_stage}${assembler.stage.n_stage}${assembler.stage.m_stage}`:'—'],
    ]
    doc.setFontSize(8.5)
    rows.forEach(([l,v])=>{
      doc.setFont('helvetica','bold'); doc.setTextColor(100,100,100); doc.text(l,margin,y)
      doc.setFont('helvetica','normal'); doc.setTextColor(20,20,20); doc.text(v,margin+52,y); y+=6
    })
    if(assembler.recommendations?.length){
      y+=2; doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(27,79,155)
      doc.text('Recommandations :', margin, y); y+=6
      assembler.recommendations.forEach((r,i)=>{
        const lines=doc.splitTextToSize(`${i===0?'✓':'!'} ${r}`,W-margin*2-4)
        doc.setFont('helvetica','normal'); doc.setFontSize(8.5); doc.setTextColor(50,50,50)
        doc.text(lines,margin+3,y); y+=lines.length*5.5
      })
    }
    y+=4
  }

  // ── Grad-CAM images ──
  if (gradcamHtml) {
    try {
      if(y>200){doc.addPage();y=20}
      doc.setFont('helvetica','bold'); doc.setFontSize(10); doc.setTextColor(27,79,155)
      doc.text('VISUALISATION GRAD-CAM — ZONES SUSPECTES', margin, y)
      doc.setDrawColor(27,79,155); doc.line(margin,y+1.5,W-margin,y+1.5); y+=8
      const parser = new DOMParser()
      const gradDoc = parser.parseFromString(gradcamHtml,'text/html')
      const imgs = gradDoc.querySelectorAll('img')
      const labels = ['Image originale','Mammo + Grad-CAM','Heatmap','Zone suspecte']
      const imgW = (W-margin*2-9)/4
      const imgH = 44
      let xi = margin
      for(let i=0;i<Math.min(imgs.length,4);i++){
        const src = imgs[i].src||imgs[i].getAttribute('src')||''
        if(src.startsWith('data:')){
          try{
            const fmt = src.includes('png')?'PNG':'JPEG'
            doc.addImage(src,fmt,xi,y,imgW,imgH,undefined,'FAST')
          }catch(e){}
        }
        doc.setFont('helvetica','normal'); doc.setFontSize(7); doc.setTextColor(120,120,120)
        doc.text(labels[i]||'',xi+imgW/2,y+imgH+4,{align:'center'})
        xi+=imgW+3
      }
      y+=imgH+14
    } catch(e){ console.warn('gradcam:', e) }
  }

  // ── Compte rendu IA ──
  if(narrative?.impression){
    if(y>230){doc.addPage();y=20}
    doc.setFont('helvetica','bold'); doc.setFontSize(10); doc.setTextColor(27,79,155)
    doc.text('COMPTE RENDU IA', margin, y)
    doc.setDrawColor(27,79,155); doc.line(margin,y+1.5,W-margin,y+1.5); y+=8
    doc.setFillColor(252,235,235)
    const impLines=doc.splitTextToSize(narrative.impression,W-margin*2-8)
    doc.roundedRect(margin,y-3,W-margin*2,impLines.length*5.5+6,2,2,'F')
    doc.setFont('helvetica','bold'); doc.setFontSize(8.5); doc.setTextColor(80,19,19)
    doc.text(impLines,margin+4,y+2); y+=impLines.length*5.5+8
    if(narrative.findings?.length){
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(50,50,50)
      doc.text('Constatations :', margin, y); y+=6
      narrative.findings.forEach(f=>{
        if(y>270){doc.addPage();y=20}
        const lines=doc.splitTextToSize(`• ${f}`,W-margin*2-4)
        doc.setFont('helvetica','normal'); doc.setFontSize(8.5); doc.setTextColor(60,60,60)
        doc.text(lines,margin+3,y); y+=lines.length*5
      })
    }
  }

  // ── Remarques radiologue ──
  if(y>230){doc.addPage();y=20}
  doc.setFont('helvetica','bold'); doc.setFontSize(10); doc.setTextColor(27,79,155)
  doc.text('REMARQUES DU RADIOLOGUE', margin, y)
  doc.setDrawColor(27,79,155); doc.line(margin,y+1.5,W-margin,y+1.5); y+=8
  const rem = remarque?.trim()||'— Aucune remarque saisie —'
  const remLines = doc.splitTextToSize(rem,W-margin*2)
  const boxH = remLines.length*5.5+16
  doc.setFillColor(248,250,255); doc.setDrawColor(199,215,248)
  doc.roundedRect(margin,y-3,W-margin*2,boxH,2,2,'FD')
  doc.setFont('helvetica','normal'); doc.setFontSize(9); doc.setTextColor(30,30,60)
  doc.text(remLines,margin+5,y+5); y+=boxH+10
  doc.setDrawColor(180,178,169); doc.line(W-margin-60,y,W-margin,y)
  doc.setFontSize(8); doc.setTextColor(180,178,169)
  doc.text('Signature du radiologue',W-margin,y+5,{align:'right'})

  // ── Footer ──
  const pc = doc.internal.getNumberOfPages()
  for(let i=1;i<=pc;i++){
    doc.setPage(i); doc.setFillColor(27,79,155); doc.rect(0,287,W,10,'F')
    doc.setFontSize(7); doc.setTextColor(255,255,255)
    doc.text('PREMIER · CHU Mohammed VI Oujda · Plateforme IA Mammographie', margin, 293)
    doc.text(`Page ${i} / ${pc}`, W-margin, 293, {align:'right'})
  }

  return doc
}

// ─── Page ViewRapport ────────────────────────────────────────────────────────
export default function ViewRapport({ rapport, onBack }) {
  const [pdfUrl,   setPdfUrl]   = useState(null)
  const [loading,  setLoading]  = useState(true)
  const [pdfDoc,   setPdfDoc]   = useState(null)

  useEffect(() => {
    if (!rapport) return
    setLoading(true)
    buildPDF(rapport).then(doc => {
      setPdfDoc(doc)
      const blob = doc.output('blob')
      const url  = URL.createObjectURL(blob)
      setPdfUrl(url)
      setLoading(false)
    }).catch(e => {
      console.error(e)
      setLoading(false)
    })
    return () => { if (pdfUrl) URL.revokeObjectURL(pdfUrl) }
  }, [rapport])

  const handleDownload = () => {
    if (!pdfDoc) return
    const fname = `PREMIER_${rapport.patient?.cin||'patient'}_${rapport.patient?.nom||''}_${new Date(rapport.date).toISOString().split('T')[0]}.pdf`
    pdfDoc.save(fname)
  }

  return (
    <div style={{ fontFamily:"'DM Sans','Segoe UI',sans-serif", display:'flex', flexDirection:'column', height:'calc(100vh - 60px)' }}>

      {/* ── Barre actions ── */}
      <div style={{ display:'flex', alignItems:'center', gap:'12px', padding:'12px 24px', background:'#fff', borderBottom:'0.5px solid #e8e7e3', flexShrink:0, boxShadow:'0 1px 3px rgba(0,0,0,0.05)' }}>
        {/* Bouton retour */}
        <button onClick={onBack}
          style={{ display:'flex', alignItems:'center', gap:'7px', background:'transparent', border:'1px solid #e5e7eb', borderRadius:'8px', padding:'8px 16px', fontSize:'13px', fontWeight:'500', color:'#374151', cursor:'pointer' }}
          onMouseEnter={e=>e.currentTarget.style.background='#f9fafb'}
          onMouseLeave={e=>e.currentTarget.style.background='transparent'}
        >
          <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
          </svg>
          Retour aux rapports
        </button>

        {/* Infos patiente */}
        {rapport?.patient && (
          <div style={{ display:'flex', alignItems:'center', gap:'14px', background:'#EFF4FF', border:'0.5px solid #c7d7f8', borderRadius:'8px', padding:'6px 14px' }}>
            <span style={{ fontSize:'12px', color:'#1B4F9B', fontWeight:'600' }}>👤 {rapport.patient.prenom} {rapport.patient.nom}</span>
            <span style={{ fontSize:'12px', color:'#6b7280' }}>CIN : {rapport.patient.cin}</span>
            <span style={{ fontSize:'12px', color:'#6b7280' }}>
              {rapport.result?.predicted_class === 'Cancer'
                ? <span style={{ color:'#791F1F', fontWeight:'600' }}>● Cancer</span>
                : <span style={{ color:'#27500A', fontWeight:'600' }}>● Normal</span>}
            </span>
          </div>
        )}

        {/* Bouton télécharger */}
        <button onClick={handleDownload} disabled={loading || !pdfDoc}
          style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:'7px', background:'#1B4F9B', border:'none', borderRadius:'8px', padding:'8px 20px', fontSize:'13px', fontWeight:'600', color:'#fff', cursor: loading?'wait':'pointer', opacity: loading?0.6:1 }}
        >
          <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          Télécharger PDF
        </button>
      </div>

      {/* ── Visionneuse PDF ── */}
      <div style={{ flex:1, background:'#525659', display:'flex', alignItems:'center', justifyContent:'center', overflow:'hidden' }}>
        {loading ? (
          <div style={{ textAlign:'center', color:'#fff' }}>
            <div style={{ width:'40px', height:'40px', border:'3px solid rgba(255,255,255,0.2)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 14px' }}/>
            <p style={{ fontSize:'14px', opacity:0.8 }}>Génération du rapport PDF...</p>
          </div>
        ) : pdfUrl ? (
          <iframe
            src={pdfUrl}
            style={{ width:'100%', height:'100%', border:'none' }}
            title="Rapport PDF"
          />
        ) : (
          <div style={{ textAlign:'center', color:'#fff' }}>
            <p style={{ fontSize:'14px' }}>Erreur lors de la génération du PDF</p>
          </div>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
 