# Certificate Verifier

An AI-powered certificate verification system that combines document understanding with cryptographic attestation for secure, scalable academic credential verification.

## 🚀 Features

### 3-Layer Verification Pipeline
- **Layer 1 - Field Extraction**: Donut model + OCR ensemble + VLM fallback for robust field extraction
- **Layer 2 - Image Forensics**: Copy-move detection, ELA analysis, noise patterns, hash integrity
- **Layer 3 - Signature Verification**: YOLO-based seal/signature detection + Siamese CNN verification
- **QR Integrity Controls**: ECDSA-signed QR codes with cryptographic verification

### Enhanced Security & Forensics
- **Tamper Detection**: Multi-method forensic analysis for image manipulation detection
- **Conservative Decision Engine**: High-confidence thresholds with automatic escalation
- **Cryptographic Attestation**: Industry-standard digital signatures and PKI
- **Hash Integrity**: SHA256 + perceptual hashing for image authentication

### Production-Ready Features
- **Parallel Processing**: All layers execute concurrently for optimal performance
- **Manual Review Workflow**: Expert review queue with evidence visualization
- **Institution Integration**: Multi-tenant system with secure APIs and bulk import
- **Comprehensive Audit Trail**: Immutable verification logs with forensic metadata
- **Real-time Dashboard**: Layer-by-layer analytics and risk monitoring

## 🏗️ Enhanced 3-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced Fusion Engine                      │
│         Conservative Decision + Risk Assessment + Audit        │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│   Layer 1   │   Layer 2   │   Layer 3   │    QR Integrity       │
│ Extraction  │  Forensics  │ Signatures  │     Controls          │
│             │             │             │                       │
│ • Donut AI  │ • Copy-Move │ • Seal Det. │ • ECDSA Signed        │
│ • OCR       │ • ELA       │ • Sig. Ver. │ • Issuer Verify       │
│ • VLM       │ • Hashing   │ • QR Scan   │ • Field Match         │
└─────────────┴─────────────┴─────────────┴───────────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │    Supabase     │
│   (React)       │◄──►│   (FastAPI)      │◄──►│  (Database +    │
│ • Layer Views   │    │ • 3-Layer API    │    │   Storage)      │
│ • Evidence UI   │    │ • Parallel Proc  │    │ • Forensics     │
│ • Review Queue  │    │ • Conservative   │    │ • Audit Trail   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Supabase account (free tier available)

## 🚀 **Quick Start (5 Minutes)**

### 🎯 **Automated Setup (Recommended)**
```bash
# 1. Clone the repository
git clone https://github.com/your-username/certificate-verifier.git
cd certificate-verifier

# 2. Create environment files automatically
python scripts/create_env_template.py

# 3. Edit environment files with your Supabase credentials
# backend/.env and frontend/.env

# 4. Run everything with one command
python run.py
```

### ⚡ **Manual Setup (Advanced)**

**1. Environment Setup:**
```bash
# Backend environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend environment  
cd ../frontend
npm install
```

**2. Start Services:**
```bash
# Terminal 1 - Backend (from backend/ directory)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend (from frontend/ directory)
npm start
```

**3. Test Everything:**
```bash
# Run automated tests
python scripts/test_setup.py
```

### 📊 **Access Points**
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/docs

### 🔧 **Detailed Setup**
For complete setup instructions including Supabase configuration, see **[SETUP_GUIDE.md](SETUP_GUIDE.md)**

## 📚 Usage

### Upload Certificate

1. Navigate to http://localhost:3000
2. Drag & drop a certificate image or click to select
3. View extraction results and risk assessment
4. Download attestation PDF or QR code for verification

### Manual Review

1. Go to `/review` for certificates requiring manual verification
2. Review extracted fields and risk factors
3. Approve or reject with reviewer notes
4. Correct fields if necessary

### Dashboard

1. Visit `/dashboard` for analytics
2. Monitor verification statistics
3. Track institution performance
4. View system health metrics

## 🔧 API Documentation

### Core Endpoints

- `POST /upload` - Upload certificate image
- `POST /verify` - Verify with manual data
- `GET /verify/{verification_id}` - Public verification page
- `GET /attestations/{attestation_id}` - Get attestation details

