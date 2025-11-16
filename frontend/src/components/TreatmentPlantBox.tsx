import { motion } from 'motion/react';
import { Factory, CheckCircle, Beaker } from 'lucide-react';

interface TreatmentPlantBoxProps {
  distance: string;
  status: 'operational' | 'offline' | 'maintenance';
  capacity: string;
}

export function TreatmentPlantBox({ distance, status, capacity }: TreatmentPlantBoxProps) {
  const statusConfig = {
    operational: {
      color: '#66BB6A',
      label: 'Operational',
    },
    offline: {
      color: '#9E9E9E',
      label: 'Offline',
    },
    maintenance: {
      color: '#FFA726',
      label: 'Maintenance',
    },
  };

  const config = statusConfig[status];

  return (
    <div className="relative">
      {/* Treatment Plant Container */}
      <div
        className="relative p-5 rounded-2xl"
        style={{
          background: 'linear-gradient(135deg, rgba(102, 187, 106, 0.15) 0%, rgba(76, 175, 80, 0.1) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(102, 187, 106, 0.4)',
          boxShadow: '0 15px 50px rgba(102, 187, 106, 0.25), inset 0 2px 4px rgba(102, 187, 106, 0.2)',
          width: '200px',
        }}
      >
        {/* Header with Icon */}
        <div className="flex items-center gap-3 mb-4">
          <motion.div
            className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(102, 187, 106, 0.3) 0%, rgba(76, 175, 80, 0.2) 100%)',
              border: '1px solid rgba(102, 187, 106, 0.5)',
            }}
            animate={{
              boxShadow: [
                '0 0 15px rgba(102, 187, 106, 0.4)',
                '0 0 25px rgba(102, 187, 106, 0.6)',
                '0 0 15px rgba(102, 187, 106, 0.4)',
              ],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          >
            <Factory className="w-6 h-6 text-[#66BB6A]" />
          </motion.div>
          <div>
            <h3 className="text-white text-sm">WWTP</h3>
            <p className="text-xs text-gray-400">Treatment Plant</p>
          </div>
        </div>

        {/* Metrics */}
        <div className="space-y-3">
          <div className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 text-[#66BB6A] mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-gray-400">Status</p>
              <p className="text-sm" style={{ color: config.color }}>
                {config.label}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <Beaker className="w-4 h-4 text-[#66BB6A] mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-gray-400">Capacity</p>
              <p className="text-white text-sm">{capacity}</p>
            </div>
          </div>

          <div className="pt-2 border-t border-white/10">
            <p className="text-xs text-gray-400">Distance</p>
            <p className="text-white text-sm">{distance}</p>
          </div>
        </div>

        {/* Animated treatment process indicator */}
        <motion.div
          className="absolute bottom-4 right-4 w-12 h-12 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(102, 187, 106, 0.3) 0%, transparent 70%)',
          }}
          animate={{
            rotate: 360,
            scale: [1, 1.2, 1],
          }}
          transition={{
            rotate: {
              duration: 8,
              repeat: Infinity,
              ease: 'linear',
            },
            scale: {
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut',
            },
          }}
        />
      </div>

      {/* Ambient Glow */}
      <motion.div
        className="absolute inset-0 rounded-2xl pointer-events-none"
        animate={{
          boxShadow: [
            '0 0 30px rgba(102, 187, 106, 0.3)',
            '0 0 45px rgba(102, 187, 106, 0.5)',
            '0 0 30px rgba(102, 187, 106, 0.3)',
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