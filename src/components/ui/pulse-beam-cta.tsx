'use client';

import { useState } from 'react';

export function PulseBeamCTA() {
  const [showForm, setShowForm] = useState(false);
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
        setMessage(data.message === 'Already subscribed' ? 'You\'re already subscribed!' : 'You\'re in! See you Friday.');
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
    <div
      className="relative flex justify-center overflow-hidden"
      style={{ padding: "4px 0 2px" }}
    >
      {/* Beam SVG background */}
      <div className="absolute inset-0 pointer-events-none">
        <svg
          viewBox="0 0 800 120"
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          <path d="M0 60 H340" stroke="rgba(15, 29, 53, 0.08)" strokeWidth="1" fill="none" />
          <path d="M460 60 H800" stroke="rgba(15, 29, 53, 0.08)" strokeWidth="1" fill="none" />
          <path d="M200 0 C200 40 340 60 340 60" stroke="rgba(15, 29, 53, 0.08)" strokeWidth="1" fill="none" />
          <path d="M600 0 C600 40 460 60 460 60" stroke="rgba(15, 29, 53, 0.08)" strokeWidth="1" fill="none" />
          <path d="M100 120 C100 80 340 60 340 60" stroke="rgba(15, 29, 53, 0.08)" strokeWidth="1" fill="none" />
          <path d="M700 120 C700 80 460 60 460 60" stroke="rgba(15, 29, 53, 0.08)" strokeWidth="1" fill="none" />

          <path d="M0 60 H340" stroke="url(#beam-grad-1)" strokeWidth="2" fill="none" strokeLinecap="round" />
          <path d="M460 60 H800" stroke="url(#beam-grad-2)" strokeWidth="2" fill="none" strokeLinecap="round" />
          <path d="M200 0 C200 40 340 60 340 60" stroke="url(#beam-grad-3)" strokeWidth="2" fill="none" strokeLinecap="round" />
          <path d="M600 0 C600 40 460 60 460 60" stroke="url(#beam-grad-4)" strokeWidth="2" fill="none" strokeLinecap="round" />
          <path d="M100 120 C100 80 340 60 340 60" stroke="url(#beam-grad-5)" strokeWidth="2" fill="none" strokeLinecap="round" />
          <path d="M700 120 C700 80 460 60 460 60" stroke="url(#beam-grad-6)" strokeWidth="2" fill="none" strokeLinecap="round" />

          <circle cx="0" cy="60" r="3" fill="rgba(15, 29, 53, 0.15)" />
          <circle cx="800" cy="60" r="3" fill="rgba(15, 29, 53, 0.15)" />
          <circle cx="200" cy="0" r="3" fill="rgba(15, 29, 53, 0.15)" />
          <circle cx="600" cy="0" r="3" fill="rgba(15, 29, 53, 0.15)" />
          <circle cx="100" cy="120" r="3" fill="rgba(15, 29, 53, 0.15)" />
          <circle cx="700" cy="120" r="3" fill="rgba(15, 29, 53, 0.15)" />

          <defs>
            {[
              { id: 1, dur: "3s", begin: "0s" },
              { id: 2, dur: "3.5s", begin: "0.5s" },
              { id: 3, dur: "2.5s", begin: "1s" },
              { id: 4, dur: "2.8s", begin: "1.5s" },
              { id: 5, dur: "3.2s", begin: "0.8s" },
              { id: 6, dur: "2.6s", begin: "1.2s" },
            ].map(({ id, dur, begin }) => (
              <linearGradient
                key={id}
                id={`beam-grad-${id}`}
                gradientUnits="userSpaceOnUse"
              >
                <stop offset="0%" stopColor="#18CCFC" stopOpacity="0">
                  <animate attributeName="offset" values="-1;1" dur={dur} begin={begin} repeatCount="indefinite" />
                </stop>
                <stop offset="30%" stopColor="#6344F5" stopOpacity="0.8">
                  <animate attributeName="offset" values="-0.7;1.3" dur={dur} begin={begin} repeatCount="indefinite" />
                </stop>
                <stop offset="60%" stopColor="#AE48FF" stopOpacity="0">
                  <animate attributeName="offset" values="-0.4;1.6" dur={dur} begin={begin} repeatCount="indefinite" />
                </stop>
              </linearGradient>
            ))}
          </defs>
        </svg>
      </div>

      {/* CTA / Subscribe */}
      <div className="relative z-[2]">
        {status === 'success' ? (
          <div
            style={{
              padding: "10px 28px",
              borderRadius: "40px",
              background: "#0a1628",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              boxShadow: "0 0 20px rgba(56, 189, 248, 0.1), 0 4px 16px rgba(0, 0, 0, 0.15)",
            }}
          >
            <span
              style={{
                fontSize: "14px",
                fontWeight: 700,
                background: "linear-gradient(to right, #34d399, #10b981)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              {message}
            </span>
          </div>
        ) : showForm ? (
          <form onSubmit={handleSubscribe} className="flex items-center gap-2">
            <input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setStatus('idle'); }}
              placeholder="your@email.com"
              required
              autoFocus
              style={{
                padding: "9px 16px",
                borderRadius: "40px",
                background: "rgba(10, 22, 40, 0.6)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                color: "#e2e8f0",
                fontSize: "14px",
                width: "220px",
                outline: "none",
                fontFamily: "inherit",
              }}
            />
            <button
              type="submit"
              disabled={status === 'loading'}
              className="cta-button"
              style={{
                padding: "10px 24px",
                borderRadius: "40px",
                background: "#0a1628",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                boxShadow: "0 0 20px rgba(56, 189, 248, 0.1), 0 4px 16px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.05)",
                cursor: status === 'loading' ? 'wait' : 'pointer',
                transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
              }}
            >
              <span
                style={{
                  fontSize: "14px",
                  fontWeight: 700,
                  letterSpacing: "0.3px",
                  background: "linear-gradient(to right, #cbd5e1, #64748b, #cbd5e1)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                {status === 'loading' ? 'Subscribing...' : 'Go'}
              </span>
            </button>
          </form>
        ) : (
          <button
            onClick={() => setShowForm(true)}
            className="cta-button relative cursor-pointer"
            style={{
              padding: "10px 28px",
              borderRadius: "40px",
              background: "#0a1628",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              boxShadow:
                "0 0 20px rgba(56, 189, 248, 0.1), 0 4px 16px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.05)",
              transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            <span
              style={{
                fontSize: "15px",
                fontWeight: 700,
                letterSpacing: "0.3px",
                background: "linear-gradient(to right, #cbd5e1, #64748b, #cbd5e1)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Subscribe
            </span>
          </button>
        )}
        {status === 'error' && (
          <div style={{ textAlign: 'center', marginTop: 6, fontSize: 13, color: '#f87171' }}>
            {message}
          </div>
        )}
      </div>

      <style
        dangerouslySetInnerHTML={{
          __html: `
            .cta-button:hover {
              box-shadow: 0 0 32px rgba(56, 189, 248, 0.2), 0 4px 20px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
              transform: scale(1.03);
            }
            .cta-button::before {
              content: '';
              position: absolute; inset: 0; border-radius: 60px;
              background: radial-gradient(75% 100% at 50% 0%, rgba(56, 189, 248, 0.4) 0%, transparent 75%);
              opacity: 0;
              transition: opacity 0.4s;
            }
            .cta-button:hover::before { opacity: 1; }
            .cta-button:hover span {
              background: linear-gradient(to right, #e2e8f0, #94a3b8, #e2e8f0) !important;
              -webkit-background-clip: text !important;
              background-clip: text !important;
            }
          `,
        }}
      />
    </div>
  );
}
