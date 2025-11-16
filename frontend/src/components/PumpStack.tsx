import { motion } from 'motion/react';
import { Power } from 'lucide-react';

interface Pump {
  id: string;
  active: boolean;
  label: string;
}

interface PumpStackProps {
  pumps: Pump[];
  position: { top: number; right: number };
}

export function PumpStack({ pumps, position }: PumpStackProps) {
  return (
    <div
      className="absolute flex flex-col gap-3"
      style={{
        top: position.top,
        right: position.right,
      }}
    >
      {pumps.map((pump, index) => (
        <motion.div
          key={pump.id}
          className="relative"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          {/* Pump Unit */}
          <div
            className="relative w-[160px] p-4 rounded-xl overflow-hidden"
            style={{
              background: pump.active
                ? 'linear-gradient(135deg, rgba(0, 229, 255, 0.15) 0%, rgba(0, 229, 255, 0.05) 100%)'
                : 'linear-gradient(135deg, rgba(55, 71, 79, 0.6) 0%, rgba(38, 50, 56, 0.4) 100%)',
              backdropFilter: 'blur(20px)',
              border: pump.active
                ? '2px solid rgba(0, 229, 255, 0.5)'
                : '2px solid rgba(255, 255, 255, 0.1)',
              boxShadow: pump.active
                ? '0 4px 24px rgba(0, 229, 255, 0.3)'
                : '0 4px 16px rgba(0, 0, 0, 0.3)',
            }}
          >
            {/* Background Pattern */}
            <div
              className="absolute inset-0 opacity-10"
              style={{
                backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px)',
              }}
            />

            <div className="relative flex items-center justify-between">
              {/* Pump Label */}
              <div>
                <p className="text-white mb-1">{pump.id}</p>
                <p className="text-xs text-gray-400">{pump.label}</p>
              </div>

              {/* Status Indicator */}
              <div className="flex flex-col items-center gap-1">
                <motion.div
                  className="relative w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{
                    background: pump.active
                      ? 'rgba(0, 229, 255, 0.2)'
                      : 'rgba(255, 255, 255, 0.05)',
                    border: pump.active
                      ? '1px solid rgba(0, 229, 255, 0.5)'
                      : '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  animate={
                    pump.active
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
                  }}
                >
                  <Power
                    className="w-5 h-5"
                    style={{
                      color: pump.active ? '#00E5FF' : '#666',
                    }}
                  />

                  {/* Rotating indicator for active pumps */}
                  {pump.active && (
                    <motion.div
                      className="absolute inset-0 rounded-lg"
                      style={{
                        border: '2px solid transparent',
                        borderTopColor: '#00E5FF',
                        borderRightColor: '#00E5FF',
                      }}
                      animate={{
                        rotate: 360,
                      }}
                      transition={{
                        duration: 3,
                        repeat: Infinity,
                        ease: 'linear',
                      }}
                    />
                  )}
                </motion.div>

                {/* ON/OFF Label */}
                <span
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{
                    background: pump.active
                      ? 'rgba(102, 187, 106, 0.2)'
                      : 'rgba(158, 158, 158, 0.2)',
                    color: pump.active ? '#66BB6A' : '#9E9E9E',
                    border: pump.active
                      ? '1px solid rgba(102, 187, 106, 0.5)'
                      : '1px solid rgba(158, 158, 158, 0.3)',
                  }}
                >
                  {pump.active ? 'ON' : 'OFF'}
                </span>
              </div>
            </div>

            {/* Active Pump Glow Effect */}
            {pump.active && (
              <motion.div
                className="absolute inset-0 rounded-xl pointer-events-none"
                animate={{
                  opacity: [0.3, 0.6, 0.3],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
                style={{
                  background: 'radial-gradient(circle at 80% 50%, rgba(0, 229, 255, 0.2) 0%, transparent 70%)',
                }}
              />
            )}
          </div>

          {/* Connection line to tunnel */}
          <motion.div
            className="absolute top-1/2 left-0 w-8 h-[2px]"
            style={{
              transform: 'translateX(-100%)',
              background: pump.active
                ? 'linear-gradient(90deg, transparent 0%, rgba(0, 229, 255, 0.6) 100%)'
                : 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 100%)',
            }}
          >
            {pump.active && (
              <motion.div
                className="absolute top-0 left-0 w-2 h-full rounded-full"
                style={{
                  background: '#00E5FF',
                  boxShadow: '0 0 10px #00E5FF',
                }}
                animate={{
                  x: [0, 32],
                  opacity: [1, 0],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              />
            )}
          </motion.div>
        </motion.div>
      ))}
    </div>
  );
}
