/*
  # Military Sensor Simulation Database Schema

  ## Overview
  This migration creates a comprehensive database schema for a military-grade sensor simulation system
  that tracks entities (aircraft, vehicles, vessels), sensor networks, and real-time detections.

  ## New Tables Created

  ### 1. `sensors`
  Stores sensor configurations and locations
  - `id` (uuid, primary key): Unique sensor identifier
  - `sensor_type` (text): Type of sensor (radar, adsb, camera, acoustic)
  - `position` (jsonb): Geographic location {lat, lon, altitude_m}
  - `max_range_m` (numeric): Maximum detection range in meters
  - `update_rate_hz` (numeric): Sensor update frequency
  - `is_active` (boolean): Operational status
  - `detection_parameters` (jsonb): Additional sensor-specific configuration
  - `created_at` (timestamptz): Record creation timestamp
  - `updated_at` (timestamptz): Last update timestamp

  ### 2. `entities`
  Tracks moving entities being monitored
  - `id` (uuid, primary key): Unique entity identifier
  - `entity_type` (text): Type of entity (aircraft, vehicle, vessel, unknown)
  - `position` (jsonb): Current position {lat, lon, altitude_m}
  - `motion` (jsonb): Movement data {heading_deg, speed_ms}
  - `movement_pattern` (text): Movement behavior (waypoint, patrol, random, evasive)
  - `metadata` (jsonb): Additional entity information
  - `last_detected` (timestamptz): Last detection timestamp
  - `confidence_level` (numeric): Detection confidence (0-1)
  - `created_at` (timestamptz): Record creation timestamp
  - `updated_at` (timestamptz): Last update timestamp

  ### 3. `detections`
  Records individual sensor detection events
  - `id` (uuid, primary key): Unique detection identifier
  - `entity_id` (uuid, foreign key): Reference to detected entity
  - `sensor_id` (uuid, foreign key): Reference to detecting sensor
  - `timestamp` (timestamptz): Detection time
  - `position` (jsonb): Detected position {lat, lon, altitude_m}
  - `confidence` (numeric): Detection confidence level (0-1)
  - `metadata` (jsonb): Additional detection data
  - `created_at` (timestamptz): Record creation timestamp

  ### 4. `simulation_state`
  Stores current simulation configuration and status
  - `id` (uuid, primary key): State identifier
  - `is_running` (boolean): Simulation running status
  - `simulation_speed` (numeric): Speed multiplier
  - `start_time` (timestamptz): Simulation start time
  - `metrics` (jsonb): Performance and system metrics
  - `created_at` (timestamptz): Record creation timestamp
  - `updated_at` (timestamptz): Last update timestamp

  ## Security Configuration

  ### Row Level Security (RLS)
  - All tables have RLS enabled for security
  - Public read access granted for demonstration purposes
  - Insert/update operations require authentication
  - Production deployments should implement stricter policies

  ## Indexes
  - Created indexes on frequently queried columns for optimal performance
  - Timestamp indexes for efficient time-based queries
  - Foreign key indexes for join operations
  - GIN indexes on JSONB columns for fast JSON queries

  ## Important Notes
  1. All timestamps use timestamptz for timezone awareness
  2. JSONB columns allow flexible schema evolution
  3. Indexes optimize real-time query performance
  4. Default values ensure data consistency
*/

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create sensors table
CREATE TABLE IF NOT EXISTS sensors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  sensor_type text NOT NULL CHECK (sensor_type IN ('radar', 'adsb', 'camera', 'acoustic')),
  position jsonb NOT NULL DEFAULT '{"lat": 0, "lon": 0, "altitude_m": 0}'::jsonb,
  max_range_m numeric NOT NULL DEFAULT 50000,
  update_rate_hz numeric NOT NULL DEFAULT 1.0,
  is_active boolean NOT NULL DEFAULT true,
  detection_parameters jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create entities table
CREATE TABLE IF NOT EXISTS entities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type text NOT NULL CHECK (entity_type IN ('aircraft', 'vehicle', 'vessel', 'unknown')),
  position jsonb NOT NULL DEFAULT '{"lat": 0, "lon": 0, "altitude_m": 0}'::jsonb,
  motion jsonb NOT NULL DEFAULT '{"heading_deg": 0, "speed_ms": 0}'::jsonb,
  movement_pattern text NOT NULL DEFAULT 'waypoint' CHECK (movement_pattern IN ('waypoint', 'patrol', 'random', 'evasive')),
  metadata jsonb DEFAULT '{}'::jsonb,
  last_detected timestamptz DEFAULT now(),
  confidence_level numeric NOT NULL DEFAULT 0.0 CHECK (confidence_level >= 0 AND confidence_level <= 1),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create detections table
CREATE TABLE IF NOT EXISTS detections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  sensor_id uuid NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
  timestamp timestamptz NOT NULL DEFAULT now(),
  position jsonb NOT NULL DEFAULT '{"lat": 0, "lon": 0, "altitude_m": 0}'::jsonb,
  confidence numeric NOT NULL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

-- Create simulation_state table
CREATE TABLE IF NOT EXISTS simulation_state (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  is_running boolean NOT NULL DEFAULT false,
  simulation_speed numeric NOT NULL DEFAULT 1.0,
  start_time timestamptz,
  metrics jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_sensors_type ON sensors(sensor_type);
CREATE INDEX IF NOT EXISTS idx_sensors_active ON sensors(is_active);
CREATE INDEX IF NOT EXISTS idx_sensors_position ON sensors USING GIN(position);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_last_detected ON entities(last_detected DESC);
CREATE INDEX IF NOT EXISTS idx_entities_position ON entities USING GIN(position);
CREATE INDEX IF NOT EXISTS idx_entities_confidence ON entities(confidence_level DESC);

CREATE INDEX IF NOT EXISTS idx_detections_entity ON detections(entity_id);
CREATE INDEX IF NOT EXISTS idx_detections_sensor ON detections(sensor_id);
CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_detections_position ON detections USING GIN(position);

CREATE INDEX IF NOT EXISTS idx_simulation_state_running ON simulation_state(is_running);

-- Enable Row Level Security
ALTER TABLE sensors ENABLE ROW LEVEL SECURITY;
ALTER TABLE entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_state ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for public read access (demonstration purposes)
CREATE POLICY "Allow public read access to sensors"
  ON sensors FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Allow public read access to entities"
  ON entities FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Allow public read access to detections"
  ON detections FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Allow public read access to simulation_state"
  ON simulation_state FOR SELECT
  TO anon, authenticated
  USING (true);

-- Create RLS policies for authenticated write access
CREATE POLICY "Allow authenticated insert on sensors"
  ON sensors FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Allow authenticated update on sensors"
  ON sensors FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow authenticated insert on entities"
  ON entities FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Allow authenticated update on entities"
  ON entities FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow authenticated delete on entities"
  ON entities FOR DELETE
  TO authenticated
  USING (true);

CREATE POLICY "Allow authenticated insert on detections"
  ON detections FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Allow authenticated insert on simulation_state"
  ON simulation_state FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Allow authenticated update on simulation_state"
  ON simulation_state FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic updated_at updates
CREATE TRIGGER update_sensors_updated_at
  BEFORE UPDATE ON sensors
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_updated_at
  BEFORE UPDATE ON entities
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_simulation_state_updated_at
  BEFORE UPDATE ON simulation_state
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
