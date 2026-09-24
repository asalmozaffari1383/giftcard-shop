# Implementation Brief

Audit and improve the Django/Next.js gift-card marketplace as one integrated system. Keep local development safe
and reproducible, preserve production security, and validate every change. Required outcomes include a runnable
Docker stack, encrypted demo inventory, development-only OTP and mock payments, callback-to-frontend flow,
HttpOnly JWT cookies, server-backed cart details and quantity changes, correct review ownership/eligibility,
product reviews, pagination, contact form, media URL handling, dynamic product SEO, responsive navigation, and
end-to-end verification from OTP login through digital-code delivery. Production-only external credentials such
as SMS provider keys and Zarinpal Merchant ID must remain outside Git.
