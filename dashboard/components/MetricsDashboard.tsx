'use client';

interface MetricsDashboardProps {
  totalDetections: number;
  activeSensors: number;
  trackedEntities: number;
  detectionRate: number;
}

export default function MetricsDashboard({
  totalDetections,
  activeSensors,
  trackedEntities,
  detectionRate
}: MetricsDashboardProps) {
  const metrics = [
    {
      label: 'Total Detections',
      value: totalDetections.toLocaleString(),
      color: 'from-cyan-500/20 to-cyan-600/10 border-cyan-500/50',
      icon: '📊',
      trend: '+12%'
    },
    {
      label: 'Active Sensors',
      value: activeSensors,
      color: 'from-green-500/20 to-green-600/10 border-green-500/50',
      icon: '📡',
      trend: '100%'
    },
    {
      label: 'Tracked Entities',
      value: trackedEntities,
      color: 'from-blue-500/20 to-blue-600/10 border-blue-500/50',
      icon: '🎯',
      trend: '+3'
    },
    {
      label: 'Detection Rate',
      value: `${detectionRate.toFixed(1)}/s`,
      color: 'from-purple-500/20 to-purple-600/10 border-purple-500/50',
      icon: '⚡',
      trend: 'Normal'
    }
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, index) => (
        <div
          key={index}
          className={`bg-gradient-to-br ${metric.color} border rounded-lg p-4 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/20`}
        >
          <div className="flex items-start justify-between mb-2">
            <span className="text-2xl">{metric.icon}</span>
            <span className="text-xs text-green-400 font-bold">{metric.trend}</span>
          </div>
          <div className="text-2xl font-bold text-white mb-1">{metric.value}</div>
          <div className="text-xs text-gray-400 uppercase tracking-wider">{metric.label}</div>
        </div>
      ))}
    </div>
  );
}
