-- Initialize database schema for wastewater multi-agent system

-- Decisions table
CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    pump_commands JSONB NOT NULL,
    reasoning TEXT,
    estimated_cost DECIMAL(10, 2),
    estimated_flow DECIMAL(10, 2),
    priority VARCHAR(20),
    confidence DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decisions_timestamp ON decisions(timestamp);
CREATE INDEX idx_decisions_priority ON decisions(priority);

-- Agent recommendations table
CREATE TABLE IF NOT EXISTS agent_recommendations (
    id SERIAL PRIMARY KEY,
    decision_id INTEGER REFERENCES decisions(id),
    agent_name VARCHAR(50) NOT NULL,
    recommendation_type VARCHAR(50),
    priority VARCHAR(20),
    confidence DECIMAL(3, 2),
    reasoning TEXT,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_recommendations_agent_name ON agent_recommendations(agent_name);
CREATE INDEX idx_agent_recommendations_decision_id ON agent_recommendations(decision_id);

-- System state history table
CREATE TABLE IF NOT EXISTS system_state (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    L1 DECIMAL(5, 2),
    V DECIMAL(10, 2),
    F1 DECIMAL(10, 2),
    F2 DECIMAL(10, 2),
    electricity_price DECIMAL(6, 3),
    price_scenario VARCHAR(20),
    active_pumps JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_state_timestamp ON system_state(timestamp);

-- Webhook events table
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20),
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_webhook_events_event_type ON webhook_events(event_type);
CREATE INDEX idx_webhook_events_processed ON webhook_events(processed);

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 4),
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP NOT NULL,
    tags JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_metric_name ON metrics(metric_name);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);

-- Performance view for dashboards
CREATE OR REPLACE VIEW decision_performance AS
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as total_decisions,
    AVG(estimated_cost) as avg_cost,
    AVG(estimated_flow) as avg_flow,
    AVG(confidence) as avg_confidence,
    COUNT(CASE WHEN priority = 'CRITICAL' THEN 1 END) as critical_decisions,
    COUNT(CASE WHEN priority = 'HIGH' THEN 1 END) as high_priority_decisions
FROM decisions
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- Agent performance view
CREATE OR REPLACE VIEW agent_performance AS
SELECT
    agent_name,
    COUNT(*) as total_recommendations,
    AVG(confidence) as avg_confidence,
    COUNT(CASE WHEN priority = 'CRITICAL' THEN 1 END) as critical_count,
    COUNT(CASE WHEN priority = 'HIGH' THEN 1 END) as high_count,
    COUNT(CASE WHEN priority = 'MEDIUM' THEN 1 END) as medium_count,
    COUNT(CASE WHEN priority = 'LOW' THEN 1 END) as low_count
FROM agent_recommendations
GROUP BY agent_name;

-- Insert sample data
INSERT INTO metrics (metric_name, metric_value, metric_unit, timestamp, tags)
VALUES
    ('system_uptime', 0, 'hours', CURRENT_TIMESTAMP, '{"source": "initialization"}'),
    ('total_decisions', 0, 'count', CURRENT_TIMESTAMP, '{"source": "initialization"}');

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wastewater;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO wastewater;
