import { motion } from 'motion/react';

interface ConnectionPipeProps {
  start: { x: number; y: number };
  end: { x: number; y: number };
  active: boolean;
  size?: 'small' | 'medium' | 'large';
}

export function ConnectionPipe({ start, end, active, size = 'medium' }: ConnectionPipeProps) {
  const isHorizontal = Math.abs(end.y - start.y) < Math.abs(end.x - start.x);
  const width = isHorizontal ? Math.abs(end.x - start.x) : 24;
  const height = isHorizontal ? 24 : Math.abs(end.y - start.y);

  const pipeThickness = size === 'large' ? 24 : size === 'medium' ? 16 : 12;

  return (
    <div
      className="absolute pointer-events-none"
      style={{
        left: start.x,
        top: start.y,
        width: isHorizontal ? width : pipeThickness,
        height: isHorizontal ? pipeThickness : height,
      }}
    >
      {/* Pipe Body */}
      <div
        className="absolute inset-0 rounded-full overflow-hidden"
        style={{
          background: active
            ? 'linear-gradient(135deg, rgba(30, 136, 229, 0.4) 0%, rgba(66, 165, 245, 0.4) 100%)'
            : 'linear-gradient(135deg, rgba(100, 100, 100, 0.3) 0%, rgba(80, 80, 80, 0.2) 100%)',
          border: active
            ? '2px solid rgba(30, 136, 229, 0.6)'
            : '2px solid rgba(100, 100, 100, 0.3)',
          boxShadow: active
            ? '0 4px 20px rgba(30, 136, 229, 0.4), inset 0 2px 4px rgba(0, 0, 0, 0.3)'
            : '0 2px 10px rgba(0, 0, 0, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.3)',
        }}
      >
        {/* Flow Particles */}
        {active && (
          <>
            {[...Array(4)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute rounded-full"
                style={{
                  width: pipeThickness * 0.4,
                  height: pipeThickness * 0.4,
                  background: 'radial-gradient(circle, #00E5FF 0%, #42A5F5 40%, transparent 70%)',
                  boxShadow: '0 0 12px rgba(0, 229, 255, 0.8)',
                  left: isHorizontal ? 0 : '50%',
                  top: isHorizontal ? '50%' : 0,
                  transform: isHorizontal ? 'translateY(-50%)' : 'translateX(-50%)',
                }}
                animate={
                  isHorizontal
                    ? { x: [-30, width + 30] }
                    : { y: [-30, height + 30] }
                }
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'linear',
                  delay: i * 0.5,
                }}
              />
            ))}
          </>
        )}

        {/* Flow Animation Wave */}
        {active && (
          <motion.div
            className="absolute inset-0"
            style={{
              background: isHorizontal
                ? 'linear-gradient(90deg, transparent 0%, rgba(0, 229, 255, 0.3) 50%, transparent 100%)'
                : 'linear-gradient(180deg, transparent 0%, rgba(0, 229, 255, 0.3) 50%, transparent 100%)',
            }}
            animate={
              isHorizontal
                ? { x: [-100, width + 100] }
                : { y: [-100, height + 100] }
            }
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        )}
      </div>

      {/* Pipe Highlight */}
      <div
        className="absolute rounded-full pointer-events-none"
        style={{
          top: isHorizontal ? 2 : 0,
          left: isHorizontal ? 0 : 2,
          width: isHorizontal ? width : pipeThickness * 0.4,
          height: isHorizontal ? pipeThickness * 0.4 : height,
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%)',
          filter: 'blur(4px)',
        }}
      />

      {/* Ambient Glow */}
      {active && (
        <motion.div
          className="absolute inset-0 rounded-full pointer-events-none"
          animate={{
            boxShadow: [
              '0 0 15px rgba(0, 229, 255, 0.3)',
              '0 0 30px rgba(0, 229, 255, 0.5)',
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
