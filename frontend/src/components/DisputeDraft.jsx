import { useState } from 'react';
import { Copy, Check, FileText } from 'lucide-react';
import './DisputeDraft.css';

export default function DisputeDraft({ draft }) {
  const [copied, setCopied] = useState(false);

  if (!draft) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(draft);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      const textarea = document.createElement('textarea');
      textarea.value = draft;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="dispute-card card animate-fade-in">
      <div className="dispute-header">
        <div className="dispute-title-group">
          <FileText size={18} className="dispute-icon" />
          <h3 className="section-title" style={{ marginBottom: 0 }}>Auto-Generated Dispute Draft</h3>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={handleCopy}>
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="dispute-text">{draft}</pre>
    </div>
  );
}
