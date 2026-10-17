"""Explicit one-shot developer write, isolated from production sensing channels."""
import os
from datetime import datetime, timezone
import json
from adapter import Http


def validate_write(response, expected_channel):
    if not isinstance(response, dict) or not isinstance(response.get("entry_id"),int) or response["entry_id"] <= 0:
        raise ValueError("ThingSpeak rejected write: no positive entry ID")
    if str(response.get("channel_id")) != str(expected_channel):
        raise ValueError("Write response channel does not match configured test channel")
    return response["entry_id"]


def main():
    if os.getenv("ENABLE_THINGSPEAK_WRITE_TEST") != "true":
        raise SystemExit("Set ENABLE_THINGSPEAK_WRITE_TEST=true to explicitly enable this developer utility")
    channel, key = os.getenv("THINGSPEAK_TEST_CHANNEL_ID"), os.getenv("THINGSPEAK_TEST_WRITE_KEY")
    if not channel or not key or channel in [os.getenv("THINGSPEAK_NODE1_CHANNEL_ID"), os.getenv("THINGSPEAK_NODE2_CHANNEL_ID")]:
        raise SystemExit("Use a separate configured test channel and its Write API key")
    status = dict(schema="1.0", acquiredAt=datetime.now(timezone.utc).isoformat(), calibrated=True, sampleIntervalMs=100, reportIntervalSeconds=30)
    payload = dict(api_key=key, field1=1.2, field2=0.0, field3=.02, field6=0, field7=1,
                   field8="developer-test", status=json.dumps(status, separators=(",", ":")))
    result = Http(retries=0).request("POST", "https://api.thingspeak.com/update.json", payload)
    print("Accepted test entry:", validate_write(result, channel))


if __name__ == "__main__":
    main()
