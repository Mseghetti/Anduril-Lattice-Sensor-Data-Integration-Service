'use client';

import { Detection, Sensor, Entity } from '@/lib/supabase';
import { useState } from 'react';
import { format } from 'date-fns';

interface ActivityFeedProps {
  detections: Detection[];
  sensors: Sensor[];
  entities: Entity[];
}

export default function ActivityFeed({ detections, sensors, entities }: ActivityFeedProps) {
  const [filter, setFilter] = useState<string>('all');

  const sensorColors: Record<string, string> = {
    radar: 'text-pink-400',
    adsb: 'text-blue-400',
    camera: 'text-green-400',
    acoustic: 'text-yellow-400'
  };

  const filteredDetections = filter === 'all'
    ? detections
    : detections.filter(d => {
        const sensor = sensors.find(s => s.id === d.sensor_id);
        return sensor?.sensor_type === filter;
      });

  const handleExport = () => {
    const data = filteredDetections.map(detection => {
      const sensor = sensors.find(s => s.id === detection.sensor_id);
      const entity = entities.find(e => e.id === detection.entity_id);
      return {
        timestamp: detection.timestamp,
        sensor_id: detection.sensor_id,
        sensor_type: sensor?.sensor_type,
        entity_id: detection.entity_id,
        entity_type: entity?.entity_type,
        callsign: entity?.metadata.callsign,
        position: detection.position,
        confidence: detection.confidence
      };
    });

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `detections_${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm rounded-lg border border-cyan-500/30 overflow-hidden h-full flex flex-col">
      <div className="bg-gray-800/80 border-b border-cyan-500/30 p-4 flex justify-between items-center">
        <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider">
          Live Activity Feed
        </h3>
        <div className="flex items-center space-x-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="text-xs bg-gray-700 text-white rounded px-2 py-1 border border-cyan-500/30 focus:outline-none focus:border-cyan-400"
          >
            <option value="all">All Sensors</option>
            <option value="radar">Radar</option>
            <option value="adsb">ADS-B</option>
            <option value="camera">Camera</option>
            <option value="acoustic">Acoustic</option>
          </select>
          <button
            onClick={handleExport}
            className="px-3 py-1 text-xs bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 rounded border border-cyan-500/50 transition-colors"
          >
            Export
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2 max-h-96">
        {filteredDetections.slice().reverse().map((detection, index) => {
          const sensor = sensors.find(s => s.id === detection.sensor_id);
          const entity = entities.find(e => e.id === detection.entity_id);

          if (!sensor || !entity) return null;

          return (
            <div
              key={`${detection.id}-${index}`}
              className="text-xs font-mono bg-gray-800/40 rounded p-2 hover:bg-gray-800/60 transition-colors border-l-2"
              style={{
                borderColor: sensor.sensor_type === 'radar' ? '#ff0080' :
                            sensor.sensor_type === 'adsb' ? '#00a8ff' :
                            sensor.sensor_type === 'camera' ? '#00ff88' : '#ffaa00'
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <span className="text-gray-400">
                    [{format(new Date(detection.timestamp), 'HH:mm:ss')}]
                  </span>
                  {' '}
                  <span className={sensorColors[sensor.sensor_type]}>
                    [{sensor.sensor_type.toUpperCase()}]
                  </span>
                  {' '}
                  <span className="text-white">detected</span>
                  {' '}
                  <span className="text-cyan-400">
                    {entity.metadata.callsign || entity.entity_type.toUpperCase()}
                  </span>
                  {' '}
                  <span className="text-white">at</span>
                  {' '}
                  <span className="text-gray-300">
                    [{detection.position.lat.toFixed(4)}, {detection.position.lon.toFixed(4)}]
                  </span>
                </div>
                <span className={`ml-2 font-bold ${
                  detection.confidence >= 0.8 ? 'text-green-400' :
                  detection.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {(detection.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}

        {filteredDetections.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            No detections recorded yet
          </div>
        )}
      </div>
    </div>
  );
}
