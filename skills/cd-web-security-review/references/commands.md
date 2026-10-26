# Commands, test levels and behaviour checks

Used by `SKILL.md`. Replace `example.com` with the target host. Stay within scope and the rate limit.

## Test levels

| Level | What it adds | Requests |
| --- | --- | --- |
| `passive` (default) | Browse as a normal user. Read headers, cookies, storage, served JavaScript, DNS and TLS. Look at public files (`robots.txt`, `sitemap.xml`, `/.well-known/security.txt`). | Only what a normal visitor's browser would send, plus `curl -I`, `openssl`, `dig` |
| `light-active` | Everything in passive, plus: <br>• one GET each to the fixed list of common exposure paths below (no wordlists) <br>• one malformed-URL request and one 404 to see error handling <br>• `OPTIONS` to list allowed methods <br>• one request with a harmless foreign `Origin` header to test CORS <br>• one harmless marker string (`zxq7test<>"'`) in a search/query parameter to see whether it comes back unencoded <br>• one off-site value in an obvious redirect parameter (`?next=`, `?returnUrl=`) to `https://example.org` <br>• fetching source maps the scripts point to | About 30 extra requests in total, rate-limited |

The fixed exposure list for `light-active` (GET once each, stop on the first 429/403 pattern):

```
/.git/HEAD  /.git/config  /.env  /.env.production  /.DS_Store  /config.json  /appsettings.json
/server-status  /phpinfo.php  /backup.zip  /db.sql  /wp-config.php.bak  /.svn/entries
/swagger.json  /openapi.json  /api-docs  /graphql (GET only, no introspection query)
/actuator  /actuator/health  /admin  /.well-known/security.txt  /robots.txt  /sitemap.xml
```

A `200` with real content (not the SPA's index page served for every path) is a finding. **Compare the response body** with the 404/SPA fallback before reporting it.

## Transport, TLS and DNS commands

Run these, replacing `example.com` with the target:

```bash
curl -sSI http://example.com/                           # plain HTTP should 301/308 to HTTPS
curl -sSI https://example.com/                          # response headers (security headers, cookies, server banners)
curl -sSI -H "Origin: https://evil.example" https://example.com/   # light-active: CORS reflection?
curl -sSI -X OPTIONS https://example.com/ | grep -iE "^(HTTP|allow|access-control-allow-methods)"   # light-active: allowed methods
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
for v in tls1 tls1_1 tls1_2 tls1_3; do echo -n "$v: "; openssl s_client -$v -connect example.com:443 -servername example.com </dev/null >/dev/null 2>&1 && echo accepted || echo refused; done
dig +short TXT example.com            # SPF
dig +short TXT _dmarc.example.com     # DMARC
dig +short CAA example.com            # CAA
dig +short DS example.com             # DNSSEC (if supported by the registrar)
```

Some `openssl` builds can't offer TLS 1.0/1.1. "Refused" for those can mean "not tested". Say which.

## Behaviour checks (by test level)

- **Errors and exceptional conditions (A10).** `light-active`: request a non-existent path, and one malformed URL (for example `/%`). Look for stack traces, framework or version banners, debug pages, or a `200` returned for errors.
- **Reflection (A05, indicator only).** `light-active`: put `zxq7test<>"'` into one search or query parameter. Does it come back in the page or DOM **unencoded**? If so, record "Suspected – needs authorised pen test". Do not try script payloads.
- **Open redirect (A01).** `light-active`: for visible redirect parameters only, try `https://example.org` once and see whether the site redirects off-domain.
- **Authentication (A07)**, with a test login the user signed in to:
  - Is the login page HTTPS, with no credentials in URLs?
  - Does the session cookie have `Secure`, `HttpOnly` and `SameSite`?
  - Does the session ID change after login (compare the cookie name and length, not the value)?
  - Does logout invalidate the session (back button, then reload an account page)?
  - Is there an idle timeout?
  - Is there MFA?
  - Are password rules and lockout messaging sensible?
  - Are error messages generic? Test with **one** fake username, only if the user named the login form in their request.
- **Access control (A01)**, with a test login: copy two or three authenticated page and API URLs. Open them in a fresh logged-out context and check you get 401/403 or a redirect, not data. **Do not** change IDs to reach other users' records. List that as needing a pen test.
- **Clickjacking (A02).** Check `X-Frame-Options` or CSP `frame-ancestors` in the **header** (frame-ancestors is ignored in a meta tag).
