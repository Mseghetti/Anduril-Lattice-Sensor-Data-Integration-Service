import { createClient } from '@supabase/supabase-js';

// Supabase configuration
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase URL or Anon Key not configured. Using placeholder values.');
}

// Create Supabase client
export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-key'
);

// TypeScript types based on database schema
export interface Position {
  lat: number;
  lon: number;
  altitude_m: number;
}

export interface Motion {
  heading_deg: number;
  speed_ms: number;
}

export interface Sensor {
  id: string;
  sensor_type: 'radar' | 'adsb' | 'camera' | 'acoustic';
  position: Position;
  max_range_m: number;
  update_rate_hz: number;
  is_active: boolean;
  detection_parameters: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Entity {
  id: string;
  entity_type: 'aircraft' | 'vehicle' | 'vessel' | 'unknown';
  position: Position;
  motion: Motion;
  movement_pattern: 'waypoint' | 'patrol' | 'random' | 'evasive';
  metadata: Record<string, any>;
  last_detected: string;
  confidence_level: number;
  created_at: string;
  updated_at: string;
}

export interface Detection {
  id: string;
  entity_id: string;
  sensor_id: string;
  timestamp: string;
  position: Position;
  confidence: number;
  metadata: Record<string, any>;
  created_at: string;
}

export interface SimulationState {
  id: string;
  is_running: boolean;
  simulation_speed: number;
  start_time: string | null;
  metrics: Record<string, any>;
  created_at: string;
  updated_at: string;
}

