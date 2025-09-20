# 3-Layer Certificate Verification Architecture

## Executive Summary

This document describes the comprehensive 3-layer verification pipeline + fusion/decision engine + human review system, hardened with forensic checks and integrity controls for certificate authentication.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced Fusion Engine                      │
│            Conservative Decision + Human Review                 │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│   Layer 1   │   Layer 2   │   Layer 3   │    QR Integrity       │
│ Extraction  │  Forensics  │ Signatures  │     Controls          │
└─────────────┴─────────────┴─────────────┴───────────────────────┘
```

## Layer 1: Field Extraction (image → structured JSON)

### Primary: Donut Fine-tuned Model
- **Output**: Canonical JSON schema for certificates
- **Fields**: name, roll_no, cert_no, course, year, grade, photo_bbox, qr_payload
- **Confidence**: Per-field confidence scores
- **Fallback**: Automatic OCR ensemble if confidence < 70%

### Fallback: Multi-OCR Ensemble
- **PaddleOCR**: Advanced deep learning OCR with angle correction
- **Tesseract**: Traditional OCR with custom configuration
- **Rule Engine**: Regex patterns for field extraction
- **Fusion**: Intelligent selection based on confidence scores

### Optional: VLM Fallback
- **BLIP-2/LLaVA**: Vision-Language Model for ambiguous cases
- **Usage**: When OCR confidence < 60%
- **Output**: Enhanced field extraction using natural language understanding

### Implementation Details
```python
class Layer1ExtractionService:
    async def extract_fields(self, image: Image.Image) -> ExtractedFields:
        # Step 1: Try Donut primary extraction
        donut_result = await self._extract_with_donut(image)
        
        if self._is_extraction_confident(donut_result):
            return donut_result
        
        # Step 2: OCR ensemble fallback
        ocr_result = await self._extract_with_ocr_ensemble(image)
        fused_result = self._fuse_extraction_results(donut_result, ocr_result)
        
        if self._is_extraction_confident(fused_result):
            return fused_result
        
        # Step 3: VLM extreme fallback
        return await self._extract_with_vlm(image, fused_result)
```

## Layer 2: Image Forensics (tamper detection)

### Global Detectors
- **Copy-Move Detection**: SIFT/ORB feature matching for duplicated regions
- **Error Level Analysis (ELA)**: JPEG compression inconsistencies
- **Double Compression**: DCT coefficient analysis for re-compression
- **Noise Analysis**: PRNU/noise correlation for pasted regions

### Regional Detectors
- **Autoencoder Anomaly**: Neural network-based anomaly detection
- **Halftone/Moiré Detection**: Print/scan artifact analysis
- **Suspicious Region Mapping**: Pixel-level tamper localization

### Hash Integrity
- **SHA256**: Cryptographic hash for exact matching
- **Perceptual Hash (pHash)**: Content-based similarity
- **PRNU Fingerprinting**: Camera sensor noise analysis

### Implementation Details
```python
class Layer2ForensicsService:
    async def analyze_image(self, image: Image.Image) -> ForensicAnalysis:
        # Run all analyses in parallel
        tasks = [
            self._detect_copy_move(gray_image),
            self._error_level_analysis(image),
            self._detect_double_compression(cv_image),
            self._analyze_noise_patterns(gray_image),
            self._calculate_image_hashes(image)
        ]
        
        results = await asyncio.gather(*tasks)
        return self._combine_forensic_results(results)
```

## Layer 3: Seal & Signature Verification

### Object Detection
- **YOLOv8/Detectron2**: Trained models for seal/signature detection
- **Traditional CV**: HoughCircles, contour analysis for fallback
- **Bounding Box**: Precise localization of verification elements

### Signature Verification
- **Siamese CNN**: Few-shot signature matching
- **Template Database**: Known signature patterns
- **Similarity Scoring**: Distance-based authenticity assessment

### Seal Verification
- **Template Matching**: Institutional seal database
- **Feature Extraction**: Shape, text, and pattern analysis
- **Semi-supervised Learning**: Adaptive seal recognition

### QR Code Verification
- **Detection**: pyzbar QR code scanning
- **Signature Verification**: ECDSA/RSA signature validation
- **Issuer Verification**: Public key infrastructure

### Implementation Details
```python
class Layer3SignatureService:
    async def verify_seals_and_signatures(self, image: Image.Image) -> SignatureVerification:
        # Parallel detection
        seal_detections = await self._detect_seals(cv_image)
        signature_detections = await self._detect_signatures(cv_image)
        qr_verification = await self._detect_and_verify_qr(image)
        
        # Verification against known templates
        seal_matches = await self._verify_detected_seals(cv_image, seal_detections)
        signature_matches = await self._verify_detected_signatures(cv_image, signature_detections)
        
        return SignatureVerification(...)
