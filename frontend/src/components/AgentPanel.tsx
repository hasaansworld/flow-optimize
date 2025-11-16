import { motion } from 'motion/react';
import { Brain, Loader2, AlertTriangle } from 'lucide-react';
import { AgentResponse, AgentMessage } from '../services/agentApi';

interface AgentPanelProps {
  hasData?: boolean;
  agentData?: AgentResponse | null;
  allMessages?: AgentMessage[];
  isLoading?: boolean;
  error?: string | null;
  currentRow?: number;
}

export function AgentPanel({ hasData = true, agentData, allMessages = [], isLoading = false, error = null, currentRow = 0 }: AgentPanelProps) {

  // Helper function to get priority color
  const getPriorityColor = (priority: string) => {
    switch (priority.toUpperCase()) {
      case 'CRITICAL':
        return {
          bg: 'rgba(239, 83, 80, 0.2)',
          color: '#EF5350',
          border: '1px solid rgba(239, 83, 80, 0.3)',
        };
      case 'HIGH':
        return {
          bg: 'rgba(255, 152, 0, 0.2)',
          color: '#FF9800',
          border: '1px solid rgba(255, 152, 0, 0.3)',
        };
      case 'MEDIUM':
        return {
          bg: 'rgba(255, 167, 38, 0.2)',
          color: '#FFA726',
          border: '1px solid rgba(255, 167, 38, 0.3)',
        };
      case 'LOW':
        return {
          bg: 'rgba(102, 187, 106, 0.2)',
          color: '#66BB6A',
          border: '1px solid rgba(102, 187, 106, 0.3)',
        };
      default:
        return {
          bg: 'rgba(158, 158, 158, 0.2)',
          color: '#9E9E9E',
          border: '1px solid rgba(158, 158, 158, 0.3)',
        };
    }
  };

  // Truncate long text
  const truncateText = (text: string, maxLength: number = 200) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  // Get active pumps from pump commands
  const activePumps = agentData?.pump_commands.filter(p => p.start) || [];

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
        <div className="flex-1">
          <h2 className="text-white" style={{ fontSize: '0.9rem' }}>AI Agent Analysis</h2>
          <p className="text-gray-400" style={{ fontSize: '0.65rem' }}>Row {currentRow} | {allMessages.length} messages</p>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="overflow-y-auto flex-1 p-6">
        {/* Error Display */}
        {error && (
          <div className="mb-4 p-3 rounded-xl" style={{
            background: 'rgba(239, 83, 80, 0.1)',
            border: '1px solid rgba(239, 83, 80, 0.3)',
          }}>
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-[#EF5350]" />
              <p className="text-[#EF5350]" style={{ fontSize: '0.75rem' }}>Error</p>
            </div>
            <p className="text-gray-400" style={{ fontSize: '0.65rem' }}>{error}</p>
          </div>
        )}

        {/* All Agent Messages Section - Display accumulated messages from all rows */}
        <div className="mb-5">
          {allMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-[#00E5FF] animate-spin mb-3" />
              <p className="text-gray-400 text-center" style={{ fontSize: '0.7rem' }}>
                Waiting for agent messages...
              </p>
            </div>
          ) : (
            <>
              <div className="mb-3">
                <h3 className="text-[#00E5FF]" style={{ fontSize: '0.8rem' }}>
                  AGENT MESSAGES ({allMessages.length})
                </h3>
              </div>
              {allMessages.slice().reverse().map((agent, index) => {
                const priorityStyle = getPriorityColor(agent.priority);
                return (
                  <motion.div
                    key={`msg-${allMessages.length - index}`}
                    className="mb-3 p-3 rounded-xl"
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                    }}
                    whileHover={{ background: 'rgba(255, 255, 255, 0.08)' }}
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <h4 className="text-white" style={{ fontSize: '0.75rem' }}>
                        {agent.agent_name.toUpperCase().replace(/_/g, ' ')}
                      </h4>
                      <span
                        className="px-1.5 py-0.5 rounded"
                        style={{
                          fontSize: '0.65rem',
                          background: priorityStyle.bg,
                          color: priorityStyle.color,
                          border: priorityStyle.border,
                        }}
                      >
                        {agent.priority.toUpperCase()}
                      </span>
                    </div>
                    <div className="mb-1.5" style={{ fontSize: '0.65rem' }}>
                      <span className="text-gray-500">Type:</span>{' '}
                      <span className="text-[#00E5FF]">{agent.recommendation_type}</span>
                    </div>
                    <p className="text-gray-300 leading-relaxed" style={{ fontSize: '0.65rem' }}>
                      {truncateText(agent.reasoning)}
                    </p>
                  </motion.div>
                );
              })}
            </>
          )}
        </div>

        {/* Coordinator Synthesis Section */}
        {agentData?.coordinator_reasoning && (
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
              <p className="text-gray-300 leading-relaxed mb-2" style={{ fontSize: '0.65rem' }}>
                {truncateText(agentData.coordinator_reasoning, 300)}
              </p>
              {agentData.priority_applied && (
                <div className="text-gray-400" style={{ fontSize: '0.6rem' }}>
                  <span className="text-gray-500">Priority Applied:</span>{' '}
                  <span className="text-[#00E5FF]">{agentData.priority_applied}</span>
                </div>
              )}
            </motion.div>
          </div>
        )}

        {/* Final Pump Commands Section */}
        {agentData?.pump_commands && (
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
                <span className="text-[#66BB6A]" style={{ fontSize: '0.75rem' }}>{activePumps.length}</span>
              </div>
              {activePumps.map((pump, index) => (
                <div key={index} className="mb-3 p-2 rounded-lg" style={{ background: 'rgba(0, 0, 0, 0.2)' }}>
                  <p className="text-gray-300" style={{ fontSize: '0.65rem' }}>
                    <span className="text-[#00E5FF]">{pump.pump_id}:</span>{' '}
                    {pump.frequency.toFixed(1)} Hz → {Math.round(pump.flow_m3h)} m³/h @ {pump.power_kw.toFixed(1)} kW
                    (η={(pump.efficiency * 100).toFixed(1)}%)
                  </p>
                </div>
              ))}
              {agentData.cost_calculation && (
                <div className="border-t border-white/10 pt-2">
                  <h5 className="text-white mb-1.5" style={{ fontSize: '0.75rem' }}>COST</h5>
                  <div className="space-y-0.5 text-gray-300" style={{ fontSize: '0.65rem' }}>
                    <div>
                      <span className="text-gray-500">Power:</span> {agentData.cost_calculation.total_power_kw.toFixed(1)} kW |{' '}
                      <span className="text-gray-500">Energy:</span> {agentData.cost_calculation.energy_consumed_kwh.toFixed(2)} kWh |{' '}
                      <span className="text-gray-500">Cost:</span>{' '}
                      <span className="text-[#FFA726]">€{agentData.cost_calculation.cost_eur.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Flow:</span> {Math.round(agentData.cost_calculation.flow_pumped_m3)} m³ |{' '}
                      <span className="text-gray-500">Specific Energy:</span>{' '}
                      {agentData.cost_calculation.specific_energy_kwh_per_m3.toFixed(6)} kWh/m³
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        )}
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
