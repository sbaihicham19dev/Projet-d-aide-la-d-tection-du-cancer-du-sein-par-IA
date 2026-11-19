export default function ResultCard({ result, preview, onReset }) {
  const isCancel = result.predicted_class === 'Non-Cancer';
  const confidence = (result.confidence * 100).toFixed(1);
  const birads = result.birads;
  const stage = result.stage;
  const narrative = result.narrative;
  const assembler = result.assembler_report;

  return (
    <div className="result-container">

      <div className="result-header">
        <div className={`result-badge ${isCancel ? 'badge-green' : 'badge-red'}`}>
          {result.predicted_class}
        </div>
        <div className="result-confidence">
          Confiance : {confidence}%
        </div>
        <button className="reset-btn" onClick={onReset}>
          Nouvelle analyse
        </button>
      </div>

      <div className="result-grid">

        {preview && (
          <div className="card">
            <h3>Image analysée</h3>
            <img src={preview} alt="Mammographie" className="result-img" />
          </div>
        )}

        {birads && (
          <div className="card">
            <h3>Score BI-RADS</h3>
            <div className={`birads-score birads-${birads.birads_score}`}>
              {birads.birads_score}
            </div>
            <p className="card-desc">{birads.description}</p>
            <p className="card-label">Risque : <strong>{birads.malignancy_risk}</strong></p>
            <p className="card-label">Recommandation : {birads.recommendation}</p>
          </div>
        )}

        {stage && (
          <div className="card">
            <h3>Stade TNM</h3>
            <div className="stage-badge">Stade {stage.stage_roman}</div>
            <p className="card-desc">{stage.description}</p>
            <p className="card-label">Traitement : {stage.treatment}</p>
            <p className="card-label">Pronostic : {stage.prognosis}</p>
          </div>
        )}

        {assembler && (
          <div className="card card-wide">
            <h3>Résumé clinique</h3>
            <p className="card-desc">{assembler.clinical_summary}</p>
            {assembler.recommendations?.map((r, i) => (
              <p key={i} className="recommendation">• {r}</p>
            ))}
            {assembler.quality_warnings?.length > 0 && (
              <div className="warning-box">
                {assembler.quality_warnings.map((w, i) => (
                  <p key={i}>⚠ {w}</p>
                ))}
              </div>
            )}
          </div>
        )}

        {narrative && (
          <div className="card card-wide">
            <h3>{narrative.title}</h3>
            <p className="narrative-impression">{narrative.impression}</p>
            <pre className="narrative-text">{narrative.narrative_text}</pre>
          </div>
        )}

      </div>
    </div>
  );
}