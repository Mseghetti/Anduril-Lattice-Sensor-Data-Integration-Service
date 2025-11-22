'use client';

import { Sensor } from '@/lib/supabase';
import { useState } from 'react';
import { toggleSensor } from '@/lib/simulation';

interface SensorDashboardProps {
  sensors: Sensor[];
  detectionCounts: Record<string, number>;
}

export default function SensorDashboard({ sensors, detectionCounts }: SensorDashboardProps) {
  const [toggling, setToggling] = useState<string | null>(null);

  const sensorIcons: Record<string, string> = {
    radar: '📡',
    adsb: '📻',
    camera: '📷',
    acoustic: '🎤'
  };

  const sensorColors: Record<string, string> = {
    radar: 'from-pink-500/20 to-pink-600/10 border-pink-500/50',
    adsb: 'from-blue-500/20 to-blue-600/10 border-blue-500/50',
    camera: 'from-green-500/20 to-green-600/10 border-green-500/50',
    acoustic: 'from-yellow-500/20 to-yellow-600/10 border-yellow-500/50'
  };

  const handleToggleSensor = async (sensorId: string, currentStatus: boolean) => {
    setToggling(sensorId);
    await toggleSensor(sensorId, !currentStatus);
    setTimeout(() => setToggling(null), 500);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {sensors.map(sensor => (
        <div
          key={sensor.id}
          className={`relative bg-gradient-to-br ${sensorColors[sensor.sensor_type]} border rounded-lg p-4 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/20`}
        >
          <div className="absolute top-2 right-2">
            <button
              onClick={() => handleToggleSensor(sensor.id, sensor.is_active)}
              disabled={toggling === sensor.id}
              className={`w-3 h-3 rounded-full transition-all duration-300 ${
                sensor.is_active
                  ? 'bg-green-500 shadow-lg shadow-green-500/50 animate-pulse'
                  : 'bg-red-500 shadow-lg shadow-red-500/50'
              }`}
              title={sensor.is_active ? 'Active - Click to disable' : 'Inactive - Click to enable'}
            />
          </div>

          <div className="flex items-start space-x-3">
            <div className="text-3xl">{sensorIcons[sensor.sensor_type]}</div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                {sensor.sensor_type}
              </h3>
              <p className="text-xs text-gray-400 font-mono">
                ID: {sensor.id.slice(0, 8)}
              </p>
            </div>
          </div>

          <div className="mt-4 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Position</span>
              <span className="text-white font-mono">
                {sensor.position.lat.toFixed(4)}, {sensor.position.lon.toFixed(4)}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Max Range</span>
              <span className="text-cyan-400 font-bold">
                {(sensor.max_range_m / 1000).toFixed(1)} km
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Update Rate</span>
              <span className="text-white font-mono">{sensor.update_rate_hz} Hz</span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Detections</span>
              <span className="text-green-400 font-bold">
                {detectionCounts[sensor.id] || 0}
              </span>
            </div>

            <div className="pt-2 border-t border-gray-700">
              <div className="flex justify-between items-center text-xs">
                <span className="text-gray-400">Status</span>
                <span className={`font-bold ${sensor.is_active ? 'text-green-400' : 'text-red-400'}`}>
                  {sensor.is_active ? '● OPERATIONAL' : '○ OFFLINE'}
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
