# Auth Layer Specification

> **Branch:** `feature/auth`  
> **Adapted from:** `vendor/fastapi-rbac`  
> **Last Updated:** 2026-04-03

---

## Overview

JWT authentication layer with simplified RBAC (2 roles only: STUDENT, ADMIN).

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| python-jose over PyJWT | Better maintained, consistent API |
| bcrypt directly (not passlib) | Avoids version incompatibility issues |
| Prisma over SQLAlchemy | Matches project's database layer |
| 2 roles only (STUDENT/ADMIN) | Simplified from vendor's complex RBAC |

---

## Files

| File | Purpose |
|------|---------|
| `schemas.py` | Pydantic request/response models |
| `utils.py` | Password hashing, JWT token creation/validation |
| `router.py` | FastAPI endpoints with rate limiting |
| `models.py` | Role constants (User model is in Prisma schema) |
| `__init__.py` | Module exports |

---

## Schemas (`schemas.py`)

### Enums

```python
class Role(str, Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"
```

### Request Models

| Model | Fields | Validation |
|-------|--------|------------|
| `RegisterRequest` | email (EmailStr), password, full_name, role | password min 8 chars, role defaults to STUDENT |
| `LoginRequest` | email (EmailStr), password | — |
| `RefreshRequest` | refresh_token | — |

### Response Models

| Model | Fields |
|-------|--------|
| `TokenResponse` | access_token, refresh_token, token_type ("bearer") |
| `UserResponse` | id, email, full_name, role, created_at |
| `MessageResponse` | message |

---

## Utils (`utils.py`)

### Password Hashing

| Function | Description |
|----------|-------------|
| `hash_password(plain: str) -> str` | bcrypt hash with rounds=12 |
| `verify_password(plain: str, hashed: str) -> bool` | Constant-time comparison |

### JWT Tokens

| Function | Description |
|----------|-------------|
| `create_access_token(data: dict) -> str` | 15 min TTL, type="access" |
| `create_refresh_token(data: dict) -> str` | 7 day TTL, type="refresh" |
| `decode_token(token, request?) -> dict` | Validates signature, logs IP on failure |
| `validate_access_token(token, request?) -> dict` | decode + verify type="access" |
| `validate_refresh_token(token, request?) -> dict` | decode + verify type="refresh" |

### Token Payload Structure

```json
{
  "sub": "user-uuid",
  "role": "STUDENT",
  "exp": 1712345678,
  "iat": 1712344778,
  "type": "access"  // or "refresh"
}
```

---

## Endpoints (`router.py`)

**Prefix:** `/api/auth`

| Method | Path | Rate Limit | Auth | Description |
|--------|------|------------|------|-------------|
| POST | `/register` | 3/min per IP | No | Create new user |
| POST | `/login` | 5/min per IP | No | Get access + refresh tokens |
| POST | `/refresh` | — | No | Exchange refresh token for new access token |
| GET | `/me` | — | JWT | Get current user profile |
| POST | `/logout` | — | JWT | Invalidate refresh token(s) |

### Security Behaviors

1. **Registration with existing email:** Returns "Invalid credentials" (not "email exists")
2. **Login with wrong password:** Returns "Invalid credentials" (not "wrong password")
3. **Login with non-existent email:** Returns "Invalid credentials" (not "user not found")
4. **Deactivated user login:** Returns "Invalid credentials"
5. **Invalid/expired token:** Returns "Invalid credentials" + logs IP to audit

---

## Configuration (from `config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `JWT_SECRET` | (required) | Secret key for signing |
| `JWT_ALGORITHM` | "HS256" | Signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token TTL |

---

## Database Models (Prisma)

### User

```prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  password  String
  fullName  String   @map("full_name")
  role      String   @default("user")
  isActive  Boolean  @default(true) @map("is_active")
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")
  
  refreshTokens RefreshToken[]
  // ... other relations
}
```

### RefreshToken

```prisma
model RefreshToken {
  id        String   @id @default(uuid())
  userId    String   @map("user_id")
  token     String   @unique
  expiresAt DateTime @map("expires_at")
  createdAt DateTime @default(now()) @map("created_at")
  
  user User @relation(...)
}
```

---

## Self-Tests (`tests/test_auth.py`)

**7 tests — ALL MUST PASS before commit**

| # | Test | What it validates |
|---|------|-------------------|
| 1 | `test_password_hash_bcrypt_rounds` | Hash uses bcrypt with rounds ≥ 12 |
| 2 | `test_password_verify_correct` | Correct password returns True |
| 3 | `test_password_verify_wrong` | Wrong password returns False |
| 4 | `test_access_token_creation` | Access token has correct claims (sub, role, type, exp, iat) |
| 5 | `test_refresh_token_creation` | Refresh token has ~7 day TTL |
| 6 | `test_token_type_validation` | Access token fails refresh validation and vice versa |
| 7 | `test_invalid_token_rejection_with_logging` | Invalid tokens raise AuthenticationError + log IP |

### Running Tests

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/test_auth.py -v
```

---

## Usage Examples

### Register

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "student@example.com", "password": "securepass123", "full_name": "John Doe"}'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student@example.com", "password": "securepass123"}'
```

### Get Current User

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

---

## Commit History

| Commit | Description |
|--------|-------------|
| `a806ef9` | feat(auth): JWT auth adapted from vendor/fastapi-rbac — RBAC, refresh tokens, rate limiting |

---

## Dependencies

```
python-jose[cryptography]
bcrypt
pydantic[email]
slowapi
```
