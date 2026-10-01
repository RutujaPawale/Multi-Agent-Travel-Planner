import React, { useState } from 'react';
import { AuthResponse } from '../types';
import { LogIn, UserPlus, Lock, Mail, User as UserIcon, AlertCircle, Loader2, Sparkles, X } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onSuccess: (authData: AuthResponse) => void;
  onClose?: () => void;
  apiBaseUrl: string;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onSuccess,
  onClose,
  apiBaseUrl
}) => {
  const [isLoginMode, setIsLoginMode] = useState<boolean>(true);
  const [email, setEmail] = useState<string>('alice@example.com');
  const [password, setPassword] = useState<string>('password123');
  const [name, setName] = useState<string>('Alice Travel');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const endpoint = isLoginMode ? `${apiBaseUrl}/api/auth/login` : `${apiBaseUrl}/api/auth/signup`;
    const payload = isLoginMode
      ? { email, password }
      : { email, password, name };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || (isLoginMode ? 'Login failed' : 'Registration failed'));
      }

      onSuccess(data);
    } catch (err: any) {
      setError(err.message || 'Authentication error. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickDemo = (userEmail: string, userName: string) => {
    setEmail(userEmail);
    setPassword('password123');
    setName(userName);
    setIsLoginMode(true);
    setError(null);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(5, 8, 16, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '16px'
    }}>
      <div style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '440px',
        overflow: 'hidden',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)'
      }}>
        {/* Header */}
        <div style={{
          padding: '24px 28px 18px',
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%)',
          borderBottom: '1px solid var(--border-color)',
          textAlign: 'center',
          position: 'relative'
        }}>
          {onClose && (
            <button
              onClick={onClose}
              type="button"
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <X size={18} />
            </button>
          )}
          <div style={{
            display: 'inline-flex',
            padding: '10px',
            background: 'var(--accent-blue)',
            borderRadius: '12px',
            marginBottom: '12px',
            boxShadow: '0 4px 14px rgba(59, 130, 246, 0.4)'
          }}>
            {isLoginMode ? <LogIn size={24} color="#ffffff" /> : <UserPlus size={24} color="#ffffff" />}
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#ffffff' }}>
            {isLoginMode ? 'Sign In to Travel Planner' : 'Create Travel Account'}
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {isLoginMode
              ? 'Access your saved trips, budget plans, and AI itinerary history'
              : 'Join to generate, save, and manage AI-powered travel itineraries'}
          </p>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: '24px 28px' }}>
          {error && (
            <div style={{
              background: 'rgba(244, 63, 94, 0.12)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              borderRadius: '8px',
              padding: '10px 14px',
              color: '#fb7185',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '18px'
            }}>
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {!isLoginMode && (
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Full Name
              </label>
              <div style={{ position: 'relative' }}>
                <UserIcon size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                <input
                  type="text"
                  required
                  placeholder="e.g. Alice Travel"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: '100%', paddingLeft: '38px' }}
                />
              </div>
            </div>
          )}

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              <input
                type="email"
                required
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ width: '100%', paddingLeft: '38px' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '22px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              <input
                type="password"
                required
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ width: '100%', paddingLeft: '38px' }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(59, 130, 246, 0.35)',
              opacity: isLoading ? 0.7 : 1
            }}
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>{isLoginMode ? 'Signing In...' : 'Creating Account...'}</span>
              </>
            ) : (
              <>
                {isLoginMode ? <LogIn size={16} /> : <UserPlus size={16} />}
                <span>{isLoginMode ? 'Sign In' : 'Sign Up'}</span>
              </>
            )}
          </button>

          {/* Toggle Login / Signup */}
          <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            {isLoginMode ? (
              <>
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setIsLoginMode(false); setError(null); }}
                  style={{ background: 'transparent', color: 'var(--accent-blue)', fontWeight: 600, textDecoration: 'underline' }}
                >
                  Create one now
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setIsLoginMode(true); setError(null); }}
                  style={{ background: 'transparent', color: 'var(--accent-blue)', fontWeight: 600, textDecoration: 'underline' }}
                >
                  Sign in
                </button>
              </>
            )}
          </div>

          {/* Quick Demo Pre-fills */}
          <div style={{
            marginTop: '20px',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Quick Demo Accounts
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={() => handleQuickDemo('alice@example.com', 'Alice Travel')}
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px'
                }}
              >
                <Sparkles size={12} color="#60a5fa" /> Alice (Default)
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemo('bob@example.com', 'Bob Explorer')}
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px'
                }}
              >
                <Sparkles size={12} color="#34d399" /> Bob (New User)
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
