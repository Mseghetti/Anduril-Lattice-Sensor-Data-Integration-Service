'use client';

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Entity, Sensor, Detection } from '@/lib/supabase';

interface TacticalMapProps {
  entities: Entity[];
  sensors: Sensor[];
  detections: Detection[];
}

export default function TacticalMap({ entities, sensors, detections }: TacticalMapProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const entityMarkersRef = useRef<Map<string, L.Marker>>(new Map());
  const sensorMarkersRef = useRef<Map<string, L.Circle>>(new Map());
  const detectionLinesRef = useRef<Map<string, L.Polyline>>(new Map());

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [37.7749, -122.4194],
      zoom: 11,
      zoomControl: true,
      attributionControl: false
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
    }).addTo(map);

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;

    const entityIcons: Record<string, string> = {
      aircraft: '✈️',
      vehicle: '🚙',
      vessel: '⛴️',
      unknown: '❓'
    };

    entities.forEach(entity => {
      const existingMarker = entityMarkersRef.current.get(entity.id);

      if (existingMarker) {
        existingMarker.setLatLng([entity.position.lat, entity.position.lon]);
      } else {
        const icon = L.divIcon({
          html: `<div style="font-size: 24px; transform: rotate(${entity.motion.heading_deg}deg); filter: drop-shadow(0 0 6px rgba(0,255,136,0.8));">${entityIcons[entity.entity_type] || '⭐'}</div>`,
          className: 'entity-marker',
          iconSize: [30, 30],
          iconAnchor: [15, 15]
        });

        const marker = L.marker([entity.position.lat, entity.position.lon], { icon })
          .addTo(mapRef.current!)
          .bindPopup(`
            <div class="text-xs">
              <strong>${entity.metadata.callsign || entity.id.slice(0, 8)}</strong><br/>
              Type: ${entity.entity_type}<br/>
              Speed: ${(entity.motion.speed_ms * 3.6).toFixed(1)} km/h<br/>
              Heading: ${entity.motion.heading_deg.toFixed(0)}°<br/>
              Altitude: ${entity.position.altitude_m}m<br/>
              Confidence: ${(entity.confidence_level * 100).toFixed(0)}%
            </div>
          `);

        entityMarkersRef.current.set(entity.id, marker);
      }
    });

    entityMarkersRef.current.forEach((marker, id) => {
      if (!entities.find(e => e.id === id)) {
        marker.remove();
        entityMarkersRef.current.delete(id);
      }
    });
  }, [entities]);

  useEffect(() => {
    if (!mapRef.current) return;

    const sensorColors: Record<string, string> = {
      radar: '#ff0080',
      adsb: '#00a8ff',
      camera: '#00ff88',
      acoustic: '#ffaa00'
    };

    sensors.forEach(sensor => {
      const existingSensor = sensorMarkersRef.current.get(sensor.id);

      if (!existingSensor) {
        const circle = L.circle([sensor.position.lat, sensor.position.lon], {
          radius: sensor.max_range_m,
          color: sensorColors[sensor.sensor_type] || '#ffffff',
          fillColor: sensorColors[sensor.sensor_type] || '#ffffff',
          fillOpacity: sensor.is_active ? 0.1 : 0.05,
          weight: 2,
          opacity: sensor.is_active ? 0.6 : 0.3,
          className: sensor.is_active ? 'sensor-pulse' : ''
        }).addTo(mapRef.current!)
          .bindPopup(`
            <div class="text-xs">
              <strong>${sensor.sensor_type.toUpperCase()}</strong><br/>
              Range: ${(sensor.max_range_m / 1000).toFixed(1)} km<br/>
              Status: ${sensor.is_active ? '🟢 Active' : '🔴 Inactive'}<br/>
              Update Rate: ${sensor.update_rate_hz} Hz
            </div>
          `);

        const centerMarker = L.circleMarker([sensor.position.lat, sensor.position.lon], {
          radius: 6,
          color: sensorColors[sensor.sensor_type] || '#ffffff',
          fillColor: sensorColors[sensor.sensor_type] || '#ffffff',
          fillOpacity: 1,
          weight: 2
        }).addTo(mapRef.current!);

        sensorMarkersRef.current.set(sensor.id, circle);
        sensorMarkersRef.current.set(sensor.id + '_center', centerMarker as any);
      }
    });
  }, [sensors]);

  useEffect(() => {
    if (!mapRef.current || detections.length === 0) return;

    const recentDetection = detections[detections.length - 1];
    const sensor = sensors.find(s => s.id === recentDetection.sensor_id);
    const entity = entities.find(e => e.id === recentDetection.entity_id);

    if (sensor && entity) {
      const sensorColors: Record<string, string> = {
        radar: '#ff0080',
        adsb: '#00a8ff',
        camera: '#00ff88',
        acoustic: '#ffaa00'
      };

      const line = L.polyline(
        [[sensor.position.lat, sensor.position.lon], [entity.position.lat, entity.position.lon]],
        {
          color: sensorColors[sensor.sensor_type] || '#ffffff',
          weight: 2,
          opacity: 0.6,
          dashArray: '5, 5'
        }
      ).addTo(mapRef.current);

      setTimeout(() => {
        line.remove();
      }, 2000);
    }
  }, [detections, sensors, entities]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainerRef} className="w-full h-full rounded-lg overflow-hidden border border-cyan-500/30" />
      <style jsx global>{`
        .entity-marker {
          background: transparent;
          border: none;
        }
        .sensor-pulse {
          animation: pulse 2s infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}
