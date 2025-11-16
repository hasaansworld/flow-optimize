import { motion } from 'motion/react';

interface WaterTunnelProps {
  waterLevel: number; // percentage
  length: number; // pixels
  position: { top: number; left: number };
}

export function WaterTunnel({ waterLevel, length, position }: WaterTunnelProps) {
  const tunnelHeight = 120;
  const waterHeight = (waterLevel / 100) * tunnelHeight;

  return (
    <div
      className="absolute"
      style={{
        top: position.top,
        left: position.left,
        width: length,
        height: tunnelHeight,
      }}
    >
      {/* Tunnel Container */}
      <div
        className="relative w-full h-full rounded-2xl overflow-hidden"
        style={{
          background: 'rgba(55, 71, 79, 0.4)',
          backdropFilter: 'blur(10px)',
          border: '2px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.5), inset 0 -4px 8px rgba(0, 0, 0, 0.3)',
        }}
      >
        {/* Ground/Bottom Layer */}
        <div
          className="absolute bottom-0 left-0 right-0 h-[20%]"
          style={{
            background: 'linear-gradient(180deg, #5D4E37 0%, #3D2F1F 100%)',
            boxShadow: 'inset 0 4px 8px rgba(0, 0, 0, 0.5)',
          }}
        />

        {/* Water Layer */}
        <motion.div
          className="absolute bottom-0 left-0 right-0"
          style={{
            height: waterHeight,
            background: 'linear-gradient(180deg, #1E88E5 0%, #0D47A1 100%)',
            boxShadow: '0 -4px 20px rgba(30, 136, 229, 0.5), inset 0 4px 12px rgba(66, 165, 245, 0.3)',
          }}
        >
          {/* Water Surface Shimmer */}
          <motion.div
            className="absolute top-0 left-0 right-0 h-[30%]"
            animate={{
              opacity: [0.4, 0.7, 0.4],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            style={{
              background: 'linear-gradient(180deg, rgba(66, 165, 245, 0.6) 0%, transparent 100%)',
            }}
          />

          {/* Animated Flow Particles - Left to Right */}
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute rounded-full"
              style={{
                width: 8 + (i % 3) * 4,
                height: 8 + (i % 3) * 4,
                background: 'radial-gradient(circle, #00E5FF 0%, #42A5F5 50%, transparent 100%)',
                boxShadow: '0 0 15px #00E5FF',
                top: `${20 + (i % 3) * 25}%`,
              }}
              animate={{
                x: [-50, length + 50],
                opacity: [0, 1, 1, 0],
              }}
              transition={{
                duration: 6 + (i % 3) * 2,
                repeat: Infinity,
                ease: 'linear',
                delay: i * 0.8,
              }}
            />
          ))}

          {/* Flow Animation Waves */}
          <motion.div
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(90deg, transparent 0%, rgba(0, 229, 255, 0.2) 50%, transparent 100%)',
            }}
            animate={{
              x: [-200, length + 200],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        </motion.div>

        {/* Glass Reflection on tunnel */}
        <div
          className="absolute top-4 left-8 w-32 h-16 rounded-full pointer-events-none"
          style={{
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%)',
            filter: 'blur(12px)',
          }}
        />

        {/* Level Markers */}
        <div className="absolute left-4 top-0 bottom-0 flex flex-col justify-between py-4 text-xs text-gray-400">
          <span>14m</span>
          <span>12m</span>
          <span>10m</span>
          <span>8m</span>
          <span>6m</span>
          <span>4m</span>
          <span>2m</span>
          <span>0m</span>
        </div>

        {/* Distance Markers at bottom */}
        <div className="absolute bottom-2 left-0 right-0 flex justify-between px-8 text-xs text-gray-500">
          <span>0</span>
          <span>20</span>
          <span>40</span>
          <span>60</span>
          <span>80</span>
          <span>100</span>
        </div>
      </div>

      {/* Ambient Glow */}
      <motion.div
        className="absolute inset-0 rounded-2xl pointer-events-none"
        animate={{
          boxShadow: [
            '0 0 30px rgba(30, 136, 229, 0.2)',
            '0 0 50px rgba(30, 136, 229, 0.3)',
            '0 0 30px rgba(30, 136, 229, 0.2)',
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
