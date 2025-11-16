import { motion } from 'motion/react';

interface InfoPanelProps {
  label: string;
  value: string;
  position: { top?: number; left?: number; right?: number; bottom?: number };
  highlight?: boolean;
  compact?: boolean;
}

export function InfoPanel({ label, value, position, highlight, compact }: InfoPanelProps) {
  return (
    <motion.div
      className="absolute"
      style={{
        ...position,
      }}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div
        className={`${compact ? 'p-3' : 'p-4'} rounded-xl`}
        style={{
          background: highlight
            ? 'rgba(0, 229, 255, 0.15)'
            : 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: highlight
            ? '2px solid rgba(0, 229, 255, 0.4)'
            : '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: highlight
            ? '0 8px 32px rgba(0, 229, 255, 0.2)'
            : '0 4px 16px rgba(0, 0, 0, 0.3)',
          minWidth: compact ? '120px' : '150px',
        }}
      >
        <p
          className={`${compact ? 'text-sm' : ''} text-gray-300 mb-1`}
        >
          {label}
        </p>
        <p
          className={`${compact ? '' : ''} text-white`}
          style={{
            color: highlight ? '#00E5FF' : '#fff',
          }}
        >
          {value}
        </p>
      </div>

      {/* Glow effect for highlighted panels */}
      {highlight && (
        <motion.div
          className="absolute inset-0 rounded-xl pointer-events-none"
          animate={{
            boxShadow: [
              '0 0 20px rgba(0, 229, 255, 0.3)',
              '0 0 40px rgba(0, 229, 255, 0.5)',
              '0 0 20px rgba(0, 229, 255, 0.3)',
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
