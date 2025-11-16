import { motion } from 'motion/react';
import { ReactNode } from 'react';

interface StatusCardProps {
  icon: ReactNode;
  title: string;
  value: string;
  status: 'good' | 'warning' | 'alert';
  trend?: string;
}

export function StatusCard({ icon, title, value, status, trend }: StatusCardProps) {
  const statusColors = {
    good: '#66BB6A',
    warning: '#FFA726',
    alert: '#EF5350',
  };

  return (
    <motion.div
      className="relative p-6 rounded-xl overflow-hidden cursor-pointer"
      style={{
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      }}
      whileHover={{
        scale: 1.02,
        boxShadow: '0 12px 48px 0 rgba(0, 0, 0, 0.5)',
      }}
      transition={{ duration: 0.2 }}
    >
      {/* Background Gradient */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          background: `linear-gradient(135deg, ${statusColors[status]}20 0%, transparent 100%)`,
        }}
      />

      {/* Content */}
      <div className="relative">
        <div className="flex items-center justify-between mb-3">
          <div className="text-gray-400">{icon}</div>
          <motion.div
            className="w-2 h-2 rounded-full"
            style={{
              background: statusColors[status],
            }}
            animate={{
              boxShadow: [
                `0 0 5px ${statusColors[status]}`,
                `0 0 15px ${statusColors[status]}`,
                `0 0 5px ${statusColors[status]}`,
              ],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        </div>

        <h3 className="text-gray-400 mb-2">{title}</h3>
        <p className="text-white mb-1">{value}</p>

        {trend && (
          <div className="flex items-center gap-1">
            <span
              className="text-xs"
              style={{
                color: status === 'good' ? statusColors.good : '#666',
              }}
            >
              {trend}
            </span>
          </div>
        )}
      </div>

      {/* Hover Glow */}
      <motion.div
        className="absolute inset-0 rounded-xl opacity-0 pointer-events-none"
        whileHover={{ opacity: 1 }}
        style={{
          boxShadow: `inset 0 0 40px ${statusColors[status]}20`,
        }}
      />
    </motion.div>
  );
}
