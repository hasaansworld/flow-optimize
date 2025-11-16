import { motion } from 'motion/react';
import { Zap } from 'lucide-react';

interface CompactPumpProps {
  id: string;
  active: boolean;
  flow: string;
}

export function CompactPump({ id, active, flow }: CompactPumpProps) {
  return (
    <motion.div
      className="relative"
      whileHover={{ scale: 1.05 }}
      transition={{ duration: 0.2 }}
    >
      {/* Pump Housing */}
      <div
        className="relative rounded-xl overflow-hidden"
        style={{
          background: active
            ? 'linear-gradient(135deg, rgba(0, 229, 255, 0.15) 0%, rgba(0, 229, 255, 0.05) 100%)'
            : 'linear-gradient(135deg, rgba(30, 30, 30, 0.5) 0%, rgba(20, 20, 20, 0.3) 100%)',
          border: active
            ? '2px solid rgba(0, 229, 255, 0.4)'
            : '2px solid rgba(100, 100, 100, 0.2)',
          boxShadow: active
            ? '0 4px 16px rgba(0, 229, 255, 0.3)'
            : '0 2px 8px rgba(0, 0, 0, 0.3)',
        }}
      >
        {/* Motor Top */}
        <div
          className="h-6 relative overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #2a3a42 0%, #1f2d35 100%)',
            borderBottom: '1px solid rgba(0, 0, 0, 0.3)',
          }}
        >
          {/* Ventilation pattern */}
          <div className="absolute inset-0 flex items-center justify-center gap-[2px]">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="w-[1px] h-2 bg-black/30" />
            ))}
          </div>
        </div>

        {/* Pump Body */}
        <div className="p-2 relative">
          <div className="flex items-center justify-between">
            {/* ID and Status */}
            <div>
              <p className="text-white text-xs mb-1">{id}</p>
              <span
                className="text-[10px] px-1.5 py-0.5 rounded"
                style={{
                  background: active ? 'rgba(102, 187, 106, 0.2)' : 'rgba(158, 158, 158, 0.2)',
                  color: active ? '#66BB6A' : '#9E9E9E',
                  border: active ? '1px solid rgba(102, 187, 106, 0.5)' : '1px solid rgba(158, 158, 158, 0.3)',
                }}
              >
                {active ? 'ON' : 'OFF'}
              </span>
            </div>

            {/* Rotating Indicator */}
            <motion.div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{
                background: active ? 'rgba(0, 229, 255, 0.2)' : 'rgba(100, 100, 100, 0.15)',
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
                className="w-3 h-3"
                style={{
                  color: active ? '#00E5FF' : '#666',
                }}
              />
            </motion.div>
          </div>

          {/* Flow info for active pumps */}
          {active && parseInt(flow) > 0 && (
            <div className="mt-1 text-[10px] text-[#00E5FF]">
              {flow}
            </div>
          )}
        </div>

        {/* Base */}
        <div
          className="h-3"
          style={{
            background: 'linear-gradient(135deg, #1f2d35 0%, #15212a 100%)',
            borderTop: '1px solid rgba(0, 0, 0, 0.3)',
          }}
        />

        {/* Active glow overlay */}
        {active && (
          <motion.div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: 'radial-gradient(circle at center, rgba(0, 229, 255, 0.15) 0%, transparent 70%)',
            }}
            animate={{
              opacity: [0.5, 0.8, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )}
      </div>

      {/* Individual pump glow */}
      {active && (
        <motion.div
          className="absolute inset-0 rounded-xl pointer-events-none"
          animate={{
            boxShadow: [
              '0 0 10px rgba(0, 229, 255, 0.4)',
              '0 0 20px rgba(0, 229, 255, 0.6)',
              '0 0 10px rgba(0, 229, 255, 0.4)',
            ],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}
    </motion.div>
  );
}
