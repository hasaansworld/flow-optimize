import { motion } from 'motion/react';
import { Waves, TrendingDown, Gauge } from 'lucide-react';

interface InflowBoxProps {
  flowRate: string;
  pressure: string;
}

export function InflowBox({ flowRate, pressure }: InflowBoxProps) {
  return (
    <div className="relative">
      {/* Inflow Container */}
      <div
        className="relative p-5 rounded-2xl"
        style={{
          background: 'linear-gradient(135deg, rgba(30, 136, 229, 0.2) 0%, rgba(13, 71, 161, 0.15) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(30, 136, 229, 0.4)',
          boxShadow: '0 15px 50px rgba(30, 136, 229, 0.3), inset 0 2px 4px rgba(66, 165, 245, 0.2)',
          width: '180px',
        }}
      >
        {/* Header with Icon */}
        <div className="flex items-center gap-3 mb-4">
          <motion.div
            className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(30, 136, 229, 0.3) 0%, rgba(13, 71, 161, 0.2) 100%)',
              border: '1px solid rgba(30, 136, 229, 0.5)',
            }}
            animate={{
              boxShadow: [
                '0 0 15px rgba(30, 136, 229, 0.4)',
                '0 0 25px rgba(30, 136, 229, 0.6)',
                '0 0 15px rgba(30, 136, 229, 0.4)',
              ],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          >
            <Waves className="w-6 h-6 text-[#42A5F5]" />
          </motion.div>
          <div>
            <h3 className="text-white text-sm">Inflow</h3>
            <p className="text-xs text-gray-400">Source</p>
          </div>
        </div>

        {/* Metrics */}
        <div className="space-y-3">
          <div className="flex items-start gap-2">
            <TrendingDown className="w-4 h-4 text-[#42A5F5] mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-gray-400">Flow Rate</p>
              <p className="text-white text-sm">{flowRate}</p>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <Gauge className="w-4 h-4 text-[#42A5F5] mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-gray-400">Pressure</p>
              <p className="text-white text-sm">{pressure}</p>
            </div>
          </div>
        </div>

        {/* Animated water ripple effect */}
        <motion.div
          className="absolute top-4 right-4 w-16 h-16 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(66, 165, 245, 0.3) 0%, transparent 70%)',
          }}
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.5, 0.2, 0.5],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      </div>

      {/* Ambient Glow */}
      <motion.div
        className="absolute inset-0 rounded-2xl pointer-events-none"
        animate={{
          boxShadow: [
            '0 0 30px rgba(30, 136, 229, 0.2)',
            '0 0 50px rgba(30, 136, 229, 0.4)',
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