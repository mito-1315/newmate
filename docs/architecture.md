# Certificate Verifier Architecture

## Overview

The Certificate Verifier is a microservice-based system that combines AI-powered document understanding with cryptographic attestation to verify academic certificates.

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │    Supabase     │
│   (React)       │◄──►│   (FastAPI)      │◄──►│  (Database +    │
│                 │    │                  │    │   Storage)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ AI Services  │
                       │ (Donut/LLM)  │
                       └──────────────┘
```

## Components

### 1. Frontend (React + Tailwind)
- **Upload Page**: Certificate image upload with drag-and-drop
- **Dashboard**: Analytics and verification statistics
- **Manual Review**: Queue for certificates requiring human review
- **QR Viewer**: Display and verify attestation QR codes

### 2. Backend (FastAPI)
- **API Gateway**: RESTful endpoints for all operations
- **Fusion Engine**: Combines multiple verification methods
- **LLM Client**: Donut model wrapper for field extraction
- **Supabase Client**: Database and storage operations

### 3. Database (Supabase/PostgreSQL)
- **verifications**: Store verification results and metadata
- **attestations**: Cryptographic attestations and signatures
- **issued_certificates**: Known valid certificates database
- **institutions**: Institution public keys and metadata
- **audit_logs**: Complete audit trail

### 4. Storage (Supabase Storage)
- Certificate images (original and processed)
- Generated QR codes and PDFs
- Public verification assets

## Data Flow

### Certificate Verification Pipeline

1. **Upload**: User uploads certificate image
2. **Preprocessing**: Image enhancement and format standardization
3. **Extraction**: Donut model extracts structured fields
4. **Fusion**: Combine AI results with legacy systems and database lookups
5. **Risk Assessment**: Calculate confidence and risk scores
6. **Attestation**: Generate cryptographic proof if verified
7. **Storage**: Store results and generate public verification URL

### Risk Scoring Algorithm

```python
risk_score = (
    extraction_confidence * 0.3 +
    database_match_score * 0.4 +
    image_quality_score * 0.1 +
    field_consistency_score * 0.2
)
```

### Attestation Generation

1. Create payload with verification data and timestamp
2. Generate SHA256 hash of image and extracted fields
3. Sign payload with ECDSA private key
4. Create QR code with verification URL and signature
5. Generate PDF attestation document
6. Store in database with public verification endpoint

## Security Features

### Cryptographic Attestation
- ECDSA P-256 signatures for tamper detection
- SHA256 hashing for image integrity
- Public key infrastructure for signature verification

### Data Protection
- Image hashing to detect duplicates and tampering
- Secure API endpoints with rate limiting
- Audit logging for all operations
- GDPR-compliant data handling

### Verification Chain
```
Certificate Image → SHA256 Hash → Extracted Fields → Risk Score → Digital Signature → QR Code → Public Verification
```

## API Endpoints

### Core Verification
- `POST /upload` - Upload and verify certificate
- `POST /verify` - Verify with manual data or URL
- `GET /certificates/{id}` - Get certificate details

### Attestations
- `GET /attestations/{id}` - Get attestation details
- `POST /verify-signature` - Verify digital signature
- `GET /verify/{verification_id}` - Public verification page

### Management
- `GET /dashboard/stats` - Analytics dashboard data
- `GET /reviews` - Pending manual reviews
- `POST /reviews/decision` - Submit review decision

### Institution Management
- `POST /institutions` - Register institution
- `GET /institutions/{domain}` - Get institution by domain
- `POST /certificates/import` - Bulk import certificates

## Deployment

### Docker Compose (Development)
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### Production (Kubernetes)
- Horizontal pod autoscaling for backend services
- CDN for frontend static assets
- Managed database (Supabase) with read replicas
- Redis for caching and session management

## Monitoring and Observability

### Metrics
- Verification throughput and latency
- AI model accuracy and confidence scores
- Database query performance
- Storage usage and costs

### Logging
- Structured JSON logs with correlation IDs
- Security events and anomaly detection
- Performance metrics and error rates
- User activity and audit trails

### Alerts
- Failed verifications above threshold
- High-risk certificate patterns
- System performance degradation
- Security breach indicators

## Scalability Considerations

### Horizontal Scaling
- Stateless backend services
- Database connection pooling
- Distributed file storage
- Load balancing with health checks

### Performance Optimization
- Image preprocessing pipeline optimization
- Model inference caching
- Database query optimization with indexes
- CDN for static assets and public verification pages

### Cost Management
- AI model inference optimization
- Storage lifecycle policies
- Database query optimization
- Monitoring and alerting for cost anomalies
