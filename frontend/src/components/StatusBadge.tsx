import { motion } from 'motion/react';

interface StatusBadgeProps {
  status: 'operational' | 'warning' | 'alert' | 'offline';
  label: string;
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const statusConfig = {
    operational: {
      color: '#66BB6A',
      bg: 'rgba(102, 187, 106, 0.2)',
      border: 'rgba(102, 187, 106, 0.5)',
    },
    warning: {
      color: '#FFA726',
      bg: 'rgba(255, 167, 38, 0.2)',
      border: 'rgba(255, 167, 38, 0.5)',
    },
    alert: {
      color: '#EF5350',
      bg: 'rgba(239, 83, 80, 0.2)',
      border: 'rgba(239, 83, 80, 0.5)',
    },
    offline: {
      color: '#9E9E9E',
      bg: 'rgba(158, 158, 158, 0.2)',
      border: 'rgba(158, 158, 158, 0.5)',
    },
  };

  const config = statusConfig[status];

  return (
    <motion.div
      className="px-4 py-2 rounded-full flex items-center gap-3"
      style={{
        background: config.bg,
        backdropFilter: 'blur(20px)',
        border: `1px solid ${config.border}`,
      }}
      animate={{
        boxShadow: [
          `0 0 20px ${config.color}30`,
          `0 0 30px ${config.color}50`,
          `0 0 20px ${config.color}30`,
        ],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    >
      {/* Pulsing Indicator */}
      <div className="relative">
        <motion.div
          className="w-3 h-3 rounded-full"
          style={{
            background: config.color,
          }}
          animate={{
            boxShadow: [
              `0 0 10px ${config.color}`,
              `0 0 20px ${config.color}`,
              `0 0 10px ${config.color}`,
            ],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            background: config.color,
          }}
          animate={{
            scale: [1, 2, 1],
            opacity: [0.6, 0, 0.6],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeOut',
          }}
        />
      </div>

      {/* Label */}
      <span className="text-white">{label}</span>
    </motion.div>
  );
}
