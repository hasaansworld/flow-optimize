import { motion } from 'motion/react';
import { Zap } from 'lucide-react';

interface RealisticPumpProps {
  id: string;
  active: boolean;
  flow: string;
  side: 'left' | 'right';
}

export function RealisticPump({ id, active, flow, side }: RealisticPumpProps) {
  return (
    <div className="relative">
      {/* Connection pipe to tunnel */}
      <motion.div
        className="absolute top-1/2 h-[3px] rounded-full"
        style={{
          [side === 'left' ? 'right' : 'left']: '100%',
          width: '60px',
          background: active
            ? 'linear-gradient(90deg, rgba(0, 229, 255, 0.6), rgba(0, 229, 255, 0.2))'
            : 'linear-gradient(90deg, rgba(100, 100, 100, 0.3), rgba(100, 100, 100, 0.1))',
          transform: side === 'left' ? 'none' : 'scaleX(-1)',
        }}
      >
        {/* Flow animation in pipe */}
        {active && (
          <motion.div
            className="absolute top-0 w-2 h-full rounded-full"
            style={{
              background: '#00E5FF',
              boxShadow: '0 0 10px #00E5FF',
              left: 0,
            }}
            animate={{
              x: [0, 60],
              opacity: [1, 0],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        )}
      </motion.div>

      {/* Pump Body */}
      <motion.div
        className="relative"
        whileHover={{ scale: 1.02 }}
        transition={{ duration: 0.2 }}
      >
        {/* Main pump housing - cylindrical look */}
        <div className="relative w-[140px]">
          {/* Motor housing (top) */}
          <div
            className="relative h-[40px] rounded-t-2xl overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, #37474F 0%, #263238 100%)',
              border: '2px solid rgba(255, 255, 255, 0.1)',
              borderBottom: 'none',
              boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.4), 0 4px 12px rgba(0, 0, 0, 0.4)',
            }}
          >
            {/* Motor top highlight */}
            <div
              className="absolute top-1 left-4 right-4 h-3 rounded-full"
              style={{
                background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%)',
                filter: 'blur(3px)',
              }}
            />
            
            {/* Ventilation slots */}
            <div className="absolute inset-0 flex items-center justify-center gap-1">
              {[...Array(8)].map((_, i) => (
                <div
                  key={i}
                  className="w-[1px] h-4 bg-black/40"
                />
              ))}
            </div>
          </div>

          {/* Pump body (main cylinder) */}
          <div
            className="relative h-[70px] overflow-hidden"
            style={{
              background: active
                ? 'linear-gradient(135deg, rgba(55, 71, 79, 0.95) 0%, rgba(38, 50, 56, 0.9) 50%, rgba(55, 71, 79, 0.95) 100%)'
                : 'linear-gradient(135deg, #37474F 0%, #263238 50%, #37474F 100%)',
              border: '2px solid rgba(255, 255, 255, 0.1)',
              borderTop: 'none',
              borderBottom: 'none',
              boxShadow: active
                ? 'inset -8px 0 16px rgba(0, 0, 0, 0.5), inset 8px 0 16px rgba(0, 229, 255, 0.1), 0 0 20px rgba(0, 229, 255, 0.3)'
                : 'inset -8px 0 16px rgba(0, 0, 0, 0.5), inset 8px 0 8px rgba(255, 255, 255, 0.03)',
            }}
          >
            {/* Cylindrical highlights */}
            <div
              className="absolute top-0 bottom-0 left-4 w-12"
              style={{
                background: 'linear-gradient(90deg, rgba(255, 255, 255, 0.15) 0%, transparent 100%)',
                filter: 'blur(8px)',
              }}
            />

            {/* Center content */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-white mb-1">{id}</p>
                <div className="flex items-center justify-center gap-2">
                  <motion.div
                    className="w-8 h-8 rounded-full flex items-center justify-center"
                    style={{
                      background: active ? 'rgba(0, 229, 255, 0.2)' : 'rgba(100, 100, 100, 0.2)',
                      border: active ? '1px solid rgba(0, 229, 255, 0.5)' : '1px solid rgba(100, 100, 100, 0.3)',
                    }}
                    animate={
                      active
                        ? {
                            rotate: 360,
                          }
                        : {}
                    }
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: 'linear',
                    }}
                  >
                    <Zap
                      className="w-4 h-4"
                      style={{
                        color: active ? '#00E5FF' : '#666',
                      }}
                    />
                  </motion.div>
                </div>
              </div>
            </div>

            {/* Vibration effect for active pumps */}
            {active && (
              <motion.div
                className="absolute inset-0"
                animate={{
                  x: [-0.5, 0.5, -0.5],
                }}
                transition={{
                  duration: 0.1,
                  repeat: Infinity,
                  ease: 'linear',
                }}
              />
            )}
          </div>

          {/* Pump base/outlet */}
          <div
            className="relative h-[35px] rounded-b-2xl overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, #263238 0%, #1a252b 100%)',
              border: '2px solid rgba(255, 255, 255, 0.1)',
              borderTop: 'none',
              boxShadow: 'inset 0 -2px 8px rgba(0, 0, 0, 0.6), 0 8px 16px rgba(0, 0, 0, 0.5)',
            }}
          >
            {/* Base ring detail */}
            <div
              className="absolute top-2 left-4 right-4 h-2"
              style={{
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '50%',
                boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.5)',
              }}
            />

            {/* Outlet pipe indicator */}
            <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-8 h-2 bg-black/60 rounded-sm" />
          </div>

          {/* Active glow effect */}
          {active && (
            <>
              <motion.div
                className="absolute inset-0 rounded-2xl pointer-events-none"
                animate={{
                  boxShadow: [
                    '0 0 20px rgba(0, 229, 255, 0.4)',
                    '0 0 35px rgba(0, 229, 255, 0.6)',
                    '0 0 20px rgba(0, 229, 255, 0.4)',
                  ],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              />
              
              {/* Internal glow */}
              <motion.div
                className="absolute inset-0 rounded-2xl pointer-events-none"
                style={{
                  background: 'radial-gradient(circle at center, rgba(0, 229, 255, 0.1) 0%, transparent 70%)',
                }}
                animate={{
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              />
            </>
          )}
        </div>

        {/* Status display below pump */}
        <div className="mt-2 text-center">
          <div
            className="inline-block px-3 py-1 rounded-full text-xs mb-1"
            style={{
              background: active ? 'rgba(102, 187, 106, 0.2)' : 'rgba(158, 158, 158, 0.2)',
              color: active ? '#66BB6A' : '#9E9E9E',
              border: active ? '1px solid rgba(102, 187, 106, 0.5)' : '1px solid rgba(158, 158, 158, 0.3)',
            }}
          >
            {active ? 'ON' : 'OFF'}
          </div>
          {active && (
            <p className="text-xs text-[#00E5FF]">{flow}</p>
          )}
        </div>
      </motion.div>
    </div>
  );
}
