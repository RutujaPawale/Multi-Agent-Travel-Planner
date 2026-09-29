export interface TripRequest {
  origin: string;
  destination: string;
  startDate: string;
  endDate: string;
  budget: number;
  preferences: string;
}

export interface FlightOption {
  rank: number;
  id: string;
  airline: string;
  flight_number: string;
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  duration: string;
  stops: number;
  price: number;
  currency: string;
  source: string;
  is_mock?: boolean;
  notes?: string;
}

export interface HotelOption {
  rank: number;
  id: string;
  name: string;
  tier?: string;
  rating: number;
  price_per_night: number;
  total_price?: number;
  currency: string;
  neighborhood?: string;
  amenities?: string[];
  link?: string;
  source?: string;
  is_mock?: boolean;
  notes?: string;
}

export interface ActivityOption {
  rank: number;
  id: string;
  name: string;
  category: string;
  estimated_cost: number;
  currency: string;
  duration: string;
  rating: number;
  description: string;
}

export interface BudgetSummary {
  user_target_budget: number;
  trip_duration_nights: number;
  estimated_flight_cost: number;
  estimated_hotel_cost: number;
  estimated_activities_cost: number;
  estimated_miscellaneous: number;
  total_estimated_expense: number;
  remaining_surplus_deficit: number;
  budget_health: string;
  recommendation: string;
  currency: string;
}

export interface AgentRun {
  id: string;
  agentName: string;
  inputData: any;
  outputData: any;
  status: string;
  errorMessage?: string;
  createdAt: string;
}

export interface ItineraryResult {
  title?: string;
  summary?: string;
  preferences_applied?: string;
  flights?: {
    count: number;
    recommended?: FlightOption;
    all_options?: FlightOption[];
  };
  accommodation?: {
    count: number;
    recommended?: HotelOption;
    all_options?: HotelOption[];
  };
  activities?: {
    count: number;
    highlights?: ActivityOption[];
  };
  financial_overview?: BudgetSummary;
  generation_timestamp?: string;
  [key: string]: any;
}

export interface TripResponse {
  id: string;
  origin: string;
  destination: string;
  startDate: string;
  endDate: string;
  budget: number;
  preferences: string;
  status: string;
  itineraryResult: ItineraryResult | any;
  agentRuns?: AgentRun[];
  createdAt: string;
}
