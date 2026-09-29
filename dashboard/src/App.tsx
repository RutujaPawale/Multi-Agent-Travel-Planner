import React, { useState, useEffect } from 'react';
import { TripRequest, TripResponse } from './types';
import { TripForm } from './components/TripForm';
import { RawJsonViewer } from './components/RawJsonViewer';
import { ItineraryDisplay } from './components/ItineraryDisplay';
import { TripHistory } from './components/TripHistory';
import { Plane, Code, LayoutDashboard, AlertCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export const App: React.FC = () => {
  const [trips, setTrips] = useState<TripResponse[]>([]);
  const [currentTrip, setCurrentTrip] = useState<TripResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isFetchingTrips, setIsFetchingTrips] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'formatted' | 'raw_json'>('formatted');
  const [error, setError] = useState<string | null>(null);

  const fetchTrips = async () => {
    setIsFetchingTrips(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/trips`);
      if (res.ok) {
        const data = await res.json();
        setTrips(data);
        if (data.length > 0 && !currentTrip) {
          setCurrentTrip(data[0]);
        }
      }
    } catch (err) {
      console.warn("Could not fetch trips from api-service:", err);
    } finally {
      setIsFetchingTrips(false);
    }
  };

  useEffect(() => {
    fetchTrips();
  }, []);

  const handleTripSubmit = async (request: TripRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/trips`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });

      if (!res.ok) {
        throw new Error(`API returned status ${res.status}: ${res.statusText}`);
      }

      const tripData: TripResponse = await res.json();
      setCurrentTrip(tripData);
      setTrips(prev => [tripData, ...prev]);
    } catch (err: any) {
      console.error("Trip creation failed:", err);
      setError(err.message || 'Failed to submit trip request. Please verify that api-service is running on port 8080.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <header style={{
        background: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-color)',
        padding: '14px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            padding: '8px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Plane size={22} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.02em' }}>
              Multi-Agent AI Travel Planner
            </h1>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              FastAPI + LangGraph • Spring Boot • React TypeScript • PostgreSQL
            </span>
          </div>
        </div>

        {/* View Switcher */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-input)',
          padding: '4px',
          borderRadius: '8px',
          border: '1px solid var(--border-color)'
        }}>
          <button
            onClick={() => setActiveTab('formatted')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              background: activeTab === 'formatted' ? 'var(--accent-blue)' : 'transparent',
              color: activeTab === 'formatted' ? '#ffffff' : 'var(--text-secondary)'
            }}
          >
            <LayoutDashboard size={14} /> Structured UI
          </button>
          <button
            onClick={() => setActiveTab('raw_json')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              background: activeTab === 'raw_json' ? 'var(--accent-blue)' : 'transparent',
              color: activeTab === 'raw_json' ? '#ffffff' : 'var(--text-secondary)'
            }}
          >
            <Code size={14} /> Raw JSON Response
          </button>
        </div>
      </header>

      {/* Main Content Layout */}
      <main style={{
        maxWidth: '1440px',
        margin: '0 auto',
        padding: '24px',
        width: '100%',
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: '24px'
      }}>
        {error && (
          <div style={{
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: '8px',
            padding: '14px 18px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            color: '#fb7185',
            fontSize: '14px'
          }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(340px, 420px) 1fr',
          gap: '24px',
          alignItems: 'start'
        }}>
          {/* Left Column: Form & History */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <TripForm onSubmit={handleTripSubmit} isLoading={isLoading} />
            <TripHistory
              trips={trips}
              selectedTripId={currentTrip?.id || null}
              onSelectTrip={(t) => setCurrentTrip(t)}
              onRefresh={fetchTrips}
              isLoading={isFetchingTrips}
            />
          </div>

          {/* Right Column: Display Active View */}
          <div style={{ minWidth: 0 }}>
            {activeTab === 'raw_json' ? (
              <RawJsonViewer data={currentTrip} title="Live API / Agent Response JSON" />
            ) : (
              currentTrip ? (
                <ItineraryDisplay trip={currentTrip} />
              ) : (
                <RawJsonViewer data={null} />
              )
            )}
          </div>
        </div>
      </main>

      <footer style={{
        textAlign: 'center',
        padding: '16px',
        fontSize: '12px',
        color: 'var(--text-muted)',
        borderTop: '1px solid var(--border-color)',
        background: 'var(--bg-secondary)'
      }}>
        Multi-Agent AI Travel Planner • Powered by LangGraph Multi-Agent Orchestration & Duffel API
      </footer>
    </div>
  );
};
