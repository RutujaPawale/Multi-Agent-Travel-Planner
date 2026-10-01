import React, { useState, useEffect, useRef } from 'react';
import { TripRequest, TripResponse, LiveAgentEvent, User, AuthResponse } from './types';
import { TripForm } from './components/TripForm';
import { RawJsonViewer } from './components/RawJsonViewer';
import { ItineraryDisplay } from './components/ItineraryDisplay';
import { TripHistory } from './components/TripHistory';
import { LiveStatusFeed } from './components/LiveStatusFeed';
import { MyTripsView } from './components/MyTripsView';
import { AuthModal } from './components/AuthModal';
import { Plane, Code, LayoutDashboard, AlertCircle, Radio, LogIn, LogOut, BookmarkCheck } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export const App: React.FC = () => {
  // Authentication State
  // Note on storage tradeoff: We store the JWT token in localStorage for SPA simplicity,
  // demo ease, and persistence across browser reloads. In high-risk financial/banking
  // production environments, HttpOnly SameSite secure cookies should be used to eliminate XSS risks.
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('travel_planner_token'));
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('travel_planner_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);

  // Trips & Navigation State
  const [trips, setTrips] = useState<TripResponse[]>([]);
  const [currentTrip, setCurrentTrip] = useState<TripResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isFetchingTrips, setIsFetchingTrips] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'formatted' | 'my_trips' | 'live_feed' | 'raw_json'>('formatted');
  const [error, setError] = useState<string | null>(null);

  // Live WebSocket streaming state
  const [liveEvents, setLiveEvents] = useState<LiveAgentEvent[]>([]);
  const [activeTripId, setActiveTripId] = useState<string | null>(null);
  const [activeTripRequest, setActiveTripRequest] = useState<TripRequest | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'reconnecting' | 'polling' | 'disconnected'>('disconnected');

  const wsRef = useRef<WebSocket | null>(null);
  const pollTimerRef = useRef<any>(null);

  const fetchTrips = async (authToken?: string) => {
    const activeJwt = authToken || token;
    if (!activeJwt) {
      setTrips([]);
      return;
    }
    setIsFetchingTrips(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/trips`, {
        headers: {
          'Authorization': `Bearer ${activeJwt}`
        }
      });
      if (res.ok) {
        const data: TripResponse[] = await res.json();
        setTrips(data);
        if (data.length > 0 && !currentTrip) {
          setCurrentTrip(data[0]);
        }
      } else if (res.status === 401) {
        handleLogout();
      }
    } catch (err) {
      console.warn("Could not fetch trips from api-service:", err);
    } finally {
      setIsFetchingTrips(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchTrips(token);
    }
    return () => {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (_) {}
      }
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, [token]);

  const handleAuthSuccess = (authData: AuthResponse) => {
    setToken(authData.token);
    setUser(authData.user);
    localStorage.setItem('travel_planner_token', authData.token);
    localStorage.setItem('travel_planner_user', JSON.stringify(authData.user));
    setIsAuthModalOpen(false);
    setError(null);
    fetchTrips(authData.token);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('travel_planner_token');
    localStorage.removeItem('travel_planner_user');
    setTrips([]);
    setCurrentTrip(null);
    setIsAuthModalOpen(true);
  };

  const handleDeleteTrip = async (tripId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/trips/${tripId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!res.ok) {
        throw new Error(`Failed to delete trip (status ${res.status})`);
      }

      setTrips(prev => prev.filter(t => t.id !== tripId));
      if (currentTrip?.id === tripId) {
        const remaining = trips.filter(t => t.id !== tripId);
        setCurrentTrip(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err: any) {
      console.error("Trip deletion error:", err);
      setError(err.message || 'Could not delete trip');
    }
  };

  const handleTripSubmit = async (request: TripRequest) => {
    // Gate trip creation behind login
    if (!token) {
      setIsAuthModalOpen(true);
      return;
    }

    // 1. Generate client-side UUID so we can connect to WebSocket before/during orchestrator execution
    const tripId = crypto.randomUUID();
    setActiveTripId(tripId);
    setActiveTripRequest(request);
    setLiveEvents([]);
    setIsLoading(true);
    setError(null);
    setActiveTab('live_feed'); // Show live feed immediately

    let hasFinished = false;

    // Clean up any lingering connections
    if (wsRef.current) {
      try { wsRef.current.close(); } catch (_) {}
    }
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
    }

    // 2. Open WebSocket connection to agent-service
    const wsHost = window.location.hostname || 'localhost';
    const wsPort = import.meta.env.VITE_AGENT_PORT || '8000';
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProto}//${wsHost}:${wsPort}/ws/trip/${tripId}?token=${encodeURIComponent(token || '')}`;

    setConnectionStatus('connecting');

    const startPollingFallback = () => {
      if (hasFinished) return;
      setConnectionStatus('polling');
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);

      pollTimerRef.current = setInterval(async () => {
        if (hasFinished) {
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
          return;
        }
        try {
          // Poll agent-service in-memory events
          const resEvents = await fetch(`http://${wsHost}:${wsPort}/ws/trip/${tripId}/events?token=${encodeURIComponent(token || '')}`, {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
          });
          if (resEvents.ok) {
            const data = await resEvents.json();
            if (data.events && Array.isArray(data.events) && data.events.length > 0) {
              setLiveEvents(data.events);
            }
          }
          // Poll api-service for completed trip record
          const resTrip = await fetch(`${API_BASE_URL}/api/trips/${tripId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (resTrip.ok) {
            const tripData: TripResponse = await resTrip.json();
            if (tripData.status === 'COMPLETED' || tripData.status === 'FAILED') {
              hasFinished = true;
              if (pollTimerRef.current) clearInterval(pollTimerRef.current);
              setCurrentTrip(tripData);
              setTrips(prev => [tripData, ...prev.filter(t => t.id !== tripData.id)]);
              setIsLoading(false);
              setConnectionStatus('disconnected');
              setActiveTab('formatted');
            }
          }
        } catch (pollErr) {
          console.warn("Polling fallback error:", pollErr);
        }
      }, 2000);
    };

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus('connected');
      };

      ws.onmessage = (event) => {
        try {
          const msg: LiveAgentEvent = JSON.parse(event.data);
          setLiveEvents(prev => {
            const isDup = prev.some(e => e.agent === msg.agent && e.status === msg.status && e.message === msg.message && e.timestamp === msg.timestamp);
            if (isDup) return prev;
            return [...prev, msg];
          });
          if (msg.status === 'COMPLETED' || msg.status === 'FAILED') {
            hasFinished = true;
          }
        } catch (e) {
          console.warn("Failed to parse WebSocket event:", e);
        }
      };

      ws.onerror = (err) => {
        console.warn("WebSocket error, initiating fallback:", err);
        startPollingFallback();
      };

      ws.onclose = () => {
        if (!hasFinished) {
          startPollingFallback();
        } else {
          setConnectionStatus('disconnected');
        }
      };
    } catch (wsInitErr) {
      console.warn("Could not initiate WebSocket, falling back to polling:", wsInitErr);
      startPollingFallback();
    }

    // 3. Concurrently invoke API service POST /api/trips with client tripId & Auth Bearer token
    try {
      const res = await fetch(`${API_BASE_URL}/api/trips`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ ...request, tripId })
      });

      if (!res.ok) {
        if (res.status === 401) {
          handleLogout();
          throw new Error("Session expired. Please sign in again.");
        }
        throw new Error(`API returned status ${res.status}: ${res.statusText}`);
      }

      const tripData: TripResponse = await res.json();
      hasFinished = true;
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        try { wsRef.current.close(); } catch (_) {}
      }
      setConnectionStatus('disconnected');
      setCurrentTrip(tripData);
      setTrips(prev => [tripData, ...prev.filter(t => t.id !== tripData.id)]);

      // Transition smoothly to full structured itinerary view
      setActiveTab('formatted');
    } catch (err: any) {
      console.error("Trip creation failed:", err);
      setError(err.message || 'Failed to submit trip request.');
    } finally {
      setIsLoading(false);
    }
  };

  // Build events for display: either live streaming events or reconstructed from currentTrip.agentRuns
  const displayedEvents: LiveAgentEvent[] = (isLoading || (liveEvents.length > 0 && activeTripId === currentTrip?.id))
    ? liveEvents
    : (currentTrip?.agentRuns || []).map(run => {
        let msg = run.errorMessage || '';
        if (!msg && typeof run.outputData === 'object' && run.outputData !== null) {
          msg = run.outputData.reason || run.outputData.summary || run.outputData.filter_message || run.outputData.message || '';
        }
        if (!msg) {
          msg = `${run.agentName} executed with status ${run.status}`;
        }
        return {
          trip_id: currentTrip?.id || '',
          agent: run.agentName,
          status: run.status,
          message: msg,
          timestamp: run.createdAt,
          details: run.outputData
        };
      });

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <header style={{
        background: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-color)',
        padding: '12px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        {/* Brand */}
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
              JWT Auth • LangGraph • WebSocket Streaming • Spring Boot 3 • PostgreSQL
            </span>
          </div>
        </div>

        {/* View Switcher */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-input)',
          padding: '4px',
          borderRadius: '8px',
          border: '1px solid var(--border-color)',
          gap: '2px'
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
            <LayoutDashboard size={14} /> Planner & Itinerary
          </button>

          <button
            onClick={() => {
              if (!token) {
                setIsAuthModalOpen(true);
              } else {
                setActiveTab('my_trips');
              }
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              background: activeTab === 'my_trips' ? 'var(--accent-blue)' : 'transparent',
              color: activeTab === 'my_trips' ? '#ffffff' : 'var(--text-secondary)'
            }}
          >
            <BookmarkCheck size={14} /> My Trips ({trips.length})
          </button>

          <button
            onClick={() => setActiveTab('live_feed')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              background: activeTab === 'live_feed' ? 'var(--accent-blue)' : 'transparent',
              color: activeTab === 'live_feed' ? '#ffffff' : 'var(--text-secondary)'
            }}
          >
            <Radio size={14} color={isLoading ? '#34d399' : undefined} className={isLoading ? 'animate-pulse' : undefined} />
            Live Feed
            {isLoading && (
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#34d399' }} className="animate-pulse" />
            )}
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
            <Code size={14} /> Raw JSON
          </button>
        </div>

        {/* User Account / Auth Section */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {token && user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '5px 12px',
                borderRadius: '8px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-color)',
                fontSize: '13px'
              }}>
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '11px',
                  color: '#ffffff'
                }}>
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontWeight: 600, lineHeight: 1.2, color: '#ffffff' }}>{user.name}</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{user.email}</span>
                </div>
              </div>

              <button
                onClick={handleLogout}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 12px',
                  borderRadius: '6px',
                  background: 'rgba(244, 63, 94, 0.12)',
                  border: '1px solid rgba(244, 63, 94, 0.3)',
                  color: '#fb7185',
                  fontSize: '12px',
                  fontWeight: 600
                }}
                title="Sign out"
              >
                <LogOut size={13} /> Logout
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsAuthModalOpen(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                color: '#ffffff',
                fontSize: '13px',
                fontWeight: 600,
                boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
              }}
            >
              <LogIn size={14} /> Sign In / Register
            </button>
          )}
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

        {/* View: My Trips */}
        {activeTab === 'my_trips' ? (
          <MyTripsView
            trips={trips}
            onSelectTrip={(t) => {
              setCurrentTrip(t);
              setActiveTab('formatted');
            }}
            onDeleteTrip={handleDeleteTrip}
            onNewTrip={() => setActiveTab('formatted')}
            isLoading={isFetchingTrips}
          />
        ) : (
          /* Default Planner Layout */
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
                onSelectTrip={(t) => {
                  setCurrentTrip(t);
                  setActiveTripId(t.id);
                  setLiveEvents([]);
                }}
                onRefresh={() => fetchTrips()}
                isLoading={isFetchingTrips}
              />
            </div>

            {/* Right Column: Display Active View */}
            <div style={{ minWidth: 0 }}>
              {activeTab === 'raw_json' ? (
                <RawJsonViewer data={currentTrip} title="Live API / Agent Response JSON" />
              ) : activeTab === 'live_feed' || isLoading ? (
                <LiveStatusFeed
                  tripId={activeTripId || currentTrip?.id || ''}
                  events={displayedEvents}
                  connectionStatus={isLoading ? connectionStatus : 'disconnected'}
                  isComplete={!isLoading && !!currentTrip}
                  tripRequest={activeTripRequest}
                  onViewItinerary={() => setActiveTab('formatted')}
                  onViewRawJson={() => setActiveTab('raw_json')}
                />
              ) : (
                currentTrip ? (
                  <ItineraryDisplay trip={currentTrip} />
                ) : (
                  <RawJsonViewer data={null} />
                )
              )}
            </div>
          </div>
        )}
      </main>

      {/* Authentication Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onSuccess={handleAuthSuccess}
        onClose={() => setIsAuthModalOpen(false)}
        apiBaseUrl={API_BASE_URL}
      />

      <footer style={{
        textAlign: 'center',
        padding: '16px',
        fontSize: '12px',
        color: 'var(--text-muted)',
        borderTop: '1px solid var(--border-color)',
        background: 'var(--bg-secondary)'
      }}>
        Multi-Agent AI Travel Planner • JWT Authentication & User Trip History • LangGraph & WebSockets
      </footer>
    </div>
  );
};
