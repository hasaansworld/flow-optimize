import { motion } from 'motion/react';
import { Brain, Loader2 } from 'lucide-react';

interface AgentPanelProps {
  hasData?: boolean;
}

export function AgentPanel({ hasData = true }: AgentPanelProps) {
  if (!hasData) {
    return (
      <div
        className="relative p-6 rounded-2xl h-full flex flex-col items-center justify-center"
        style={{
          background: 'linear-gradient(135deg, rgba(55, 71, 79, 0.8) 0%, rgba(38, 50, 56, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          border: '3px solid rgba(255, 255, 255, 0.15)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.7), inset 0 2px 4px rgba(255, 255, 255, 0.1)',
        }}
      >
        <Loader2 className="w-8 h-8 text-[#00E5FF] animate-spin mb-4" />
        <p className="text-gray-400 text-center">Waiting for agent's response...</p>
      </div>
    );
  }

  return (
    <div
      className="relative rounded-2xl h-full flex flex-col"
      style={{
        background: 'linear-gradient(135deg, rgba(55, 71, 79, 0.8) 0%, rgba(38, 50, 56, 0.9) 100%)',
        backdropFilter: 'blur(20px)',
        border: '3px solid rgba(255, 255, 255, 0.15)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.7), inset 0 2px 4px rgba(255, 255, 255, 0.1)',
      }}
    >
      {/* Header - Pinned at top */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/20 flex-shrink-0">
        <Brain className="w-5 h-5 text-[#00E5FF]" />
        <h2 className="text-white" style={{ fontSize: '0.9rem' }}>AI Agent Analysis</h2>
      </div>

      {/* Scrollable Content */}
      <div className="overflow-y-auto flex-1 p-6">
        {/* Specialist Agent Assessments Section */}
        <div className="mb-5">
          {/* Inflow Forecasting */}
          <motion.div
            className="mb-3 p-3 rounded-xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
            whileHover={{ background: 'rgba(255, 255, 255, 0.08)' }}
          >
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-white" style={{ fontSize: '0.75rem' }}>INFLOW_FORECASTING</h4>
              <span
                className="px-1.5 py-0.5 rounded"
                style={{
                  fontSize: '0.65rem',
                  background: 'rgba(255, 167, 38, 0.2)',
                  color: '#FFA726',
                  border: '1px solid rgba(255, 167, 38, 0.3)',
                }}
              >
                MEDIUM
              </span>
            </div>
            <div className="mb-1.5" style={{ fontSize: '0.65rem' }}>
              <span className="text-gray-500">Type:</span> <span className="text-[#00E5FF]">inflow_forecast</span>
            </div>
            <p className="text-gray-300 leading-relaxed" style={{ fontSize: '0.65rem' }}>
              The current inflow is 601 m³/15min, which is within the dry weather threshold {"(<"}1000 m³/15min). The LSTM forecast shows a slight increase in inflow ov...
            </p>
          </motion.div>

          {/* Energy Cost */}
          <motion.div
            className="mb-3 p-3 rounded-xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
            whileHover={{ background: 'rgba(255, 255, 255, 0.08)' }}
          >
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-white" style={{ fontSize: '0.75rem' }}>ENERGY_COST</h4>
              <span
                className="px-1.5 py-0.5 rounded"
                style={{
                  fontSize: '0.65rem',
                  background: 'rgba(255, 167, 38, 0.2)',
                  color: '#FFA726',
                  border: '1px solid rgba(255, 167, 38, 0.3)',
                }}
              >
                MEDIUM
              </span>
            </div>
            <div className="mb-1.5" style={{ fontSize: '0.65rem' }}>
              <span className="text-gray-500">Type:</span> <span className="text-[#00E5FF]">cost_optimization</span>
            </div>
            <p className="text-gray-300 leading-relaxed" style={{ fontSize: '0.65rem' }}>
              The current electricity price of 0.497 EUR/kWh is relatively high compared to the identified cheap windows in the next 24 hours. The average prices du...
            </p>
          </motion.div>

          {/* Pump Efficiency */}
          <motion.div
            className="mb-3 p-3 rounded-xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
            whileHover={{ background: 'rgba(255, 255, 255, 0.08)' }}
          >
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-white" style={{ fontSize: '0.75rem' }}>PUMP_EFFICIENCY</h4>
              <span
                className="px-1.5 py-0.5 rounded"
                style={{
                  fontSize: '0.65rem',
                  background: 'rgba(255, 167, 38, 0.2)',
                  color: '#FFA726',
                  border: '1px solid rgba(255, 167, 38, 0.3)',
                }}
              >
                MEDIUM
              </span>
            </div>
            <div className="mb-1.5" style={{ fontSize: '0.65rem' }}>
              <span className="text-gray-500">Type:</span> <span className="text-[#00E5FF]">pump_selection</span>
            </div>
            <p className="text-gray-300 leading-relaxed" style={{ fontSize: '0.65rem' }}>
              I recommend pump combination 1.1 as it meets the flow requirement while maintaining high efficiency. Additionally, it allows for operational smoothnes...
            </p>
          </motion.div>

          {/* Water Level Safety */}
          <motion.div
            className="mb-3 p-3 rounded-xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
            whileHover={{ background: 'rgba(255, 255, 255, 0.08)' }}
          >
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-white" style={{ fontSize: '0.75rem' }}>WATER_LEVEL_SAFETY</h4>
              <span
                className="px-1.5 py-0.5 rounded"
                style={{
                  fontSize: '0.65rem',
                  background: 'rgba(102, 187, 106, 0.2)',
                  color: '#66BB6A',
                  border: '1px solid rgba(102, 187, 106, 0.3)',
                }}
              >
                LOW
              </span>
            </div>
            <div className="mb-1.5" style={{ fontSize: '0.65rem' }}>
              <span className="text-gray-500">Type:</span> <span className="text-[#00E5FF]">safety_assessment</span>
            </div>
            <p className="text-gray-300 leading-relaxed" style={{ fontSize: '0.65rem' }}>
              The current water level is at 1.51m, which is well within the safe range of 0-8m. The alarm threshold is set at 7.2m, and there is a substantial margi...
            </p>
          </motion.div>

          {/* Flow Smoothness */}
          <motion.div
            className="mb-3 p-3 rounded-xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
            whileHover={{ background: 'rgba(255, 255, 255, 0.08)' }}
          >
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-white" style={{ fontSize: '0.75rem' }}>FLOW_SMOOTHNESS</h4>
              <span
                className="px-1.5 py-0.5 rounded"
                style={{
                  fontSize: '0.65rem',
                  background: 'rgba(102, 187, 106, 0.2)',
                  color: '#66BB6A',
                  border: '1px solid rgba(102, 187, 106, 0.3)',
                }}
              >
                LOW
              </span>
            </div>
            <div className="mb-1.5" style={{ fontSize: '0.65rem' }}>
              <span className="text-gray-500">Type:</span> <span className="text-[#00E5FF]">flow_smoothness</span>
            </div>
            <p className="text-gray-300 leading-relaxed" style={{ fontSize: '0.65rem' }}>
              The current flow outflow (F2) is 3070 m³/h, which is within the acceptable maximum flow change limit of 2000 m³/h per 15 minutes. The recent flow vari...
            </p>
          </motion.div>

          {/* Constraint Compliance */}
          <motion.div
            className="mb-3 p-3 rounded-xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
            whileHover={{ background: 'rgba(255, 255, 255, 0.08)' }}
          >
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-white" style={{ fontSize: '0.75rem' }}>CONSTRAINT_COMPLIANCE</h4>
              <span
                className="px-1.5 py-0.5 rounded"
                style={{
                  fontSize: '0.65rem',
                  background: 'rgba(239, 83, 80, 0.2)',
                  color: '#EF5350',
                  border: '1px solid rgba(239, 83, 80, 0.3)',
                }}
              >
                CRITICAL
              </span>
            </div>
            <div className="mb-1.5" style={{ fontSize: '0.65rem' }}>
              <span className="text-gray-500">Type:</span> <span className="text-[#00E5FF]">constraint_compliance</span>
            </div>
            <p className="text-gray-300 leading-relaxed" style={{ fontSize: '0.65rem' }}>
              The current state of the wastewater pumping station indicates that no pumps are running, which violates the constraint requiring at least one pump to ...
            </p>
          </motion.div>
        </div>

        {/* Coordinator Synthesis Section */}
        <div className="mb-5">
          <div className="mb-2">
            <h3 className="text-[#00E5FF]" style={{ fontSize: '0.8rem' }}>
              COORDINATOR SYNTHESIS
            </h3>
          </div>
          <motion.div
            className="p-3 rounded-xl"
            style={{
              background: 'rgba(0, 229, 255, 0.1)',
              border: '1px solid rgba(0, 229, 255, 0.3)',
            }}
          >
            <h4 className="text-white mb-2" style={{ fontSize: '0.75rem' }}>Coordinator Decision</h4>
            <p className="text-gray-300 leading-relaxed" style={{ fontSize: '0.65rem' }}>
              Agent 6 indicates a non-compliance status as no pumps are currently running, which violates regulations requiring at least one pump operational. Safety (Agent 4) confirms no immediate risk, allowing u...
            </p>
          </motion.div>
        </div>

        {/* Final Pump Commands Section */}
        <div>
          <div className="mb-2">
            <h3 className="text-[#00E5FF]" style={{ fontSize: '0.8rem' }}>
              FINAL PUMP COMMANDS
            </h3>
          </div>
          <motion.div
            className="p-3 rounded-xl"
            style={{
              background: 'rgba(102, 187, 106, 0.1)',
              border: '1px solid rgba(102, 187, 106, 0.3)',
            }}
          >
            <div className="mb-2">
              <span className="text-white" style={{ fontSize: '0.75rem' }}>Active Pumps: </span>
              <span className="text-[#66BB6A]" style={{ fontSize: '0.75rem' }}>1</span>
            </div>
            <div className="mb-3 p-2 rounded-lg" style={{ background: 'rgba(0, 0, 0, 0.2)' }}>
              <p className="text-gray-300" style={{ fontSize: '0.65rem' }}>
                <span className="text-[#00E5FF]">P1L:</span> 50.0 Hz → 3330 m³/h @ 400.0 kW (η=84.8%)
              </p>
            </div>
            <div className="border-t border-white/10 pt-2">
              <h5 className="text-white mb-1.5" style={{ fontSize: '0.75rem' }}>COST</h5>
              <div className="space-y-0.5 text-gray-300" style={{ fontSize: '0.65rem' }}>
                <div>
                  <span className="text-gray-500">Power:</span> 400.0 kW | 
                  <span className="text-gray-500"> Energy:</span> 100.00 kWh | 
                  <span className="text-gray-500"> Cost:</span> <span className="text-[#FFA726]">€49.70</span>
                </div>
                <div>
                  <span className="text-gray-500">Flow:</span> 832 m³ | 
                  <span className="text-gray-500"> Specific Energy:</span> 0.120120 kWh/m³
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Glow Effect */}
      <motion.div
        className="absolute inset-0 rounded-2xl pointer-events-none"
        animate={{
          boxShadow: [
            '0 0 30px rgba(0, 229, 255, 0.15)',
            '0 0 45px rgba(0, 229, 255, 0.25)',
            '0 0 30px rgba(0, 229, 255, 0.15)',
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