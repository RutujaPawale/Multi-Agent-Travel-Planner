import React, { useState } from 'react';
import { TripRequest } from '../types';
import { Send, Sparkles, Calendar, DollarSign, MapPin, Tag } from 'lucide-react';

interface TripFormProps {
  onSubmit: (request: TripRequest) => void;
  isLoading: boolean;
}

export const TripForm: React.FC<TripFormProps> = ({ onSubmit, isLoading }) => {
  const [origin, setOrigin] = useState('JFK');
  const [destination, setDestination] = useState('CDG');
  const [startDate, setStartDate] = useState('2026-10-15');
  const [endDate, setEndDate] = useState('2026-10-22');
  const [budget, setBudget] = useState(2500);
  const [preferences, setPreferences] = useState('Central boutique hotel, art museums, walking food tours');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!origin.trim() || !destination.trim() || !startDate || !endDate) {
      alert('Please fill in Origin, Destination, Start Date, and End Date.');
      return;
    }
    onSubmit({
      origin: origin.trim().toUpperCase(),
      destination: destination.trim().toUpperCase(),
      startDate,
      endDate,
      budget: Number(budget),
      preferences: preferences.trim()
    });
  };

  const applyPreset = (presetOrigin: string, presetDest: string, presetBudget: number, presetPref: string) => {
    setOrigin(presetOrigin);
    setDestination(presetDest);
    setBudget(presetBudget);
    setPreferences(presetPref);
  };

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius)',
      padding: '24px',
      border: '1px solid var(--border-color)',
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={20} color="var(--accent-blue)" />
          Plan New Itinerary
        </h2>
        <span className="badge badge-blue">Multi-Agent LangGraph</span>
      </div>

      {/* Preset Buttons */}
      <div style={{ marginBottom: '16px' }}>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
          Quick Demo Presets:
        </span>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <button
            type="button"
            onClick={() => applyPreset('JFK', 'CDG', 2500, 'Boutique hotel in Le Marais, Michelin star dining, Louvre & Orsay')}
            style={{
              background: 'var(--bg-input)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '12px'
            }}
          >
            🇫🇷 NYC → Paris ($2500)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('SFO', 'HND', 3200, 'Shinjuku/Shibuya base, Ramen tasting, teamLab Borderless, Akihabara')}
            style={{
              background: 'var(--bg-input)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '12px'
            }}
          >
            🇯🇵 SFO → Tokyo ($3200)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('LHR', 'DXB', 2200, 'Luxury beach resort, Desert safari with BBQ, Burj Khalifa sky deck')}
            style={{
              background: 'var(--bg-input)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '12px'
            }}
          >
            🇦🇪 London → Dubai ($2200)
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Origin & Destination */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <MapPin size={14} color="var(--accent-cyan)" /> Origin (City or IATA)
            </label>
            <input
              type="text"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="e.g. JFK or New York"
              required
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <MapPin size={14} color="var(--accent-rose)" /> Destination (City or IATA)
            </label>
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. CDG or Paris"
              required
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Start Date & End Date */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <Calendar size={14} color="var(--accent-amber)" /> Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <Calendar size={14} color="var(--accent-amber)" /> End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              required
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Budget */}
        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
            <DollarSign size={14} color="var(--accent-green)" /> Budget (USD)
          </label>
          <input
            type="number"
            min="100"
            step="50"
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            required
            style={{ width: '100%' }}
          />
        </div>

        {/* Preferences */}
        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
            <Tag size={14} color="var(--accent-purple)" /> Travel Preferences & Special Notes
          </label>
          <textarea
            rows={2}
            value={preferences}
            onChange={(e) => setPreferences(e.target.value)}
            placeholder="e.g. Vegetarian dining, non-stop flights preferred, quiet boutique hotel"
            style={{ width: '100%', resize: 'vertical' }}
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          style={{
            marginTop: '8px',
            backgroundColor: isLoading ? 'var(--text-muted)' : 'var(--accent-blue)',
            color: '#ffffff',
            fontWeight: 600,
            padding: '12px 20px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '15px',
            boxShadow: '0 4px 14px rgba(59, 130, 246, 0.4)',
            transition: 'background-color 0.2s, transform 0.1s'
          }}
        >
          {isLoading ? (
            <>
              <div style={{ width: '18px', height: '18px', border: '2px solid #fff', borderTopColor: 'transparent', borderRadius: '50%' }} className="animate-spin" />
              <span>Orchestrating Agents (LangGraph Pipeline)...</span>
            </>
          ) : (
            <>
              <Send size={16} />
              <span>Generate Multi-Agent Travel Plan</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
