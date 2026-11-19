import { useState } from "react";
import logo from "../assets/logo-chu.png";
import { registerMedecin } from "../services/api";

export default function RegisterPage({ onRegister, onSwitchToLogin }) {
  const [nom, setNom] = useState("");
  const [prenom, setPrenom] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const passwordStrength = (pwd) => {
    if (pwd.length === 0) return { label: '', pct: 0, color: '#e5e7eb' };
    if (pwd.length < 6) return { label: 'Faible', pct: 33, color: '#E24B4A' };
    if (pwd.length < 10) return { label: 'Moyen', pct: 66, color: '#F5A623' };
    return { label: 'Fort', pct: 100, color: '#27B562' };
  };
  const strength = passwordStrength(password);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }
    if (password.length < 6) {
      setError("Le mot de passe doit contenir au moins 6 caractères.");
      return;
    }

    setLoading(true);
    try {
      const data = await registerMedecin({ email, password, nom, prenom });
      onRegister(data);
    } catch (err) {
      setError(err.response?.data?.error || "Erreur lors de l'inscription.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "'DM Sans','Inter',system-ui,sans-serif" }}>
      <style>{`
        @keyframes fadeInLeft  { from { opacity:0; transform:translateX(-24px) } to { opacity:1; transform:translateX(0) } }
        @keyframes fadeInRight { from { opacity:0; transform:translateX(24px)  } to { opacity:1; transform:translateX(0) } }
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
        .login-input:focus { border-color:#1B4F9B !important; box-shadow:0 0 0 3px rgba(27,79,155,0.12) !important; outline:none; }
        .login-btn:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 8px 24px rgba(27,79,155,0.45) !important; }
      `}</style>

      {/* ── GAUCHE ── */}
      <div style={{
        width:'48%', flexShrink:0, position:'relative', overflow:'hidden',
        background:'linear-gradient(155deg,#1B4F9B 0%,#0f2d5c 60%,#091d3d 100%)',
        display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
        padding:'3rem 3rem',
      }}>
        <div style={{ position:'absolute', top:-100, right:-100, width:320, height:320, borderRadius:'50%', background:'rgba(255,255,255,0.03)' }}/>
        <div style={{ position:'absolute', bottom:-80, left:-80, width:240, height:240, borderRadius:'50%', background:'rgba(255,255,255,0.03)' }}/>
        <div style={{ position:'absolute', top:'30%', right:-50, width:160, height:160, borderRadius:'50%', background:'rgba(245,166,35,0.08)' }}/>

        <div style={{ position:'relative', display:'flex', flexDirection:'column', alignItems:'center', gap:'2rem', animation:'fadeInLeft .7s ease', maxWidth:380 }}>
          <div style={{ animation:'float 4s ease-in-out infinite' }}>
            <div style={{ background:'#fff', borderRadius:20, padding:'20px 32px', boxShadow:'0 20px 60px rgba(0,0,0,0.25)', display:'flex', alignItems:'center', justifyContent:'center' }}>
              <img src={logo} alt="CHU Logo" style={{ height:70, width:'auto' }} />
            </div>
          </div>

          <div style={{ textAlign:'center' }}>
            <div style={{ display:'inline-flex', alignItems:'center', gap:6, background:'rgba(245,166,35,0.15)', border:'1px solid rgba(245,166,35,0.3)', borderRadius:9999, padding:'5px 14px', marginBottom:14 }}>
              <div style={{ width:6, height:6, borderRadius:'50%', background:'#F5A623' }}/>
              <span style={{ fontSize:10, fontWeight:700, color:'#F5A623', letterSpacing:'0.1em' }}>PLATEFORME · IA MÉDICALE</span>
            </div>
                     <h1 style={{ color:'#fff', fontSize:24, fontWeight:800, margin:'0 0 10px', lineHeight:1.3 }}>
  Centre Hospitalier-Universitaire<br/>Mohammed VI
</h1>
            <p style={{ color:'rgba(255,255,255,0.55)', fontSize:13, margin:0, lineHeight:1.7 }}>
              Créez votre compte pour rejoindre la plateforme<br/>de diagnostic IA — Oujda
            </p>
          </div>

          <div style={{ width:'100%', height:'0.5px', background:'rgba(255,255,255,0.1)' }}/>

          <div style={{ display:'flex', flexDirection:'column', gap:8, width:'100%' }}>
            {[
              { icon:'🔬', label:'Détection automatique des zones suspectes' },
              { icon:'📊', label:'Classification BI-RADS Score 0 à 6' },
              { icon:'📋', label:'Génération de rapports PDF professionnels' },
              { icon:'📈', label:'Tableau de bord analytique en temps réel' },
            ].map(f => (
              <div key={f.label} style={{ display:'flex', alignItems:'center', gap:10, background:'rgba(255,255,255,0.05)', borderRadius:8, padding:'9px 12px', border:'0.5px solid rgba(255,255,255,0.08)' }}>
                <span style={{ fontSize:14 }}>{f.icon}</span>
                <span style={{ fontSize:12, color:'rgba(255,255,255,0.7)', fontWeight:500 }}>{f.label}</span>
              </div>
            ))}
          </div>

          <p style={{ fontSize:10, color:'rgba(255,255,255,0.25)', textAlign:'center', margin:0 }}>
            © 2026 CHU Mohammed VI Oujda · Tous droits réservés
          </p>
        </div>
      </div>

      {/* ── DROITE ── */}
      <div style={{
        flex:1, background:'#F7F9FC',
        display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
        padding:'3rem 2rem', position:'relative', overflowY:'auto',
      }}>
        <div style={{ position:'absolute', inset:0, backgroundImage:'radial-gradient(#1B4F9B10 1px, transparent 1px)', backgroundSize:'24px 24px', pointerEvents:'none' }}/>

        <div style={{ position:'relative', width:'100%', maxWidth:400, animation:'fadeInRight .7s ease' }}>

          <div style={{ background:'#fff', borderRadius:20, padding:'36px 36px', boxShadow:'0 4px 40px rgba(0,0,0,0.08)', border:'0.5px solid #e5e7eb' }}>

            <div style={{ textAlign:'center', marginBottom:28 }}>
              <div style={{ width:56, height:56, borderRadius:16, background:'linear-gradient(135deg,#1B4F9B,#0f2d5c)', display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 14px', boxShadow:'0 8px 20px rgba(27,79,155,0.3)' }}>
                <svg width="26" height="26" fill="none" stroke="#fff" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
                </svg>
              </div>
              <h2 style={{ fontSize:22, fontWeight:800, color:'#1a1a2e', margin:'0 0 6px' }}>Créer un compte</h2>
              <p style={{ fontSize:13, color:'#9ca3af', margin:0 }}>Rejoignez la plateforme </p>
            </div>

            <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:16 }}>

              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
                <div>
                  <label style={{ display:'block', fontSize:11, fontWeight:700, color:'#374151', marginBottom:6, textTransform:'uppercase', letterSpacing:'.07em' }}>
                    Prénom
                  </label>
                  <input
                    className="login-input"
                    type="text" value={prenom} required
                    onChange={e => setPrenom(e.target.value)}
                    style={{ width:'100%', boxSizing:'border-box', height:46, padding:'0 14px', border:'1px solid #e5e7eb', borderRadius:10, background:'#FAFAFA', fontSize:14, color:'#1a1a2e' }}
                  />
                </div>
                <div>
                  <label style={{ display:'block', fontSize:11, fontWeight:700, color:'#374151', marginBottom:6, textTransform:'uppercase', letterSpacing:'.07em' }}>
                    Nom
                  </label>
                  <input
                    className="login-input"
                    type="text" value={nom} required
                    onChange={e => setNom(e.target.value)}
                    style={{ width:'100%', boxSizing:'border-box', height:46, padding:'0 14px', border:'1px solid #e5e7eb', borderRadius:10, background:'#FAFAFA', fontSize:14, color:'#1a1a2e' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display:'block', fontSize:11, fontWeight:700, color:'#374151', marginBottom:6, textTransform:'uppercase', letterSpacing:'.07em' }}>
                  Adresse email
                </label>
                <div style={{ position:'relative' }}>
                  <svg style={{ position:'absolute', left:13, top:'50%', transform:'translateY(-50%)', width:16, height:16 }} fill="none" viewBox="0 0 24 24" stroke="#9ca3af" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                  </svg>
                  <input
                    className="login-input"
                    type="email" value={email} required
                    onChange={e => setEmail(e.target.value)}
                    style={{ width:'100%', boxSizing:'border-box', height:46, padding:'0 14px 0 42px', border:'1px solid #e5e7eb', borderRadius:10, background:'#FAFAFA', fontSize:14, color:'#1a1a2e' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display:'block', fontSize:11, fontWeight:700, color:'#374151', marginBottom:6, textTransform:'uppercase', letterSpacing:'.07em' }}>
                  Mot de passe
                </label>
                <div style={{ position:'relative' }}>
                  <svg style={{ position:'absolute', left:13, top:'50%', transform:'translateY(-50%)', width:16, height:16 }} fill="none" viewBox="0 0 24 24" stroke="#9ca3af" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                  </svg>
                  <input
                    className="login-input"
                    type={showPass ? 'text' : 'password'} value={password} required
                    onChange={e => setPassword(e.target.value)}
                    style={{ width:'100%', boxSizing:'border-box', height:46, padding:'0 46px 0 42px', border:'1px solid #e5e7eb', borderRadius:10, background:'#FAFAFA', fontSize:14, color:'#1a1a2e' }}
                  />
                  <button type="button" onClick={() => setShowPass(!showPass)}
                    style={{ position:'absolute', right:13, top:'50%', transform:'translateY(-50%)', background:'none', border:'none', cursor:'pointer', padding:0, color:'#9ca3af', display:'flex' }}>
                    {showPass
                      ? <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
                      : <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                    }
                  </button>
                </div>
                {password && (
                  <div style={{ marginTop: 8 }}>
                    <div style={{ height: 4, background: '#e5e7eb', borderRadius: 9999, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${strength.pct}%`, background: strength.color, transition: 'all .3s' }} />
                    </div>
                    <span style={{ fontSize: 11, color: strength.color, fontWeight: 600, marginTop: 4, display: 'block' }}>
                      Sécurité : {strength.label}
                    </span>
                  </div>
                )}
              </div>

          <div>
  <label style={{ display:'block', fontSize:11, fontWeight:700, color:'#374151', marginBottom:6, textTransform:'uppercase', letterSpacing:'.07em' }}>
    Confirmer le mot de passe
  </label>
  <div style={{ position:'relative' }}>
    <svg style={{ position:'absolute', left:13, top:'50%', transform:'translateY(-50%)', width:16, height:16 }} fill="none" viewBox="0 0 24 24" stroke={confirmPassword && confirmPassword === password ? '#27B562' : '#9ca3af'} strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
    </svg>
    <input
      className="login-input"
      type={showConfirm ? 'text' : 'password'} value={confirmPassword} required
      onChange={e => setConfirmPassword(e.target.value)}
      style={{
        width:'100%', boxSizing:'border-box', height:46, padding:'0 76px 0 42px',
        border: confirmPassword
          ? (confirmPassword === password ? '1.5px solid #27B562' : '1.5px solid #E24B4A')
          : '1px solid #e5e7eb',
        borderRadius:10, background:'#FAFAFA', fontSize:14, color:'#1a1a2e',
        boxShadow: confirmPassword && confirmPassword === password ? '0 0 0 3px rgba(39,181,98,0.12)' : 'none',
        transition: 'border-color .2s, box-shadow .2s',
      }}
    />
    {confirmPassword && confirmPassword === password && (
      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="#27B562" strokeWidth={2.5}
        style={{ position:'absolute', right:42, top:'50%', transform:'translateY(-50%)' }}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    )}
    <button type="button" onClick={() => setShowConfirm(!showConfirm)}
      style={{ position:'absolute', right:13, top:'50%', transform:'translateY(-50%)', background:'none', border:'none', cursor:'pointer', padding:0, color:'#9ca3af', display:'flex' }}>
      {showConfirm
        ? <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
        : <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
      }
    </button>
  </div>
  {confirmPassword && (
    <span style={{
      fontSize:11, fontWeight:600, marginTop:6, display:'flex', alignItems:'center', gap:5,
      color: confirmPassword === password ? '#27B562' : '#E24B4A',
    }}>
      {confirmPassword === password
        ? <><svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/></svg>Mots de passe identiques</>
        : 'Les mots de passe ne correspondent pas'}
    </span>
  )}
</div>

              {error && (
                <div style={{ display:'flex', alignItems:'center', gap:8, background:'#FCEBEB', border:'0.5px solid #F09595', borderRadius:8, padding:'10px 14px' }}>
                  <svg width="14" height="14" fill="#791F1F" viewBox="0 0 20 20" style={{ flexShrink:0 }}>
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
                  </svg>
                  <span style={{ fontSize:12, color:'#791F1F', fontWeight:500 }}>{error}</span>
                </div>
              )}

              <button className="login-btn" type="submit" disabled={loading}
                style={{ height:48, background:'linear-gradient(135deg,#1B4F9B,#0f2d5c)', color:'#fff', border:'none', borderRadius:10, fontSize:14, fontWeight:700, cursor:loading?'wait':'pointer', display:'flex', alignItems:'center', justifyContent:'center', gap:8, boxShadow:'0 4px 16px rgba(27,79,155,0.35)', marginTop:4 }}>
                {loading
                  ? <><span style={{ width:16, height:16, border:'2px solid rgba(255,255,255,.3)', borderTopColor:'#fff', borderRadius:'50%', display:'inline-block', animation:'spin 0.8s linear infinite' }}/> Création en cours…</>
                  : <>Créer mon compte <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg></>
                }
              </button>
            </form>

            <p style={{ textAlign:'center', fontSize:13, color:'#6b7280', marginTop:20 }}>
              Déjà un compte ?{' '}
              <button onClick={onSwitchToLogin} style={{ background:'none', border:'none', color:'#1B4F9B', fontWeight:700, cursor:'pointer', fontSize:13, padding:0 }}>
                Se connecter
              </button>
            </p>
          </div>

          <p style={{ textAlign:'center', fontSize:11, color:'#9ca3af', marginTop:20 }}>
            CHU Mohammed VI Oujda · PREMIER v1.0 · © 2026
          </p>
        </div>
      </div>
    </div>
  );
}