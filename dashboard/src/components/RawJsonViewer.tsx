import React, { useState } from 'react';
import { Copy, Check, Download, Code } from 'lucide-react';

interface RawJsonViewerProps {
  data: any;
  title?: string;
}

export const RawJsonViewer: React.FC<RawJsonViewerProps> = ({ data, title = "Raw JSON Response" }) => {
  const [copied, setCopied] = useState(false);

  if (!data) {
    return (
      <div style={{
        background: 'var(--bg-secondary)',
        borderRadius: 'var(--radius)',
        padding: '32px',
        textAlign: 'center',
        color: 'var(--text-muted)',
        border: '1px dashed var(--border-color)'
      }}>
        <Code size={36} style={{ marginBottom: '8px', opacity: 0.5 }} />
        <p>No trip response received yet. Submit the form above to generate itinerary data.</p>
      </div>
    );
  }

  const jsonString = JSON.stringify(data, null, 2);
  const lineCount = jsonString.split('\n').length;
  const byteCount = new Blob([jsonString]).size;

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trip-itinerary-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius)',
      border: '1px solid var(--border-color)',
      overflow: 'hidden',
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)'
    }}>
      {/* Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 18px',
        background: 'var(--bg-input)',
        borderBottom: '1px solid var(--border-color)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Code size={18} color="var(--accent-blue)" />
          <span style={{ fontWeight: 600, fontSize: '14px' }}>{title}</span>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            ({lineCount} lines, {(byteCount / 1024).toFixed(1)} KB)
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleCopy}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--bg-card)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '12px'
            }}
          >
            {copied ? <Check size={14} color="var(--accent-green)" /> : <Copy size={14} />}
            {copied ? 'Copied!' : 'Copy JSON'}
          </button>
          <button
            onClick={handleDownload}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--bg-card)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '12px'
            }}
          >
            <Download size={14} />
            Export
          </button>
        </div>
      </div>

      {/* JSON Preformatted Code */}
      <div style={{
        padding: '16px',
        maxHeight: '560px',
        overflowY: 'auto',
        overflowX: 'auto',
        background: '#070a12',
        fontSize: '13px',
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace'
      }}>
        <pre style={{ margin: 0, color: '#e2e8f0', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {jsonString}
        </pre>
      </div>
    </div>
  );
};
