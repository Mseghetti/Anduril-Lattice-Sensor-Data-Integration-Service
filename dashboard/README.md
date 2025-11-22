# Tactical Sensor Network Dashboard

A professional military-grade web application that simulates real-time sensor and drone operations through an interactive dashboard.

## Features

### Interactive Real-Time Map System
- Dark-themed mapping interface using Leaflet.js
- Moving entities (aircraft, vehicles, vessels) with custom military-style icons
- Real-time movement trails and detection visualizations
- Sensor network with detection range circles and animated pulse effects
- Click functionality for detailed entity/sensor information

### Comprehensive Sensor Dashboard
- Four sensor types: Radar, ADS-B, Optical Cameras, Acoustic Arrays
- Real-time detection count and operational status
- Geographic coordinates and maximum range display
- Interactive sensor enable/disable controls

### Entity Management Interface
- Sortable data table with entity tracking
- Expandable rows with detailed information
- Color-coded confidence indicators
- Entity removal functionality

### Live Activity Feed
- Real-time detection events stream
- Filtering by sensor type
- Export functionality (JSON format)
- Color-coded by sensor type

### Simulation Control Panel
- Start/stop simulation controls
- Speed adjustment (0.5x, 1x, 2x, 5x)
- Add random entities dynamically
- Quick scenario presets

### System Metrics Dashboard
- Total detections counter
- Active sensors count
- Tracked entities display
- Detection rate monitoring

## Technology Stack

- **Frontend**: Next.js 16 with React
- **Styling**: Tailwind CSS with dark military theme
- **Mapping**: Leaflet.js with dark map tiles
- **Database**: Supabase (PostgreSQL)
- **Real-time**: Supabase Realtime subscriptions
- **Animations**: Framer Motion
- **Charts**: Recharts
- **Type Safety**: TypeScript

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000)

4. Click "START" to begin the simulation

## Usage

1. **Start Simulation**: Click the green "START" button in the Control Panel
2. **View Entities**: Entities will appear on the map and in the table
3. **Monitor Detections**: Watch the Activity Feed for real-time detection events
4. **Adjust Speed**: Use speed controls to slow down or speed up the simulation
5. **Add Entities**: Click "Add Random Entity" to introduce new targets
6. **Toggle Sensors**: Click the status indicator on sensor cards to enable/disable
7. **Export Data**: Use the "Export" button in the Activity Feed to save detection logs

## Architecture

- **Database Schema**: Entities, Sensors, Detections, and Simulation State tables
- **Real-time Updates**: WebSocket connections via Supabase Realtime
- **Simulation Engine**: Client-side entity movement and sensor detection logic
- **Responsive Design**: Optimized for desktop and large displays

## Color Scheme

- Primary Background: Dark navy/black (#0a0e1a)
- Accent Colors: Tactical green (#00ff88) and electric blue (#00a8ff)
- Sensor Colors:
  - Radar: Pink (#ff0080)
  - ADS-B: Blue (#00a8ff)
  - Camera: Green (#00ff88)
  - Acoustic: Yellow (#ffaa00)

## Security

- Row Level Security (RLS) enabled on all tables
- Public read access for demonstration
- Authenticated write access required for modifications

## Deployment

This project can be deployed to Vercel:

```bash
npm run build
```

Check out the [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
