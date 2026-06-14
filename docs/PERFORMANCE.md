# Performance Notes

## Bottleneck Review

- **Redirect endpoint:** expected bottlenecks are Redis rate-limit/cache lookups,
  DB fallback on cache miss, and background producer scheduling. The route now
  logs `rate_limit_ms`, `cache_lookup_ms`, `db_fallback_ms`, and
  `total_response_ms` as structured fields on the `redirect_timing` log event.
- **Analytics dashboard queries:** dashboard reads use `link_analytics_daily`,
  not raw `click_events`. See `docs/QUERY_PLANS.md` for expected index scans.
- **Bulk shortening:** DB dedup was already batched. The concrete request-path
  inefficiency found was sequential Redis cache priming for newly created links.

## Bulk Cache Priming Before/After

Change: `bulk_create_links` now gathers cache writes for newly created links
instead of awaiting each Redis write one by one.

Local benchmark command:

```powershell
@'
import asyncio
from time import perf_counter

async def fake_cache_write(_):
    await asyncio.sleep(0.005)

async def sequential(n):
    start = perf_counter()
    for index in range(n):
        await fake_cache_write(index)
    return (perf_counter() - start) * 1000

async def parallel(n):
    start = perf_counter()
    await asyncio.gather(*(fake_cache_write(index) for index in range(n)))
    return (perf_counter() - start) * 1000

async def main():
    n = 50
    before = [await sequential(n) for _ in range(5)]
    after = [await parallel(n) for _ in range(5)]
    print("sequential_ms=", [round(v, 2) for v in before])
    print("parallel_ms=", [round(v, 2) for v in after])
    print("sequential_avg_ms=", round(sum(before) / len(before), 2))
    print("parallel_avg_ms=", round(sum(after) / len(after), 2))

asyncio.run(main())
'@ | python -
```

Measured on Windows in this workspace:

```text
sequential_ms= [776.78, 783.59, 782.13, 778.99, 784.61]
parallel_ms= [16.66, 15.02, 15.25, 15.42, 15.05]
sequential_avg_ms= 781.22
parallel_avg_ms= 15.48
improvement= 98.0%
```

This is a synthetic async round-trip benchmark, not a Redis throughput test. It
measures the request-path serialization removed by the code change.

## Redirect Load Test Scenario

Install one of:

```powershell
go install github.com/rakyll/hey@latest
```

or use a packaged `hey` binary.

Recommended local scenario after starting Postgres, Redis, Kafka, and the API:

```powershell
hey -z 30s -c 100 -disable-redirects http://127.0.0.1:8000/r/{short_code}
```

Capture:

- requests/sec
- p50, p95, p99 latency
- non-2xx/3xx counts
- API `redirect_timing` logs for cache hit rate and DB fallback time

This environment could not run the full redirect load test because Docker
Desktop/Postgres was not reachable. Earlier attempts to connect to compose
Postgres failed with `ConnectionRefusedError`, and Docker API access failed
because the Docker Desktop Linux engine pipe was unavailable.

## Pool Tuning

API database engine defaults are now configurable:

- `DB_POOL_SIZE`, default `10`
- `DB_MAX_OVERFLOW`, default `20`
- `DB_POOL_TIMEOUT_SECONDS`, default `30`

Rule of thumb for the API service:

- Start with `pool_size ~= worker_processes * expected_concurrent_db_requests_per_process`.
- Keep `max_overflow` below the database's connection budget after reserving
  connections for migrations, admin tools, and the analytics worker.
- Monitor pool checkout latency; sustained waits mean the pool or query latency
  is too small/slow.

Redis client pooling is configurable with `REDIS_MAX_CONNECTIONS`, default `100`.
Redirect traffic does two Redis operations on the cache-hit path today: rate
limit and link-cache lookup.
