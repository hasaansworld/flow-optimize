// API service for calling the n8n workflow

export interface PumpCommand {
  pump_id: string;
  start: boolean;
  frequency: number;
  flow_m3h: number;
  power_kw: number;
  efficiency: number;
}

export interface AgentMessage {
  agent_name: string;
  priority: string;
  confidence: number;
  recommendation_type: string;
  reasoning: string;
  key_data?: any;
}

export interface CostCalculation {
  total_power_kw: number;
  energy_consumed_kwh: number;
  cost_eur: number;
  flow_pumped_m3: number;
  specific_energy_kwh_per_m3: number;
}

export interface AgentResponse {
  timestamp: string;
  pump_commands: PumpCommand[];
  coordinator_reasoning: string;
  priority_applied: string;
  conflicts_resolved: string[];
  confidence: number;
  cost_calculation: CostCalculation;
  constraint_violations: any[];
  agent_messages: AgentMessage[];
  L1: number;  // Tunnel level in meters (0-8m)
  V: number;   // Volume in m³
  F1: number;  // Inflow in m³/15min
  F2: number;  // Outflow in m³/h
  electricity_price: number;  // Price in EUR/kWh
}

// Configure your backend API URL here
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000');
const N8N_BASE_URL = import.meta.env.VITE_N8N_BASE_URL || (typeof window !== 'undefined' ? `${window.location.origin}/n8n` : 'http://localhost:5678');
const SYNTHESIZE_URL = `${N8N_BASE_URL}/webhook/wastewater-decision`

export async function fetchAgentData(rowNumber: number): Promise<AgentResponse> {
  try {
    // Call the backend with the row number
    const synthesizeResponse = await fetch(SYNTHESIZE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ row_number: rowNumber }),
    });

    if (!synthesizeResponse.ok) {
      throw new Error(`Failed to synthesize decision: ${synthesizeResponse.status}`);
    }

    const data = await synthesizeResponse.json();
    return data;
  } catch (error) {
    console.error('Error fetching agent data:', error);
    throw error;
  }
}

export async function triggerAgentWorkflow(params?: any): Promise<AgentResponse> {
  try {
    const response = await fetch(SYNTHESIZE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params || {}),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error triggering agent workflow:', error);
    throw error;
  }
}
