# API Contracts

## Authentication

All API endpoints require authentication except for public verification endpoints.

```http
Authorization: Bearer <jwt_token>
```

## Core Verification APIs

### Upload Certificate

**Endpoint:** `POST /upload`

**Request:**
```http
Content-Type: multipart/form-data

file: <certificate_image>
```

**Response:**
```json
{
  "verification_id": "ver_abc123def456",
  "status": "verified",
  "extracted_fields": {
    "name": "John Doe",
    "institution": "University of Technology",
    "course_name": "Computer Science",
    "issue_date": "2023-06-15",
    "certificate_id": "CS2023-001234",
    "grade": "First Class Honours"
  },
  "risk_score": {
    "overall_score": 0.85,
    "confidence": 0.92,
    "risk_level": "low",
    "factors": []
  },
  "attestation": {
    "attestation_id": "att_xyz789abc123",
    "signature": "MEUCIQD5...",
    "public_key": "-----BEGIN PUBLIC KEY-----\nMFkw...",
    "qr_code_url": "data:image/png;base64,iVBOR...",
    "created_at": "2023-08-15T10:30:00Z"
  },
  "image_url": "https://storage.supabase.co/...",
  "processed_at": "2023-08-15T10:30:00Z",
  "requires_manual_review": false
}
```

**Error Response:**
```json
{
  "detail": "Invalid image file: unsupported format",
  "error_code": "INVALID_FILE_FORMAT"
}
```

### Verify Certificate by Data

**Endpoint:** `POST /verify`

**Request:**
```json
{
  "image_url": "https://example.com/cert.jpg",
  "manual_fields": {
    "name": "John Doe",
    "institution": "University of Technology",
    "course_name": "Computer Science",
    "certificate_id": "CS2023-001234"
  }
}
```

**Response:** Same as upload response

### Get Certificate Details

**Endpoint:** `GET /certificates/{certificate_id}`

**Response:**
```json
{
  "certificate_id": "CS2023-001234",
  "student_name": "John Doe",
  "institution": "University of Technology",
  "course_name": "Computer Science",
  "issue_date": "2023-06-15",
  "grade": "First Class Honours",
  "status": "active",
  "verification_count": 3
}
```

## Attestation APIs

### Get Attestation

**Endpoint:** `GET /attestations/{attestation_id}`

**Response:**
```json
{
  "attestation_id": "att_xyz789abc123",
  "verification_id": "ver_abc123def456",
  "signature": "MEUCIQD5...",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMFkw...",
  "qr_code_url": "data:image/png;base64,iVBOR...",
  "pdf_url": "https://storage.supabase.co/.../attestation.pdf",
  "created_at": "2023-08-15T10:30:00Z",
  "payload": {
    "verification_id": "ver_abc123def456",
    "extracted_fields": {...},
    "timestamp": "2023-08-15T10:30:00Z",
    "image_hash": "sha256:abc123..."
  }
}
```

### Verify Signature

**Endpoint:** `POST /verify-signature`

**Request:**
```json
{
  "attestation_id": "att_xyz789abc123",
  "signature": "MEUCIQD5...",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMFkw..."
}
```

**Response:**
```json
{
  "valid": true,
  "attestation_id": "att_xyz789abc123",
  "verified_at": "2023-08-15T11:00:00Z"
}
```

## Manual Review APIs

### Get Pending Reviews

**Endpoint:** `GET /reviews`

**Query Parameters:**
- `status`: pending, all, approved, rejected
- `search`: search term for filtering
- `limit`: number of results (default: 50)
- `offset`: pagination offset

**Response:**
```json
{
  "reviews": [
    {
      "verification_id": "ver_abc123def456",
      "status": "pending",
      "extracted_fields": {...},
      "risk_score": {...},
      "image_url": "https://storage.supabase.co/...",
      "submitted_at": "2023-08-15T10:30:00Z",
      "requires_review_reason": "No database match found"
    }
  ],
  "total_count": 15,
  "has_more": true
}
```

### Submit Review Decision

**Endpoint:** `POST /reviews/decision`

