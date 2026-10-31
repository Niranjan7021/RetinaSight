import { useEffect, useRef, useState } from 'react';
import { Activity, ArrowUpRight, CheckCircle2, CircleHelp, Clock3, Database, FileDown, FileImage, FlaskConical, HeartPulse, History, ImagePlus, Info, Layers3, ScanEye, ShieldCheck, UploadCloud, X } from 'lucide-react';
import SwarmCursor from './components/SwarmCursor';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';
const fmtDate = (v) => { try { return new Date(v).toLocaleString(); } catch { return v; } };

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [apiState, setApiState] = useState('checking');
  const inputRef = useRef(null);

  async function loadHistory() {
    try { const r = await fetch(`${API}/api/screenings`); if (!r.ok) throw new Error(); const d = await r.json(); setHistory(d.items || []); setApiState('online'); }
    catch { setApiState('offline'); }
  }
  useEffect(() => { loadHistory(); }, []);
  useEffect(() => { if (!file) { setPreview(''); return; } const url = URL.createObjectURL(file); setPreview(url); return () => URL.revokeObjectURL(url); }, [file]);

  function chooseFile(f) {
    setError(''); setResult(null);
    if (!f) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(f.type)) { setError('Please choose a JPG, PNG, or WebP image.'); return; }
    if (f.size > 12 * 1024 * 1024) { setError('Maximum file size is 12 MB.'); return; }
    setFile(f);
  }
  async function runScreening(e) {
    e.preventDefault(); if (!file) { setError('Upload a fundus image to continue.'); return; }
    setBusy(true); setError(''); setResult(null);
    try {
      const form = new FormData(); form.append('image', file);
      const response = await fetch(`${API}/api/screenings`, { method: 'POST', body: form });
      const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Screening request failed.');
      setResult(data); await loadHistory();
    } catch (err) { setError(`${err.message || 'Could not connect to the backend.'} Make sure the Flask API is running on port 5000.`); }
    finally { setBusy(false); }
  }
  async function openHistory(item) {
    try { const r = await fetch(`${API}/api/screenings/${item.id}`); const d = await r.json(); if (r.ok) { setResult(d); setFile(null); setPreview(''); window.scrollTo({ top: 0, behavior: 'smooth' }); } }
    catch { setError('Unable to load that screening record.'); }
  }
  const downloadReport = (id) => { window.open(`${API}/api/screenings/${id}/report`, '_blank', 'noopener,noreferrer'); };

  return <div className="app-shell">
    <header className="topbar">
      <a className="brand" href="#home"><span className="brand-icon"><ScanEye size={22}/></span><span><b>Retina<span className="blue">Sight</span></b><small>SCREENING STUDIO</small></span></a>
      <nav><a className="active" href="#workspace">Workspace</a><a href="#history">Screening history</a><a href="#about">About</a></nav>
      <div className="status"><span className={`status-dot ${apiState === 'online' ? 'live' : ''}`}/>{apiState === 'online' ? 'API connected' : apiState === 'offline' ? 'API offline' : 'Connecting'}</div>
    </header>

    <main id="home">
      <section className="hero">
        <SwarmCursor count={800} size={2.6} spread={90} swirl={0.6} clickEffect="burst" color="#111827" accentColor="#2786ff" className="hero-swarm">
          <div className="hero-inner">
            <div className="eyebrow"><span className="eyebrow-line"/> COMPUTER VISION · HEALTHCARE <span className="tag">Solution</span></div>
            <div className="creator-credit">
              <span className="creator-dot"></span>
                CREATED BY NIRANJAN
            </div>
            <h1>See beyond the<br/><span>surface.</span></h1>
            <p className="hero-copy">A retinal screening workflow for fundus images — built to organize image review, model outputs, and explainable reporting in one place.</p>
            <div className="hero-actions"><a className="primary-btn" href="#workspace">Start a screening <ArrowUpRight size={17}/></a><a className="text-link" href="#about">Explore the workflow <span>↘</span></a></div>
            <div className="hero-foot"><span><ShieldCheck size={15}/> Screening support, not diagnosis</span><span><Layers3 size={15}/> CNN-ready architecture</span></div>
          </div>
          <div className="hero-orb" aria-hidden="true"><div className="orb-ring ring-one"/><div className="orb-ring ring-two"/><div className="orb-core"><ScanEye size={66}/><span>RETINA<br/>ANALYSIS</span></div><div className="orb-point p-one"/><div className="orb-point p-two"/><div className="orb-point p-three"/></div>
          <div className="hero-grid" aria-hidden="true"/>
        </SwarmCursor>
      </section>

      <section className="metric-row" aria-label="Platform capabilities">
        <div className="metric"><span className="metric-icon"><FileImage size={18}/></span><div><b>Fundus input</b><small>JPG · PNG · WebP</small></div></div>
        <div className="metric"><span className="metric-icon"><Activity size={18}/></span><div><b>Model-ready API</b><small>Plug in your trained CNN</small></div></div>
        <div className="metric"><span className="metric-icon"><Database size={18}/></span><div><b>Local records</b><small>SQLite screening history</small></div></div>
        <div className="metric"><span className="metric-icon"><FileDown size={18}/></span><div><b>Exportable report</b><small>CSV screening summary</small></div></div>
      </section>

      <section className="section workspace" id="workspace">
        <div className="section-heading"><div><div className="kicker">01 / SCREENING WORKSPACE</div><h2>Start with a fundus image.</h2><p>Upload an image to validate its format and create a screening record.</p></div><div className="demo-badge"><span/> DEMO PIPELINE</div></div>
        <div className="workspace-grid">
          <form className="panel upload-panel" onSubmit={runScreening}>
            <div className="panel-heading"><div className="step-num">01</div><div><h3>Image input</h3><p>Choose a retinal fundus image</p></div></div>
            <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={e => chooseFile(e.target.files?.[0])}/>
            {!preview ? <button type="button" className="dropzone" onClick={() => inputRef.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); chooseFile(e.dataTransfer.files?.[0]); }}><span className="upload-icon"><UploadCloud size={25}/></span><b>Drop image here</b><span>or <u>browse files</u></span><small>JPG, PNG or WebP · up to 12 MB</small></button> : <div className="preview-box"><img src={preview} alt="Selected fundus image preview"/><div className="preview-overlay"><span><CheckCircle2 size={15}/> Image selected</span><button type="button" aria-label="Remove image" onClick={() => {setFile(null);setResult(null);}}><X size={16}/></button></div><div className="file-meta"><FileImage size={16}/><span>{file?.name || 'Previous screening image'}</span><small>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Saved record'}</small></div></div>}
            {error && <div className="error-msg" role="alert"><Info size={16}/>{error}</div>}
            <div className="input-note"><Info size={15}/><span>Use de-identified images only. Uploaded images are saved locally by this demo backend.</span></div>
            <button className="primary-btn submit-btn" type="submit" disabled={busy || !file}>{busy ? <><span className="spinner"/> Checking image…</> : <>Run screening workflow <ArrowUpRight size={17}/></>}</button>
          </form>

          <div className="panel result-panel">
            <div className="panel-heading"><div className="step-num blue-step">02</div><div><h3>Screening output</h3><p>Quality checks and model response</p></div><span className="live-label">LIVE VIEW</span></div>
            {!result ? <div className="empty-result"><div className="empty-graphic"><div className="scan-circle"><ScanEye size={31}/></div><span className="scan-cross cross-a"/><span className="scan-cross cross-b"/></div><h3>Awaiting image input</h3><p>Your screening record and output summary will appear here after upload.</p><div className="empty-checks"><span><CheckCircle2 size={15}/> File validation</span><span><CheckCircle2 size={15}/> Quality heuristics</span><span><CheckCircle2 size={15}/> Report generation</span></div></div> : <div className="result-content">
              <div className="result-status"><span className="warning-icon"><FlaskConical size={18}/></span><div><b>{result.result?.headline || 'Screening record loaded'}</b><small>Record ID · {result.id?.slice(0, 8)}</small></div></div>
              <div className="result-grid"><div className="result-tile"><small>Image dimensions</small><b>{result.width} × {result.height}</b></div><div className="result-tile"><small>Basic quality check</small><b className="quality-text">{result.quality}</b></div><div className="result-tile"><small>Model status</small><b className="muted-value">{result.result?.model_status || 'Not configured'}</b></div><div className="result-tile"><small>Confidence score</small><b className="muted-value">—</b></div></div>
              <div className="notice-box"><Info size={17}/><div><b>Demo mode — no disease prediction</b><p>A trained CNN is not connected. No disease class, severity, or confidence score is inferred from this image.</p></div></div>
              <div className="output-notes"><b>Workflow notes</b>{(result.result?.visual_notes || []).map((n, i) => <p key={i}><span>{String(i + 1).padStart(2, '0')}</span>{n}</p>)}</div>
              <button className="secondary-btn report-btn" onClick={() => downloadReport(result.id)}><FileDown size={16}/> Download screening report (CSV)</button>
            </div>}
          </div>
        </div>
        <div className="safety-line"><ShieldCheck size={17}/><p><b>Clinical safety note:</b> This starter website is not a medical device. Its demo pipeline does not detect retinal disease and must not be used for diagnosis, treatment, or referral decisions.</p></div>
      </section>

      <section className="section history-section" id="history">
        <div className="section-heading"><div><div className="kicker">02 / LOCAL DATABASE</div><h2>Recent screenings.</h2><p>Records stored in the backend's SQLite database on this machine.</p></div><button className="secondary-btn refresh-btn" onClick={loadHistory}><History size={16}/> Refresh history</button></div>
        <div className="history-panel">
          <div className="history-head"><span>IMAGE / RECORD</span><span>DATE CREATED</span><span>QUALITY CHECK</span><span>STATUS</span><span></span></div>
          {history.length === 0 ? <div className="history-empty"><Clock3 size={19}/><span>No records yet. Upload an image to create your first screening entry.</span></div> : history.slice(0, 8).map(item => <div className="history-row" key={item.id}><div className="history-file"><span className="mini-file"><FileImage size={16}/></span><span><b>{item.filename}</b><small>#{item.id.slice(0, 8)} · {item.width}×{item.height}</small></span></div><span className="date-cell">{fmtDate(item.created_at)}</span><span><i className={`quality-dot ${item.quality === 'Basic checks passed' ? 'good' : ''}`}/>{item.quality}</span><span><i className="history-status-dot"/> Demo saved</span><button className="open-record" onClick={() => openHistory(item)} aria-label={`Open ${item.filename}`}><ArrowUpRight size={17}/></button></div>)}
          <div className="history-foot"><span><Database size={14}/> {history.length} record{history.length === 1 ? '' : 's'} loaded (up to 100)</span><span>Stored locally · SQLite</span></div>
        </div>
      </section>

      <section className="section about-section" id="about"><div className="about-copy"><div className="kicker">03 / PROJECT OVERVIEW</div><h2>Built for careful<br/><span>computer vision.</span></h2><p>The challenge is to develop a CNN-based system that can classify retinal disease categories, estimate severity, handle image variation, and highlight relevant regions — while making uncertainty clear.</p><p className="about-disclaimer">This starter provides the complete web workflow and a safe model-integration point. Real disease classification remains disabled until a trained model and validation process are supplied.</p></div><div className="feature-list"><div><span><ScanEye size={20}/></span><section><b>Fundus image workflow</b><p>Upload, preview, validate, and save an image screening record.</p></section></div><div><span><Activity size={20}/></span><section><b>CNN integration point</b><p>Swap the clearly marked demo function for your trained TensorFlow or PyTorch model.</p></section></div><div><span><ShieldCheck size={20}/></span><section><b>Explainability-ready</b><p>Designed to add Grad-CAM visualizations and confidence calibration after model validation.</p></section></div><div><span><Database size={20}/></span><section><b>Reproducible records</b><p>Store screening metadata in SQLite and export a compact CSV report.</p></section></div></div></section>
    </main>
    <footer><a className="brand footer-brand" href="#home"><span className="brand-icon"><ScanEye size={18}/></span><span><b>Retina<span className="blue">Sight</span></b><small>SCREENING STUDIO</small></span></a><span>CNN-Based Retinal Screening</span><span>Demo build · Not for clinical use</span></footer>
  </div>;
}
