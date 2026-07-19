# User Account Self-Service

Endpoints for an authenticated patient to update their own profile details or delete their own account. Both live under the `patients` router (`PatientViewSet` in `app/viewsets.py`) — there is no separate route, the same `/patients/<id>/` endpoint is used, scoped to the caller's own record.

Auth: requires a valid token (`Authorization: Token <token>`), same as the rest of the API.

## 1. Look up your own patient ID

Non-staff users only ever see their own record when listing patients:

```
GET /patients/
Authorization: Token <token>
```

```json
[
  {
    "id": 7,
    "user": 3,
    "firstName": "Jane",
    "lastName": "Doe",
    "phone": "5551234567",
    "date_of_birth": "1990-01-01",
    "address": "123 Main St",
    "is_email_verified": true,
    ...
  }
]
```

Use the `id` from this response (`7` above) for the endpoints below.

## 2. Update your own details

```
PATCH /patients/<id>/
Content-Type: application/json
Authorization: Token <token>

{
  "phone": "5559876543",
  "address": "456 New Address"
}
```

(`PUT` also works if you send the full object.)

- Only your own patient record is reachable — `<id>` must match the patient linked to your account, otherwise it 404s (it's outside your queryset).
- **Editable fields:** `firstName`, `lastName`, `phone`, `date_of_birth`, `address`.
- **Not editable by you:** `user`, `is_email_verified`, `email_verification_token`, `password_reset_token`, `password_reset_token_created_at` — these are system-managed. Attempting to set any of them raises a validation error.

| Status | Body | When |
|---|---|---|
| 200 | updated patient object | success |
| 400 | `{"You cannot update '<field>'"}` | tried to change a restricted field |
| 404 | — | `<id>` isn't your own patient record |

To change your password, use the password reset flow instead (see `docs/PASSWORD_RESET.md`) — there is no direct "set password" field on this endpoint.

## 3. Delete your own account

```
DELETE /patients/<id>/
Authorization: Token <token>
```

- `<id>` must be your own patient record (same scoping as above); deleting someone else's returns a validation error.
- This permanently deletes both your `Patient` profile and your underlying `User` (login/account), and cleans up related appointments:
  - For each of your appointments, the linked slot is freed (`is_booked = False`) if it belongs to a doctor, or deleted outright if it was a slot you created yourself.
  - Your appointments are removed as part of deleting the patient record.
  - The whole operation runs in a single transaction — it either fully succeeds or fully rolls back.
- There is no confirmation step or grace period — this is immediate and irreversible. Your token/session is invalidated since the underlying `User` no longer exists.

| Status | Body | When |
|---|---|---|
| 204 | — | success, account deleted |
| 400 | `{"You are not allowed to delete this patient"}` | `<id>` belongs to another user |
| 404 | — | `<id>` isn't your own patient record |

## Notes

- Staff/admin users hit the same endpoints but with different behavior: they can update/delete **any** patient, without the field whitelist, and use bulk slot-freeing logic instead of per-appointment cleanup.
- These endpoints are implemented in `PatientViewSet.perform_update` / `PatientViewSet.perform_destroy` (`app/viewsets.py`).
