# 🔌 REST API Testing Framework

> A professional Python-based REST API testing framework with a modern web dashboard — status code validation, JSON schema checking, payload integrity, latency benchmarking, and automated Postman collection export.
[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Try_It_Now-success?style=for-the-badge&logoColor=white)](https://rest-api-testing-framework.onrender.com) [![Status](https://img.shields.io/website?url=https%3A%2F%2Frest-api-testing-framework.onrender.com&label=Status&style=for-the-badge)](https://rest-api-testing-framework.onrender.com)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![Postman](https://img.shields.io/badge/Postman-Export-ff6c37?logo=postman&logoColor=white)](https://postman.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Built by **[Sandrine Uwineza](https://linkedin.com/in/sandrineuwineza)** — Technical Support Engineer · CCNA Certified · Computer Engineering BSc

---

## 🔍 What It Does

When a web application reports an issue, a Technical Support or Application Support Engineer traces the problem through the API layer. This framework automates that diagnostic workflow — running systematic validation checks against every configured endpoint and producing a structured report.

**Four validation modules run on every endpoint:**

| Module | What it validates |
|---|---|
| **Status Validator** | HTTP status code matches expected (200, 404, 500, etc.) |
| **Schema Validator** | JSON response fields exist and have correct types |
| **Latency Validator** | Response time is within defined SLA threshold |
| **Payload Validator** | No null values, empty fields, or oversized payloads |

---

## 🖥️ Web Dashboard

A modern, responsive web dashboard provides three views:

- **Run Suite** — execute all configured endpoints with tag filtering
- **Custom Test** — test any URL instantly with configurable parameters
- **Endpoints** — view all configured endpoint definitions

---

## ⚡ Quick Start

```bash
# Clone
git clone https://github.com/sandrineuwineza/rest-api-testing-framework.git
cd rest-api-testing-framework

# Virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# Install
pip install -r requirements.txt

# Run web dashboard
python app.py
```

Open **http://localhost:5000**

---

## 🗂️ Project Structure

```
rest-api-testing-framework/
├── app.py                         # Flask server + REST API
├── runner.py                      # Core test execution engine
├── requirements.txt
├── Procfile                       # Railway / Render deployment
├── render.yaml
├── railway.toml
│
├── config/
│   └── endpoints.json             # Endpoint definitions + config
│
├── validators/
│   ├── status_validator.py        # HTTP status code validation
│   ├── schema_validator.py        # JSON schema + field validation
│   ├── latency_validator.py       # Response time benchmarking
│   └── payload_validator.py      # Payload integrity checks
│
├── exporters/
│   └── postman_exporter.py       # Postman Collection v2.1 generator
│
├── reports/
│   └── report_generator.py       # Markdown + JSON report output
│
├── templates/
│   └── index.html                # Modern web dashboard
│
└── tests/
    └── test_framework.py         # 30+ unit + integration tests
```

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/api/config` | Return endpoint configuration |
| GET | `/api/tags` | List all available tags |
| POST | `/api/run` | Run full test suite |
| POST | `/api/run/endpoint` | Test a single custom endpoint |
| GET | `/api/export/postman` | Download Postman Collection |
| POST | `/api/report/markdown` | Download Markdown report |

**Example — Run full suite:**
```bash
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Example — Run smoke tests only:**
```bash
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"tag": "smoke"}'
```

**Example — Test a custom endpoint:**
```bash
curl -X POST http://localhost:5000/api/run/endpoint \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.github.com/users/sandrineuwineza",
    "method": "GET",
    "expected_status": 200,
    "latency_threshold_ms": 3000
  }'
```

---

## ⚙️ Configuring Endpoints

Edit `config/endpoints.json` to add your own API endpoints:

```json
{
  "name": "My API Test Suite",
  "base_url": "https://api.mycompany.com",
  "endpoints": [
    {
      "id": "get_users",
      "name": "GET Users List",
      "method": "GET",
      "path": "/v1/users",
      "expected_status": 200,
      "expected_schema": {
        "users": "array",
        "total": "integer"
      },
      "expected_fields": ["users", "total", "page"],
      "latency_threshold_ms": 1500,
      "tags": ["smoke", "users"]
    }
  ]
}
```

---

## 📦 Postman Collection Export

The framework auto-generates a Postman Collection v2.1 from your endpoint configuration — including pre-written test scripts for each endpoint.

```bash
# Download via API
curl http://localhost:5000/api/export/postman -o collection.json

# Or click "Export Postman" in the dashboard
```

Import the downloaded `collection.json` directly into Postman.

---

## 🧪 Running Tests

```bash
# All tests
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ -v --cov=. --cov-report=html

# Specific class
python -m pytest tests/ -v -k TestLatencyValidator
```

**Test coverage:** 30+ tests across 5 test classes covering all four validators and the Flask API.

---

## 🚀 Deployment (Free)

### Render.com (Recommended)
1. Push to GitHub
2. [render.com](https://render.com) → New → Web Service
3. Connect repo — reads `render.yaml` automatically
4. Live in ~3 minutes — free forever

### Railway
1. Push to GitHub
2. [railway.app](https://railway.app) → New Project → GitHub repo
3. Reads `railway.toml` automatically

---

## 🛠️ Skills Demonstrated

```
API Testing:      Status codes · Schema validation · Payload integrity
                  Latency benchmarking · Response header checks
Python:           Modular architecture · dataclasses · urllib
                  Concurrent test execution · pytest
Postman:          Collection v2.1 generation · Test scripts
                  Environment variables · Folder structure
Flask:            REST API design · Route handlers · JSON responses
Engineering:      Root cause analysis methodology · Error handling
                  SLA threshold management · Technical reporting
Documentation:    OpenAPI-style endpoint reference · Inline docstrings
                  Professional Markdown report generation
```

---

## 📄 License

MIT License

---

## 👤 Author

**Sandrine Uwineza** — Technical Support Engineer

🔗 [LinkedIn](https://linkedin.com/in/sandrineuwineza) · 📧 mrs.uwineza@gmail.com · 📍 Tlalnepantla de Baz, Estado de México

> *"Built from real production support experience at Opina Platform — where REST API debugging was the primary diagnostic tool for resolving incidents on a live web application serving active users."*
