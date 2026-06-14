# Token storage choice

The current API returns bearer access and refresh tokens in JSON responses and does
not set httpOnly cookies. The web app stores both tokens in `localStorage` so the
client can attach `Authorization: Bearer ...` and refresh after a `401`.

Tradeoff: `localStorage` is vulnerable to token theft if an XSS bug is introduced.
The preferred production direction is backend-managed httpOnly, secure, same-site
cookies for refresh/session state, with the access token kept in memory. The API
client is centralized so that swap can happen without touching feature code.
