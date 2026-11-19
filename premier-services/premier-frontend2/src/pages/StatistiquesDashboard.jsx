import { useEffect, useRef } from 'react'

const GRID = 'rgba(128,128,128,.1)'

function useChart(id, config) {
  const ref = useRef(null)
  useEffect(() => {
    let chart = null
    import('chart.js/auto').then(({ default: Chart }) => {
      if (ref.current) chart = new Chart(ref.current, config)
    })
    return () => chart?.destroy()
  }, [])
  return ref
}

/* ── Barres horizontales avec % ─────────────────────────────────────────── */
function HBars({ items, color }) {
  const max = items[0][1]
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
      {items.map(([label, val]) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div title={label} style={{ width: 140, flexShrink: 0, fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {label.replace(/_/g, ' ')}
          </div>
          <div style={{ flex: 1, background: 'var(--color-background-secondary)', borderRadius: 3, height: 16, overflow: 'hidden', position: 'relative' }}>
            <div style={{ width: `${Math.round(val / max * 100)}%`, height: '100%', background: color, borderRadius: 3 }} />
            <span style={{ position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)', fontSize: 10, fontWeight: 500, color: 'var(--color-text-secondary)' }}>
              {Math.round(val / max * 100)}%
            </span>
          </div>
          <div style={{ width: 38, textAlign: 'right', fontSize: 11, fontWeight: 500, color: 'var(--color-text-secondary)', flexShrink: 0 }}>{val}</div>
        </div>
      ))}
    </div>
  )
}

/* ── KPI Card ────────────────────────────────────────────────────────────── */
function KPI({ label, value, valueColor, sub, badge, badgeStyle }) {
  return (
    <div style={{ background: 'var(--color-background-secondary)', borderRadius: 8, padding: '14px 16px' }}>
      <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginBottom: 6, lineHeight: 1.3 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 500, color: valueColor, lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', marginTop: 5 }}>{sub}</div>
      {badge && (
        <span style={{ display: 'inline-block', fontSize: 10, fontWeight: 500, padding: '2px 8px', borderRadius: 20, marginTop: 6, ...badgeStyle }}>
          {badge}
        </span>
      )}
    </div>
  )
}

/* ── Alert Box ───────────────────────────────────────────────────────────── */
function Alert({ type, title, text }) {
  const styles = {
    danger:  { bg: '#FCEBEB', border: '#E24B4A', titleColor: '#A32D2D' },
    warn:    { bg: '#FAEEDA', border: '#EF9F27', titleColor: '#633806' },
    success: { bg: '#E1F5EE', border: '#1D9E75', titleColor: '#085041' },
  }
  const s = styles[type]
  return (
    <div style={{ background: s.bg, borderLeft: `3px solid ${s.border}`, borderRadius: 8, padding: '12px 14px', marginBottom: 10 }}>
      <div style={{ fontSize: 12, fontWeight: 500, color: s.titleColor, marginBottom: 2 }}>{title}</div>
      <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>{text}</div>
    </div>
  )
}

/* ── Card wrapper ────────────────────────────────────────────────────────── */
function Card({ title, children, style }) {
  return (
    <div style={{ background: 'var(--color-background-primary)', border: '0.5px solid var(--color-border-tertiary)', borderRadius: 12, padding: '1rem 1.25rem', ...style }}>
      {title && <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 12 }}>{title}</div>}
      {children}
    </div>
  )
}

/* ── Interprétation ──────────────────────────────────────────────────────── */
function Interp({ children }) {
  return (
    <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.7, padding: '10px 12px', background: 'var(--color-background-secondary)', borderRadius: 8, marginTop: 10 }}>
      {children}
    </div>
  )
}

/* ── Legend ──────────────────────────────────────────────────────────────── */
function Legend({ items }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 10 }}>
      {items.map(([label, color]) => (
        <span key={label} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--color-text-secondary)' }}>
          <span style={{ width: 9, height: 9, borderRadius: 2, background: color, flexShrink: 0 }} />
          {label}
        </span>
      ))}
    </div>
  )
}

/* ── Divider ─────────────────────────────────────────────────────────────── */
const Divider = () => <hr style={{ border: 'none', borderTop: '0.5px solid var(--color-border-tertiary)', margin: '1.5rem 0' }} />

/* ── Charts ──────────────────────────────────────────────────────────────── */
function BiradsChart() {
  const ref = useChart('birads', {
    type: 'bar',
    data: {
      labels: ['BI-RADS 0', 'BI-RADS 1', 'BI-RADS 2', 'BI-RADS 3', 'BI-RADS 4', 'BI-RADS 5'],
      datasets: [
        { label: 'Malin',     data: [59,3,2,102,731,560], backgroundColor: '#E24B4A', borderRadius: 0, stack: 's' },
        { label: 'Bénin',     data: [179,0,49,303,887,11], backgroundColor: '#1D9E75', borderRadius: 0, stack: 's' },
        { label: 'Bénin CB',  data: [0,0,593,72,15,2],    backgroundColor: '#888780', borderRadius: 0, stack: 's' },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { stacked: true, grid: { color: GRID }, ticks: { font: { size: 10 }, autoSkip: false, maxRotation: 0 } }, y: { stacked: true, grid: { color: GRID }, ticks: { font: { size: 11 } } } } },
  })
  return <canvas ref={ref} role="img" aria-label="Stacked bar BI-RADS pathologie" />
}

