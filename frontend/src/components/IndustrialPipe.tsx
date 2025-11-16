import { motion } from 'motion/react';

interface IndustrialPipeProps {
  start: { x: number; y: number };
  end: { x: number; y: number };
  active: boolean;
}

export function IndustrialPipe({ start, end, active }: IndustrialPipeProps) {
  const length = Math.abs(end.x - start.x);
  const pipeHeight = 28;

  return (
    <div
      className="absolute"
      style={{
        left: start.x,
        top: start.y - pipeHeight / 2,
        width: length,
        height: pipeHeight,
      }}
    >
      {/* Main Pipe Body - Metallic with segments */}
      <div className="relative w-full h-full">
        {/* Bottom shadow layer */}
        <div
          className="absolute bottom-0 left-0 right-0 h-1/2 rounded-full"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.4) 100%)',
          }}
        />

        {/* Main pipe cylinder */}
        <div
          className="absolute inset-0 rounded-full overflow-hidden"
          style={{
            background: active
              ? 'linear-gradient(180deg, #546E7A 0%, #37474F 50%, #263238 100%)'
              : 'linear-gradient(180deg, #4A5A62 0%, #2F3D44 50%, #1F2A30 100%)',
            boxShadow: active
              ? '0 4px 12px rgba(0, 0, 0, 0.6), inset 0 2px 4px rgba(255, 255, 255, 0.1), inset 0 -2px 4px rgba(0, 0, 0, 0.4)'
              : '0 3px 8px rgba(0, 0, 0, 0.5), inset 0 2px 4px rgba(255, 255, 255, 0.05), inset 0 -2px 4px rgba(0, 0, 0, 0.4)',
          }}
        >
          {/* Top highlight */}
          <div
            className="absolute top-0 left-0 right-0 h-[30%] rounded-t-full"
            style={{
              background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.15) 0%, transparent 100%)',
            }}
          />

          {/* Bottom shadow */}
          <div
            className="absolute bottom-0 left-0 right-0 h-[30%] rounded-b-full"
            style={{
              background: 'linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.3) 100%)',
            }}
          />

          {/* Segmented pipe joints */}
          {[0, 0.33, 0.66, 1].map((position, i) => (
            <div
              key={i}
              className="absolute top-0 bottom-0"
              style={{
                left: `${position * 100}%`,
                width: '3px',
                background: 'linear-gradient(180deg, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0.2) 50%, rgba(0, 0, 0, 0.4) 100%)',
                boxShadow: '1px 0 2px rgba(255, 255, 255, 0.1)',
              }}
            />
          ))}

          {/* Flow glow effect - only subtle glow, no particles */}
          {active && (
            <motion.div
              className="absolute inset-0"
              style={{
                background: 'linear-gradient(90deg, transparent 0%, rgba(0, 229, 255, 0.08) 50%, transparent 100%)',
              }}
              animate={{
                x: [-100, length + 100],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
              }}
            />
          )}
        </div>

        {/* Pipe flanges/connectors at ends */}
        <div
          className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-8 rounded"
          style={{
            background: 'linear-gradient(135deg, #455A64 0%, #263238 100%)',
            border: '1px solid rgba(0, 0, 0, 0.3)',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.4), inset 0 1px 2px rgba(255, 255, 255, 0.1)',
          }}
        >
          {/* Bolt details */}
          {[0.25, 0.75].map((pos, i) => (
            <div
              key={i}
              className="absolute w-1.5 h-1.5 rounded-full"
              style={{
                left: '50%',
                top: `${pos * 100}%`,
                transform: 'translate(-50%, -50%)',
                background: 'radial-gradient(circle, #1a1a1a 0%, #000 100%)',
                boxShadow: 'inset 0 1px 1px rgba(255, 255, 255, 0.2)',
              }}
            />
          ))}
        </div>

        <div
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-6 h-8 rounded"
          style={{
            background: 'linear-gradient(135deg, #455A64 0%, #263238 100%)',
            border: '1px solid rgba(0, 0, 0, 0.3)',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.4), inset 0 1px 2px rgba(255, 255, 255, 0.1)',
          }}
        >
          {/* Bolt details */}
          {[0.25, 0.75].map((pos, i) => (
            <div
              key={i}
              className="absolute w-1.5 h-1.5 rounded-full"
              style={{
                left: '50%',
                top: `${pos * 100}%`,
                transform: 'translate(-50%, -50%)',
                background: 'radial-gradient(circle, #1a1a1a 0%, #000 100%)',
                boxShadow: 'inset 0 1px 1px rgba(255, 255, 255, 0.2)',
              }}
            />
          ))}
        </div>

        {/* Active glow around pipe */}
        {active && (
          <motion.div
            className="absolute inset-0 rounded-full pointer-events-none"
            animate={{
              boxShadow: [
                '0 0 15px rgba(0, 229, 255, 0.2)',
                '0 0 25px rgba(0, 229, 255, 0.35)',
                '0 0 15px rgba(0, 229, 255, 0.2)',
              ],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )}
      </div>
    </div>
  );
}
