# Official sources (security)

The checks in this skill are self-contained, so reviews work without web access. Use these sources to:

1. **Check standards are current** at the start of a run (SKILL.md Phase 0).
2. **Link every finding** to the official guidance in the report's **Reference** column.
3. **Resolve doubt.** Read the relevant cheat sheet before recommending a fix.

Sources last reviewed: 2026-10-26.

## Standards status (as of the date above)

| Standard | Status | What we use it for |
| --- | --- | --- |
| [OWASP Top 10:2025](https://owasp.org/Top10/2025/) | Current edition, released November 2025. No 2026 edition announced; editions come roughly every 3–4 years (2017, 2021, 2025). | Risk categories for every finding (A01–A10) |
| [OWASP ASVS 5.0](https://owasp.org/www-project-application-security-verification-standard/) | Current, released May 2025 | Detailed, testable requirements. Map findings to ASVS chapters and levels (below). |
| [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) | Current stable guide | How to test. Use it to scope the "needs a pen test" list. |
| [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/) | Maintained | Recommended header values |
| [RFC 9116](https://www.rfc-editor.org/rfc/rfc9116) | Standard | `security.txt` format |
| [ICO storage and access technologies guidance](https://ico.org.uk/for-organisations/guide-to-pecr/cookies-and-similar-technologies/) | Final guidance published April 2026 (UK PECR) | Consent before non-essential cookies, tracking and analytics |
| [NCSC secure development and deployment](https://www.ncsc.gov.uk/collection/developers-collection) | Maintained | UK government secure development principles |

**Standards check (Phase 0):** if you can search the web, confirm:
- the OWASP Top 10 edition is still 2025
- ASVS is still 5.0

If a newer edition exists, say so in the report's Scope section and tell the user. Keep mapping to the edition this skill uses unless the user asks to switch.

## OWASP Top 10:2025 categories

| ID | Name |
| --- | --- |
| A01:2025 | Broken Access Control |
| A02:2025 | Security Misconfiguration |
| A03:2025 | Software Supply Chain Failures |
| A04:2025 | Cryptographic Failures |
| A05:2025 | Injection |
| A06:2025 | Insecure Design |
| A07:2025 | Authentication Failures |
| A08:2025 | Software or Data Integrity Failures |
| A09:2025 | Security Logging & Alerting Failures |
| A10:2025 | Mishandling of Exceptional Conditions |

Index: https://owasp.org/Top10/2025/ (it redirects to top10.owasp.org). Link the index or the category page.

## ASVS 5.0 chapter mapping

Use this to add an ASVS reference to findings and to summarise coverage. Chapter numbers changed from ASVS 4.0. When you cite a specific requirement ID (e.g. `V3.4.2`), check it against the [official ASVS 5.0 document](https://owasp.org/www-project-application-security-verification-standard/). If you can't check, cite the chapter only.

| ASVS 5.0 chapter | Covers (in this skill) |
| --- | --- |
| V1 Encoding and Sanitization | XSS sinks, injection (code mode) |
| V2 Validation and Business Logic | Input validation, workflow abuse (pen test) |
| V3 Web Frontend Security | Security headers, CSP, cookies' browser-side flags, CORS, clickjacking, SRI, `target=_blank` |
| V4 API and Web Service | API endpoints, GraphQL/CMS exposure, WebSockets |
| V5 File Handling | Uploads, path traversal |
| V6 Authentication | Login, MFA, password handling |
| V7 Session Management | Session cookies, rotation, logout, timeout |
| V8 Authorization | Access control between users and roles (mostly pen test) |
| V9 Self-contained Tokens | JWT verification, algorithms, expiry |
| V10 OAuth and OIDC | Third-party sign-in flows |
| V11 Cryptography | Hashing, randomness, key handling |
| V12 Secure Communication | HTTPS, TLS versions, HSTS, certificates |
| V13 Configuration | Secrets management, debug/source maps, exposed files, dependency hygiene |
| V14 Data Protection | Personal data, caching of sensitive pages, client storage |
| V15 Secure Coding and Architecture | Dependencies, unsafe functions, deserialisation, concurrency |
| V16 Security Logging and Error Handling | Error pages, stack traces, security event logging |
| V17 WebRTC | Real-time media (only if used) |

Chapter names were confirmed in part from OWASP conference material. Treat the official document as authoritative.

## Cheat sheets for remediation

Base URL: `https://cheatsheetseries.owasp.org/cheatsheets/<Name>.html`

| Topic | Cheat sheet name |
| --- | --- |
| Security headers | `HTTP_Headers_Cheat_Sheet` |
| CSP | `Content_Security_Policy_Cheat_Sheet` |
| XSS | `Cross_Site_Scripting_Prevention_Cheat_Sheet`, `DOM_based_XSS_Prevention_Cheat_Sheet` |
| SQL injection | `SQL_Injection_Prevention_Cheat_Sheet` |
| Command injection | `OS_Command_Injection_Defense_Cheat_Sheet` |
| CSRF | `Cross-Site_Request_Forgery_Prevention_Cheat_Sheet` |
| Sessions | `Session_Management_Cheat_Sheet` |
| Authentication | `Authentication_Cheat_Sheet`, `Password_Storage_Cheat_Sheet`, `Multifactor_Authentication_Cheat_Sheet` |
| Authorisation | `Authorization_Cheat_Sheet`, `Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet` |
| Redirects | `Unvalidated_Redirects_and_Forwards_Cheat_Sheet` |
| Secrets | `Secrets_Management_Cheat_Sheet` |
| TLS | `Transport_Layer_Security_Cheat_Sheet`, `HTTP_Strict_Transport_Security_Cheat_Sheet` |
| Third-party scripts | `Third_Party_Javascript_Management_Cheat_Sheet` |
| Dependencies | `Vulnerable_Dependency_Management_Cheat_Sheet` |
| Errors and logging | `Error_Handling_Cheat_Sheet`, `Logging_Cheat_Sheet` |
| CI/CD | `CI_CD_Security_Cheat_Sheet` |
| Docker | `Docker_Security_Cheat_Sheet` |
| File upload | `File_Upload_Cheat_Sheet` |
| Deserialisation | `Deserialization_Cheat_Sheet` |
| Browser storage | `HTML5_Security_Cheat_Sheet` |

If a cheat sheet link 404s (OWASP occasionally renames them), use the [cheat sheet index](https://cheatsheetseries.owasp.org/) instead.

## Header and platform references

- **MDN HTTP headers reference:** `https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/<Header-Name>`, e.g. `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`, `Set-Cookie`
- **MDN HTTP Observatory** (header scoring): https://developer.mozilla.org/en-US/observatory. It's a third-party scan; only run it with the user's agreement.
- **Advisory databases for CVE look-ups:**
  - https://osv.dev/
  - https://github.com/advisories
  - https://nvd.nist.gov/

## How to cite in the report

- **Reference column:** the OWASP 2025 category, plus the ASVS chapter, plus the most relevant cheat sheet or MDN page. Example: `A02 · ASVS V3 · [CSP cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)`.
- **Dependency findings:** link the advisory itself (GHSA/CVE).
- **Sources section:** the standards used, with the date you checked they were current.
