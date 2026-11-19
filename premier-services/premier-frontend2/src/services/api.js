import axios from 'axios';

const API_BASE = 'http://localhost:8080';

export const analyzeMammography = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(
    `${API_BASE}/api/pipeline/analyze`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    }
  );
  return response.data;
};

export const checkHealth = async () => {
  const response = await axios.get(`${API_BASE}/api/pipeline/health-all`);
  return response.data;
};

export const analyzeGradcam = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(
    `${API_BASE}/api/pipeline/analyze/gradcam`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
      responseType: 'text',
    }
  );
  return response.data;
};

// ── Rapports ──────────────────────────────────────────────────────────────
export const saveRapport = async (patient, result, remarque, pdfDataUri, medecinId) => {
  const isCancer = result?.predicted_class === 'Cancer';

  const response = await axios.post(`${API_BASE}/api/rapports`, {
    medecinId,
    cin: patient?.cin || '',
    nom: patient?.nom || '',
    prenom: patient?.prenom || '',
    telephone: patient?.telephone || '',
    dateNaissance: patient?.dateNaissance || null,
    coteExamine: patient?.cote || '',
    resultat: result?.predicted_class || '—',
    confidence: result?.confidence || 0,
    biradsScore: isCancer ? result?.birads?.birads_score : null,
    malignancyRisk: isCancer ? result?.birads?.malignancy_risk : null,
    stade: isCancer ? result?.assembler_report?.stage?.stage : null,
    localisation: isCancer ? result?.assembler_report?.localization?.quadrant_fr : null,
    tailleTumeur: isCancer ? result?.assembler_report?.tumorsize?.diameter_cm : null,
    classification: isCancer ? result?.assembler_report?.classification?.predicted_class : null,
    remarque: remarque || '',
    pdfBase64: pdfDataUri || null,
  });
  return response.data;
};

export const fetchRapports = async (medecinId) => {
  const response = await axios.get(`${API_BASE}/api/rapports`, {
    params: medecinId ? { medecinId } : {},
  });
  return response.data;
};

// ✅ Récupère l'URL directe du PDF stocké sur disque
export const getPdfUrl = (rapportId) => `${API_BASE}/api/rapports/${rapportId}/pdf`;

// ── Médecins (Auth) ──────────────────────────────────────────────────────
export const loginMedecin = async (email, password) => {
  const response = await axios.post(`${API_BASE}/api/medecins/login`, { email, password });
  return response.data;
};

export const registerMedecin = async (data) => {
  const response = await axios.post(`${API_BASE}/api/medecins/register`, data);
  return response.data;
};