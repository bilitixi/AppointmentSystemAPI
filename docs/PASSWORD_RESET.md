# Password Reset

Endpoints for the "forgot password" flow. Both are `AllowAny` (no auth token required) and mirror the existing email-verification pattern.

## 1. Request a reset link

```
POST /forgot_password/
Content-Type: application/json

{
  "username": "user@example.com"
}
```

- `username` is the user's login username (email).
- Looks up the `User` and their `Patient` profile. If found, generates a token, stores it (with a timestamp) on the `Patient` record, and emails a reset link:
  `{FRONTEND_URL}/reset-password/{token}`
- **Always returns the same generic response**, whether or not the account exists, to avoid leaking which usernames are registered:

```json
{ "message": "If an account with that email exists, a password reset link has been sent." }
```

| Status | Body | When |
|---|---|---|
| 200 | generic message above | account exists or not (indistinguishable) |
| 400 | `{"message": "username is required"}` | missing `username` field |

## 2. Reset the password

```
POST /reset_password/
Content-Type: application/json

{
  "token": "<token from the email link>",
  "new_password": "NewStrongPass123!"
}
```

- Looks up the `Patient` by `password_reset_token`.
- Token is valid for **1 hour** from when it was issued; expired or unknown tokens are rejected.
- `new_password` is validated with Django's standard password validators (`AUTH_PASSWORD_VALIDATORS` in `settings.py`: minimum length, not too common, not entirely numeric, not too similar to user attributes).
- On success, sets the new password, clears the token (single use), and the user can log in via `POST /auth/` with the new password.

| Status | Body | When |
|---|---|---|
| 200 | `{"message": "Password reset successfully"}` | success |
| 400 | `{"message": "token and new_password are required"}` | missing fields |
| 400 | `{"message": "Invalid or expired password reset link"}` | unknown token or token older than 1 hour |
| 400 | `{"message": [<validation errors>]}` | password fails Django's validators |

## Notes

- Requires migration `0003_patient_password_reset_token_and_more` to be applied (`python manage.py migrate`) — it adds `password_reset_token` and `password_reset_token_created_at` to `Patient`.
- Emails are sent via Django's `send_mail`, using the same `EMAIL_*` / `DEFAULT_FROM_EMAIL` / `FRONTEND_URL` settings as email verification. In dev (`EMAIL_BACKEND` unset), emails print to the console instead of sending.
- A password reset token is single-use: it's cleared after a successful reset or after it expires and reset is attempted again.
