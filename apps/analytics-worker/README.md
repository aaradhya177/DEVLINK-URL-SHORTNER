# DEVLINK Analytics Worker

Python worker for consuming Kafka `click-events` messages and writing raw click
rows plus daily rollups.

## Run locally

```powershell
poetry install
poetry run devlink-analytics-worker
```

## GeoIP database

Geo resolution uses a local MaxMind GeoLite2 City database when available.

1. Create a MaxMind account.
2. Download `GeoLite2-City.mmdb`.
3. Set `GEOIP_DATABASE_PATH=/absolute/path/to/GeoLite2-City.mmdb`.

If no database is configured, the worker logs `geoip_database_unavailable` and
stores empty geo fields.

## Processing guarantees

Kafka delivery is treated as at-least-once. Each message includes an `event_id`;
the worker first inserts into `click_events` with `ON CONFLICT DO NOTHING`, then
only increments aggregates when the raw insert succeeds. Replayed messages
therefore do not double-count `link_analytics_daily` or `links.click_count`.

Offsets are committed after malformed messages are logged/skipped or after
database writes are committed. If the database is slow, the consumer naturally
applies backpressure by processing sequentially before committing the next
offset.
