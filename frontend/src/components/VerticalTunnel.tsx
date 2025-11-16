import { motion } from 'motion/react';

interface VerticalTunnelProps {
  waterLevel: number; // percentage
  height: number;
  width: number;
}

export function VerticalTunnel({ waterLevel, height, width }: VerticalTunnelProps) {
  const waterHeight = (waterLevel / 100) * height;

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
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6), inset -10px 0 20px rgba(0, 0, 0, 0.4), inset 10px 0 20px rgba(255, 255, 255, 0.05)',
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
            boxShadow: '0 -8px 30px rgba(30, 136, 229, 0.6), inset 0 10px 30px rgba(66, 165, 245, 0.4), inset -20px 0 40px rgba(0, 0, 0, 0.3)',
          }}
        >
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

          {/* Upward flowing particles */}
          {[...Array(12)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute rounded-full"
              style={{
                width: 6 + (i % 4) * 3,
                height: 6 + (i % 4) * 3,
                background: 'radial-gradient(circle, #00E5FF 0%, #42A5F5 40%, transparent 70%)',
                boxShadow: '0 0 12px rgba(0, 229, 255, 0.8)',
                left: `${15 + (i % 5) * 15}%`,
              }}
              animate={{
                y: [waterHeight, -50],
                opacity: [0, 1, 1, 0],
                scale: [0.8, 1.2, 1, 0.8],
              }}
              transition={{
                duration: 4 + (i % 3),
                repeat: Infinity,
                ease: 'easeInOut',
                delay: i * 0.4,
              }}
            />
          ))}

          {/* Vertical flow waves */}
          <motion.div
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(180deg, transparent 0%, rgba(0, 229, 255, 0.15) 50%, transparent 100%)',
            }}
            animate={{
              y: [-100, height + 100],
            }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: 'linear',
            }}
          />

          {/* Turbulence effect */}
          <motion.div
            className="absolute inset-0"
            style={{
              background: 'radial-gradient(ellipse at 30% 50%, rgba(0, 229, 255, 0.2) 0%, transparent 60%)',
            }}
            animate={{
              x: [0, 40, 0, -40, 0],
              opacity: [0.3, 0.6, 0.3],
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        </motion.div>

        {/* Glass/Cylinder highlight effect */}
        <div
          className="absolute top-12 left-8 w-20 h-40 rounded-full pointer-events-none"
          style={{
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.25) 0%, transparent 100%)',
            filter: 'blur(20px)',
          }}
        />

        {/* Depth markers on the side */}
        <div className="absolute left-4 top-0 bottom-0 flex flex-col justify-between py-8 text-xs text-gray-500">
          {[14, 12, 10, 8, 6, 4, 2, 0].map((level) => (
            <div key={level} className="flex items-center gap-2">
              <div className="w-3 h-[1px] bg-gray-600" />
              <span>{level}m</span>
            </div>
          ))}
        </div>

        {/* Distance markers at bottom */}
        <div className="absolute bottom-8 left-0 right-0 flex flex-col items-center gap-1 text-xs text-gray-600">
          <div className="h-3 w-[1px] bg-gray-600" />
          <span>0</span>
        </div>
        <div className="absolute top-1/4 left-0 right-0 flex flex-col items-center gap-1 text-xs text-gray-600">
          <div className="h-3 w-[1px] bg-gray-600" />
          <span>20</span>
        </div>
        <div className="absolute top-1/2 left-0 right-0 flex flex-col items-center gap-1 text-xs text-gray-600">
          <div className="h-3 w-[1px] bg-gray-600" />
          <span>40</span>
        </div>
        <div className="absolute top-3/4 left-0 right-0 flex flex-col items-center gap-1 text-xs text-gray-600">
          <div className="h-3 w-[1px] bg-gray-600" />
          <span>60</span>
        </div>
      </div>

      {/* Ambient blue glow */}
      <motion.div
        className="absolute inset-0 rounded-3xl pointer-events-none"
        animate={{
          boxShadow: [
            '0 0 40px rgba(30, 136, 229, 0.3)',
            '0 0 60px rgba(30, 136, 229, 0.5)',
            '0 0 40px rgba(30, 136, 229, 0.3)',
          ],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
    </div>
  );
}
