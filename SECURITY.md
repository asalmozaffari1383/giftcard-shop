# Security Policy

- Never commit `.env`, Fernet keys, fingerprint keys, SMS credentials, JWT signing keys or payment credentials.
- Report suspected vulnerabilities privately to the repository owner instead of opening a public issue.
- Treat decrypted digital inventory as highly sensitive and expose it only through the completed order detail endpoint.
- Rotate Fernet keys by prepending a new key while retaining old keys during re-encryption. Do not rotate `INVENTORY_FINGERPRINT_KEY`; it is required for stable duplicate detection.
- Require HTTPS, database backups, restricted PostgreSQL/Redis networking, staff MFA and gateway settlement reconciliation before production launch.
