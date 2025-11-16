import { motion } from 'motion/react';
import { CompactPump } from './CompactPump';
import { Settings, Activity } from 'lucide-react';

interface Pump {
  id: string;
  active: boolean;
  flow: string;
}

interface PumpingStationBoxProps {
  pumps: Pump[];
}

export function PumpingStationBox({ pumps }: PumpingStationBoxProps) {
  const activePumpCount = pumps.filter(p => p.active).length;
  const totalFlow = pumps
    .filter(p => p.active)
    .reduce((sum, p) => sum + parseInt(p.flow), 0);

  return (
    <div className="relative">
      {/* Pumping Station Container */}
      <div
        className="relative p-4 rounded-2xl"
        style={{
          background: 'linear-gradient(135deg, rgba(55, 71, 79, 0.8) 0%, rgba(38, 50, 56, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          border: '3px solid rgba(255, 255, 255, 0.15)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.7), inset 0 2px 4px rgba(255, 255, 255, 0.1)',
          width: '280px',
        }}
      >
        {/* Station Header */}
        <div className="mb-3 pb-2 border-b border-white/10">
          <div className="flex items-center gap-2 mb-1">
            <Settings className="w-4 h-4 text-[#00E5FF]" />
            <h3 className="text-white text-sm">Pumping Station</h3>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1">
              <Activity className="w-3 h-3 text-gray-400" />
              <span className="text-gray-400">Active:</span>
              <span className="text-[#66BB6A]">{activePumpCount}/{pumps.length}</span>
            </div>
            {totalFlow > 0 && (
              <div className="text-gray-400">
                <span>Flow: </span>
                <span className="text-[#00E5FF]">{totalFlow} m³/h</span>
              </div>
            )}
          </div>
        </div>

        {/* Pumps Grid - 2 columns x 4 rows */}
        <div className="grid grid-cols-2 gap-2">
          {pumps.map((pump) => (
            <CompactPump
              key={pump.id}
              id={pump.id}
              active={pump.active}
              flow={pump.flow}
            />
          ))}
        </div>

        {/* Control Panel Pattern */}
        <div
          className="absolute inset-0 rounded-2xl pointer-events-none opacity-5"
          style={{
            backgroundImage: `
              repeating-linear-gradient(0deg, transparent, transparent 10px, rgba(255,255,255,0.1) 10px, rgba(255,255,255,0.1) 11px),
              repeating-linear-gradient(90deg, transparent, transparent 10px, rgba(255,255,255,0.1) 10px, rgba(255,255,255,0.1) 11px)
            `,
          }}
        />
      </div>

      {/* Station Glow */}
      <motion.div
        className="absolute inset-0 rounded-2xl pointer-events-none"
        animate={{
          boxShadow: [
            '0 0 30px rgba(0, 229, 255, 0.2)',
            '0 0 50px rgba(0, 229, 255, 0.35)',
            '0 0 30px rgba(0, 229, 255, 0.2)',
          ],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
    </div>
  );
}