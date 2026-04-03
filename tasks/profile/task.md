# Block: PROFILE
## Status: PENDING BUILD
## Pentest findings will be written here after the block is built.

### Overview
User profile management with eligibility-related fields.

### Endpoints
- GET /api/profile
- PUT /api/profile

### Data Fields
- Personal info (name, DOB, gender)
- Category (SC/ST/OBC/General/EWS)
- Income details
- Location (state, district)
- Education details
- Disability status

### Security Requirements
- User can only access their own profile
- Input validation on all fields
- Sanitize before storage