function SubtletyChart() {
  const ref = useChart('subtlety', {
    type: 'bar',
    data: {
      labels: ['Niv. 1 (très difficile)', 'Niv. 2', 'Niv. 3 (moyen)', 'Niv. 4', 'Niv. 5 (évidente)'],
      datasets: [{ data: [174,439,964,875,1114], backgroundColor: ['#E24B4A','#D85A30','#EF9F27','#1D9E75','#0F6E56'], borderRadius: 3, borderSkipped: false }],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { grid: { color: GRID }, ticks: { font: { size: 10 }, maxRotation: 0 } }, y: { grid: { color: GRID }, ticks: { font: { size: 11 } } } } },
  })
  return <canvas ref={ref} role="img" aria-label="Bar chart subtilité 1 à 5" />
}

function TypePathoChart() {
  const ref = useChart('typepatho', {
    type: 'bar',
    data: {
      labels: ['Malin', 'Bénin', 'Bénin sans CB'],
      datasets: [
        { label: 'Calcification', data: [673,658,541], backgroundColor: '#534AB7', borderRadius: 3, borderSkipped: false },
        { label: 'Masse',         data: [784,771,141], backgroundColor: '#D85A30', borderRadius: 3, borderSkipped: false },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { grid: { color: GRID }, ticks: { font: { size: 11 } } }, y: { grid: { color: GRID }, ticks: { font: { size: 11 } } } } },
  })
  return <canvas ref={ref} role="img" aria-label="Grouped bar malignité par type anomalie" />
}

const CALC_TYPES = [
  ['PLEOMORPHIC',664],['AMORPHOUS',138],['PUNCTATE',106],['LUCENT CENTER',93],
  ['VASCULAR',82],['FINE LINEAR BR.',77],['COARSE',35],['ROUND & REGULAR',31],
]
const CALC_DIST = [
  ['CLUSTERED',740],['SEGMENTAL',168],['REGIONAL',99],['LINEAR',90],
  ['DIFFUSE SCATTERED',37],['CLUSTERED-LINEAR',25],['CLUST-SEGMENTAL',5],['LINEAR-SEGMENTAL',5],
]

