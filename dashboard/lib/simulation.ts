import { supabase, Entity, Sensor, Position } from './supabase';

// Calculate distance between two positions in meters
function calculateDistance(pos1: Position, pos2: Position): number {
  const R = 6371000; // Earth radius in meters
  const lat1 = pos1.lat * Math.PI / 180;
  const lat2 = pos2.lat * Math.PI / 180;
  const deltaLat = (pos2.lat - pos1.lat) * Math.PI / 180;
  const deltaLon = (pos2.lon - pos1.lon) * Math.PI / 180;

  const a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) *
    Math.sin(deltaLon / 2) * Math.sin(deltaLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

// Initialize simulation with default sensors and state
export async function initializeSimulation() {
  // Check if simulation state exists
  const { data: existingState } = await supabase
    .from('simulation_state')
    .select('*')
    .limit(1)
    .single();

  if (!existingState) {
    // Create initial simulation state
    await supabase
      .from('simulation_state')
      .insert({
        is_running: false,
        simulation_speed: 1.0,
        metrics: {}
      });
  }

  // Check if sensors exist
  const { data: existingSensors } = await supabase
    .from('sensors')
    .select('*');

  if (!existingSensors || existingSensors.length === 0) {
    // Create default sensors
    const defaultSensors = [
      {
        sensor_type: 'radar',
        position: { lat: 37.7749, lon: -122.4194, altitude_m: 100 },
        max_range_m: 50000,
        update_rate_hz: 1.0,
        is_active: true,
        detection_parameters: { frequency_hz: 2400000000 }
      },
      {
        sensor_type: 'adsb',
        position: { lat: 37.7849, lon: -122.4094, altitude_m: 50 },
        max_range_m: 300000,
        update_rate_hz: 1.0,
        is_active: true,
        detection_parameters: { mode: 'S' }
      },
      {
        sensor_type: 'camera',
        position: { lat: 37.7649, lon: -122.4294, altitude_m: 200 },
        max_range_m: 10000,
        update_rate_hz: 0.5,
        is_active: true,
        detection_parameters: { resolution: '4K', fov_deg: 60 }
      },
      {
        sensor_type: 'acoustic',
        position: { lat: 37.7549, lon: -122.4394, altitude_m: 10 },
        max_range_m: 5000,
        update_rate_hz: 10.0,
        is_active: true,
        detection_parameters: { sensitivity_db: -120 }
      }
    ];

    await supabase
      .from('sensors')
      .insert(defaultSensors);
  }
}

// Update entity positions based on their motion
export async function updateEntityPositions(deltaTime: number) {
  const { data: entities } = await supabase
    .from('entities')
    .select('*');

  if (!entities) return;

  for (const entity of entities) {
    const motion = entity.motion as { heading_deg: number; speed_ms: number };
    const position = entity.position as Position;

    // Calculate new position based on heading and speed
    const headingRad = (motion.heading_deg * Math.PI) / 180;
    const distance = motion.speed_ms * deltaTime; // meters
    const earthRadius = 6371000; // meters

    const lat1 = position.lat * Math.PI / 180;
    const lon1 = position.lon * Math.PI / 180;

    const lat2 = Math.asin(
      Math.sin(lat1) * Math.cos(distance / earthRadius) +
      Math.cos(lat1) * Math.sin(distance / earthRadius) * Math.cos(headingRad)
    );

    const lon2 = lon1 + Math.atan2(
      Math.sin(headingRad) * Math.sin(distance / earthRadius) * Math.cos(lat1),
      Math.cos(distance / earthRadius) - Math.sin(lat1) * Math.sin(lat2)
    );

    const newPosition: Position = {
      lat: lat2 * 180 / Math.PI,
      lon: lon2 * 180 / Math.PI,
      altitude_m: position.altitude_m
    };

    // Update entity position
    await supabase
      .from('entities')
      .update({
        position: newPosition,
        updated_at: new Date().toISOString()
      })
      .eq('id', entity.id);
  }
}

// Detect entities within sensor ranges
export async function detectEntities() {
  const { data: sensors } = await supabase
    .from('sensors')
    .select('*')
    .eq('is_active', true);

  const { data: entities } = await supabase
    .from('entities')
    .select('*');

  if (!sensors || !entities) return;

  for (const sensor of sensors) {
    const sensorPos = sensor.position as Position;

    for (const entity of entities) {
      const entityPos = entity.position as Position;
      const distance = calculateDistance(sensorPos, entityPos);

      // Check if entity is within sensor range
      if (distance <= sensor.max_range_m) {
        // Calculate confidence based on distance (closer = higher confidence)
        const confidence = Math.max(0.3, 1.0 - (distance / sensor.max_range_m));

        // Create detection
        await supabase
          .from('detections')
          .insert({
            entity_id: entity.id,
            sensor_id: sensor.id,
            timestamp: new Date().toISOString(),
            position: entityPos,
            confidence: confidence,
            metadata: {
              distance_m: distance,
              sensor_type: sensor.sensor_type
            }
          });

        // Update entity last_detected and confidence
        await supabase
          .from('entities')
          .update({
            last_detected: new Date().toISOString(),
            confidence_level: Math.max(entity.confidence_level, confidence),
            updated_at: new Date().toISOString()
          })
          .eq('id', entity.id);
      }
    }
  }
}

// Start simulation
export async function startSimulation() {
  const { data: state } = await supabase
    .from('simulation_state')
    .select('*')
    .limit(1)
    .single();

  if (state) {
    await supabase
      .from('simulation_state')
      .update({
        is_running: true,
        start_time: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .eq('id', state.id);
  } else {
    await supabase
      .from('simulation_state')
      .insert({
        is_running: true,
        simulation_speed: 1.0,
        start_time: new Date().toISOString()
      });
  }
}

// Stop simulation
export async function stopSimulation() {
  const { data: state } = await supabase
    .from('simulation_state')
    .select('*')
    .limit(1)
    .single();

  if (state) {
    await supabase
      .from('simulation_state')
      .update({
        is_running: false,
        updated_at: new Date().toISOString()
      })
      .eq('id', state.id);
  }
}

// Update simulation speed
export async function updateSimulationSpeed(speed: number) {
  const { data: state } = await supabase
    .from('simulation_state')
    .select('*')
    .limit(1)
    .single();

  if (state) {
    await supabase
      .from('simulation_state')
      .update({
        simulation_speed: speed,
        updated_at: new Date().toISOString()
      })
      .eq('id', state.id);
  }
}

// Add a new entity
export async function addEntity(entityData: Partial<Entity>) {
  await supabase
    .from('entities')
    .insert({
      entity_type: entityData.entity_type || 'unknown',
      position: entityData.position || { lat: 37.7749, lon: -122.4194, altitude_m: 0 },
      motion: entityData.motion || { heading_deg: 0, speed_ms: 0 },
      movement_pattern: entityData.movement_pattern || 'random',
      metadata: entityData.metadata || {},
      confidence_level: entityData.confidence_level || 0.5
    });
}

// Remove an entity
export async function removeEntity(entityId: string) {
  await supabase
    .from('entities')
    .delete()
    .eq('id', entityId);
}

// Toggle sensor active status
export async function toggleSensor(sensorId: string, isActive: boolean) {
  await supabase
    .from('sensors')
    .update({
      is_active: isActive,
      updated_at: new Date().toISOString()
    })
    .eq('id', sensorId);
}

