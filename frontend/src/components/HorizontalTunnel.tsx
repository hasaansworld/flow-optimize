import { motion } from 'motion/react';

interface HorizontalTunnelProps {
  waterLevel: number; // percentage
  width: number;
  height: number;
}

export function HorizontalTunnel({ waterLevel, width, height }: HorizontalTunnelProps) {
  const waterHeight = (waterLevel / 100) * height;
  const alarmLevel = 75;
  const maxLevel = 80;

  return (
    <div
      className="relative"
      style={{
        width: width,
        height: height,
      }}
    >
      {/* Tunnel Container with depth */}
      <div
        className="relative w-full h-full rounded-3xl overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, rgba(55, 71, 79, 0.5) 0%, rgba(38, 50, 56, 0.3) 100%)',
          backdropFilter: 'blur(10px)',
          border: '3px solid rgba(255, 255, 255, 0.15)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6), inset 0 -10px 20px rgba(0, 0, 0, 0.4), inset 0 10px 20px rgba(255, 255, 255, 0.05)',
        }}
      >
        {/* Bottom sediment layer */}
        <div
          className="absolute bottom-0 left-0 right-0 h-[8%]"
          style={{
            background: 'linear-gradient(180deg, rgba(93, 78, 55, 0.6) 0%, rgba(61, 47, 31, 0.8) 100%)',
            boxShadow: 'inset 0 8px 16px rgba(0, 0, 0, 0.6)',
          }}
        />

        {/* Water with gradient */}
        <motion.div
          className="absolute bottom-0 left-0 right-0 rounded-b-3xl"
          style={{
            height: waterHeight,
            background: 'linear-gradient(180deg, #1E88E5 0%, #1565C0 50%, #0D47A1 100%)',
            boxShadow: '0 -8px 30px rgba(30, 136, 229, 0.6), inset 0 10px 30px rgba(66, 165, 245, 0.4), inset 0 -20px 40px rgba(0, 0, 0, 0.3)',
          }}
        >
          {/* Water surface line - Current Level */}
          <div
            className="absolute top-0 left-0 right-0 h-[3px]"
            style={{
              background: '#00E5FF',
              boxShadow: '0 0 10px #00E5FF, 0 0 20px rgba(0, 229, 255, 0.5)',
            }}
          >
            {/* Shimmer effect on water line */}
            <motion.div
              className="absolute top-0 h-full w-[100px]"
              style={{
                background: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.6) 50%, transparent 100%)',
              }}
              animate={{
                x: [-100, width + 100],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'linear',
              }}
            />
          </div>

          {/* Water surface shimmer */}
          <motion.div
            className="absolute top-0 left-0 right-0 h-[8%]"
            animate={{
              opacity: [0.3, 0.8, 0.3],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            style={{
              background: 'linear-gradient(180deg, rgba(66, 165, 245, 0.9) 0%, transparent 100%)',
            }}
          />

          {/* Horizontal flowing particles */}
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute rounded-full"
              style={{
                width: 6 + (i % 3) * 2,
                height: 6 + (i % 3) * 2,
                background: 'radial-gradient(circle, #00E5FF 0%, #42A5F5 40%, transparent 70%)',
                boxShadow: '0 0 12px rgba(0, 229, 255, 0.8)',
                top: `${20 + (i % 4) * 20}%`,
              }}
              animate={{
                x: [-50, width + 50],
                opacity: [0, 1, 1, 0],
              }}
              transition={{
                duration: 5 + (i % 3),
                repeat: Infinity,
                ease: 'linear',
                delay: i * 0.5,
              }}
            />
          ))}

          {/* Horizontal flow waves */}
          <motion.div
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(90deg, transparent 0%, rgba(0, 229, 255, 0.15) 50%, transparent 100%)',
            }}
            animate={{
              x: [-200, width + 200],
            }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        </motion.div>

        {/* Alarm Level Line (75%) - Dotted Orange */}
        <div
          className="absolute left-0 right-0"
          style={{
            bottom: `${alarmLevel}%`,
          }}
        >
          <div
            className="relative h-[2px]"
            style={{
              backgroundImage: 'repeating-linear-gradient(90deg, #FFA726 0px, #FFA726 10px, transparent 10px, transparent 20px)',
              boxShadow: '0 0 8px rgba(255, 167, 38, 0.5)',
            }}
          />
          <div
            className="absolute left-4 -top-6 px-2 py-1 rounded text-xs"
            style={{
              background: 'rgba(255, 167, 38, 0.2)',
              color: '#FFA726',
              border: '1px solid rgba(255, 167, 38, 0.5)',
              backdropFilter: 'blur(10px)',
            }}
          >
            Alarm - 75%
          </div>
        </div>

        {/* Maximum Level Line (80%) - Solid Red */}
        <div
          className="absolute left-0 right-0"
          style={{
            bottom: `${maxLevel}%`,
          }}
        >
          <div
            className="relative h-[3px]"
            style={{
              background: '#EF5350',
              boxShadow: '0 0 12px rgba(239, 83, 80, 0.6)',
            }}
          />
          <div
            className="absolute right-4 -top-6 px-2 py-1 rounded text-xs"
            style={{
              background: 'rgba(239, 83, 80, 0.2)',
              color: '#EF5350',
              border: '1px solid rgba(239, 83, 80, 0.5)',
              backdropFilter: 'blur(10px)',
            }}
          >
            Maximum Level - 80%
          </div>
        </div>

        {/* Glass/Cylinder highlight effect */}
        <div
          className="absolute top-8 left-12 w-40 h-20 rounded-full pointer-events-none"
          style={{
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.25) 0%, transparent 100%)',
            filter: 'blur(20px)',
          }}
        />

        {/* Depth markers on the left side */}
        <div className="absolute left-4 top-0 bottom-0 flex flex-col justify-between py-6 text-xs text-gray-500">
          {[14, 12, 10, 8, 6, 4, 2, 0].map((level) => (
            <div key={level} className="flex items-center gap-2">
              <div className="w-3 h-[1px] bg-gray-600" />
              <span>{level}m</span>
            </div>
          ))}
        </div>

        {/* Distance markers at bottom */}
        <div className="absolute bottom-2 left-0 right-0 flex justify-between px-12 text-xs text-gray-600">
          <span>0m</span>
          <span>25m</span>
          <span>50m</span>
          <span>75m</span>
          <span>100m</span>
        </div>

        {/* Current water level percentage display */}
        <div
          className="absolute left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg"
          style={{
            bottom: `${waterLevel}%`,
            transform: 'translateX(-50%) translateY(50%)',
            background: 'rgba(0, 229, 255, 0.2)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(0, 229, 255, 0.4)',
            color: '#00E5FF',
            textShadow: '0 0 10px rgba(0, 229, 255, 0.8)',
          }}
        >
          {waterLevel}%
        </div>
      </div>

      {/* Ambient Glow */}
      <motion.div
        className="absolute inset-0 rounded-2xl pointer-events-none"
        animate={{
          boxShadow: [
            '0 0 40px rgba(30, 136, 229, 0.3)',
            '0 0 60px rgba(30, 136, 229, 0.5)',
            '0 0 40px rgba(30, 136, 229, 0.3)',
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