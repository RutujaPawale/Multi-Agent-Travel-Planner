import React, { useState } from 'react';
import { TripResponse } from '../types';
import { Plane, Calendar, DollarSign, Trash2, ArrowRight, Sparkles, Compass, Building, Wallet, Loader2 } from 'lucide-react';

interface MyTripsViewProps {
  trips: TripResponse[];
  onSelectTrip: (trip: TripResponse) => void;
  onDeleteTrip: (tripId: string) => Promise<void>;
  onNewTrip: () => void;
  isLoading: boolean;
}

export const MyTripsView: React.FC<MyTripsViewProps> = ({
  trips,
  onSelectTrip,
  onDeleteTrip,
  onNewTrip,
  isLoading
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [filterQuery, setFilterQuery] = useState<string>('');

  const filteredTrips = trips.filter(t => {
    if (!filterQuery.trim()) return true;
    const q = filterQuery.toLowerCase();
    return t.destination.toLowerCase().includes(q) ||
           t.origin.toLowerCase().includes(q) ||
           (t.preferences && t.preferences.toLowerCase().includes(q));
  });

  const handleDelete = async (e: React.MouseEvent, tripId: string) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this trip and its itinerary history?")) {
      return;
    }
    setDeletingId(tripId);
    try {
      await onDeleteTrip(tripId);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius)',
      border: '1px solid var(--border-color)',
      overflow: 'hidden',
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px',
        borderBottom: '1px solid var(--border-color)',
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(139, 92, 246, 0.08) 100%)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 700 }}>My Saved Trips</h2>
            <span className="badge badge-blue">{trips.length} Saved</span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Browse and manage all AI-generated travel plans and agent execution records.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Search destination..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            style={{
              padding: '6px 12px',
              fontSize: '13px',
              width: '180px',
              borderRadius: '6px'
            }}
          />
          <button
            onClick={onNewTrip}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
            }}
          >
            <Sparkles size={14} /> Plan New Trip
          </button>
        </div>
      </div>

      {/* Trips Grid / List */}
      <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {isLoading ? (
          <div style={{
            textAlign: 'center',
            padding: '48px 16px',
            color: 'var(--text-muted)'
          }}>
            <Loader2 size={32} className="spin" style={{ marginBottom: '12px', color: 'var(--accent-blue)' }} />
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Loading saved trips...
            </h3>
          </div>
        ) : filteredTrips.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '48px 16px',
            color: 'var(--text-muted)'
          }}>
            <Plane size={36} color="var(--border-color)" style={{ marginBottom: '12px' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              {filterQuery ? 'No trips match your search' : 'No trips saved yet'}
            </h3>
            <p style={{ fontSize: '13px', marginTop: '4px', maxWidth: '360px', margin: '6px auto 18px' }}>
              {filterQuery ? 'Try searching for a different destination or clear your filter.' : 'Submit a trip request on the planner form to generate your first AI travel itinerary.'}
            </p>
            {!filterQuery && (
              <button
                onClick={onNewTrip}
                style={{
                  padding: '8px 18px',
                  borderRadius: '8px',
                  background: 'var(--accent-blue)',
                  color: '#ffffff',
                  fontWeight: 600,
                  fontSize: '13px'
                }}
              >
                Plan a Trip Now
              </button>
            )}
          </div>
        ) : (
          filteredTrips.map((trip) => {
            const rawResult = trip.itineraryResult || {};
            const itinerary = rawResult.final_itinerary || rawResult;
            const flightCount = itinerary.flights?.count || rawResult.flight_options?.length || 0;
            const hotelCount = itinerary.accommodation?.count || rawResult.hotel_options?.length || 0;
            const activityCount = itinerary.activities?.count || rawResult.activity_options?.length || 0;
            const totalCost = itinerary.financial_overview?.total_estimated_expense ||
                              itinerary.financial_overview?.total_estimated_cost ||
                              rawResult.budget_summary?.total_estimated_cost ||
                              null;

            const isDeleting = deletingId === trip.id;

            return (
              <div
                key={trip.id}
                onClick={() => onSelectTrip(trip)}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '10px',
                  padding: '18px 20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  transition: 'border-color 0.2s, transform 0.2s',
                  flexWrap: 'wrap',
                  gap: '16px',
                  position: 'relative'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-highlight)';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                {/* Left side: Route & Dates */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', minWidth: '220px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '17px', fontWeight: 700, color: '#ffffff' }}>
                      {trip.origin} → {trip.destination}
                    </span>
                    <span className={`badge ${trip.status === 'COMPLETED' ? 'badge-green' : (trip.status === 'FAILED' ? 'badge-rose' : 'badge-amber')}`}>
                      {trip.status}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Calendar size={13} /> {trip.startDate} to {trip.endDate}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <DollarSign size={13} /> Budget: ${trip.budget.toLocaleString()}
                    </span>
                  </div>

                  {trip.preferences && (
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      Preferences: {trip.preferences.length > 55 ? trip.preferences.substring(0, 55) + '...' : trip.preferences}
                    </div>
                  )}
                </div>

                {/* Middle: Components breakdown */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  <div title="Flights curated" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Plane size={14} color="#60a5fa" />
                    <span>{flightCount} flight{flightCount !== 1 ? 's' : ''}</span>
                  </div>
                  <div title="Hotels curated" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Building size={14} color="#34d399" />
                    <span>{hotelCount} hotel{hotelCount !== 1 ? 's' : ''}</span>
                  </div>
                  <div title="Activities scheduled" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Compass size={14} color="#fbbf24" />
                    <span>{activityCount} activit{activityCount !== 1 ? 'ies' : 'y'}</span>
                  </div>
                  {totalCost !== null && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600, color: '#ffffff' }}>
                      <Wallet size={14} color="#a78bfa" />
                      <span>${Number(totalCost).toLocaleString()} total</span>
                    </div>
                  )}
                </div>

                {/* Right side: Actions */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    onClick={(e) => { e.stopPropagation(); onSelectTrip(trip); }}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '6px',
                      background: 'var(--bg-input)',
                      border: '1px solid var(--border-color)',
                      color: 'var(--accent-blue)',
                      fontSize: '12px',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    View Itinerary <ArrowRight size={13} />
                  </button>

                  <button
                    onClick={(e) => handleDelete(e, trip.id)}
                    disabled={isDeleting}
                    style={{
                      padding: '8px 10px',
                      borderRadius: '6px',
                      background: 'rgba(244, 63, 94, 0.1)',
                      border: '1px solid rgba(244, 63, 94, 0.25)',
                      color: '#fb7185',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                    title="Delete trip"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
