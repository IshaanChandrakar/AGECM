-- ThingSpeak channel clearing can restart entry IDs. Retain all prior observations.
ALTER TABLE telemetry DROP CONSTRAINT cloud_identity;
ALTER TABLE telemetry ADD CONSTRAINT cloud_observation_identity UNIQUE(channel_id,entry_id,cloud_created_at);
ALTER TABLE ingestion_state ADD COLUMN last_cloud_created_at TIMESTAMP WITH TIME ZONE;
UPDATE ingestion_state SET last_cloud_created_at=(
 SELECT MAX(t.cloud_created_at) FROM telemetry t
 WHERE t.node_id=ingestion_state.node_id AND t.channel_id=ingestion_state.channel_id
 AND t.schema_version=ingestion_state.schema_version AND t.source='cloud_hardware'
);
