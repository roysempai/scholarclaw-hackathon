# Block: AUTH
## Status: PENDING BUILD
## Pentest findings will be written here after the block is built.

### Overview
Authentication module using JWT with access/refresh token pattern.

### Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/refresh
- POST /api/auth/logout

### Security Requirements
- Password hashing with bcrypt
- JWT with short-lived access tokens (15 min)
- Refresh token rotation
- Rate limiting on auth endpoints
