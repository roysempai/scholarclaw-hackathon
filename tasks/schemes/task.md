# Block: SCHEMES
## Status: PENDING BUILD
## Pentest findings will be written here after the block is built.

### Overview
Scholarship scheme management with eligibility checking and draft generation.

### Endpoints
- GET /api/schemes
- GET /api/schemes/{id}
- POST /api/schemes/{id}/check-eligibility
- POST /api/schemes/{id}/draft-application

### Features
- Scheme listing with pagination
- Filtering by category, state
- Eligibility matching
- AI-powered draft generation

### Security Requirements
- Rate limiting on AI endpoints
- Token usage tracking
- Audit logging for all AI calls
