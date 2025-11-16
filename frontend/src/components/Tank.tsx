import { motion } from 'motion/react';
import { Droplets, Thermometer } from 'lucide-react';

interface TankProps {
  id: string;
  label: string;
  level: number;
  capacity: string;
  status: 'good' | 'warning' | 'alert';
  temperature?: string;
  isOutput?: boolean;
}

export function Tank({ id, label, level, capacity, status, temperature, isOutput }: TankProps) {
  const statusColors = {
    good: '#66BB6A',
    warning: '#FFA726',
    alert: '#EF5350',
  };

  return (
    <div className="relative">
      {/* Tank Container */}
      <div className="relative w-[200px] h-[250px]">
        {/* Glass Container */}
        <div
          className="absolute inset-0 rounded-2xl overflow-hidden"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(10px)',
            border: '2px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
          }}
        >
          {/* Water Fill with Gradient */}
          <motion.div
            className="absolute bottom-0 left-0 right-0 rounded-b-2xl"
            initial={{ height: 0 }}
            animate={{ height: `${level}%` }}
            transition={{ duration: 2, ease: 'easeOut' }}
            style={{
              background: isOutput
                ? 'linear-gradient(180deg, #42A5F5 0%, #1E88E5 100%)'
                : 'linear-gradient(180deg, #1E88E5 0%, #0D47A1 100%)',
              boxShadow: `0 -20px 40px rgba(30, 136, 229, 0.4), inset 0 10px 20px rgba(66, 165, 245, 0.3)`,
            }}
          >
            {/* Water Surface Animation */}
            <motion.div
              className="absolute top-0 left-0 right-0 h-[20px]"
              animate={{
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              style={{
                background: 'linear-gradient(180deg, rgba(66, 165, 245, 0.8) 0%, transparent 100%)',
              }}
            />

            {/* Bubbles */}
            {!isOutput && (
              <>
                <motion.div
                  className="absolute bottom-[20%] left-[30%] w-2 h-2 rounded-full bg-white/30"
                  animate={{
                    y: [-100, -250],
                    opacity: [0, 1, 0],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    delay: 0,
                  }}
                />
                <motion.div
                  className="absolute bottom-[10%] left-[60%] w-3 h-3 rounded-full bg-white/20"
                  animate={{
                    y: [-100, -250],
                    opacity: [0, 1, 0],
                  }}
                  transition={{
                    duration: 4,
                    repeat: Infinity,
                    delay: 1,
                  }}
                />
                <motion.div
                  className="absolute bottom-[15%] left-[75%] w-2 h-2 rounded-full bg-white/25"
                  animate={{
                    y: [-100, -250],
                    opacity: [0, 1, 0],
                  }}
                  transition={{
                    duration: 3.5,
                    repeat: Infinity,
                    delay: 2,
                  }}
                />
              </>
            )}
          </motion.div>

          {/* Glass Highlight */}
          <div
            className="absolute top-4 left-4 w-12 h-24 rounded-full"
            style={{
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.4) 0%, transparent 100%)',
              filter: 'blur(8px)',
            }}
          />

          {/* Level Indicator Lines */}
          <div className="absolute left-4 right-4 top-[25%] h-[1px] bg-white/10" />
          <div className="absolute left-4 right-4 top-[50%] h-[1px] bg-white/10" />
          <div className="absolute left-4 right-4 top-[75%] h-[1px] bg-white/10" />
        </div>

        {/* Status Glow */}
        <motion.div
          className="absolute inset-0 rounded-2xl pointer-events-none"
          animate={{
            boxShadow: [
              `0 0 20px ${statusColors[status]}40`,
              `0 0 30px ${statusColors[status]}60`,
              `0 0 20px ${statusColors[status]}40`,
            ],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />

        {/* Level Percentage Badge */}
        <div
          className="absolute top-4 right-4 px-3 py-1 rounded-full text-white"
          style={{
            background: 'rgba(0, 229, 255, 0.2)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(0, 229, 255, 0.3)',
            boxShadow: '0 0 20px rgba(0, 229, 255, 0.3)',
          }}
        >
          {level}%
        </div>
      </div>

      {/* Info Card Below Tank */}
      <div
        className="mt-4 p-4 rounded-xl"
        style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        }}
      >
        <div className="flex items-center gap-2 mb-2">
          <Droplets className="w-4 h-4 text-[#00E5FF]" />
          <h3 className="text-white">{label}</h3>
        </div>
        <div className="space-y-1">
          <p className="text-gray-400 text-xs">Capacity: {capacity}</p>
          {temperature && (
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <Thermometer className="w-3 h-3" />
              <span>{temperature}</span>
            </div>
          )}
          <div className="flex items-center gap-2 mt-2">
            <div
              className="w-2 h-2 rounded-full"
              style={{
                background: statusColors[status],
                boxShadow: `0 0 10px ${statusColors[status]}`,
              }}
            />
            <span className="text-xs" style={{ color: statusColors[status] }}>
              {status === 'good' ? 'Normal' : status === 'warning' ? 'Attention' : 'Alert'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