```

## QR Integrity Controls

### Prevention
- **Signed QR Payloads**: ECDSA/RSA signatures for tamper detection
- **Minimal Payload**: Essential data only (id, cert_no, issued, issuer_pubkey_id)
- **Expiration**: Time-limited validity
- **Version Control**: Payload schema versioning

### Detection
- **Signature Verification**: Cryptographic validation on upload
- **Issuer Validation**: Public key infrastructure verification
- **Field Consistency**: Cross-validation with extracted fields
- **Replay Protection**: Timestamp and nonce validation

### Implementation Details
```python
class QRIntegrityService:
    async def generate_certificate_qr(self, certificate_data: Dict) -> Tuple[str, Dict]:
        payload = await self._create_qr_payload(certificate_data, institution_id)
        signed_payload = await self._sign_qr_payload(payload, institution_keys)
        qr_image = await self._generate_qr_image(signed_payload)
        return qr_image, signed_payload
    
    async def verify_qr_integrity(self, qr_data: str) -> QRIntegrityCheck:
        qr_payload = json.loads(qr_data)
        signature_valid = await self._verify_qr_signature(qr_payload)
        issuer_verified = await self._verify_issuer(qr_payload)
        return QRIntegrityCheck(...)
```

## Enhanced Fusion Engine

### Weighted Fusion
```python
fusion_weights = {
    "extraction_confidence": 0.25,    # Layer 1
    "database_match": 0.30,           # Database verification
    "forensic_score": 0.25,           # Layer 2 (inverted tamper probability)
    "signature_score": 0.15,          # Layer 3
    "qr_integrity": 0.05              # QR verification
}
```

### Conservative Decision Thresholds
```python
decision_thresholds = {
    "auto_approve": 0.85,     # High confidence auto-approval
    "manual_review": 0.60,    # Medium confidence requires review
    "auto_reject": 0.30       # Low confidence auto-rejection
}
```

### Risk Assessment
- **Tamper Detection**: Immediate rejection for high tamper probability
- **Signature Invalidity**: Rejection for failed cryptographic verification
- **Database Mismatch**: Manual review for missing records
- **Consistency Checks**: Cross-layer validation

### Implementation Details
```python
class EnhancedFusionEngine:
    async def verify_certificate(self, image_data: bytes) -> CertificateResponse:
        # Execute all layers in parallel
        layer1_result = await self.layer1_service.extract_fields(image)
        layer2_result = await self.layer2_service.analyze_image(image)
        layer3_result = await self.layer3_service.verify_seals_and_signatures(image)
        qr_result = await self.qr_service.verify_qr_integrity(qr_data)
        
        # Enhanced fusion scoring
        risk_score = await self._calculate_enhanced_risk_score(layer_results, db_check)
        
        # Conservative decision engine
        status, requires_review, rationale = self._make_verification_decision(risk_score, layer_results)
        
        return CertificateResponse(...)
```

## Institution Integration & Database

### Central PostgreSQL with RLS
- **Row Level Security**: Multi-tenant data isolation
- **Scalable Schema**: JSONB for flexible field storage
- **Audit Trail**: Immutable verification logs
- **Performance**: Indexed queries for fast lookups

### Secure APIs
- **mTLS**: Mutual TLS for institution communication
- **API Keys**: Rate-limited access tokens
- **Public Key Management**: Institution key registration
- **Bulk Import**: CSV/ERP integration endpoints

### Database Schema
```sql
-- Core verification table
CREATE TABLE verifications (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    layer_results JSONB,
    risk_score JSONB,
    requires_manual_review BOOLEAN,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Institution management
CREATE TABLE institutions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    public_key TEXT NOT NULL,
    domain TEXT UNIQUE
);

-- Known certificates database
CREATE TABLE issued_certificates (
    certificate_id TEXT,
    student_name TEXT,
    institution TEXT,
    course_name TEXT,
    issue_date DATE,
    UNIQUE(certificate_id, institution)
);
```

## Attestation & Audit

### Digital Attestation
- **PKI/eSign Provider**: Industry-standard digital signatures
- **PDF Generation**: Signed attestation documents
- **QR Linking**: Public verification endpoints
- **Blockchain Ready**: Future immutable storage

### Audit Trail
- **Signed Metadata**: Cryptographically signed logs
- **Immutable Storage**: Append-only audit records
- **Compliance**: GDPR, SOX, regulatory requirements
- **Blockchain Integration**: Optional distributed ledger

### Implementation
```python
async def _generate_enhanced_attestation(self, verification_id: str) -> AttestationData:
    payload = {
        "verification_id": verification_id,
        "risk_assessment": risk_score.dict(),
        "timestamp": datetime.utcnow().isoformat(),
        "attestation_version": "3.0"
    }
    
    qr_data_url, signed_payload = await self.qr_service.generate_certificate_qr(payload)
    attestation_id = await self.supabase_client.store_attestation(attestation_data)
    
    return AttestationData(...)
