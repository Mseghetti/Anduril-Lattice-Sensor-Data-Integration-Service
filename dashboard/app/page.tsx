'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { supabase, Entity, Sensor, Detection, SimulationState } from '@/lib/supabase';
import { initializeSimulation, updateEntityPositions, detectEntities } from '@/lib/simulation';
import SensorDashboard from '@/components/SensorDashboard';
import EntityTable from '@/components/EntityTable';
import ActivityFeed from '@/components/ActivityFeed';
import ControlPanel from '@/components/ControlPanel';
import MetricsDashboard from '@/components/MetricsDashboard';

const TacticalMap = dynamic(() => import('@/components/TacticalMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-gray-900/50 rounded-lg border border-cyan-500/30">
      <div className="text-cyan-400 animate-pulse">Loading tactical map...</div>
    </div>
  )
});

export default function Dashboard() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null);
  const [detectionCounts, setDetectionCounts] = useState<Record<string, number>>({});
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const init = async () => {
      await initializeSimulation();
      setIsInitialized(true);
    };
    init();
  }, []);

  useEffect(() => {
    if (!isInitialized) return;

    const fetchData = async () => {
      const [entitiesRes, sensorsRes, detectionsRes, stateRes] = await Promise.all([
        supabase.from('entities').select('*'),
        supabase.from('sensors').select('*'),
        supabase.from('detections').select('*').order('timestamp', { ascending: false }).limit(100),
        supabase.from('simulation_state').select('*').limit(1).single()
      ]);

      if (entitiesRes.data) setEntities(entitiesRes.data);
      if (sensorsRes.data) setSensors(sensorsRes.data);
      if (detectionsRes.data) setDetections(detectionsRes.data);
      if (stateRes.data) setSimulationState(stateRes.data);

      if (detectionsRes.data) {
        const counts: Record<string, number> = {};
        detectionsRes.data.forEach(d => {
          counts[d.sensor_id] = (counts[d.sensor_id] || 0) + 1;
        });
        setDetectionCounts(counts);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);

    return () => clearInterval(interval);
  }, [isInitialized]);

  useEffect(() => {
    if (!simulationState?.is_running) return;

    const simulationInterval = setInterval(async () => {
      const deltaTime = simulationState.simulation_speed * 1.0;
      await updateEntityPositions(deltaTime);
      await detectEntities();
    }, 1000);

    return () => clearInterval(simulationInterval);
  }, [simulationState?.is_running, simulationState?.simulation_speed]);

  useEffect(() => {
    const entitiesSubscription = supabase
      .channel('entities_changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'entities' }, payload => {
        if (payload.eventType === 'INSERT') {
          setEntities(prev => [...prev, payload.new as Entity]);
        } else if (payload.eventType === 'UPDATE') {
          setEntities(prev => prev.map(e => e.id === payload.new.id ? payload.new as Entity : e));
        } else if (payload.eventType === 'DELETE') {
          setEntities(prev => prev.filter(e => e.id !== payload.old.id));
        }
      })
      .subscribe();

    const detectionsSubscription = supabase
      .channel('detections_changes')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'detections' }, payload => {
        setDetections(prev => [payload.new as Detection, ...prev].slice(0, 100));
      })
      .subscribe();

    const simulationSubscription = supabase
      .channel('simulation_changes')
      .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'simulation_state' }, payload => {
        setSimulationState(payload.new as SimulationState);
      })
      .subscribe();

    const sensorsSubscription = supabase
      .channel('sensors_changes')
      .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'sensors' }, payload => {
        setSensors(prev => prev.map(s => s.id === payload.new.id ? payload.new as Sensor : s));
      })
      .subscribe();

    return () => {
      entitiesSubscription.unsubscribe();
      detectionsSubscription.unsubscribe();
      simulationSubscription.unsubscribe();
      sensorsSubscription.unsubscribe();
    };
  }, []);

  const activeSensorsCount = sensors.filter(s => s.is_active).length;
  const detectionRate = detections.length > 0 ? detections.length / 60 : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <div className="relative">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgwLDI1NSwxMzYsMC4wNSkiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-20" />
      </div>

      <div className="relative z-10 p-6 space-y-6">
        <header className="text-center py-8 border-b border-cyan-500/30">
          <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 mb-2 tracking-tight">
            TACTICAL SENSOR NETWORK
          </h1>
          <p className="text-gray-400 text-sm uppercase tracking-widest">
            Advanced Multi-Sensor Surveillance System
          </p>
        </header>

        <MetricsDashboard
          totalDetections={detections.length}
          activeSensors={activeSensorsCount}
          trackedEntities={entities.length}
          detectionRate={detectionRate}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="h-[500px]">
              <TacticalMap entities={entities} sensors={sensors} detections={detections} />
            </div>

            <SensorDashboard sensors={sensors} detectionCounts={detectionCounts} />

            <EntityTable entities={entities} />
          </div>

          <div className="space-y-6">
            <ControlPanel simulationState={simulationState} />
            <ActivityFeed detections={detections} sensors={sensors} entities={entities} />
          </div>
        </div>

        <footer className="text-center py-6 text-xs text-gray-500 border-t border-cyan-500/30">
          <p>CLASSIFIED - FOR DEMONSTRATION PURPOSES ONLY</p>
          <p className="mt-1">Advanced Sensor Integration & Real-Time Tracking System</p>
        </footer>
      </div>
    </div>
  );
}
