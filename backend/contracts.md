# ScholarClaw API Contracts

## Base URL
`/api`

---

## Authentication (`/api/auth`)

### POST `/api/auth/register`
**Auth Required:** No

**Request:**
```json
{
  "email": "string",
  "password": "string",
  "full_name": "string"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string",
  "created_at": "datetime"
}
```

---

### POST `/api/auth/login`
**Auth Required:** No

**Request:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### POST `/api/auth/refresh`
**Auth Required:** No (uses refresh token)

**Request:**
```json
{
  "refresh_token": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### POST `/api/auth/logout`
**Auth Required:** Yes

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

## Profile (`/api/profile`)

### GET `/api/profile`
**Auth Required:** Yes

**Response (200):**
```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string",
  "date_of_birth": "date",
  "gender": "string",
  "category": "string",
  "annual_income": "number",
  "state": "string",
  "district": "string",
  "education_level": "string",
  "institution": "string",
  "course": "string",
  "percentage": "number",
  "disability_status": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

### PUT `/api/profile`
**Auth Required:** Yes

**Request:**
```json
{
  "full_name": "string",
  "date_of_birth": "date",
  "gender": "string",
  "category": "string",
  "annual_income": "number",
  "state": "string",
  "district": "string",
  "education_level": "string",
  "institution": "string",
  "course": "string",
  "percentage": "number",
  "disability_status": "boolean"
}
```

**Response (200):**
```json
{
  "id": "uuid",
  "message": "Profile updated successfully"
}
```

---

## Schemes (`/api/schemes`)

### GET `/api/schemes`
**Auth Required:** Yes

**Query Params:**
- `page` (int, default: 1)
- `limit` (int, default: 20)
- `category` (string, optional)
- `state` (string, optional)

**Response (200):**
```json
{
  "schemes": [
    {
      "id": "uuid",
      "name": "string",
      "provider": "string",
      "amount": "number",
      "deadline": "date",
      "eligibility_summary": "string",
      "match_score": "number"
    }
  ],
  "total": "number",
  "page": "number",
  "pages": "number"
}
```

---

### GET `/api/schemes/{scheme_id}`
**Auth Required:** Yes

**Response (200):**
```json
{
  "id": "uuid",
  "name": "string",
  "provider": "string",
  "description": "string",
  "amount": "number",
  "deadline": "date",
  "eligibility_criteria": {
    "category": ["string"],
    "income_limit": "number",
    "states": ["string"],
    "education_levels": ["string"],
    "min_percentage": "number"
  },
  "required_documents": ["string"],
  "application_url": "string",
  "match_score": "number",
  "eligibility_status": "eligible | ineligible | partial",
  "missing_criteria": ["string"]
}
```

---

### POST `/api/schemes/{scheme_id}/check-eligibility`
**Auth Required:** Yes

**Response (200):**
```json
{
  "scheme_id": "uuid",
  "is_eligible": "boolean",
  "match_score": "number",
  "met_criteria": ["string"],
  "unmet_criteria": ["string"],
  "recommendations": ["string"]
}
```

---

### POST `/api/schemes/{scheme_id}/draft-application`
**Auth Required:** Yes

**Response (200):**
```json
{
  "scheme_id": "uuid",
  "draft": {
    "personal_statement": "string",
    "answers": [
      {
        "question": "string",
        "answer": "string"
      }
    ]
  },
  "token_usage": "number",
  "audit_hash": "string"
}
```

---

## Audit (`/api/audit`)

### GET `/api/audit/chain`
**Auth Required:** Yes

**Query Params:**
- `page` (int, default: 1)
- `limit` (int, default: 50)

**Response (200):**
```json
{
  "entries": [
    {
      "id": "uuid",
      "timestamp": "datetime",
      "action": "string",
      "agent": "string",
      "input_hash": "string",
      "output_hash": "string",
      "previous_hash": "string",
      "current_hash": "string"
    }
  ],
  "total": "number",
  "chain_valid": "boolean"
}
```

---

### GET `/api/audit/verify`
**Auth Required:** Yes

**Response (200):**
```json
{
  "chain_valid": "boolean",
  "total_entries": "number",
  "last_verified": "datetime",
  "invalid_entries": ["uuid"]
}
```

---

### GET `/api/audit/attacks`
**Auth Required:** Yes (Admin only)

**Response (200):**
```json
{
  "attacks": [
    {
      "id": "uuid",
      "timestamp": "datetime",
      "attack_type": "string",
      "source_ip": "string",
      "user_id": "uuid",
      "payload_preview": "string",
      "blocked": "boolean"
    }
  ],
  "total": "number"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to access this resource"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```