/* ── Dashboard principal ─────────────────────────────────────────────────── */
export default function StatistiquesDashboard() {
  return (
    <div style={{ fontFamily: 'var(--font-sans, system-ui)', fontSize: 13, color: 'var(--color-text-primary)' }}>

      {/* En-tête */}
      <div style={{ marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '0.5px solid var(--color-border-tertiary)' }}>
        <h2 style={{ fontSize: 20, fontWeight: 600, color: '#0B1F3A', marginBottom: 3 }}>Rapport statistique clinique — CBIS-DDSM</h2>
        <p style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Dataset de référence mammographie · 3 568 cas · CHU Mohammed VI Oujda</p>
      </div>

      {/* ── SECTION 1 : Malignité ─────────────────────────────────────────── */}
      <p style={{ fontSize: 10, fontWeight: 500, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--color-text-tertiary)', marginBottom: '.75rem' }}>
        Indicateurs clés de malignité
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))', gap: 10, marginBottom: '1.25rem' }}>
        <KPI label="Taux de malignité global"      value="40.8%" valueColor="#A32D2D" sub="1 457 cas malins / 3 568" badge="Surveillance requise"  badgeStyle={{ background: '#FCEBEB', color: '#A32D2D' }} />
        <KPI label="Taux de bénignité confirmée"   value="40.1%" valueColor="#085041" sub="1 429 cas bénins"         badge="Pas d'intervention"   badgeStyle={{ background: '#E1F5EE', color: '#085041' }} />
        <KPI label="Bénin sans rappel"             value="19.1%" valueColor="#633806" sub="682 cas — suivi léger"    badge="Surveillance 6 mois"  badgeStyle={{ background: '#FAEEDA', color: '#633806' }} />
        <KPI label="Malignité calcifications"      value="35.9%" valueColor="#A32D2D" sub="673 / 1 872 calcifications" badge="Biopsie BI-RADS 4–5" badgeStyle={{ background: '#FCEBEB', color: '#A32D2D' }} />
        <KPI label="Malignité masses"              value="46.2%" valueColor="#A32D2D" sub="784 / 1 696 masses"       badge="Risque élevé"          badgeStyle={{ background: '#FCEBEB', color: '#A32D2D' }} />
      </div>

      <Alert type="danger"
        title="Alerte clinique — masses plus malignes que les calcifications"
        text="46.2% des masses sont malignes vs 35.9% des calcifications. Une masse détectée doit systématiquement déclencher une évaluation BI-RADS ≥ 4 avec biopsie si nécessaire." />
      <Alert type="warn"
        title="19.1% de cas bénins sans rappel — risque de sous-diagnostic"
        text="Ces cas pourraient masquer des lésions à faible évolutivité. Un suivi mammographique à 6 mois reste recommandé pour ce groupe." />

      <Divider />

      {/* ── SECTION 2 : BI-RADS ──────────────────────────────────────────── */}
      <p style={{ fontSize: 10, fontWeight: 500, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--color-text-tertiary)', marginBottom: '.75rem' }}>
        Malignité par score BI-RADS
      </p>
      <Card title="Répartition pathologique par score BI-RADS" style={{ marginBottom: 14 }}>
        <Legend items={[['Malin', '#E24B4A'], ['Bénin', '#1D9E75'], ['Bénin sans CB', '#888780']]} />
        <div style={{ height: 220 }}><BiradsChart /></div>
        <Interp>
          <strong style={{ fontWeight: 500 }}>Lecture clinique :</strong> BI-RADS 4 concentre le plus grand volume de cas suspects (1 633), dont 44.8% malins.
          BI-RADS 5 présente un taux de malignité de <strong style={{ fontWeight: 500 }}>97.7%</strong> (560/573) — biopsie immédiate obligatoire.
          BI-RADS 2 est quasi exclusivement bénin sans rappel (92%).
        </Interp>
      </Card>

      <Divider />

      {/* ── SECTION 3 : Subtilité ────────────────────────────────────────── */}
      <p style={{ fontSize: 10, fontWeight: 500, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--color-text-tertiary)', marginBottom: '.75rem' }}>
        Subtilité de détection — difficulté radiologique
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))', gap: 10, marginBottom: '1.25rem' }}>
        <KPI label="Lésions très subtiles (niv. 1–2)" value="17.1%" valueColor="#0C447C" sub="613 cas difficiles"  badge="Expertise requise"  badgeStyle={{ background: '#E6F1FB', color: '#0C447C' }} />
        <KPI label="Subtilité intermédiaire (niv. 3)" value="27.0%" valueColor="#633806" sub="964 cas modérés"    badge="Double lecture"     badgeStyle={{ background: '#FAEEDA', color: '#633806' }} />
        <KPI label="Lésions visibles (niv. 4–5)"      value="55.9%" valueColor="#085041" sub="1 989 cas évidents" badge="Détection standard"  badgeStyle={{ background: '#E1F5EE', color: '#085041' }} />
      </div>
      <Card title="Distribution de la subtilité (1 = très difficile → 5 = évidente)" style={{ marginBottom: 14 }}>
        <div style={{ height: 180 }}><SubtletyChart /></div>
        <Interp>
          <strong style={{ fontWeight: 500 }}>Implication IA :</strong> 17.1% des lésions sont de subtilité 1–2, donc invisibles à l'œil non expert.
          C'est précisément là que le pipeline PREMIER apporte le plus de valeur clinique — ces cas justifient son intégration comme aide à la décision.
        </Interp>
      </Card>

      <Divider />

      {/* ── SECTION 4 : Calcifications ───────────────────────────────────── */}
      <p style={{ fontSize: 10, fontWeight: 500, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--color-text-tertiary)', marginBottom: '.75rem' }}>
        Types de calcifications — profil de risque
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
        <Card title="Types morphologiques — fréquence">
          <HBars items={CALC_TYPES} color="#185FA5" />
          <Interp><strong style={{ fontWeight: 500 }}>PLEOMORPHIC</strong> représente 56.3% des calcifications — forme la plus associée à la malignité selon les critères ACR.</Interp>
        </Card>
        <Card title="Distribution anatomique">
          <HBars items={CALC_DIST} color="#534AB7" />
          <Interp><strong style={{ fontWeight: 500 }}>CLUSTERED</strong> (62.7%) est le pattern le plus fréquent. Les formes SEGMENTAL et LINEAR ont un risque malin plus élevé.</Interp>
        </Card>
      </div>

      <Alert type="danger"
        title="Calcifications PLEOMORPHIC — indicateur de malignité prioritaire"
        text="664 cas PLEOMORPHIC détectés. Ce type est classé ACR BI-RADS 'hautement suspect' — toute détection doit déclencher une évaluation BI-RADS ≥ 4B avec biopsie stéréotaxique recommandée." />
      <Alert type="success"
        title="LUCENT CENTER et ROUND — calcifications bénignes de référence"
        text="Ces types correspondent à des calcifications typiquement bénignes (adénofibromes, calcifications vasculaires). Leur présence isolée permet une surveillance simple à 12 mois." />

      <Divider />

      {/* ── SECTION 5 : Comparaison ──────────────────────────────────────── */}
      <p style={{ fontSize: 10, fontWeight: 500, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--color-text-tertiary)', marginBottom: '.75rem' }}>
        Comparaison masses vs calcifications
      </p>
      <Card title="Taux de malignité par type d'anomalie et pathologie">
        <Legend items={[['Calcification', '#534AB7'], ['Masse', '#D85A30']]} />
        <div style={{ height: 200 }}><TypePathoChart /></div>
      </Card>

    </div>
  )
}