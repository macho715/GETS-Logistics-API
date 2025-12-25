# GETS Logistics API

[![Production Status](https://img.shields.io/badge/status-production-green)](https://gets-logistics-api.vercel.app)
[![API Version](https://img.shields.io/badge/version-1.7.0-blue)](https://gets-logistics-api.vercel.app)
[![Schema Version](https://img.shields.io/badge/schema-2025--12--25-orange)](https://gets-logistics-api.vercel.app/health)
[![Uptime](https://img.shields.io/badge/uptime-100%25-success)](https://gets-logistics-api.vercel.app/health)

**RESTful API for HVDC Project Logistics Management**

Real-time shipment tracking, approval monitoring, and bottleneck analysis powered by Airtable with ChatGPT Actions integration.

🌐 **Production**: https://gets-logistics-api.vercel.app
📊 **Health Check**: https://gets-logistics-api.vercel.app/health
📚 **Full Documentation**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## ✨ Key Features

- 🔄 **Real-time Airtable Integration** - Direct API connection with 5 RPS rate limiting
- 🔒 **Schema Lock System** - Immutable table IDs and protected fields (20 fields)
- 🚀 **Serverless Architecture** - Vercel Edge Network with global CDN
- 🤖 **ChatGPT Actions Ready** - OpenAPI 3.1 schema for Custom GPT integration
- 📊 **Comprehensive Monitoring** - SLA tracking, bottleneck analysis, KPI dashboards
- 🛡️ **Zero-Downtime Deployment** - Deploy preflight validation with schema versioning
- ⚡ **High Performance** - <2s response time, 99.9% uptime

---

## 🚀 Quick Start

### 1. Test the API

```bash
# Health check
curl https://gets-logistics-api.vercel.app/health

# Get approval summary
curl https://gets-logistics-api.vercel.app/approval/summary

# Get shipment status
curl https://gets-logistics-api.vercel.app/document/status/SCT-0143
```

### 2. For ChatGPT Integration

1. Open ChatGPT → Create Custom GPT
2. Go to Actions → Import from URL
3. Use: `https://gets-logistics-api.vercel.app/openapi.yaml`
4. Set Authentication: None
5. Test and publish

---

## 📋 API Endpoints

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/` | GET | API info & capabilities | [Try it](https://gets-logistics-api.vercel.app/) |
| `/health` | GET | System health & schema validation | [Try it](https://gets-logistics-api.vercel.app/health) |
| `/status/summary` | GET | Global shipment KPIs | [Try it](https://gets-logistics-api.vercel.app/status/summary) |
| `/approval/summary` | GET | Approval statistics with SLA tracking | [Try it](https://gets-logistics-api.vercel.app/approval/summary) |
| `/bottleneck/summary` | GET | Bottleneck analysis & aging | [Try it](https://gets-logistics-api.vercel.app/bottleneck/summary) |
| `/document/status/{shptNo}` | GET | Document status for shipment | Example: `/document/status/SCT-0143` |
| `/approval/status/{shptNo}` | GET | Approval status for shipment | Example: `/approval/status/SCT-0143` |
| `/document/events/{shptNo}` | GET | Event history for shipment | Example: `/document/events/SCT-0143` |
| `/record/{id}` | GET | Get record by Airtable ID | Example: `/record/recXXXX` |

**All endpoints return JSON** with `schemaVersion` and `timestamp` in Asia/Dubai timezone (+04:00).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Client Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ ChatGPT  │  │Dashboard │  │ Operations Bots │  │
│  └────┬─────┘  └────┬─────┘  └────────┬────────┘  │
└───────┼─────────────┼──────────────────┼───────────┘
        │             │                  │
        └─────────────┼──────────────────┘
                      │
            ┌─────────▼──────────┐
            │  Vercel Edge CDN   │
            │   (Global Network) │
            └─────────┬──────────┘
                      │
        ┌─────────────▼─────────────┐
        │   Flask API (Serverless)  │
        │  ┌───────────────────┐    │
        │  │ api/app.py        │    │
        │  ├───────────────────┤    │
        │  │ AirtableClient    │    │
        │  │ SchemaValidator   │    │
        │  │ Monitoring        │    │
        │  └───────────────────┘    │
        └─────────────┬─────────────┘
                      │
            ┌─────────▼──────────┐
            │   Airtable Base    │
            │  (SSOT - 10 Tables)│
            └────────────────────┘
```

### Core Components

- **API Layer**: Flask 3.0.0 on Python 3.11
- **Data Source**: Airtable (10 tables, 20 protected fields)
- **Platform**: Vercel Serverless Functions
- **Schema Lock**: Version `2025-12-25T00:32:52+0400`
- **Rate Limiting**: 5 requests/second per base
- **Timezone**: Asia/Dubai (+04:00)

---

## 🔧 Development Setup

### Prerequisites

- Python 3.11+
- Git
- Airtable Personal Access Token

### Local Installation

```bash
# Clone repository
git clone https://github.com/macho715/GETS-Logistics-API.git
cd GETS-Logistics-API

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export AIRTABLE_API_TOKEN="your_token_here"

# Run locally
flask --app api.app run --port 8000
```

### Testing

```bash
# Run all tests
pytest -q

# Run with coverage
pytest --cov=api --cov-report=term-missing

# Check test coverage (target ≥80%)
pytest --cov=api --cov-report=html
```

### Code Quality

```bash
# Format code
black . && isort .

# Lint code
ruff check .

# Type checking
mypy api/
```

---

## 🚢 Deployment

### Vercel Deployment (Recommended)

**⚠️ IMPORTANT: Always run preflight before deploying!**

```bash
# 1. Set production URL
export PROD_URL="https://gets-logistics-api.vercel.app"

# 2. Run deploy preflight
chmod +x scripts/deploy_preflight.sh
./scripts/deploy_preflight.sh

# 3. Deploy only if preflight passes
git push origin main  # Auto-deploys via GitHub integration
```

### Deploy Preflight Checks

The preflight script validates:
- ✅ `/health` endpoint returns HTTP 200
- ✅ `schemaVersion` matches `2025-12-25T00:32:52+0400`
- ✅ PROD_URL is valid HTTPS URL

**If preflight fails**: STOP. Do not deploy until issues are resolved.

### Manual Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy to production
vercel --prod
```

### Environment Variables (Vercel)

Set these in Vercel Dashboard → Project Settings → Environment Variables:

```
AIRTABLE_API_TOKEN=your_personal_access_token
```

---

## 📊 Example Responses

### GET /health

```json
{
  "status": "healthy",
  "version": "1.7.0",
  "timestamp": "2025-12-25T20:48:26.110153+04:00",
  "lockedConfig": {
    "schemaVersion": "2025-12-25T00:32:52+0400",
    "tablesLocked": 10,
    "protectedFields": 20,
    "versionMatch": true,
    "schemaGaps": ["evidence_links", "event_key", "incoterm_hs"]
  },
  "airtable": {
    "connected": true,
    "baseId": "appnLz06h07aMm366",
    "tables": 10
  }
}
```

### GET /approval/summary

```json
{
  "summary": {
    "total": 2,
    "pending": 1,
    "approved": 1,
    "rejected": 0,
    "expired": 0
  },
  "byType": {
    "FANR": {
      "total": 1,
      "pending": 1,
      "approved": 0
    },
    "COMMERCIAL": {
      "total": 1,
      "pending": 0,
      "approved": 1
    }
  },
  "critical": {
    "overdue": 1,
    "d5": 0,
    "d15": 0
  },
  "schemaVersion": "2025-12-25T00:32:52+0400",
  "timestamp": "2025-12-25T20:48:39.574475+04:00"
}
```

### GET /document/status/{shptNo}

```json
{
  "shptNo": "SCT-0143",
  "doc": {
    "boeStatus": "SUBMITTED",
    "doStatus": "NOT_STARTED",
    "cooStatus": "UNKNOWN",
    "hblStatus": "UNKNOWN",
    "ciplStatus": "UNKNOWN"
  },
  "bottleneck": {
    "code": "NONE",
    "since": null,
    "riskLevel": "LOW"
  },
  "action": {
    "nextAction": "FANR 승인 상태 확인 및 가속 요청",
    "owner": "Customs/Compliance",
    "dueAt": "2025-12-25T12:00:00+04:00"
  },
  "meta": {
    "lastUpdated": "2025-12-25T20:48:51.707984+04:00",
    "dataLagMinutes": 1208
  }
}
```

---

## 🎯 Schema Lock System

### Protected Fields (20 fields - Rename Forbidden)

These field names are used in `filterByFormula` queries and **must not be renamed**:

**Shipments (7 fields):**
- `shptNo`, `currentBottleneckCode`, `bottleneckSince`, `riskLevel`
- `nextAction`, `actionOwner`, `dueAt`

**Documents (3 fields):**
- `shptNo`, `docType`, `status`

**Actions (6 fields):**
- `shptNo`, `status`, `priority`, `dueAt`, `actionText`, `owner`

**Events (4 fields):**
- `timestamp`, `shptNo`, `entityType`, `toStatus`

### Schema Version

**Current**: `2025-12-25T00:32:52+0400`

All API responses include `schemaVersion` for drift detection. If schema changes, regenerate lock file:

```bash
cd HVDC_Airtable_LockAndMappingGenPack_2025-12-24
python lock_schema_and_generate_mapping.py
```

---

## 🛡️ Cursor Rules Pack Integration

This project uses **cursor_only_pack_gets_v1** for development governance:

- 🛡️ **ZERO Fail-safe** - Prevents blind deployments
- 📋 **TDD Workflow** - RED → GREEN → REFACTOR
- 🔍 **Quality Gates** - Coverage ≥85%, Lint 0 warnings
- 🔐 **Security Scanning** - bandit + pip-audit

### Quick Commands

```bash
# Initialize pre-commit hooks
python tools/init_settings.py --precommit

# Run deploy preflight
./scripts/deploy_preflight.sh

# Run tests
pytest -q

# Run linters
ruff check . && black --check . && isort --check-only .
```

---

## 📈 Performance Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Response Time** | <3s | ~1-2s | ✅ |
| **Uptime** | 99.9% | 100% | ✅ |
| **Error Rate** | <1% | 0% | ✅ |
| **Success Rate** | ≥95% | 100% | ✅ |
| **Airtable Rate Limit** | 5 RPS | Compliant | ✅ |
| **Schema Validation** | 100% | 100% | ✅ |

**Last Performance Test**: 2025-12-25 20:49:33
**All 9 endpoints operational**: ✅

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Schema Version Mismatch

```bash
⚠️ WARNING: Schema version mismatch detected!
```

**Solution**: Regenerate `airtable_locked_config.py` using the schema generator.

#### 2. Airtable 422 UNKNOWN_FIELD_NAME

**Cause**: Field name doesn't exist in Airtable
**Solution**: Verify field names in `airtable_schema.lock.json`

#### 3. Rate Limiting (429 Too Many Requests)

**Cause**: Exceeded 5 requests/second limit
**Solution**: API automatically retries with 30s backoff. No action needed.

#### 4. Vercel Cache Issues

If seeing stale code after deployment:

```bash
# Force cache clear
git commit --allow-empty -m "chore: force Vercel cache clear"
git push origin main
```

---

## 📚 Documentation

### Core Documents

- **[AGENTS.md](AGENTS.md)** - Cursor Agent operating rules & deployment guidelines
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture with diagrams
- **[CHATGPT_SCHEMA_GUIDE.md](CHATGPT_SCHEMA_GUIDE.md)** - ChatGPT Actions integration guide
- **[VERCEL_DEPLOYMENT_GUIDE.md](VERCEL_DEPLOYMENT_GUIDE.md)** - Detailed deployment instructions

### Phase Documentation

- `PHASE_2_1_IMPLEMENTATION.md` - AirtableClient implementation
- `PHASE_2_2_IMPLEMENTATION.md` - SchemaValidator implementation
- `PHASE_2_3_IMPLEMENTATION.md` - Locked Mapping integration

---

## 🔮 Roadmap

### Phase 2.4 (Next - Q1 2026)
- [ ] Add Evidence link fields to Documents/Approvals/Actions/Events
- [ ] Add Incoterm and HS code fields to Shipments
- [ ] Implement BOE RED auto-detection rules
- [ ] Real-time WebSocket notifications

### Phase 3.0 (Q2 2026)
- [ ] GraphQL API layer
- [ ] Advanced analytics dashboard
- [ ] ML-based bottleneck prediction
- [ ] Multi-language support (EN/KO/AR)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Run tests (`pytest -q`)
4. Run linters (`ruff check . && black --check .`)
5. Commit changes (`git commit -m 'feat: Add AmazingFeature'`)
6. Push to branch (`git push origin feature/AmazingFeature`)
7. Open Pull Request

**Commit Convention**: [Conventional Commits](https://www.conventionalcommits.org/)
**Code Style**: Black + Ruff + isort

---

## 📄 License

This project is proprietary and confidential.
© 2025 HVDC Project Logistics Team. All rights reserved.

---

## 📞 Support & Contact

- **GitHub Issues**: [Report a bug](https://github.com/macho715/GETS-Logistics-API/issues)
- **Production API**: https://gets-logistics-api.vercel.app
- **Vercel Dashboard**: https://vercel.com/chas-projects-08028e73/gets-api
- **API Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🏆 Acknowledgments

- **Platform**: Vercel Edge Network
- **Data Source**: Airtable
- **Framework**: Flask
- **AI Integration**: OpenAI ChatGPT Actions

---

**Built with ❤️ for HVDC Project Logistics**

**Last Updated**: 2025-12-25
**Status**: ✅ Production Ready
**Version**: 1.7.0
