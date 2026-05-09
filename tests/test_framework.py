"""
tests/test_framework.py — Unit and integration tests.

Run with:  python -m pytest tests/ -v
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from validators.status_validator  import validate_status, get_status_category, is_success
from validators.schema_validator  import validate_schema, validate_required_fields, validate_headers
from validators.latency_validator import validate_latency, classify_latency, summarise_latencies
from validators.payload_validator import validate_payload, compare_payloads


# ── Status Validator Tests ─────────────────────────────────────────────────────

class TestStatusValidator:
    def test_matching_status_passes(self):
        r = validate_status("ep1","Test",200,200)
        assert r.passed is True

    def test_mismatched_status_fails(self):
        r = validate_status("ep1","Test",200,404)
        assert r.passed is False
        assert "404" in r.message

    def test_expected_404_passes(self):
        r = validate_status("ep2","Not Found",404,404)
        assert r.passed is True

    def test_expected_500_passes(self):
        r = validate_status("ep3","Server Error",500,500)
        assert r.passed is True

    def test_status_category_2xx(self):
        assert "2xx" in get_status_category(200)

    def test_status_category_4xx(self):
        assert "4xx" in get_status_category(404)

    def test_status_category_5xx(self):
        assert "5xx" in get_status_category(500)

    def test_is_success_true(self):
        assert is_success(200) is True
        assert is_success(201) is True

    def test_is_success_false(self):
        assert is_success(404) is False
        assert is_success(500) is False


# ── Schema Validator Tests ─────────────────────────────────────────────────────

class TestSchemaValidator:
    def test_valid_schema_passes(self):
        body   = {"name": "Sandrine", "age": 28, "active": True}
        schema = {"name": "string", "age": "integer", "active": "boolean"}
        r = validate_schema("ep1","Test",body,schema)
        assert r.passed is True
        assert len(r.errors) == 0

    def test_missing_field_fails(self):
        body   = {"name": "Sandrine"}
        schema = {"name": "string", "email": "string"}
        r = validate_schema("ep1","Test",body,schema)
        assert r.passed is False
        assert any("email" in e for e in r.errors)

    def test_wrong_type_fails(self):
        body   = {"age": "not-a-number"}
        schema = {"age": "integer"}
        r = validate_schema("ep1","Test",body,schema)
        assert r.passed is False

    def test_non_dict_body_fails(self):
        r = validate_schema("ep1","Test", ["list","not","dict"], {"key":"string"})
        assert r.passed is False

    def test_empty_schema_passes(self):
        r = validate_schema("ep1","Test",{"any":"data"},{})
        assert r.passed is True

    def test_required_fields_pass(self):
        body   = {"id": 1, "name": "Test", "status": "active"}
        fields = ["id", "name", "status"]
        r = validate_required_fields("ep1","Test",body,fields)
        assert r.passed is True

    def test_missing_required_field_fails(self):
        body   = {"id": 1}
        fields = ["id", "name"]
        r = validate_required_fields("ep1","Test",body,fields)
        assert r.passed is False
        assert any("name" in e for e in r.errors)

    def test_header_validation_pass(self):
        headers  = {"Content-Type": "application/json", "X-Request-Id": "abc123"}
        expected = {"Content-Type": "application/json"}
        r = validate_headers("ep1","Test",headers,expected)
        assert r.passed is True

    def test_missing_header_fails(self):
        headers  = {"Content-Type": "application/json"}
        expected = {"Authorization": "Bearer token"}
        r = validate_headers("ep1","Test",headers,expected)
        assert r.passed is False


# ── Latency Validator Tests ────────────────────────────────────────────────────

class TestLatencyValidator:
    def test_fast_response_passes(self):
        r = validate_latency("ep1","Test",150,2000)
        assert r.passed is True
        assert r.tier in ("excellent","good","acceptable")

    def test_slow_response_fails(self):
        r = validate_latency("ep1","Test",3000,2000)
        assert r.passed is False

    def test_exactly_at_threshold_passes(self):
        r = validate_latency("ep1","Test",2000,2000)
        assert r.passed is True

    def test_latency_classification(self):
        assert classify_latency(50)   == "excellent"
        assert classify_latency(200)  == "good"
        assert classify_latency(500)  == "acceptable"
        assert classify_latency(2000) == "slow"
        assert classify_latency(5000) == "critical"

    def test_summarise_latencies(self):
        results = [
            validate_latency("e1","A",100,2000),
            validate_latency("e2","B",200,2000),
            validate_latency("e3","C",300,2000),
        ]
        s = summarise_latencies(results)
        assert s["count"]  == 3
        assert s["min_ms"] == 100
        assert s["max_ms"] == 300
        assert s["avg_ms"] == 200.0
        assert s["passed"] == 3


# ── Payload Validator Tests ────────────────────────────────────────────────────

class TestPayloadValidator:
    def test_valid_payload_passes(self):
        body = {"id": 1, "name": "Sandrine", "active": True}
        r = validate_payload("ep1","Test",body)
        assert r.passed is True
        assert r.payload_size_bytes > 0

    def test_null_fields_flagged(self):
        body = {"id": 1, "name": None}
        r = validate_payload("ep1","Test",body,check_nulls=True)
        assert r.passed is False
        assert any("name" in i for i in r.issues)

    def test_empty_string_flagged(self):
        body = {"name": "   ", "email": ""}
        r = validate_payload("ep1","Test",body,check_empty=True)
        assert r.passed is False

    def test_empty_array_flagged(self):
        r = validate_payload("ep1","Test",[])
        assert r.passed is False

    def test_payload_comparison_match(self):
        a = {"id": 1, "name": "Sandrine"}
        b = {"id": 1, "name": "Sandrine"}
        result = compare_payloads(a, b)
        assert result["match"] is True

    def test_payload_comparison_mismatch(self):
        a = {"id": 1, "name": "Sandrine"}
        b = {"id": 2, "name": "Sandrine"}
        result = compare_payloads(a, b)
        assert result["match"] is False
        assert len(result["differences"]) > 0

    def test_payload_comparison_ignore_keys(self):
        a = {"id": 1, "timestamp": "2026-01-01"}
        b = {"id": 1, "timestamp": "2026-06-01"}
        result = compare_payloads(a, b, ignore_keys=["timestamp"])
        assert result["match"] is True


# ── Flask API Tests ────────────────────────────────────────────────────────────

class TestFlaskAPI:
    @pytest.fixture
    def client(self):
        from app import app
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_index_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_health_endpoint(self, client):
        r    = client.get("/health")
        data = r.get_json()
        assert r.status_code == 200
        assert data["status"] == "healthy"

    def test_config_endpoint(self, client):
        r    = client.get("/api/config")
        data = r.get_json()
        assert r.status_code == 200
        assert "endpoints" in data
        assert "base_url" in data

    def test_tags_endpoint(self, client):
        r    = client.get("/api/tags")
        data = r.get_json()
        assert r.status_code == 200
        assert isinstance(data, list)

    def test_run_endpoint_missing_url(self, client):
        r = client.post("/api/run/endpoint", json={})
        assert r.status_code == 400

    def test_postman_export(self, client):
        r = client.get("/api/export/postman")
        assert r.status_code == 200
        assert r.content_type == "application/json"
        data = json.loads(r.data)
        assert "info" in data
        assert "item" in data
