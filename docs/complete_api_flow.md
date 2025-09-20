# Complete Certificate Verification Flow & API Documentation

## Flow Overview

### University → Student → Employer Workflow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UNIVERSITY    │    │     STUDENT     │    │    EMPLOYER     │
│   (Issuer)      │    │   (Recipient)   │    │   (Verifier)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. Issue Certificate  │                       │
         ├──────────────────────►│                       │
         │    (QR + Image)       │                       │
         │                       │ 2. Present Certificate│
         │                       ├──────────────────────►│
         │                       │   (Physical/Digital)  │
         │                       │                       │
         │                       │ 3. Scan QR Code      │
         │                       │◄──────────────────────┤
         │                       │                       │
         │ 4. Public Verification API Call              │
         │◄──────────────────────────────────────────────┤
         │                       │                       │
         │ 5. Return Verification Result                 │
         ├──────────────────────────────────────────────►│
         │    (✅ Authentic or ❌ Invalid)               │
         │                       │                       │
```

## 1. University Certificate Issuance

### Issue Single Certificate

**Endpoint:** `POST /api/issue/certificate`

**Description:** University issues a certificate with QR code and digital attestation.

**Request:**
```json
{
  "certificate_data": {
    "certificate_id": "CS2023-001234",
    "student_name": "John Doe",
    "roll_no": "2021CS001",
    "course_name": "Computer Science",
    "institution": "University of Technology",
    "issue_date": "2023-12-15",
    "year": "2023",
    "grade": "First Class Honours"
  },
  "institution_id": "univ_tech_001"
}
```

**Response:**
```json
{
  "issuance_id": "iss_abc123def456",
  "certificate_id": "CS2023-001234",
  "status": "issued",
  "certificate_image_url": "https://storage.supabase.co/certificates/iss_abc123def456.png",
  "qr_code_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "verification_url": "https://verify.certisafe.com/verify/iss_abc123def456",
  "attestation": {
    "attestation_id": "att_xyz789",
    "signature": "MEQCIG7n8...",
    "public_key": "-----BEGIN PUBLIC KEY-----\nMFkwEwYH..."
  },
  "issued_at": "2023-12-15T10:30:00Z",
  "expires_at": "2033-12-15T10:30:00Z"
}
```

### Bulk Certificate Import

**Endpoint:** `POST /api/issue/bulk`

**Description:** Bulk import certificates from CSV/ERP data.

**Request:**
```json
{
  "certificates_data": {
    "certificates": [
      {
        "certificate_id": "CS2023-001234",
        "student_name": "John Doe",
        "course_name": "Computer Science",
        "institution": "University of Technology",
        "issue_date": "2023-12-15",
        "grade": "First Class"
      },
      {
        "certificate_id": "CS2023-001235",
        "student_name": "Jane Smith",
        "course_name": "Data Science",
        "institution": "University of Technology",
        "issue_date": "2023-12-15",
        "grade": "Second Class"
      }
    ]
  },
  "institution_id": "univ_tech_001"
}
```

**Response:**
```json
{
  "total": 2,
  "successful": [
    {
      "row": 1,
      "certificate_id": "CS2023-001234",
      "issuance_id": "iss_abc123",
      "verification_url": "https://verify.certisafe.com/verify/iss_abc123"
    },
    {
      "row": 2,
      "certificate_id": "CS2023-001235", 
      "issuance_id": "iss_def456",
      "verification_url": "https://verify.certisafe.com/verify/iss_def456"
    }
  ],
  "failed": [],
  "report_url": "/api/reports/bulk_20231215_103000",
  "processed_at": "2023-12-15T10:30:00Z"
}
```

## 2. Student Receives Certificate

The student receives:
1. **Physical/Digital Certificate** with embedded QR code
2. **Verification URL** that can be shared with employers
3. **QR Code** containing signed verification data

## 3. Employer Verification (QR Scanning)

### Public Verification by Attestation ID

**Endpoint:** `GET /api/verify/{attestation_id}`

**Description:** Main endpoint for employer verification when scanning QR code.

**Example Request:** `GET /api/verify/iss_abc123def456`

**Response (✅ Valid Certificate):**
```json
{
  "valid": true,
  "attestation_id": "iss_abc123def456",
  "certificate_details": {
    "certificate_id": "CS2023-001234",
    "student_name": "John Doe",
    "course_name": "Computer Science",
    "institution": "University of Technology",
    "issue_date": "2023-12-15",
    "year": "2023",
    "grade": "First Class Honours"
  },
  "verification_details": {
    "signature_valid": true,
    "image_integrity": {
      "available": true,
      "sha256_hash": "abc123...",
      "perceptual_hash": "def456...",
      "integrity_verified": true
    },
    "certificate_status": {
      "valid": true,
      "status": "issued",
      "active": true,
      "expired": false,
      "revoked": false
    },
    "verified_at": "2023-12-15T14:30:00Z"
  },
  "issuer_information": {
    "institution": "University of Technology",
    "institution_id": "univ_tech_001",
    "public_key_verified": true
  },
  "verification_metadata": {
    "verification_method": "qr_attestation",
    "attestation_created": "2023-12-15T10:30:00Z",
    "certificate_issued": "2023-12-15T10:30:00Z"
  }
}
```

**Response (❌ Invalid Certificate):**
```json
{
  "valid": false,
  "error": "Invalid attestation signature",
  "error_code": "INVALID_SIGNATURE"
}
```

### Get Certificate Image

**Endpoint:** `GET /api/verify/{attestation_id}/image`

**Description:** Get the verified certificate image for display.

**Response:**
```json
{
  "image_url": "https://storage.supabase.co/certificates/iss_abc123def456.png",
  "image_hashes": {
    "sha256": "abc123...",
    "phash": "def456...",
    "integrity_hash": "xyz789..."
  },
  "certificate_id": "CS2023-001234",
  "issued_at": "2023-12-15T10:30:00Z"
}
```

### Verify by QR Data

**Endpoint:** `POST /api/verify/qr`

**Description:** Alternative verification method using raw QR code data.

**Request:**
```json
{
  "qr_content": "{\"payload\":{\"version\":\"1.0\",\"type\":\"certificate_verification\",\"issuer_id\":\"univ_tech_001\",\"data\":{\"certificate_id\":\"CS2023-001234\",\"student_name\":\"John Doe\"}},\"signature\":\"MEQCIG7n8...\",\"public_key\":\"-----BEGIN PUBLIC KEY-----\\n...\"}"
}
```

**Response:**
```json
{
  "valid": true,
  "qr_verification": {
    "qr_detected": true,
    "qr_decoded": true,
    "signature_valid": true,
    "issuer_verified": true,
    "certificate_id_match": true,
    "issue_date_match": true
  },
  "certificate_details": {
    "certificate_id": "CS2023-001234",
    "student_name": "John Doe",
    "course_name": "Computer Science",
    "institution": "University of Technology"
  },
  "field_consistency": {
    "all_match": true,
    "match_percentage": 100,
    "discrepancies": []
  }
}
```

## 4. Advanced Verification (3-Layer Analysis)

### Enhanced Verification with Forensic Analysis

**Endpoint:** `POST /api/verify`

**Description:** Complete 3-layer verification with forensic analysis (for internal use).

**Request:**
```json
{
  "file": "<multipart_form_data>",
  "reference_hash": "abc123...",
  "requester_id": "institution_id"
}
```

**Response:**
```json
{
  "verification_id": "ver_xyz789",
  "status": "verified",
  "layer_results": {
    "layer1_extraction": {
      "name": "John Doe",
      "certificate_id": "CS2023-001234",
      "extraction_method": "donut_primary",
      "field_confidences": {
        "name": 0.95,
        "certificate_id": 0.87
      },
      "extraction_time": 1.2
    },
    "layer2_forensics": {
      "copy_move_score": 0.1,
      "ela_score": 0.15,
      "tamper_probability": 0.12,
      "hash_match": true,
      "suspicious_regions": [],
      "tamper_types": []
    },
    "layer3_signatures": {
      "seals_detected": 1,
      "signatures_detected": 1,
      "seal_authenticity_score": 0.9,
      "signature_authenticity_score": 0.85,
      "qr_signature_valid": true
    },
    "qr_integrity": {
      "qr_detected": true,
      "qr_decoded": true,
      "signature_valid": true,
      "issuer_verified": true
    }
  },
  "risk_score": {
    "extraction_confidence": 0.91,
    "database_match_score": 0.95,
    "forensic_score": 0.88,
    "signature_score": 0.875,
    "qr_integrity_score": 1.0,
    "overall_score": 0.92,
    "confidence": 0.95,
    "risk_level": "low",
    "risk_factors": [],
    "authenticity_indicators": [
      "Primary AI extraction successful",
      "Database record match found",
      "QR digital signature verified"
    ]
  },
  "decision_rationale": "High confidence verification (score: 0.92)",
  "requires_manual_review": false,
  "processing_time_total_ms": 4200
}
```

## 5. Institution Management

### Register Institution

**Endpoint:** `POST /api/institutions/register`

**Request:**
```json
{
  "institution_data": {
    "name": "University of Technology",
    "domain": "unitech.edu",
    "contact_email": "admin@unitech.edu",
    "public_key": "-----BEGIN PUBLIC KEY-----\nMFkwEwYH...",
    "verification_endpoints": ["https://unitech.edu/verify"],
    "certificate_templates": ["default", "engineering", "business"]
  }
}
```

**Response:**
```json
{
  "institution_id": "univ_tech_001",
  "status": "registered"
}
```

### Import Certificate Database

**Endpoint:** `POST /api/institutions/{institution_id}/certificates/import`

**Request:**
```json
{
  "certificates_data": {
    "certificates": [
      {
        "certificate_id": "CS2023-001234",
        "student_name": "John Doe",
        "course_name": "Computer Science",
        "issue_date": "2023-12-15",
        "year": "2023"
      }
    ]
  }
}
```

**Response:**
```json
{
  "imported_count": 1,
  "status": "success"
}
```

## 6. Analytics & Monitoring

### Verification Statistics

**Endpoint:** `GET /api/analytics/verification-stats`

**Response:**
```json
{
  "total_verifications": 1250,
  "successful_verifications": 1180,
  "failed_verifications": 70,
  "verification_rate": 94.4,
  "tamper_detections": 15,
  "period": "30_days"
}
```

## Integration Examples

### Frontend Integration (React)

```javascript
// Employer scanning QR code
const verifyQRCode = async (qrData) => {
  try {
    const response = await fetch(`/api/verify/qr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ qr_content: qrData })
    });
    
    const result = await response.json();
    
    if (result.valid) {
      displayCertificate(result.certificate_details);
    } else {
      showError(result.error);
    }
  } catch (error) {
    showError('Verification failed');
  }
};

// University issuing certificate
const issueCertificate = async (certificateData) => {
  const response = await fetch('/api/issue/certificate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      certificate_data: certificateData,
      institution_id: 'univ_tech_001'
    })
  });
  
  return await response.json();
};
```

### Mobile App Integration

```javascript
// QR Scanner Integration
import { Camera } from 'react-native-camera-kit';

const QRScanner = () => {
  const onQRRead = async (event) => {
    const qrData = event.nativeEvent.codeStringValue;
    
    // Check if it's a verification URL
    if (qrData.includes('/verify/')) {
      const attestationId = qrData.split('/verify/')[1];
      const verification = await verifyByAttestationId(attestationId);
      showVerificationResult(verification);
    }
  };

  return (
    <Camera
      scanBarcode={true}
      onReadCode={onQRRead}
      showFrame={true}
    />
  );
};
```

## Security Considerations

### Authentication & Authorization

1. **Institution APIs**: Require API keys and mTLS
2. **Public Verification**: Rate limited, no authentication required
3. **Internal APIs**: RBAC with JWT tokens

### Data Protection

1. **Image Storage**: Encrypted at rest in Supabase Storage
2. **Database**: Row-level security (RLS) enabled
3. **Transit**: All APIs use HTTPS/TLS 1.3
4. **QR Signatures**: ECDSA P-256 with rotating keys

### Audit & Compliance

1. **Immutable Logs**: All verification attempts logged
2. **Forensic Evidence**: Tamper detection results stored
3. **GDPR Compliance**: Data retention and deletion policies
4. **Institution Compliance**: Support for regulatory requirements

This completes the comprehensive certificate verification flow with QR integrity controls, 3-layer forensic analysis, and secure institution integration! 🎉
