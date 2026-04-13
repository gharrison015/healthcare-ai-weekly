'use client';

import { useState } from 'react';

export default function SubscribePage() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  async function handleSubscribe(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;

    setStatus('loading');
    try {
      const res = await fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus('success');
        setMessage(data.message === 'Already subscribed' ? 'You\'re already on the list.' : 'You\'re in. See you Friday.');
        setEmail('');
      } else {
        setStatus('error');
        setMessage(data.error || 'Something went wrong');
      }
    } catch {
      setStatus('error');
      setMessage('Network error. Try again.');
    }
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: 'calc(100vh - 120px)',
      padding: '40px 20px',
    }}>
      <div style={{
        maxWidth: 440,
        width: '100%',
        textAlign: 'center',
      }}>
        <h1 style={{
          fontSize: 32,
          fontWeight: 800,
          color: '#0f172a',
          marginBottom: 8,
        }}>
          Get the Brief
        </h1>
        <p style={{
          fontSize: 16,
          color: '#64748b',
          marginBottom: 32,
          lineHeight: 1.5,
        }}>
          AI healthcare intelligence delivered to your inbox every Friday morning. No spam, unsubscribe anytime.
        </p>

        {status === 'success' ? (
          <div style={{
            padding: '16px 24px',
            borderRadius: 12,
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            color: '#059669',
            fontWeight: 600,
            fontSize: 15,
          }}>
            {message}
          </div>
        ) : (
          <form onSubmit={handleSubscribe}>
            <input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setStatus('idle'); }}
              placeholder="you@company.com"
              required
              style={{
                width: '100%',
                padding: '14px 18px',
                borderRadius: 10,
                border: '1px solid #e2e8f0',
                fontSize: 15,
                color: '#0f172a',
                background: 'white',
                outline: 'none',
                fontFamily: 'inherit',
                boxSizing: 'border-box',
                marginBottom: 12,
              }}
            />
            <button
              type="submit"
              disabled={status === 'loading'}
              style={{
                width: '100%',
                padding: '14px 24px',
                borderRadius: 10,
                background: '#0284C7',
                color: 'white',
                fontSize: 15,
                fontWeight: 700,
                border: 'none',
                cursor: status === 'loading' ? 'wait' : 'pointer',
                fontFamily: 'inherit',
                transition: 'background 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#0369a1')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '#0284C7')}
            >
              {status === 'loading' ? 'Subscribing...' : 'Subscribe'}
            </button>
            {status === 'error' && (
              <div style={{ marginTop: 10, fontSize: 14, color: '#ef4444' }}>
                {message}
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
