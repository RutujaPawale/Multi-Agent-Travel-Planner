import React, { useState } from 'react';
import { TripResponse, FlightOption, HotelOption, ActivityOption, AgentRun } from '../types';
import { Plane, Building, Compass, Wallet, Database, Clock, ChevronDown, ChevronRight, CheckCircle2, AlertCircle } from 'lucide-react';

interface ItineraryDisplayProps {
  trip: TripResponse;
}

export const ItineraryDisplay: React.FC<ItineraryDisplayProps> = ({ trip }) => {
  const [activeTab, setActiveTab] = useState<'flights' | 'hotels' | 'activities' | 'budget' | 'agent_runs'>('flights');
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);

  const rawResult = trip.itineraryResult || {};
  const itinerary = rawResult.final_itinerary || rawResult;
  const flights: FlightOption[] = itinerary.flights?.all_options || rawResult.flight_options || [];
  const hotels: HotelOption[] = itinerary.accommodation?.all_options || rawResult.hotel_options || [];
  const activities: ActivityOption[] = itinerary.activities?.highlights || rawResult.activity_options || [];
  const budget = itinerary.financial_overview || rawResult.budget_summary;
  const agentRuns: AgentRun[] = trip.agentRuns || [];

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius)',
      border: '1px solid var(--border-color)',
      overflow: 'hidden',
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)'
    }}>
      {/* Header Banner */}
      <div style={{
        padding: '20px 24px',
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%)',
        borderBottom: '1px solid var(--border-color)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <span className="badge badge-green" style={{ marginBottom: '6px' }}>
              {trip.status}
            </span>
            <h1 style={{ fontSize: '20px', fontWeight: 700, marginTop: '4px' }}>
              {itinerary.title || `${trip.origin} → ${trip.destination}`}
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '2px' }}>
              {itinerary.summary || `Travel plan from ${trip.origin} to ${trip.destination} (${trip.startDate} - ${trip.endDate})`}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '16px', background: 'var(--bg-input)', padding: '10px 16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Target Budget</div>
              <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-green)' }}>
                ${Number(trip.budget).toLocaleString()}
              </div>
            </div>
            <div style={{ width: '1px', background: 'var(--border-color)' }} />
            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Dates</div>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>
                {trip.startDate} to {trip.endDate}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-color)',
        background: 'var(--bg-card)',
        overflowX: 'auto'
      }}>
        <button
          onClick={() => setActiveTab('flights')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            fontSize: '13px',
            fontWeight: 600,
            color: activeTab === 'flights' ? 'var(--accent-blue)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'flights' ? '2px solid var(--accent-blue)' : '2px solid transparent',
            background: 'transparent'
          }}
        >
          <Plane size={16} /> Flights ({flights.length})
        </button>

        <button
          onClick={() => setActiveTab('hotels')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            fontSize: '13px',
            fontWeight: 600,
            color: activeTab === 'hotels' ? 'var(--accent-blue)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'hotels' ? '2px solid var(--accent-blue)' : '2px solid transparent',
            background: 'transparent'
          }}
        >
          <Building size={16} /> Hotels ({hotels.length})
        </button>

        <button
          onClick={() => setActiveTab('activities')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            fontSize: '13px',
            fontWeight: 600,
            color: activeTab === 'activities' ? 'var(--accent-blue)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'activities' ? '2px solid var(--accent-blue)' : '2px solid transparent',
            background: 'transparent'
          }}
        >
          <Compass size={16} /> Activities (Stub)
        </button>

        <button
          onClick={() => setActiveTab('budget')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            fontSize: '13px',
            fontWeight: 600,
            color: activeTab === 'budget' ? 'var(--accent-blue)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'budget' ? '2px solid var(--accent-blue)' : '2px solid transparent',
            background: 'transparent'
          }}
        >
          <Wallet size={16} /> Budget Breakdown (Stub)
        </button>

        <button
          onClick={() => setActiveTab('agent_runs')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            fontSize: '13px',
            fontWeight: 600,
            color: activeTab === 'agent_runs' ? 'var(--accent-blue)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'agent_runs' ? '2px solid var(--accent-blue)' : '2px solid transparent',
            background: 'transparent'
          }}
        >
          <Database size={16} /> PostgreSQL Agent Runs ({agentRuns.length})
        </button>
      </div>

      {/* Tab Content */}
      <div style={{ padding: '24px' }}>
        {/* FLIGHTS TAB */}
        {activeTab === 'flights' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Top 3 Flight Options (Ranked by Price)
              </h3>
              <span className="badge badge-purple">
                {flights[0]?.is_mock ? 'Mock Fallback' : (flights[0]?.source || 'Live API')}
              </span>
            </div>

            {flights.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No flight results found.</p>
            ) : (
              flights.map((flight, idx) => (
                <div
                  key={flight.id || idx}
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '16px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '16px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '50%',
                      background: idx === 0 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.1)',
                      color: idx === 0 ? 'var(--accent-green)' : 'var(--accent-blue)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '14px'
                    }}>
                      #{idx + 1}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {flight.airline} ({flight.flight_number})
                        {idx === 0 && <span className="badge badge-green">Cheapest Option</span>}
                      </div>
                      <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        Route: {flight.origin} → {flight.destination} • Duration: {flight.duration} • Stops: {flight.stops}
                      </div>
                      {flight.departure_time && (
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Dep: {flight.departure_time} | Arr: {flight.arrival_time}
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--accent-green)' }}>
                      ${Number(flight.price).toFixed(2)}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Total {flight.currency} (1 adult)
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* HOTELS TAB */}
        {activeTab === 'hotels' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 600 }}>
                Top 3 Hotel Options (Ranked by Rating & Price)
              </h3>
              <span className="badge badge-purple">
                {hotels[0]?.is_mock ? 'Mock Fallback' : (hotels[0]?.source || 'Live API')}
              </span>
            </div>

            {hotels.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No hotel results found within budget cap.</p>
            ) : (
              hotels.map((hotel, idx) => (
                <div
                  key={hotel.id || idx}
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '50%',
                      background: idx === 0 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.1)',
                      color: idx === 0 ? 'var(--accent-green)' : 'var(--accent-blue)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '14px',
                      flexShrink: 0
                    }}>
                      #{idx + 1}
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 600, fontSize: '15px' }}>{hotel.name}</span>
                        {idx === 0 && <span className="badge badge-green">Top Pick</span>}
                        <span style={{ fontSize: '12px', color: 'var(--accent-amber)', fontWeight: 600 }}>
                          ★ {Number(hotel.rating).toFixed(1)}
                        </span>
                        {hotel.tier && <span className="badge badge-blue">{hotel.tier}</span>}
                      </div>

                      {hotel.neighborhood && (
                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                          Location: {hotel.neighborhood}
                        </div>
                      )}

                      {hotel.notes && (
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', fontStyle: 'italic' }}>
                          ℹ️ {hotel.notes}
                        </div>
                      )}

                      {hotel.link && (
                        <div style={{ marginTop: '6px' }}>
                          <a
                            href={hotel.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ fontSize: '12px', color: 'var(--accent-blue)', textDecoration: 'none' }}
                          >
                            🔗 Identifier: {hotel.id}
                          </a>
                        </div>
                      )}

                      {hotel.amenities && hotel.amenities.length > 0 && (
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
                          {hotel.amenities.map((amenity, aIdx) => (
                            <span key={aIdx} style={{ fontSize: '11px', background: 'var(--bg-input)', padding: '2px 8px', borderRadius: '4px', color: 'var(--text-muted)' }}>
                              {amenity}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--accent-blue)' }}>
                      ${Number(hotel.price_per_night).toFixed(2)}/night
                    </div>
                    {hotel.total_price && (
                      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginTop: '2px' }}>
                        Total: ${Number(hotel.total_price).toFixed(2)} {hotel.currency}
                      </div>
                    )}
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Allocated Lodging Budget
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* ACTIVITIES TAB */}
        {activeTab === 'activities' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Recommended Activities (Stubbed Agent)</h3>
              <span className="badge badge-amber">Stub Data</span>
            </div>

            {activities.map((act, idx) => (
              <div
                key={act.id || idx}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '16px 20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  flexWrap: 'wrap',
                  gap: '12px'
                }}
              >
                <div style={{ maxWidth: '75%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 600, fontSize: '15px' }}>{act.name}</span>
                    <span className="badge badge-purple">{act.category}</span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                    {act.description}
                  </p>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
                    Duration: {act.duration} • Rating: ★ {act.rating}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--accent-purple)' }}>
                    ${act.estimated_cost}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Per participant</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* BUDGET TAB */}
        {activeTab === 'budget' && budget && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Financial Projection (Stubbed Agent)</h3>
              <span className={`badge ${budget.remaining_surplus_deficit >= 0 ? 'badge-green' : 'badge-rose'}`}>
                {budget.budget_health}
              </span>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '14px'
            }}>
              <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Estimated Flights</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                  ${budget.estimated_flight_cost}
                </div>
              </div>

              <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Hotels ({budget.trip_duration_nights} nights)</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                  ${budget.estimated_hotel_cost}
                </div>
              </div>

              <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Activities & Tours</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                  ${budget.estimated_activities_cost}
                </div>
              </div>

              <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Buffer / Incidentals</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                  ${budget.estimated_miscellaneous}
                </div>
              </div>
            </div>

            <div style={{
              background: 'var(--bg-input)',
              padding: '16px 20px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <div>
                <div style={{ fontWeight: 600 }}>Total Projected Cost: ${budget.total_estimated_expense}</div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {budget.recommendation}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Net Balance</div>
                <div style={{
                  fontSize: '18px',
                  fontWeight: 700,
                  color: budget.remaining_surplus_deficit >= 0 ? 'var(--accent-green)' : 'var(--accent-rose)'
                }}>
                  {budget.remaining_surplus_deficit >= 0 ? `+$${budget.remaining_surplus_deficit}` : `-$${Math.abs(budget.remaining_surplus_deficit)}`}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* POSTGRESQL AGENT RUNS TAB */}
        {activeTab === 'agent_runs' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600 }}>PostgreSQL `agent_runs` Execution Log</h3>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Records captured in real-time by the orchestrator and agents into PostgreSQL.
                </p>
              </div>
              <span className="badge badge-blue">{agentRuns.length} Steps Recorded</span>
            </div>

            {agentRuns.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No agent run records in database for this trip.</p>
            ) : (
              agentRuns.map((run, idx) => {
                const isExpanded = expandedRunId === (run.id || String(idx));
                return (
                  <div
                    key={run.id || idx}
                    style={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      overflow: 'hidden'
                    }}
                  >
                    <div
                      onClick={() => setExpandedRunId(isExpanded ? null : (run.id || String(idx)))}
                      style={{
                        padding: '12px 16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        background: 'var(--bg-input)'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        {run.status === 'SUCCESS' || run.status === 'COMPLETED' ? (
                          <CheckCircle2 size={16} color="var(--accent-green)" />
                        ) : (
                          <AlertCircle size={16} color="var(--accent-amber)" />
                        )}
                        <span style={{ fontWeight: 600, fontSize: '14px' }}>
                          Step {idx + 1}: {run.agentName}
                        </span>
                        <span className={`badge ${run.status === 'SUCCESS' || run.status === 'COMPLETED' ? 'badge-green' : 'badge-blue'}`}>
                          {run.status}
                        </span>
                        {run.errorMessage && (
                          <span className="badge badge-amber" title={run.errorMessage} style={{ fontSize: '11px' }}>
                            Fallback: {run.errorMessage.length > 35 ? run.errorMessage.substring(0, 35) + '...' : run.errorMessage}
                          </span>
                        )}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        <Clock size={12} />
                        {run.createdAt ? new Date(run.createdAt).toLocaleTimeString() : 'N/A'}
                      </div>
                    </div>

                    {isExpanded && (
                      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', background: '#080c16' }}>
                        {run.errorMessage && (
                          <div style={{
                            background: 'rgba(245, 158, 11, 0.1)',
                            border: '1px solid rgba(245, 158, 11, 0.3)',
                            borderRadius: '6px',
                            padding: '10px 14px',
                            color: '#fbbf24',
                            fontSize: '12px'
                          }}>
                            <strong>Fallback Notice / Reason:</strong> {run.errorMessage}
                          </div>
                        )}
                        <div>
                          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                            Agent Input Data:
                          </div>
                          <pre style={{
                            background: 'var(--bg-input)',
                            padding: '10px',
                            borderRadius: '6px',
                            fontSize: '12px',
                            overflowX: 'auto',
                            color: '#93c5fd'
                          }}>
                            {JSON.stringify(run.inputData, null, 2)}
                          </pre>
                        </div>

                        <div>
                          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                            Agent Output Data:
                          </div>
                          <pre style={{
                            background: 'var(--bg-input)',
                            padding: '10px',
                            borderRadius: '6px',
                            fontSize: '12px',
                            overflowX: 'auto',
                            color: '#86efac'
                          }}>
                            {JSON.stringify(run.outputData, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
};