**Request:**
```json
{
  "verification_id": "ver_abc123def456",
  "approved": true,
  "reviewer_notes": "Certificate verified manually through institution portal",
  "corrected_fields": {
    "name": "John A. Doe",
    "issue_date": "2023-06-16"
  }
}
```

**Response:**
```json
{
  "success": true,
  "verification_id": "ver_abc123def456",
  "updated_status": "verified",
  "reviewed_at": "2023-08-15T11:30:00Z"
}
```

## Dashboard APIs

### Get Dashboard Statistics

**Endpoint:** `GET /dashboard/stats`

**Query Parameters:**
- `range`: 7d, 30d, 90d (default: 7d)

**Response:**
```json
{
  "total_verifications": 1250,
  "verified_certificates": 1100,
  "failed_verifications": 75,
  "pending_reviews": 75,
  "risk_distribution": [
    {"risk_level": "low", "count": 850},
    {"risk_level": "medium", "count": 250},
    {"risk_level": "high", "count": 100},
    {"risk_level": "critical", "count": 50}
  ],
  "daily_verifications": [
    {"date": "2023-08-14", "verifications": 45},
    {"date": "2023-08-15", "verifications": 52}
  ],
  "institution_stats": [
    {
      "name": "University of Technology",
      "verified": 120,
      "failed": 5,
      "pending": 3
    }
  ],
  "active_attestations": 1100,
  "failed_signatures": 2,
  "tamper_attempts": 0,
  "active_users": 25,
  "new_registrations": 5,
  "api_calls_today": 234
}
```

## Institution Management APIs

### Register Institution

**Endpoint:** `POST /institutions`

**Request:**
```json
{
  "name": "University of Technology",
  "domain": "university-tech.edu",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMFkw...",
  "contact_email": "registrar@university-tech.edu",
  "verification_endpoint": "https://university-tech.edu/verify"
}
```

**Response:**
```json
{
  "institution_id": "inst_abc123",
  "name": "University of Technology",
  "status": "active",
  "registered_at": "2023-08-15T12:00:00Z"
}
```

### Import Certificates

**Endpoint:** `POST /certificates/import`

**Request:**
```json
{
  "certificates": [
    {
      "student_name": "John Doe",
      "course_name": "Computer Science",
      "institution": "University of Technology",
      "issue_date": "2023-06-15",
      "certificate_id": "CS2023-001234",
      "grade": "First Class Honours"
    }
  ]
}
```

**Response:**
```json
{
  "imported_count": 1,
  "failed_count": 0,
  "errors": []
}
```

## Public Verification APIs

### Public Certificate Verification

**Endpoint:** `GET /verify/{verification_id}` (No auth required)

**Response:**
```json
{
  "verification_id": "ver_abc123def456",
  "status": "verified",
  "certificate_details": {
    "name": "John Doe",
    "institution": "University of Technology",
    "course_name": "Computer Science",
    "issue_date": "2023-06-15"
  },
  "verified_at": "2023-08-15T10:30:00Z",
  "attestation_valid": true,
  "qr_code_url": "data:image/png;base64,iVBOR..."
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_FILE_FORMAT` | Unsupported image format |
| `FILE_TOO_LARGE` | File exceeds size limit |
| `EXTRACTION_FAILED` | AI model extraction failed |
| `DATABASE_ERROR` | Database operation failed |
| `SIGNATURE_INVALID` | Digital signature verification failed |
| `ATTESTATION_NOT_FOUND` | Attestation ID not found |
| `VERIFICATION_NOT_FOUND` | Verification ID not found |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/upload` | 10 requests/minute |
| `/verify` | 20 requests/minute |
| `/verify-signature` | 100 requests/minute |
| Dashboard APIs | 60 requests/minute |
| Public APIs | 100 requests/minute |

## Webhooks

### Verification Complete

```json
{
  "event": "verification.completed",
  "verification_id": "ver_abc123def456",
  "status": "verified",
  "timestamp": "2023-08-15T10:30:00Z",
  "data": {
    "extracted_fields": {...},
    "risk_score": {...}
  }
}
```

### Manual Review Required

```json
{
  "event": "review.required",
  "verification_id": "ver_abc123def456",
  "reason": "No database match found",
  "timestamp": "2023-08-15T10:30:00Z"
}
```
