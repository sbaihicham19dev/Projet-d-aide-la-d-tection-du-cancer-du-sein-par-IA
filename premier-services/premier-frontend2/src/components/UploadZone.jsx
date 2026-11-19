import { useRef, useState } from 'react';

export default function UploadZone({ onUpload, loading, error, preview }) {
  const inputRef = useRef();
  const [dragging, setDragging] = useState(false);

  const handleFile = (file) => {
    if (file && file.type.startsWith('image/')) {
      onUpload(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="upload-container">
      <div
        className={`upload-zone ${dragging ? 'dragging' : ''} ${loading ? 'loading' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !loading && inputRef.current.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files[0])}
        />

        {loading ? (
          <div className="loading-state">
            <div className="spinner" />
            <p>Analyse en cours...</p>
            <p className="loading-sub">Detection · Classification · BI-RADS · Narrative</p>
          </div>
        ) : preview ? (
          <div className="preview-state">
            <img src={preview} alt="Mammographie" className="preview-img" />
            <p>Analyse en cours...</p>
          </div>
        ) : (
          <div className="idle-state">
            <div className="upload-icon">+</div>
            <p>Glisser une mammographie ici</p>
            <p className="upload-sub">ou cliquer pour sélectionner</p>
            <p className="upload-formats">JPG, PNG, DICOM acceptés</p>
          </div>
        )}
      </div>

      {error && <div className="error-box">{error}</div>}
    </div>
  );
}