'use client';

import { Entity } from '@/lib/supabase';
import { useState } from 'react';
import { removeEntity } from '@/lib/simulation';

interface EntityTableProps {
  entities: Entity[];
}

export default function EntityTable({ entities }: EntityTableProps) {
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [sortField, setSortField] = useState<keyof Entity>('last_detected');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const sortedEntities = [...entities].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];

    if (sortField === 'position' || sortField === 'motion') {
      return 0;
    }

    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortDirection === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }

    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    }

    return 0;
  });

  const handleSort = (field: keyof Entity) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const entityTypeIcons: Record<string, string> = {
    aircraft: '✈️',
    vehicle: '🚙',
    vessel: '⛴️',
    unknown: '❓'
  };

  const handleRemove = async (entityId: string) => {
    if (confirm('Are you sure you want to remove this entity?')) {
      await removeEntity(entityId);
    }
  };

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm rounded-lg border border-cyan-500/30 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-800/80 border-b border-cyan-500/30">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-bold text-cyan-400 uppercase tracking-wider">
                Type
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-bold text-cyan-400 uppercase tracking-wider cursor-pointer hover:text-cyan-300"
                onClick={() => handleSort('id')}
              >
                ID {sortField === 'id' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-4 py-3 text-left text-xs font-bold text-cyan-400 uppercase tracking-wider">
                Position
              </th>
              <th className="px-4 py-3 text-left text-xs font-bold text-cyan-400 uppercase tracking-wider">
                Speed
              </th>
              <th className="px-4 py-3 text-left text-xs font-bold text-cyan-400 uppercase tracking-wider">
                Heading
              </th>
              <th className="px-4 py-3 text-left text-xs font-bold text-cyan-400 uppercase tracking-wider">
                Altitude
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-bold text-cyan-400 uppercase tracking-wider cursor-pointer hover:text-cyan-300"
                onClick={() => handleSort('confidence_level')}
              >
                Confidence {sortField === 'confidence_level' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-4 py-3 text-left text-xs font-bold text-cyan-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/50">
            {sortedEntities.map(entity => (
              <>
                <tr
                  key={entity.id}
                  className="hover:bg-cyan-500/5 transition-colors cursor-pointer"
                  onClick={() => setExpandedRow(expandedRow === entity.id ? null : entity.id)}
                >
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="text-2xl">{entityTypeIcons[entity.entity_type]}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-mono text-xs text-white">
                      {entity.metadata.callsign || entity.id.slice(0, 8)}
                    </div>
                    <div className="text-xs text-gray-400 capitalize">
                      {entity.entity_type}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-mono text-xs text-white">
                      {entity.position.lat.toFixed(4)}
                    </div>
                    <div className="font-mono text-xs text-gray-400">
                      {entity.position.lon.toFixed(4)}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs text-white">
                      {(entity.motion.speed_ms * 3.6).toFixed(1)} km/h
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs text-white">
                      {entity.motion.heading_deg.toFixed(0)}°
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs text-white">
                      {entity.position.altitude_m}m
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`font-bold text-xs ${getConfidenceColor(entity.confidence_level)}`}>
                      {(entity.confidence_level * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemove(entity.id);
                      }}
                      className="px-2 py-1 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded border border-red-500/50 transition-colors"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
                {expandedRow === entity.id && (
                  <tr className="bg-gray-800/40">
                    <td colSpan={8} className="px-4 py-4">
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div>
                          <h4 className="text-cyan-400 font-bold mb-2">Movement Pattern</h4>
                          <p className="text-white capitalize">{entity.movement_pattern}</p>
                        </div>
                        <div>
                          <h4 className="text-cyan-400 font-bold mb-2">Last Detected</h4>
                          <p className="text-white font-mono">
                            {new Date(entity.last_detected).toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <h4 className="text-cyan-400 font-bold mb-2">Metadata</h4>
                          <pre className="text-white font-mono text-xs bg-gray-900/50 p-2 rounded overflow-auto">
                            {JSON.stringify(entity.metadata, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <h4 className="text-cyan-400 font-bold mb-2">Full ID</h4>
                          <p className="text-white font-mono break-all">{entity.id}</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
