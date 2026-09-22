# Digital Products Marketplace API

Django 5.2 / DRF backend with PostgreSQL row locks, encrypted digital stock, mobile OTP, JWT, and Zarinpal payments. All persisted prices are **integer Tomans**; gateway requests use `IRR` with `amount_toman * 10`. Timestamps are timezone-aware Gregorian UTC in storage/API, with an additional Jalali display string in order responses.

## Run locally

1. Start PostgreSQL and Redis; create the database/user listed in `.env.example` (PostgreSQL is required for advisory locks and `SELECT FOR UPDATE`).
2. Create a Python 3.12 environment, install `requirements.txt`, and export environment variables from a private `.env` (the project does not auto-load it). Generate an encryption key with `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`.
3. Run `python manage.py migrate`, `python manage.py createsuperuser`, `python manage.py runserver`.
4. Separately run `celery -A config worker -l info` and `celery -A config beat -l info` for SMS and reservation expiry. In production use a process manager and TLS reverse proxy; set `DEBUG=false`, strong independent secrets, trusted hosts/origins, HTTPS provider endpoints, and real Zarinpal credentials. Restrict database/Redis access and back up the Fernet keys separately. New Fernet keys go first in the comma-separated list; retain old keys until all inventory has been re-encrypted.

HSTS is enabled for the host in production. Set `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` only after every subdomain is permanently HTTPS-ready; Django's deploy check intentionally warns about disabled preload.

## Lifecycle

- `POST /api/v1/auth/otp/request/` and `/otp/verify/` normalize Iranian mobile numbers to `+989…` and accept Persian digits. Challenges expire after five minutes, allow three requests per rolling five minutes and five verification attempts. SMS uses a configurable HTTPS template API and is queued only after DB commit. Configure the provider's exact payload contract in `apps/users/tasks.py`.
- `POST /api/v1/orders/cart/` accepts `variant` and `quantity`; `POST /api/v1/orders/checkout/` optionally accepts `coupon_code`. Checkout locks cart, coupon, variant and inventory rows, snapshots prices and reserves codes for 15 minutes. Beat expires unpaid orders and releases stock/coupon slots.
- `POST /api/v1/payments/initiate/` requires `order_id` and a client-generated stable `idempotency_key` (8–80 chars). Redirect the buyer to `payment_url`. The GET callback checks the saved authority and verifies remotely with Zarinpal before atomically assigning the reserved codes. Repeated successful callbacks are safe. A verified but expired/understocked order enters `RECONCILIATION` for operator review/refund; **never** treat a browser callback alone as proof of payment. Refund execution is an operator action, not an automatic API transition.
- After confirming a full refund outside this service, a verified admin can `POST /api/v1/payments/{uuid}/refund-record/` with an `external_reference` to audit the event. Refunding the fulfillment payment marks the order `REFUNDED`; refunding an extra/reconciled charge leaves a completed order intact. This endpoint **does not issue money transfers**; do not call it before the gateway/bank confirms the refund.
- `GET /api/v1/orders/{uuid}/` reveals codes only to the order owner after completion; list responses omit them. Admin never displays plaintext. API schema and Swagger UI: `/api/v1/schema/` and `/api/v1/docs/`.
- Verified staff members with `is_staff` and a support/admin role can list and respond to tickets under `/api/v1/support/staff/tickets/`; customers can only access their own tickets.
- `GET /api/v1/integrations/torob/products/?page=1` uses `X-Feed-Key`; `?format=xml` returns XML. It returns a stable 100-item-per-page variant feed, newest first, with prices in Tomans and `instock`/`outofstock`. This is a **partner-specific v1-style feed with requested extra fields** (`page_unique_id`, `title`); it is not Torob API v3 (which requires POST/JWT and a different response schema). Agree on the contract with Torob before registering the URL. Set `PUBLIC_BASE_URL` to a public domain and adapt `page_url` to the customer-facing storefront when available.

Integration tests for checkout/fulfillment require a running PostgreSQL instance; SQLite does not exercise the locking semantics. The included fast unit tests run without a database.

With a test database role allowed to create databases, run `python manage.py test apps.users apps.inventory apps.payments apps.orders` to exercise the full flow. Run `python manage.py spectacular --validate` to verify the OpenAPI schema.

## Operational safeguards

Keep callbacks reachable over HTTPS, monitor `PaymentTransaction` entries in `RECONCILIATION`, and reconcile them against gateway settlements before manual refunds. Run `flushexpiredtokens` daily for SimpleJWT blacklist cleanup. Enforce staff MFA and database backups operationally; neither is implemented by this API. Do not log OTPs, payment credentials, or decrypted codes. Use a payment gateway sandbox and provider-specific SMS staging credentials before production rollout.
