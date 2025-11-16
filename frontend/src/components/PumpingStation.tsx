import { motion } from 'motion/react';
import { Zap, Activity, Gauge } from 'lucide-react';

interface PumpingStationProps {
  activepumps: number;
  totalPumps: number;
  pressure: string;
  flowRate: string;
}

export function PumpingStation({ activepumps, totalPumps, pressure, flowRate }: PumpingStationProps) {
  return (
    <div className="relative w-[230px]">
      {/* Main Control Panel */}
      <div
        className="p-6 rounded-2xl"
        style={{
          background: 'linear-gradient(135deg, #37474F 0%, #263238 100%)',
          border: '2px solid rgba(0, 229, 255, 0.2)',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
        }}
      >
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-[#00E5FF]" />
          <h3 className="text-white">Pumping Station</h3>
        </div>

        {/* Pump Grid */}
        <div className="grid grid-cols-5 gap-2 mb-4">
          {Array.from({ length: totalPumps }).map((_, index) => (
            <motion.div
              key={index}
              className="relative aspect-square rounded-lg"
              style={{
                background: index < activepumps
                  ? 'linear-gradient(135deg, rgba(0, 229, 255, 0.3) 0%, rgba(0, 229, 255, 0.1) 100%)'
                  : 'rgba(255, 255, 255, 0.05)',
                border: index < activepumps
                  ? '1px solid rgba(0, 229, 255, 0.5)'
                  : '1px solid rgba(255, 255, 255, 0.1)',
              }}
              animate={
                index < activepumps
                  ? {
                      boxShadow: [
                        '0 0 10px rgba(0, 229, 255, 0.3)',
                        '0 0 20px rgba(0, 229, 255, 0.6)',
                        '0 0 10px rgba(0, 229, 255, 0.3)',
                      ],
                    }
                  : {}
              }
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: index * 0.2,
              }}
            >
              {/* Pump Active Indicator */}
              {index < activepumps && (
                <motion.div
                  className="absolute inset-0 flex items-center justify-center"
                  animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: 'easeInOut',
                    delay: index * 0.3,
                  }}
                >
                  <div className="w-2 h-2 rounded-full bg-[#00E5FF]" />
                </motion.div>
              )}

              {/* Pump Number */}
              <div className="absolute bottom-0 right-0 p-0.5">
                <span className="text-[8px] text-gray-500">{index + 1}</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Metrics */}
        <div className="space-y-3">
          <div
            className="p-3 rounded-lg"
            style={{
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-[#00E5FF]" />
              <span className="text-xs text-gray-400">Flow Rate</span>
            </div>
            <p className="text-white">{flowRate}</p>
          </div>

          <div
            className="p-3 rounded-lg"
            style={{
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            <div className="flex items-center gap-2 mb-1">
              <Gauge className="w-4 h-4 text-[#00E5FF]" />
              <span className="text-xs text-gray-400">Pressure</span>
            </div>
            <p className="text-white">{pressure}</p>
          </div>

          {/* Status Bar */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-gray-400">Status</span>
            <motion.div
              className="px-2 py-1 rounded-full text-xs text-white"
              style={{
                background: 'rgba(102, 187, 106, 0.2)',
                border: '1px solid rgba(102, 187, 106, 0.5)',
              }}
              animate={{
                boxShadow: [
                  '0 0 10px rgba(102, 187, 106, 0.3)',
                  '0 0 20px rgba(102, 187, 106, 0.5)',
                  '0 0 10px rgba(102, 187, 106, 0.3)',
                ],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              ACTIVE
            </motion.div>
          </div>
        </div>
      </div>

      {/* Ambient Glow */}
      <motion.div
        className="absolute inset-0 rounded-2xl pointer-events-none"
        animate={{
          boxShadow: [
            '0 0 30px rgba(0, 229, 255, 0.2)',
            '0 0 50px rgba(0, 229, 255, 0.3)',
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