### Dashboard Endpoints

- `GET /dashboard/stats` - Get analytics data
- `GET /reviews` - Get pending reviews
- `POST /reviews/decision` - Submit review decision

### Institution Management

- `POST /institutions` - Register institution
- `POST /certificates/import` - Bulk import certificates

See `docs/api_contracts.md` for complete API documentation.

## 🎯 Week-by-Week Development Plan

### Week 0-1: Foundation
- [x] Setup Supabase project and database schema
- [x] FastAPI backend with core API structure
- [x] React frontend skeleton
- [x] Basic upload and verification flow

### Week 2-3: Layer 1 Implementation + Donut Fine-tuning
- [ ] Prepare labeled dataset (200-500 certificate images)
- [ ] Fine-tune Donut model for certificate schema output
- [ ] Implement PaddleOCR + Tesseract ensemble fallback
- [ ] Deploy Layer 1 extraction service with confidence thresholds
- [ ] VLM integration for edge cases

### Week 4: QR Signing + Attestation Flow
- [ ] ECDSA key generation and secure storage
- [ ] QR payload signing with institution keys
- [ ] Image fingerprinting (SHA256 + pHash + PRNU)
- [ ] Attestation record creation with forensic metadata
- [ ] Public verification endpoints with QR scanning

### Week 5: Fusion Engine + Forensic Integration
- [ ] Complete Layer 2 forensic analysis implementation
- [ ] Layer 3 YOLO training for seal/signature detection
- [ ] Enhanced fusion scoring with conservative thresholds
- [ ] Tamper detection integration with decision engine
- [ ] Cross-layer consistency validation

### Week 6: Manual Review UI + Evidence Visualization
- [ ] Review queue with layer-by-layer evidence display
- [ ] Forensic heatmaps and suspicious region overlays
- [ ] Reviewer workflow with field correction
- [ ] Signed PDF attestation generation
- [ ] QR code embedding in attestation documents

### Week 7: Institution Onboarding + Multi-tenant Security
- [ ] Institution key management and registration
- [ ] Bulk CSV import with field mapping validation
- [ ] mTLS API endpoints for secure integration
- [ ] Public key verification and trust management
- [ ] Row-level security implementation

### Week 8: Production Deployment + Security Audit
- [ ] Comprehensive 3-layer integration testing
- [ ] Performance optimization and GPU acceleration
- [ ] Security audit and penetration testing
- [ ] Docker/Kubernetes deployment with monitoring
- [ ] Forensic evidence storage and compliance setup

## 🔒 Enhanced Security Features

- **3-Layer Forensic Analysis**: Multi-method tamper detection and evidence collection
- **Conservative Decision Engine**: High-confidence thresholds with automatic escalation
- **Cryptographic Attestation**: ECDSA P-256 signatures with PKI infrastructure
- **Image Integrity**: SHA256 + perceptual hashing + PRNU fingerprinting
- **QR Code Security**: Signed payloads with issuer verification
- **Comprehensive Audit**: Immutable forensic evidence trail
- **Multi-tenant Security**: Row-level security with institution isolation
- **API Security**: mTLS, rate limiting, and access control

## 📊 Monitoring

- Verification throughput and latency metrics
- AI model accuracy tracking
- Database performance monitoring
- Security event logging
- Cost optimization alerts

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up
```

## 🚀 Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Use production profile
docker-compose --profile production up -d

# Or deploy to Kubernetes
kubectl apply -f k8s/
```

## 📖 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Contracts](docs/api_contracts.md)
- [Database Schema](docs/database_schema.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Create an [issue](https://github.com/your-username/certificate-verifier/issues) for bug reports
- Join our [Discord](https://discord.gg/certificate-verifier) for community support
- Email: support@certificate-verifier.com

## 🙏 Acknowledgments

- [Donut](https://github.com/clovaai/donut) for document understanding
- [Supabase](https://supabase.com) for backend infrastructure
- [FastAPI](https://fastapi.tiangolo.com) for the API framework
- [React](https://reactjs.org) for the frontend framework
