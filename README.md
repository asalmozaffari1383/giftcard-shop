# Digital Products Marketplace

The RTL storefront lives in `frontend/` and is built with Next.js, TypeScript and Tailwind CSS.

## Run the full stack

Run `docker compose up --build`, then open:

- Storefront: `http://localhost:3000`
- API: `http://localhost:8000/api/v1/`
- API docs: `http://localhost:8000/api/v1/docs/`
- Admin: `http://localhost:8000/admin/`

### Local development login and payment

The ignored local `.env` can enable `DEVELOPMENT_OTP_CODE=123456` and `PAYMENT_GATEWAY=mock`. These options are
accepted only while Django `DEBUG=true`; the mock gateway is rejected in production. Use any valid Iranian mobile
number, enter `123456`, add a product, and complete the mock payment to exercise real reservation, callback,
fulfillment, and encrypted-code delivery without contacting an external provider.

To switch to Zarinpal, set `PAYMENT_GATEWAY=zarinpal`, remove `DEVELOPMENT_OTP_CODE`, provide
`ZARINPAL_MERCHANT_ID`, and rebuild/restart the services. Never commit the real `.env` file.

Seed or replenish the local sample catalog with:

```bash
docker compose exec web python manage.py seed_demo_data
```

For standalone frontend development, copy `frontend/.env.example` to `frontend/.env.local`, then run `npm install` and `npm run dev` inside `frontend/`. See `FRONTEND_TASKS.md` for the implementation roadmap and production follow-ups.

Production placeholders, the separate Docker stack, final credential handoff, HTTPS routing, backup and restore steps are documented in `PRODUCTION_READINESS.md`. Real host, SMS and gateway values are intentionally deferred to the final deployment stage and must only be stored in the ignored `.env.production` file.

## Backend

Django 5.2 / DRF backend with PostgreSQL row locks, encrypted digital stock, mobile OTP, JWT, and Zarinpal payments. All persisted prices are **integer Tomans**; gateway requests use `IRR` with `amount_toman * 10`. Timestamps are timezone-aware Gregorian UTC in storage/API, with an additional Jalali display string in order responses.

## Run locally

### Docker (recommended)

Run `docker compose up --build`. PostgreSQL, Redis, Django, Celery worker and Celery beat start together. The local defaults in `compose.yaml` are development-only and must never be reused in production.

Health endpoints:

- `GET /health/live/` checks that the web process is running.
- `GET /health/ready/` checks PostgreSQL and Redis readiness.

### Manual setup

1. Start PostgreSQL and Redis; create the database/user listed in `.env.example` (PostgreSQL is required for advisory locks and `SELECT FOR UPDATE`).
2. Create a Python 3.12 environment, install `requirements.txt`, and export environment variables from a private `.env` (the project does not auto-load it). Generate an encryption key with `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`. Generate a separate random `INVENTORY_FINGERPRINT_KEY` of at least 32 characters.
3. Run `python manage.py migrate`, `python manage.py createsuperuser`, `python manage.py runserver`.
4. Separately run `celery -A config worker -l info` and `celery -A config beat -l info` for SMS, reservation expiry and stale payment cleanup. In production use a process manager and TLS reverse proxy; set `DEBUG=false`, strong independent secrets, trusted hosts/origins, HTTPS provider endpoints, and real Zarinpal credentials. Restrict database/Redis access and back up encryption secrets separately. New Fernet keys go first in the comma-separated list; retain old keys until all inventory has been re-encrypted. `INVENTORY_FINGERPRINT_KEY` must remain stable permanently, otherwise duplicate-code detection cannot recognize older inventory.

HSTS is enabled for the host in production. Set `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` only after every subdomain is permanently HTTPS-ready; Django's deploy check intentionally warns about disabled preload.

## Lifecycle

