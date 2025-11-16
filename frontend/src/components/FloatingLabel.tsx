import { motion } from 'motion/react';
import { ArrowDownRight, ArrowDownLeft, ArrowUpLeft } from 'lucide-react';

interface FloatingLabelProps {
  text: string;
  value: string;
  position: { top?: number; left?: number; right?: number; bottom?: number };
  direction?: 'down-right' | 'down-left' | 'up-left';
  highlight?: boolean;
  compact?: boolean;
}

export function FloatingLabel({ text, value, position, direction = 'down-right', highlight, compact }: FloatingLabelProps) {
  const arrowIcons = {
    'down-right': ArrowDownRight,
    'down-left': ArrowDownLeft,
    'up-left': ArrowUpLeft,
  };
  
  const ArrowIcon = arrowIcons[direction];

  return (
    <motion.div
      className="absolute"
      style={{
        ...position,
      }}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: 'easeOut' }}
    >
      {/* Floating text without heavy box */}
      <div className="relative">
        {/* Subtle backdrop glow */}
        {highlight && (
          <motion.div
            className="absolute -inset-4 rounded-2xl"
            style={{
              background: 'radial-gradient(circle, rgba(0, 229, 255, 0.15) 0%, transparent 70%)',
              filter: 'blur(20px)',
            }}
            animate={{
              scale: [1, 1.1, 1],
              opacity: [0.5, 0.8, 0.5],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )}

        {/* Main text */}
        <div className="relative">
          <div className="flex items-center gap-2 mb-1">
            <motion.div
              animate={{
                x: direction === 'down-right' ? [0, 3, 0] : direction === 'down-left' ? [0, -3, 0] : [0, -3, 0],
                y: direction === 'up-left' ? [0, -3, 0] : [0, 3, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              <ArrowIcon
                className="w-5 h-5"
                style={{
                  color: highlight ? '#00E5FF' : '#42A5F5',
                  filter: 'drop-shadow(0 0 8px rgba(66, 165, 245, 0.6))',
                }}
              />
            </motion.div>
            <h3
              className={compact ? 'text-sm' : ''}
              style={{
                color: highlight ? '#00E5FF' : '#42A5F5',
                textShadow: highlight
                  ? '0 0 20px rgba(0, 229, 255, 0.8), 0 0 40px rgba(0, 229, 255, 0.4)'
                  : '0 0 10px rgba(66, 165, 245, 0.6)',
              }}
            >
              {text}
            </h3>
          </div>

          {/* Value with glow effect */}
          <motion.p
            className="text-white pl-7"
            style={{
              textShadow: '0 2px 8px rgba(0, 0, 0, 0.8)',
            }}
            animate={
              highlight
                ? {
                    textShadow: [
                      '0 0 10px rgba(0, 229, 255, 0.3), 0 2px 8px rgba(0, 0, 0, 0.8)',
                      '0 0 20px rgba(0, 229, 255, 0.6), 0 2px 8px rgba(0, 0, 0, 0.8)',
                      '0 0 10px rgba(0, 229, 255, 0.3), 0 2px 8px rgba(0, 0, 0, 0.8)',
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
            {value}
          </motion.p>

          {/* Decorative line */}
          <motion.div
            className="absolute -bottom-2 left-7 h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent"
            style={{
              width: compact ? '80px' : '120px',
            }}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 1, delay: 0.5 }}
          />
        </div>
      </div>
    </motion.div>
  );
}
