import { useState } from 'react';
import { HorizontalTunnel } from './components/HorizontalTunnel';
import { PumpingStationBox } from './components/PumpingStationBox';
import { TreatmentPlantBox } from './components/TreatmentPlantBox';
import { InflowBox } from './components/InflowBox';
import { StatusCard } from './components/StatusCard';
import { StatusBadge } from './components/StatusBadge';
import { FloatingLabel } from './components/FloatingLabel';
import { IndustrialPipe } from './components/IndustrialPipe';
import { AgentPanel } from './components/AgentPanel';
import { Activity, Droplets, Gauge, TrendingUp } from 'lucide-react';

export default function App() {
  // 8 Pumps in the station
  const [pumpStates] = useState([
    { id: 'P1.1', active: false, flow: '0 m³/h' },
    { id: 'P1.2', active: false, flow: '0 m³/h' },
    { id: 'P1.3', active: true, flow: '1650 m³/h' },
    { id: 'P2.1', active: false, flow: '0 m³/h' },
    { id: 'P2.2', active: true, flow: '1547 m³/h' },
    { id: 'P2.3', active: false, flow: '0 m³/h' },
    { id: 'P3', active: false, flow: '0 m³/h' },
    { id: 'P4', active: false, flow: '0 m³/h' },
  ]);

  const activePumpCount = pumpStates.filter(p => p.active).length;
  const waterLevel = 62; // 62% current level

  // Fixed pipe Y position
  const pipeY = 250;

  // Component positions
  const inflowPos = { left: 60, top: 160 };
  const inflowWidth = 180;

  const tunnelPos = { left: 320, top: 130 };
  const tunnelWidth = 420;

  const pumpingPos = { left: 820, top: 50 }; // Uplifted more
  const pumpingWidth = 280;

  const treatmentPos = { left: 1160, top: 150 };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1a1a2e] via-[#16213e] to-[#0f1419] overflow-auto">
      {/* Header */}
      <div className="px-8 py-8 pb-0">
        <div className="max-w-[1600px] mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-white mb-2 flex items-center gap-3">
                <Droplets className="w-10 h-10 text-[#00E5FF]" />
                HSY Blominmäki Wastewater Pumping Station
              </h1>
              <p className="text-gray-400">{new Date().toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              })}</p>
            </div>
            <StatusBadge status="operational" label="System Operational" />
          </div>

          {/* Status Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <StatusCard
              icon={<Activity className="w-5 h-5" />}
              title="Inflow"
              value="1202 m³/15min"
              status="good"
              trend="Normal"
            />
            <StatusCard
              icon={<Droplets className="w-5 h-5" />}
              title="Outflow"
              value="3197 m³/h"
              status="good"
              trend="Stable"
            />
            <StatusCard
              icon={<Gauge className="w-5 h-5" />}
              title="Water Level"
              value="2.33 m"
              status="good"
              trend="Volume: 9685 m³"
            />
            <StatusCard
              icon={<TrendingUp className="w-5 h-5" />}
              title="Active Pumps"
              value={`${activePumpCount} / ${pumpStates.length}`}
              status={activePumpCount >= 2 ? 'good' : 'warning'}
              trend="Operating"
            />
          </div>
        </div>
      </div>

      {/* Main System Visualization with Right Panel */}
      <div className="flex" style={{ height: 'calc(100vh - 400px)', minHeight: '600px' }}>

        {/* Left Section - Main Visualization (80%) */}
        <div className="flex-1 pl-8">
          <div className="relative h-full max-w-[1400px]">

            {/* Inflow Box - Left */}
            <div className="absolute" style={{ left: inflowPos.left, top: inflowPos.top }}>
              <InflowBox
                flowRate="1202 m³/15min"
                pressure="2.1 bar"
              />
            </div>

            {/* Connection Pipe from Inflow to Tunnel */}
            <IndustrialPipe
              start={{ x: inflowPos.left + inflowWidth, y: pipeY }}
              end={{ x: tunnelPos.left, y: pipeY }}
              active={true}
            />

            {/* Horizontal Water Tunnel - Center Left */}
            <div className="absolute" style={{ left: tunnelPos.left, top: tunnelPos.top }}>
              <HorizontalTunnel
                waterLevel={waterLevel}
                width={tunnelWidth}
                height={240}
              />

              {/* Tunnel Level Info */}
              <FloatingLabel
                text="L1 = 2.33 m"
                value="V = 9685 m³"
                position={{ top: -50, left: 150 }}
                compact
              />
            </div>

            {/* Connection Pipe from Tunnel to Pumping Station */}
            <IndustrialPipe
              start={{ x: tunnelPos.left + tunnelWidth, y: pipeY }}
              end={{ x: pumpingPos.left, y: pipeY }}
              active={true}
            />

            {/* Pumping Station Box - Center */}
            <div className="absolute" style={{ left: pumpingPos.left, top: pumpingPos.top }}>
              <PumpingStationBox pumps={pumpStates} />
            </div>

            {/* Connection Pipe from Pumping Station to Treatment Plant */}
            <IndustrialPipe
              start={{ x: pumpingPos.left + pumpingWidth, y: pipeY }}
              end={{ x: treatmentPos.left, y: pipeY }}
              active={activePumpCount > 0}
            />

            {/* Treatment Plant Box - Right */}
            <div className="absolute" style={{ left: treatmentPos.left, top: treatmentPos.top }}>
              <TreatmentPlantBox
                distance="30m"
                status="operational"
                capacity="15000 m³/day"
              />
            </div>
          </div>
        </div>

        {/* Right Section - Agent Panel (20%) */}
        <div className="flex-shrink-0 px-4" style={{ width: '20%', minWidth: '320px', maxWidth: '400px' }}>
          <div className="h-full">
            <AgentPanel hasData={true} />
          </div>
        </div>

      </div>

      {/* Footer */}
      <div className="px-8 mt-8 text-center text-gray-500">
        <p>Real-time monitoring • All systems operating within normal parameters</p>
      </div>
    </div>
  );
}