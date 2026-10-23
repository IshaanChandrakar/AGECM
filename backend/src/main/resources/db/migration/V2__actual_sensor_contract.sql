-- Preserve every legacy record; the active API is scoped to schema 2.0.
ALTER TABLE telemetry ADD COLUMN temperature DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN humidity DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN co_max DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN ch4_max DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN distance_now DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN dev_max DOUBLE PRECISION;
ALTER TABLE telemetry ADD COLUMN status_worst INTEGER;
ALTER TABLE telemetry ADD COLUMN fault_any INTEGER;
ALTER TABLE telemetry ADD COLUMN sample_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE telemetry ADD COLUMN timestamp_basis VARCHAR(32);
ALTER TABLE telemetry ADD COLUMN field_issues VARCHAR(2000);
ALTER TABLE telemetry ADD COLUMN status_text VARCHAR(2000);
ALTER TABLE telemetry ALTER COLUMN acquired_at DROP NOT NULL;
ALTER TABLE telemetry ALTER COLUMN boot_id DROP NOT NULL;
ALTER TABLE telemetry ALTER COLUMN sequence DROP NOT NULL;
ALTER TABLE telemetry ALTER COLUMN quality_flags DROP NOT NULL;
ALTER TABLE telemetry ALTER COLUMN calibrated DROP NOT NULL;
ALTER TABLE telemetry ALTER COLUMN feature_ready DROP NOT NULL;
ALTER TABLE telemetry ALTER COLUMN rule_version DROP NOT NULL;
ALTER TABLE telemetry ALTER COLUMN state DROP NOT NULL;
ALTER TABLE telemetry ALTER COLUMN health DROP NOT NULL;
ALTER TABLE ingestion_state ADD COLUMN schema_version VARCHAR(20) DEFAULT '1.0';
CREATE INDEX telemetry_v2_time ON telemetry(schema_version,source,node_id,sample_at DESC);
-- End obsolete active tilt-rule episodes without deleting history.
UPDATE alerts SET resolved_at=CURRENT_TIMESTAMP WHERE resolved_at IS NULL;
