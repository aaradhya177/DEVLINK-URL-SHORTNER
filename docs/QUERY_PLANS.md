# Query Plan Review

This note documents the expected plans for the highest-risk queries. Run the
`EXPLAIN (ANALYZE, BUFFERS)` statements against a migrated local or staging
database with production-shaped row counts before changing indexes further.

## Redirect Lookup

Query shape:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM links
WHERE short_code = 'abc123';
```

Expected plan:

```text
Index Scan using ux_links_short_code on links
  Index Cond: (short_code = 'abc123')
```

Review: the redirect hot path is protected by `ux_links_short_code`, so lookup
should be a single-row unique index scan. The partial
`ix_links_active_redirect_lookup` can help active-only probes, but the current
repository intentionally fetches by unique code first so it can distinguish
missing links from inactive, expired, or flagged links.

Index action: no new index needed.

## Analytics Timeseries

Query shape:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT stat_date, COALESCE(SUM(click_count), 0)
FROM link_analytics_daily
WHERE link_id = 44000001
  AND stat_date >= DATE '2026-06-01'
  AND stat_date <= DATE '2026-06-30'
GROUP BY stat_date
ORDER BY stat_date ASC;
```

Expected plan:

```text
Index Scan using pk_link_analytics_daily on link_analytics_daily
  Index Cond: ((link_id = 44000001) AND (stat_date >= ...) AND (stat_date <= ...))
```

Review: after migration `20260614_0005`, the primary key starts with
`(link_id, stat_date, country, device_type, browser, os, referer_domain)`. That
prefix supports the dashboard timeseries range scan and grouping without raw
`click_events`.

Index action: no new index needed for day-granularity link timeseries. If future
dashboards query all links by date without a `link_id`, keep
`ix_link_analytics_daily_stat_date`.

## Link Listing With Pagination

Query shape:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM links
WHERE (
    owner_id = '00000000-0000-0000-0000-000000000001'
    OR workspace_id IN (
        SELECT workspace_id
        FROM workspace_members
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
    )
)
AND is_active = true
ORDER BY created_at DESC
LIMIT 25 OFFSET 0;
```

Expected plan:

```text
BitmapOr
  Bitmap Index Scan on ix_links_owner_id_created_at
  Bitmap Index Scan on ix_links_workspace_id_created_at
Index Scan using ix_workspace_members_user_id
Sort by links.created_at DESC
```

Review: the query has two access paths because users see owned links and
workspace links. Existing indexes support each branch and the membership
subquery. For very large accounts, keyset pagination with separate `UNION ALL`
branches can reduce sort work, but that is not justified until `EXPLAIN ANALYZE`
shows sort cost dominating.

Index action: no new index needed now. Revisit with production row counts if
owners commonly have more than 100k visible links.

## Bulk Shortening

Current query pattern for 50 URLs:

- Normalize/hash inputs in process.
- One batched query for existing `long_url_hash` values.
- One transaction commit for new `Link` objects.
- Cache priming is now gathered concurrently instead of awaited sequentially.

Index action: the existing `ix_links_long_url_hash_workspace_id` supports the
batched dedup lookup. A future refinement could add `owner_id` into that index if
`EXPLAIN ANALYZE` shows heavy filtering after matching common URL hashes.