```

## Performance & Scalability

### Parallel Processing
- **Layer Execution**: All layers run concurrently
- **GPU Acceleration**: CUDA for model inference
- **Thread Pools**: CPU-bound tasks parallelization
- **Async I/O**: Non-blocking database operations

### Caching Strategy
- **Model Cache**: Keep AI models in memory
- **Result Cache**: Redis for frequent lookups
- **CDN**: Static assets and public verification pages
- **Database Optimization**: Query optimization and indexing

### Monitoring
```python
# Processing time tracking
processing_time_ms = {
    "layer1_ms": layer1_time * 1000,
    "layer2_ms": layer2_time * 1000,
    "layer3_ms": layer3_time * 1000,
    "total_ms": total_time * 1000
}
```

## Security Considerations

### Cryptographic Security
- **ECDSA P-256**: Industry-standard elliptic curve signatures
- **Key Rotation**: Regular key updates
- **Secure Storage**: Hardware security modules (HSM)
- **Perfect Forward Secrecy**: Session-based encryption

### Input Validation
- **File Type Validation**: MIME type and magic number checks
- **Size Limits**: 10MB maximum file size
- **Malware Scanning**: Virus and malware detection
- **Content Filtering**: Reject non-certificate images

### Access Control
- **RBAC**: Role-based access control
- **API Rate Limiting**: DDoS protection
- **IP Whitelisting**: Trusted institution IPs
- **Audit Logging**: Complete access trail

## Week-by-Week Implementation Plan

### Week 0-1: Infrastructure + Basic API + UI Skeleton ✅
- FastAPI skeleton with enhanced 3-layer architecture ✅
- Supabase database schema with forensics tables ✅
- React UI with layer visualization ✅
- Basic API contracts and documentation ✅

### Week 2-3: Layer 1 Implementation + Donut Fine-tuning
- [ ] Prepare labeled dataset (200-500 certificate images)
- [ ] Fine-tune Donut model for certificate schema
- [ ] Implement OCR ensemble fallback
- [ ] Deploy Layer 1 extraction service
- [ ] Integration testing with confidence thresholds

### Week 4: QR Signing + Attestation Flow
- [ ] Implement ECDSA key generation and management
- [ ] QR payload signing and verification
- [ ] Image fingerprinting (SHA256 + pHash)
- [ ] Attestation record creation
- [ ] Public verification endpoints

### Week 5: Fusion Engine + Forensic Integration
- [ ] Complete Layer 2 forensic implementation
- [ ] Layer 3 signature/seal detection training
- [ ] Enhanced fusion scoring algorithm
- [ ] Conservative decision thresholds tuning
- [ ] Integration testing across all layers

### Week 6: Manual Review UI + Attestation PDF
- [ ] Review queue with layer visualizations
- [ ] Evidence overlay (heatmaps, bounding boxes)
- [ ] Reviewer workflow and approval system
- [ ] PDF attestation generation
- [ ] QR code embedding in attestations

### Week 7: Institution Onboarding + CSV Import
- [ ] Institution key management system
- [ ] Bulk CSV import with field mapping
- [ ] API endpoints for institution integration
- [ ] Public key verification system
- [ ] Multi-tenant security implementation

### Week 8: End-to-End Testing + Deployment
- [ ] Comprehensive integration testing
- [ ] Performance optimization and load testing
- [ ] Security audit and penetration testing
- [ ] Production deployment (Docker/K8s)
- [ ] Monitoring and alerting setup

## Integration Points & Contracts

### Model Outputs
```json
{
  "layer1_extraction": {
    "name": "John Doe",
    "certificate_id": "CS2023-001234",
    "extraction_method": "donut_primary",
    "field_confidences": {"name": 0.95, "certificate_id": 0.87}
  },
  "layer2_forensics": {
    "tamper_probability": 0.15,
    "copy_move_score": 0.1,
    "ela_score": 0.2,
    "hash_match": true
  },
  "layer3_signatures": {
    "seals_detected": 1,
    "signatures_detected": 1,
    "qr_signature_valid": true
  }
}
```

### Verification API
```python
POST /api/v1/verify
{
  "file": <multipart_form_data>,
  "requester_id": "institution_id"
}

Response:
{
  "verification_id": "ver_abc123def456",
  "status": "verified",
  "layer_results": {...},
  "risk_score": {...},
  "decision_rationale": "High confidence verification",
  "attestation": {...}
}
```

### Acceptance Criteria

1. **Donut Field Extraction**: Per-field accuracy ≥ 85% on pilot dataset
2. **QR Signature Verification**: End-to-end cryptographic validation
3. **Fusion Risk Scoring**: Conservative thresholds with <5% false positives
4. **Manual Review UI**: Complete evidence presentation and workflow
5. **Performance**: <10 seconds total processing time per certificate
6. **Security**: Pass security audit and penetration testing

## Deployment Architecture

### Production Stack
```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: certificate-verifier
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: certificate-verifier:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: GPU_ENABLED
          value: "true"
```

### Monitoring & Alerting
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Sentry**: Error tracking and alerting
- **Custom Metrics**: Per-layer performance tracking

This architecture provides a robust, scalable, and secure certificate verification system with conservative decision-making and comprehensive forensic analysis.
