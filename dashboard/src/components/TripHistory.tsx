import React from 'react';
import { TripResponse } from '../types';
import { History, Calendar, DollarSign, ArrowRight } from 'lucide-react';

interface TripHistoryProps {
  trips: TripResponse[];
  selectedTripId: string | null;
  onSelectTrip: (trip: TripResponse) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const TripHistory: React.FC<TripHistoryProps> = ({
  trips,
  selectedTripId,
  onSelectTrip,
  onRefresh,
  isLoading
}) => {
  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius)',
      padding: '20px',
      border: '1px solid var(--border-color)',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <History size={16} color="var(--accent-blue)" />
          Recent Trips ({trips.length})
        </h3>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          style={{
            background: 'var(--bg-input)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-secondary)',
            borderRadius: '6px',
            padding: '4px 8px',
            fontSize: '11px'
          }}
        >
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {trips.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>
            No saved trips found. Submit a trip above to start!
          </p>
        ) : (
          trips.map((trip) => {
            const isSelected = selectedTripId === trip.id;
            return (
              <div
                key={trip.id}
                onClick={() => onSelectTrip(trip)}
                style={{
                  background: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'var(--bg-card)',
                  border: isSelected ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '12px 14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600, fontSize: '14px' }}>
                    {trip.origin} → {trip.destination}
                  </span>
                  <span className={`badge ${trip.status === 'COMPLETED' ? 'badge-green' : 'badge-amber'}`} style={{ fontSize: '10px' }}>
                    {trip.status}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Calendar size={12} /> {trip.startDate}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <DollarSign size={12} /> ${Number(trip.budget).toLocaleString()}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                    View details <ArrowRight size={10} />
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