- `POST /api/v1/auth/otp/request/` and `/otp/verify/` normalize Iranian mobile numbers to `+989…` and accept Persian digits. Challenges expire after five minutes, allow three requests per rolling five minutes and five verification attempts. SMS uses a configurable HTTPS template API and is queued only after DB commit. Configure the provider's exact payload contract in `apps/users/tasks.py`.
- `POST /api/v1/orders/cart/` accepts `variant` and `quantity`; `POST /api/v1/orders/checkout/` optionally accepts `coupon_code` and requires a stable `Idempotency-Key` header (8–80 characters). Reusing the same key returns the original order instead of reserving inventory twice. Checkout locks user, cart, coupon, variant and inventory rows, snapshots prices and reserves codes for 15 minutes. Beat expires unpaid orders and releases stock/coupon slots.
- `POST /api/v1/payments/initiate/` requires `order_id` and a client-generated stable `idempotency_key` (8–80 chars). Redirect the buyer to `payment_url`. GET and POST callbacks check the saved authority and verify remotely with Zarinpal before atomically assigning the reserved codes. Repeated successful callbacks are safe. `GET /api/v1/payments/{uuid}/` lets only the order owner poll status. Gateway attempts stuck in `INITIATING` for more than five minutes are failed automatically so payment can be retried. A verified but expired/understocked order enters `RECONCILIATION` for operator review/refund; **never** treat a browser callback alone as proof of payment.
- After confirming a full refund outside this service, a verified admin can `POST /api/v1/payments/{uuid}/refund-record/` with an `external_reference` to audit the event. Refunding the fulfillment payment marks the order `REFUNDED`; refunding an extra/reconciled charge leaves a completed order intact. This endpoint **does not issue money transfers**; do not call it before the gateway/bank confirms the refund.
- `GET /api/v1/orders/{uuid}/` reveals codes only to the order owner after completion; list responses omit them. Admin never displays plaintext. API schema and Swagger UI: `/api/v1/schema/` and `/api/v1/docs/`.
- Verified staff members with `is_staff` and a support/admin role can list, respond to and change ticket status under `/api/v1/support/staff/tickets/`; customers can only access and close their own tickets.
- Only verified purchasers can create reviews. Customers may edit/delete their own review; editing resets approval to `PENDING`. Product responses include approved `rating_average` and `rating_count`.
- `GET /api/v1/integrations/torob/products/?page=1` uses `X-Feed-Key`; `?format=xml` returns XML. It returns a stable 100-item-per-page variant feed, newest first, with prices in Tomans and `instock`/`outofstock`. This is a **partner-specific v1-style feed with requested extra fields** (`page_unique_id`, `title`); it is not Torob API v3 (which requires POST/JWT and a different response schema). Agree on the contract with Torob before registering the URL. Set `PUBLIC_BASE_URL` to a public domain and adapt `page_url` to the customer-facing storefront when available.

## Inventory import

Prepare a UTF-8 text file with one secret per line, then validate and import it:

```bash
python manage.py import_digital_items --variant-sku SKU-10-US --file codes.txt --dry-run
python manage.py import_digital_items --variant-sku SKU-10-US --file codes.txt
```

Imports are atomic, capped at 10,000 items and reject duplicates both inside the file and across existing encrypted inventory. Plaintext is never stored.

## Quality checks

`make test-fast` runs the complete logical suite against an in-memory test database. `make lint`, `make check` and `make schema` validate style, migrations and OpenAPI. Running `python manage.py test` against PostgreSQL additionally exercises the production database backend. GitHub Actions runs lint, migrations, 19 API/domain tests and schema validation with real PostgreSQL and Redis on every push and pull request.

SQLite cannot prove row-locking behavior under concurrency, so PostgreSQL CI remains mandatory before deployment.

## Operational safeguards

Keep callbacks reachable over HTTPS, monitor `PaymentTransaction` entries in `RECONCILIATION`, and reconcile them against gateway settlements before manual refunds. Run `flushexpiredtokens` daily for SimpleJWT blacklist cleanup. Enforce staff MFA and database backups operationally; neither is implemented by this API. Do not log OTPs, payment credentials, or decrypted codes. Use a payment gateway sandbox and provider-specific SMS staging credentials before production rollout.
