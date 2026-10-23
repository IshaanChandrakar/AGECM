-- Keep the firmware sentinel for traceability while plotting missing distance as a gap.
ALTER TABLE telemetry ADD COLUMN raw_distance_now DOUBLE PRECISION;
