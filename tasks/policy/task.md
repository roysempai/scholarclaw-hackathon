# Block: POLICY
## Status: PENDING BUILD
## Pentest findings will be written here after the block is built.

### Overview
Role-based access control (RBAC) using vendor/fastapi-rbac patterns.

### Roles
- **user** - Standard user access
- **admin** - Full administrative access
- **auditor** - Read-only audit access

### Permissions
- read:profile, write:profile
- read:schemes, apply:schemes
- read:audit, admin:audit
- read:attacks

### Security Requirements
- Permission checks on all endpoints
- Resource ownership verification
- Admin-only routes protected
