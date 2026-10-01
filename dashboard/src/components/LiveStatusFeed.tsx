import React, { useEffect, useRef, useState } from 'react';
import { LiveAgentEvent, TripRequest } from '../types';
import {
  Plane,
  Building,
  Compass,
  Wallet,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Loader2,
  Radio,
  Clock,
  ChevronDown,
  ChevronRight,
  Code
} from 'lucide-react';

interface LiveStatusFeedProps {
  tripId: string;
  events: LiveAgentEvent[];
  connectionStatus: 'connecting' | 'connected' | 'reconnecting' | 'polling' | 'disconnected';
  isComplete: boolean;
  tripRequest?: TripRequest | null;
  onViewItinerary?: () => void;
  onViewRawJson?: () => void;
}

export const LiveStatusFeed: React.FC<LiveStatusFeedProps> = ({
  tripId,
  events,
  connectionStatus,
  isComplete,
  tripRequest,
  onViewItinerary,
  onViewRawJson
}) => {
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);

  // Auto-scroll to latest event as they arrive
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events, autoScroll]);

  const getAgentIcon = (agent: string) => {
    const lower = agent.toLowerCase();
    if (lower.includes('flight')) return <Plane size={16} color="#60a5fa" />;
    if (lower.includes('hotel')) return <Building size={16} color="#34d399" />;
    if (lower.includes('activity')) return <Compass size={16} color="#fbbf24" />;
    if (lower.includes('budget')) return <Wallet size={16} color="#a78bfa" />;
    if (lower.includes('synth')) return <Sparkles size={16} color="#f472b6" />;
    return <Radio size={16} color="#38bdf8" />;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'STARTED':
        return (
          <span className="badge badge-blue" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <Loader2 size={12} className="animate-spin" /> In Progress
          </span>
        );
      case 'SUCCESS':
        return (
          <span className="badge badge-green" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={12} /> Success
          </span>
        );
      case 'REPLANNING':
        return (
          <span
            className="badge badge-amber"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontWeight: 700,
              background: 'rgba(245, 158, 11, 0.25)',
              border: '1px solid #f59e0b'
            }}
          >
            <RefreshCw size={12} className="animate-spin" /> Re-planning
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="badge badge-purple" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <Sparkles size={12} /> Completed
          </span>
        );
      case 'FAILED':
        return (
          <span className="badge badge-rose" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <AlertCircle size={12} /> Failed
          </span>
        );
      default:
        return <span className="badge badge-blue">{status}</span>;
    }
  };

  const getConnectionPill = () => {
    switch (connectionStatus) {
      case 'connected':
        return (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: 'var(--accent-green)',
            background: 'rgba(16, 185, 129, 0.12)',
            padding: '4px 10px',
            borderRadius: '9999px',
            border: '1px solid rgba(16, 185, 129, 0.3)'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: 'var(--accent-green)',
              display: 'inline-block'
            }} className="animate-pulse" />
            <span>Live Streaming (WebSocket)</span>
          </div>
        );
      case 'connecting':
        return (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: '#60a5fa',
            background: 'rgba(59, 130, 246, 0.12)',
            padding: '4px 10px',
            borderRadius: '9999px',
            border: '1px solid rgba(59, 130, 246, 0.3)'
          }}>
            <Loader2 size={12} className="animate-spin" />
            <span>Connecting...</span>
          </div>
        );
      case 'reconnecting':
        return (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: '#fbbf24',
            background: 'rgba(245, 158, 11, 0.12)',
            padding: '4px 10px',
            borderRadius: '9999px',
            border: '1px solid rgba(245, 158, 11, 0.3)'
          }}>
            <RefreshCw size={12} className="animate-spin" />
            <span>Reconnecting WebSocket...</span>
          </div>
        );
      case 'polling':
        return (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: '#a78bfa',
            background: 'rgba(139, 92, 246, 0.12)',
            padding: '4px 10px',
            borderRadius: '9999px',
            border: '1px solid rgba(139, 92, 246, 0.3)'
          }}>
            <Radio size={12} />
            <span>Polling Fallback Active</span>
          </div>
        );
      case 'disconnected':
      default:
        return (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: 'var(--text-muted)',
            background: 'var(--bg-input)',
            padding: '4px 10px',
            borderRadius: '9999px',
            border: '1px solid var(--border-color)'
          }}>
            <CheckCircle2 size={12} color="var(--accent-green)" />
            <span>Stream Complete</span>
          </div>
        );
    }
  };

  // Re-planning count
  const replanEvents = events.filter(e => e.status === 'REPLANNING');

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius)',
      border: '1px solid var(--border-color)',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)'
    }}>
      {/* Header */}
      <div style={{
        padding: '18px 24px',
        borderBottom: '1px solid var(--border-color)',
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(139, 92, 246, 0.08) 100%)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'rgba(59, 130, 246, 0.2)',
            padding: '8px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Radio size={20} color="#60a5fa" />
          </div>
          <div>
            <h2 style={{ fontSize: '17px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              Real-Time Agent Execution Feed
              {replanEvents.length > 0 && (
                <span className="badge badge-amber" style={{ fontSize: '11px' }}>
                  {replanEvents.length} Re-Plan Cycle{replanEvents.length > 1 ? 's' : ''}
                </span>
              )}
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              LangGraph Multi-Agent Orchestration • Trip ID: <code style={{ color: '#93c5fd' }}>{tripId ? tripId.substring(0, 8) + '...' : 'pending'}</code>
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {getConnectionPill()}
          {onViewRawJson && (
            <button
              onClick={onViewRawJson}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                background: 'var(--bg-card)',
                color: 'var(--text-secondary)',
                border: '1px solid var(--border-color)'
              }}
              title="Inspect raw events"
            >
              <Code size={14} /> Debug
            </button>
          )}
        </div>
      </div>

      {/* Target Trip Banner */}
      {tripRequest && (
        <div style={{
          padding: '10px 24px',
          background: 'var(--bg-input)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '13px',
          color: 'var(--text-secondary)',
          flexWrap: 'wrap',
          gap: '8px'
        }}>
          <div>
            <strong style={{ color: '#ffffff' }}>{tripRequest.origin} → {tripRequest.destination}</strong>
            <span style={{ margin: '0 8px', color: 'var(--text-muted)' }}>•</span>
            <span>{tripRequest.startDate} to {tripRequest.endDate}</span>
          </div>
          <div>
            <span>Target Budget: <strong style={{ color: '#34d399' }}>${tripRequest.budget.toLocaleString()}</strong></span>
          </div>
        </div>
      )}

      {/* Event Stream Container */}
      <div style={{
        padding: '20px 24px',
        maxHeight: '520px',
        minHeight: '280px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        {events.length === 0 ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '48px 16px',
            textAlign: 'center',
            color: 'var(--text-muted)'
          }}>
            <Loader2 size={32} className="animate-spin" color="#3b82f6" style={{ marginBottom: '12px' }} />
            <p style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Connecting to agent orchestrator...</p>
            <p style={{ fontSize: '12px', marginTop: '4px' }}>
              Streaming agent execution steps for flights, hotels, activities, and budget evaluation.
            </p>
          </div>
        ) : (
          events.map((evt, idx) => {
            const isReplan = evt.status === 'REPLANNING';
            const isFailed = evt.status === 'FAILED';
            const isStarted = evt.status === 'STARTED';
            const isCompleted = evt.status === 'COMPLETED';
            const isExpanded = expandedIndex === idx;

            // Distinct card styling for re-planning and standard steps
            const cardBg = isReplan
              ? 'rgba(245, 158, 11, 0.08)'
              : isFailed
              ? 'rgba(244, 63, 94, 0.08)'
              : 'var(--bg-card)';

            const cardBorder = isReplan
              ? 'rgba(245, 158, 11, 0.4)'
              : isFailed
              ? 'rgba(244, 63, 94, 0.4)'
              : isCompleted
              ? 'rgba(16, 185, 129, 0.4)'
              : 'var(--border-color)';

            return (
              <div
                key={idx}
                style={{
                  background: cardBg,
                  border: `1px solid ${cardBorder}`,
                  borderRadius: '10px',
                  padding: '14px 16px',
                  transition: 'all 0.2s ease',
                  borderLeft: isReplan ? '4px solid #f59e0b' : (isCompleted ? '4px solid #10b981' : undefined)
                }}
              >
                {/* Event Top Bar */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px',
                  flexWrap: 'wrap',
                  gap: '8px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                      padding: '5px',
                      borderRadius: '6px',
                      background: 'var(--bg-input)',
                      display: 'flex',
                      alignItems: 'center'
                    }}>
                      {getAgentIcon(evt.agent)}
                    </div>
                    <span style={{ fontWeight: 700, fontSize: '14px', color: '#ffffff' }}>
                      {evt.agent}
                    </span>
                    {getStatusBadge(evt.status)}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
                    <Clock size={12} />
                    <span>{evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : 'Just now'}</span>
                  </div>
                </div>

                {/* Event Message */}
                <div style={{
                  fontSize: '13px',
                  lineHeight: '1.5',
                  color: isReplan ? '#fef3c7' : (isStarted ? '#93c5fd' : 'var(--text-primary)'),
                  fontWeight: isReplan ? 600 : 400
                }}>
                  {evt.message}
                </div>

                {/* Re-planning adaptive callout */}
                {isReplan && (
                  <div style={{
                    marginTop: '10px',
                    padding: '8px 12px',
                    background: 'rgba(245, 158, 11, 0.15)',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: '#fbbf24',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <RefreshCw size={14} className="animate-spin" />
                    <span><strong>Adaptive Loop Triggered:</strong> Re-routing graph to re-query with lower spending cap.</span>
                  </div>
                )}

                {/* Collapsible Details */}
                {evt.details && Object.keys(evt.details).length > 0 && (
                  <div style={{ marginTop: '8px' }}>
                    <button
                      onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                      style={{
                        background: 'transparent',
                        color: 'var(--text-muted)',
                        fontSize: '11px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '2px 0'
                      }}
                    >
                      {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      {isExpanded ? 'Hide payload' : 'View payload'}
                    </button>

                    {isExpanded && (
                      <pre style={{
                        marginTop: '6px',
                        padding: '10px',
                        background: '#080c16',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        fontSize: '11px',
                        color: '#94a3b8',
                        overflowX: 'auto',
                        maxHeight: '180px'
                      }}>
                        {JSON.stringify(evt.details, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      {/* Footer controls & completion action */}
      <div style={{
        padding: '14px 24px',
        borderTop: '1px solid var(--border-color)',
        background: 'var(--bg-input)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
          />
          Auto-scroll live feed
        </label>

        {isComplete && onViewItinerary && (
          <button
            onClick={onViewItinerary}
            style={{
              padding: '8px 18px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
            }}
          >
            <Sparkles size={14} /> View Final Itinerary
          </button>
        )}
      </div>
    </div>
  );
};
