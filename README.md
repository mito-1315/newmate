# Certificate Verifier

An AI-powered certificate verification system that combines document understanding with cryptographic attestation for secure, scalable academic credential verification.

## 🚀 Features

- **AI-Powered Extraction**: Uses Donut model for intelligent field extraction from certificate images
- **Fusion Engine**: Combines multiple verification methods (AI + legacy + database matching)
- **Cryptographic Attestation**: ECDSA signatures and QR codes for tamper-proof verification
- **Risk Scoring**: Multi-factor risk assessment with confidence metrics
- **Manual Review**: Human-in-the-loop verification for edge cases
- **Institution Management**: Support for multiple institutions with public key infrastructure
- **Real-time Dashboard**: Analytics and monitoring for verification operations
- **Supabase Integration**: Modern backend with PostgreSQL and real-time features

## 🏗️ Architecture

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

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Supabase account (free tier available)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/certificate-verifier.git
cd certificate-verifier
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Database
DATABASE_URL=postgresql://postgres:[password]@db.supabase.co:5432/postgres

# AI Services (Optional)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Security
SECRET_KEY=your_secret_key_here

# Storage
STORAGE_BUCKET=certificates
MAX_FILE_SIZE=10485760

# Development
DEBUG=true
```

### 3. Supabase Setup

1. Create a new Supabase project
2. Run the database schema from `docs/database_schema.md`
3. Set up storage bucket named "certificates"
4. Configure RLS policies as documented

### 4. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 5. Development Setup (Alternative)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

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

### Week 2-3: AI Integration
- [ ] Prepare dataset (200-500 labeled images)
- [ ] Fine-tune Donut model for certificate extraction
- [ ] Deploy extraction microservice
- [ ] Integration with Supabase storage

### Week 4: Attestation System
- [ ] Generate ECDSA key pairs
- [ ] Implement digital signatures
- [ ] QR code generation and verification
- [ ] PDF attestation generation

### Week 5: Fusion Engine
- [ ] Combine Donut + legacy model outputs
- [ ] Database matching algorithm
- [ ] Risk scoring implementation
- [ ] Fusion endpoint deployment

### Week 6: Manual Review
- [ ] Review queue UI implementation
- [ ] Reviewer workflow
- [ ] Field correction interface
- [ ] Attestation PDF generation

### Week 7: Institution Onboarding
- [ ] CSV import functionality
- [ ] Institution public key management
- [ ] Multi-tenant support
- [ ] Bulk certificate upload

### Week 8: Production Deployment
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Security audit
- [ ] Docker/K8s deployment

## 🔒 Security Features

- **Cryptographic Attestation**: ECDSA P-256 signatures
- **Image Integrity**: SHA256 hashing and perceptual hashing
- **Audit Trail**: Complete operation logging
- **Rate Limiting**: API endpoint protection
- **Row Level Security**: Multi-tenant data isolation

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
