# n8n Workflow Integration Guide

## Overview

The frontend application is now integrated with an n8n workflow to fetch real-time agent analysis data and update the pump states dynamically.

## Features

- **Real-time Agent Messages**: Displays agent analysis messages in the right panel
- **Dynamic Pump Updates**: Updates pump states based on agent recommendations
- **Auto-refresh**: Polls the n8n workflow every 30 seconds for updates
- **Error Handling**: Shows appropriate error states when API calls fail
- **Loading States**: Displays loading indicators while fetching data

## Setup Instructions

### 1. Configure the n8n Workflow URL

Create a `.env` file in the `frontend` directory:

```bash
cp .env.example .env
```

Edit `.env` and set your n8n workflow webhook URL:

```env
VITE_N8N_WORKFLOW_URL=http://localhost:5678/webhook/agent-workflow
```

### 2. n8n Workflow Requirements

Your n8n workflow should return JSON data in the following format:

```json
{
  "timestamp": "2024-11-30T23:45:00",
  "pump_commands": [
    {
      "pump_id": "P1L",
      "start": true,
      "frequency": 50,
      "flow_m3h": 3330,
      "power_kw": 386,
      "efficiency": 0.848
    }
  ],
  "coordinator_reasoning": "Agent decision explanation...",
  "priority_applied": "COMPLIANCE / SAFETY",
  "conflicts_resolved": ["..."],
  "confidence": 0.85,
  "cost_calculation": {
    "total_power_kw": 386,
    "energy_consumed_kwh": 96.5,
    "cost_eur": 1313.08,
    "flow_pumped_m3": 832.5,
    "specific_energy_kwh_per_m3": 0.116
  },
  "constraint_violations": [],
  "agent_messages": [
    {
      "agent_name": "inflow_forecasting",
      "priority": "HIGH",
      "confidence": 0.85,
      "recommendation_type": "inflow_forecast",
      "reasoning": "Analysis of inflow patterns...",
      "key_data": {}
    }
  ]
}
```

### 3. Pump ID Mapping

The system maps between UI pump IDs and agent pump IDs:

- `P1.1` → `1.1` or `P1L`
- `P1.2` → `1.2`
- `P1.3` → `1.3`
- `P1.4` → `1.4`
- `P2.1` → `2.1` or `P2L`
- `P2.2` → `2.2`
- `P2.3` → `2.3`
- `P2.4` → `2.4`
- `P3` → `P3`
- `P4` → `P4`

### 4. Start the Frontend

```bash
npm install
npm run dev
```

The application will:
- Fetch agent data on initial load
- Poll for updates every 30 seconds
- Display agent messages in the right panel
- Update pump visualizations based on commands

## API Service

The API service is located at `src/services/agentApi.ts` and provides:

- `fetchAgentData()`: GET request to fetch current agent data
- `triggerAgentWorkflow(params)`: POST request to trigger the workflow with parameters

## Components Updated

1. **App.tsx**: Main application with state management and API integration
2. **AgentPanel.tsx**: Right panel displaying agent messages and recommendations
3. **agentApi.ts**: API service for n8n workflow communication

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure your n8n workflow has proper CORS headers configured.

### Connection Failed

- Verify the n8n workflow URL is correct
- Check that the n8n instance is running
- Ensure the webhook is active in n8n

### No Data Displayed

- Check browser console for errors
- Verify the API response format matches the expected schema
- Ensure the workflow returns valid JSON

## Development

To modify the polling interval, edit the `setInterval` value in `App.tsx`:

```typescript
const interval = setInterval(loadAgentData, 30000); // 30 seconds
```

To disable polling during development:

```typescript
// Comment out the interval
// const interval = setInterval(loadAgentData, 30000);
```
