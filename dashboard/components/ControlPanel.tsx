'use client';

import { SimulationState } from '@/lib/supabase';
import { startSimulation, stopSimulation, updateSimulationSpeed, addEntity } from '@/lib/simulation';
import { useState } from 'react';

interface ControlPanelProps {
  simulationState: SimulationState | null;
}

export default function ControlPanel({ simulationState }: ControlPanelProps) {
  const [speed, setSpeed] = useState(simulationState?.simulation_speed || 1.0);
  const [isAddingEntity, setIsAddingEntity] = useState(false);

  const handleStart = async () => {
    await startSimulation();
  };

  const handleStop = async () => {
    await stopSimulation();
  };

  const handleSpeedChange = async (newSpeed: number) => {
    setSpeed(newSpeed);
    await updateSimulationSpeed(newSpeed);
  };

  const handleAddEntity = async () => {
    setIsAddingEntity(true);
    const entityTypes = ['aircraft', 'vehicle', 'vessel'];
    const randomType = entityTypes[Math.floor(Math.random() * entityTypes.length)];

    await addEntity({
      entity_type: randomType as any,
      position: {
        lat: 37.7749 + (Math.random() - 0.5) * 0.2,
        lon: -122.4194 + (Math.random() - 0.5) * 0.2,
        altitude_m: randomType === 'aircraft' ? Math.random() * 5000 : randomType === 'vessel' ? 0 : 50
      },
      motion: {
        heading_deg: Math.random() * 360,
        speed_ms: randomType === 'aircraft' ? 80 + Math.random() * 80 : randomType === 'vehicle' ? 15 + Math.random() * 20 : 10 + Math.random() * 10
      },
      movement_pattern: 'random',
      metadata: { callsign: `NEW-${Math.floor(Math.random() * 1000)}` },
      confidence_level: 0.5 + Math.random() * 0.5
    });

    setIsAddingEntity(false);
  };

  const speedOptions = [
    { value: 0.5, label: '0.5x' },
    { value: 1.0, label: '1x' },
    { value: 2.0, label: '2x' },
    { value: 5.0, label: '5x' }
  ];

  const isRunning = simulationState?.is_running || false;

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm rounded-lg border border-cyan-500/30 p-4">
      <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-4">
        Simulation Control
      </h3>

      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={isRunning ? handleStop : handleStart}
            className={`flex-1 px-4 py-2 rounded font-bold text-sm transition-all duration-300 ${
              isRunning
                ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/50'
                : 'bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/50'
            }`}
          >
            {isRunning ? '⏸ PAUSE' : '▶ START'}
          </button>

          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
            <span className="text-xs text-gray-400">
              {isRunning ? 'Running' : 'Stopped'}
            </span>
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-2">Simulation Speed</label>
          <div className="grid grid-cols-4 gap-2">
            {speedOptions.map(option => (
              <button
                key={option.value}
                onClick={() => handleSpeedChange(option.value)}
                className={`px-3 py-2 rounded text-xs font-bold transition-all duration-300 ${
                  speed === option.value
                    ? 'bg-cyan-500/30 text-cyan-400 border border-cyan-500'
                    : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:bg-gray-800'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-700 pt-4">
          <label className="block text-xs text-gray-400 mb-2">Entity Management</label>
          <button
            onClick={handleAddEntity}
            disabled={isAddingEntity}
            className="w-full px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 rounded border border-cyan-500/50 font-bold text-sm transition-all duration-300 disabled:opacity-50"
          >
            {isAddingEntity ? '⏳ Adding...' : '+ Add Random Entity'}
          </button>
        </div>

        <div className="border-t border-gray-700 pt-4">
          <label className="block text-xs text-gray-400 mb-2">Quick Scenarios</label>
          <div className="grid grid-cols-2 gap-2">
            <button className="px-3 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded border border-purple-500/50 text-xs font-bold transition-all duration-300">
              Air Defense
            </button>
            <button className="px-3 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded border border-blue-500/50 text-xs font-bold transition-all duration-300">
              Maritime Patrol
            </button>
            <button className="px-3 py-2 bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 rounded border border-orange-500/50 text-xs font-bold transition-all duration-300">
              Border Security
            </button>
            <button className="px-3 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded border border-yellow-500/50 text-xs font-bold transition-all duration-300">
              Urban Surveillance
            </button>
          </div>
        </div>

        {simulationState?.start_time && isRunning && (
          <div className="border-t border-gray-700 pt-4">
            <div className="text-xs text-gray-400">
              Uptime: {Math.floor((Date.now() - new Date(simulationState.start_time).getTime()) / 1000)}s
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
