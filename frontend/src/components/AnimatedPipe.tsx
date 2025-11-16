import { motion } from 'motion/react';

interface AnimatedPipeProps {
  start: { x: number; y: number };
  end: { x: number; y: number };
  active: boolean;
  horizontal?: boolean;
}

export function AnimatedPipe({ start, end, active, horizontal = false }: AnimatedPipeProps) {
  const width = horizontal ? Math.abs(end.x - start.x) : 20;
  const height = horizontal ? 20 : Math.abs(end.y - start.y);

  return (
    <div
      className="absolute"
      style={{
        left: start.x,
        top: start.y,
        width: horizontal ? width : 20,
        height: horizontal ? 20 : height,
      }}
    >
      {/* Pipe Body */}
      <div
        className="absolute inset-0 rounded-full overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, rgba(30, 136, 229, 0.3) 0%, rgba(66, 165, 245, 0.3) 100%)',
          border: '2px solid rgba(30, 136, 229, 0.5)',
          boxShadow: '0 4px 20px rgba(30, 136, 229, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.3)',
        }}
      >
        {/* Flow Particles */}
        {active && (
          <>
            <motion.div
              className="absolute w-3 h-3 rounded-full"
              style={{
                background: 'radial-gradient(circle, #00E5FF 0%, transparent 70%)',
                boxShadow: '0 0 10px #00E5FF',
              }}
              animate={
                horizontal
                  ? { x: [-20, width + 20] }
                  : { y: [-20, height + 20] }
              }
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
                delay: 0,
              }}
            />
            <motion.div
              className="absolute w-2 h-2 rounded-full"
              style={{
                background: 'radial-gradient(circle, #42A5F5 0%, transparent 70%)',
                boxShadow: '0 0 8px #42A5F5',
              }}
              animate={
                horizontal
                  ? { x: [-20, width + 20] }
                  : { y: [-20, height + 20] }
              }
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
                delay: 0.5,
              }}
            />
            <motion.div
              className="absolute w-2 h-2 rounded-full"
              style={{
                background: 'radial-gradient(circle, #00E5FF 0%, transparent 70%)',
                boxShadow: '0 0 8px #00E5FF',
              }}
              animate={
                horizontal
                  ? { x: [-20, width + 20] }
                  : { y: [-20, height + 20] }
              }
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
                delay: 1,
              }}
            />
            <motion.div
              className="absolute w-3 h-3 rounded-full"
              style={{
                background: 'radial-gradient(circle, #1E88E5 0%, transparent 70%)',
                boxShadow: '0 0 10px #1E88E5',
              }}
              animate={
                horizontal
                  ? { x: [-20, width + 20] }
                  : { y: [-20, height + 20] }
              }
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
                delay: 1.5,
              }}
            />
          </>
        )}

        {/* Flow Animation Gradient */}
        {active && (
          <motion.div
            className="absolute inset-0"
            style={{
              background: horizontal
                ? 'linear-gradient(90deg, transparent 0%, rgba(0, 229, 255, 0.3) 50%, transparent 100%)'
                : 'linear-gradient(180deg, transparent 0%, rgba(0, 229, 255, 0.3) 50%, transparent 100%)',
            }}
            animate={
              horizontal
                ? { x: [-width, width * 2] }
                : { y: [-height, height * 2] }
            }
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        )}
      </div>

      {/* Pipe Highlight */}
      <div
        className="absolute rounded-full"
        style={{
          top: horizontal ? 2 : 0,
          left: horizontal ? 0 : 2,
          width: horizontal ? width : 8,
          height: horizontal ? 8 : height,
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%)',
          filter: 'blur(2px)',
          pointerEvents: 'none',
        }}
      />

      {/* Ambient Glow */}
      {active && (
        <motion.div
          className="absolute inset-0 rounded-full pointer-events-none"
          animate={{
            boxShadow: [
              '0 0 15px rgba(0, 229, 255, 0.3)',
              '0 0 25px rgba(0, 229, 255, 0.5)',
              '0 0 15px rgba(0, 229, 255, 0.3)',
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
  );
}
