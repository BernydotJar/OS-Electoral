# CampaignOS API error contract

CampaignOS uses `application/problem+json` responses compatible with RFC 9457. Every structured problem contains a stable machine code and the request correlation ID. Error detail is intentionally sanitized.

## Rate-limit errors

### `429 RATE_LIMIT_EXCEEDED`

Returned after authentication and applicable exact authorization when the reviewed operation budget is exhausted.

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/problem+json
Retry-After: 17
X-Correlation-ID: <bounded server value>
```

```json
{
  "type": "https://campaignos.example/problems/rate_limit_exceeded",
  "title": "Too many requests",
  "status": 429,
  "detail": "The request rate for this operation is temporarily limited",
  "instance": "/api/v1/...",
  "code": "RATE_LIMIT_EXCEEDED",
  "correlation_id": "..."
}
```

`Retry-After` is an integer number of seconds, derived from database time. Responses never include tenant ID, principal ID, raw bucket key, request count, configured limit, email, IP address, token or campaign payload.

### `503 RATE_LIMIT_UNAVAILABLE`

Returned when a protected endpoint lacks its reviewed policy metadata or when enforcement is enabled but the PostgreSQL decision cannot be persisted. The request fails closed before domain execution.

```json
{
  "title": "Service unavailable",
  "status": 503,
  "detail": "Request protection is temporarily unavailable",
  "code": "RATE_LIMIT_UNAVAILABLE"
}
```

## UI localization boundary

Machine codes and HTTP semantics are locale-neutral. A frontend that surfaces throttling must translate retry guidance into Spanish and English, preserve keyboard access and visible focus, avoid countdown-only interaction, and respect reduced-motion preferences. This increment changes no frontend surface; existing generic error handling remains authoritative until a separate approved UI feature is specified.
