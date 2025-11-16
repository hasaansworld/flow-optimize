import { useState, useEffect, useCallback } from 'react';
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
import { fetchAgentData, AgentResponse, AgentMessage } from './services/agentApi';

export default function App() {
  // Agent data state
  const [agentData, setAgentData] = useState<AgentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Row number tracking for sequential API calls
  const [currentRow, setCurrentRow] = useState(10);
  const [isProcessing, setIsProcessing] = useState(false);

  // Accumulated agent messages from all rows
  const [allAgentMessages, setAllAgentMessages] = useState<AgentMessage[]>([]);

  // System state values from API
  const [waterLevel, setWaterLevel] = useState(0.5); // L1 in meters
  const [waterLevelPercent, setWaterLevelPercent] = useState(6.25); // L1 as percentage of 8m
  const [volume, setVolume] = useState(0); // V in m³
  const [inflow, setInflow] = useState(0); // F1 in m³/15min
  const [outflow, setOutflow] = useState(0); // F2 in m³/h
  const [electricityPrice, setElectricityPrice] = useState(0); // EUR/kWh

  // Pump states derived from agent data
  const [pumpStates, setPumpStates] = useState([
    { id: 'P1.1', active: false, flow: '0 m³/h' },
    { id: 'P1.2', active: false, flow: '0 m³/h' },
    { id: 'P1.3', active: false, flow: '0 m³/h' },
    { id: 'P2.1', active: false, flow: '0 m³/h' },
    { id: 'P2.2', active: false, flow: '0 m³/h' },
    { id: 'P2.3', active: false, flow: '0 m³/h' },
    { id: 'P3', active: false, flow: '0 m³/h' },
    { id: 'P4', active: false, flow: '0 m³/h' },
  ]);

  // Update system state and pump states based on agent response
  const updatePumpStates = useCallback((data: AgentResponse) => {
    // Update system state values
    setWaterLevel(data.L1);
    setWaterLevelPercent(Math.round((data.L1 / 8) * 100)); // Convert to percentage and round to whole number
    setVolume(data.V);
    setInflow(data.F1);
    setOutflow(data.F2);
    setElectricityPrice(data.electricity_price);

    // Update pump states
    setPumpStates(prevPumpStates => {
      return prevPumpStates.map(pump => {
        // Map UI pump IDs to agent pump IDs
        // Note: P1L maps to pump 1.1, P2L maps to pump 1.2 (based on user clarification)
        const pumpIdMap: { [key: string]: string[] } = {
          'P1.1': ['1.1', 'P1L', 'P1.1'],
          'P1.2': ['1.2', 'P2L', 'P1.2'],
          'P1.3': ['1.3'],
          'P1.4': ['1.4'],
          'P2.1': ['2.1'],
          'P2.2': ['2.2'],
          'P2.3': ['2.3'],
          'P2.4': ['2.4'],
          'P3': ['P3'],
          'P4': ['P4'],
        };

        const possibleIds = pumpIdMap[pump.id] || [pump.id];

        // Find all matching pump commands
        const matchingCommands = data.pump_commands.filter(cmd =>
          possibleIds.includes(cmd.pump_id)
        );

        // Prefer active pumps over inactive ones
        const pumpCommand = matchingCommands.find(cmd => cmd.start) || matchingCommands[0];

        if (pumpCommand) {
          return {
            id: pump.id,
            active: pumpCommand.start,
            flow: `${Math.round(pumpCommand.flow_m3h)} m³/h`,
          };
        }
        return pump;
      });
    });
  }, []);

  // Fetch agent data for a specific row
  const loadAgentDataForRow = useCallback(async (rowNumber: number) => {
    try {
      setIsLoading(true);
      const data = await fetchAgentData(rowNumber);
      setAgentData(data);
      updatePumpStates(data);

      // Accumulate agent messages
      if (data.agent_messages && data.agent_messages.length > 0) {
        setAllAgentMessages(prev => [...prev, ...data.agent_messages]);
      }

      setError(null);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent data');
      console.error(`Error loading agent data for row ${rowNumber}:`, err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [updatePumpStates]);

  // Process rows sequentially from 1 to 1500
  const processAllRows = useCallback(async () => {
    setIsProcessing(true);

    for (let row = 1; row <= 1500; row++) {
      try {
        setCurrentRow(row);
        await loadAgentDataForRow(row);

        // Small delay to ensure UI updates are visible
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (err) {
        console.error(`Failed to process row ${row}, stopping:`, err);
        setIsProcessing(false);
        return;
      }
    }

    setIsProcessing(false);
    console.log('Completed processing all 1500 rows');
  }, [loadAgentDataForRow]);

  // Start processing rows on mount
  useEffect(() => {
    processAllRows();
  }, [processAllRows]);

  const activePumpCount = pumpStates.filter(p => p.active).length;

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
              <p className="text-[#00E5FF] mt-1">
                {isProcessing ? `Processing Row: ${currentRow} / 1500` : `Completed Row: ${currentRow}`}
              </p>
            </div>
            <StatusBadge status="operational" label="System Operational" />
          </div>

          {/* Status Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <StatusCard
              icon={<Activity className="w-5 h-5" />}
              title="Inflow"
              value={`${Math.round(inflow)} m³/15min`}
              status="good"
              trend="Normal"
            />
            <StatusCard
              icon={<Droplets className="w-5 h-5" />}
              title="Outflow"
              value={`${Math.round(outflow)} m³/h`}
              status="good"
              trend={`€${electricityPrice.toFixed(3)}/kWh`}
            />
            <StatusCard
              icon={<Gauge className="w-5 h-5" />}
              title="Water Level"
              value={`${waterLevel.toFixed(2)} m`}
              status={waterLevel > 7.2 ? 'warning' : 'good'}
              trend={`Volume: ${Math.round(volume)} m³`}
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
                flowRate={`${Math.round(inflow)} m³/15min`}
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
                waterLevel={waterLevelPercent}
                width={tunnelWidth}
                height={240}
              />

              {/* Tunnel Level Info */}
              <FloatingLabel
                text={`L1 = ${waterLevel.toFixed(2)} m`}
                value={`V = ${Math.round(volume)} m³`}
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
            <AgentPanel
              hasData={!isLoading && agentData !== null}
              agentData={agentData}
              allMessages={allAgentMessages}
              isLoading={isLoading}
              error={error}
              currentRow={currentRow}
            />
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