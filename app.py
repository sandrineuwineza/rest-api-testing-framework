"""
app.py — REST API Testing Framework — Flask Web Application

Provides a modern web dashboard and REST API for running
API tests, viewing results, and exporting Postman collections.

Author: Sandrine Uwineza
"""

import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, Response

from runner    import run_suite, run_endpoint
from exporters.postman_exporter import export_postman_collection
from reports.report_generator   import generate_markdown_report, generate_json_report

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Load default config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "endpoints.json")

def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


# ── Web Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status":    "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service":   "rest-api-testing-framework",
        "version":   "1.0.0"
    })


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def api_config():
    """Return the current endpoint configuration."""
    config = load_config()
    return jsonify(config)


@app.route("/api/run", methods=["POST"])
def api_run():
    """
    Run the full test suite or a filtered subset.

    Body (optional):
    {
        "tag": "smoke",
        "endpoint_ids": ["get_basic", "post_json"],
        "base_url": "https://custom-api.com"
    }
    """
    data        = request.get_json(silent=True) or {}
    config      = load_config()

    # Allow custom base_url override
    if "base_url" in data:
        config["base_url"] = data["base_url"]

    tag          = data.get("tag")
    endpoint_ids = data.get("endpoint_ids")

    suite = run_suite(config, tag=tag, endpoint_ids=endpoint_ids)
    report = generate_json_report(suite)
    return jsonify(report)


@app.route("/api/run/endpoint", methods=["POST"])
def api_run_single():
    """
    Run a single custom endpoint test.

    Body:
    {
        "url": "https://api.example.com/users",
        "method": "GET",
        "expected_status": 200,
        "latency_threshold_ms": 2000,
        "headers": {},
        "body": {}
    }
    """
    data = request.get_json(silent=True) or {}

    url    = data.get("url", "").strip()
    method = data.get("method", "GET").upper()

    if not url:
        return jsonify({"error": "url is required"}), 400

    # Build endpoint config from request
    from urllib.parse import urlparse
    parsed   = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    path     = parsed.path + (f"?{parsed.query}" if parsed.query else "")

    endpoint = {
        "id":                   "custom",
        "name":                 f"{method} {url}",
        "method":               method,
        "path":                 path,
        "expected_status":      data.get("expected_status",      200),
        "latency_threshold_ms": data.get("latency_threshold_ms", 2000),
        "headers":              data.get("headers",              {}),
        "body":                 data.get("body"),
        "expected_schema":      data.get("expected_schema",      {}),
        "expected_fields":      data.get("expected_fields",      []),
        "tags":                 ["custom"],
    }

    config  = load_config()
    result  = run_endpoint(endpoint, base_url, config.get("default_headers", {}), 10)

    return jsonify({
        "endpoint_id":  result.endpoint_id,
        "endpoint_name":result.endpoint_name,
        "method":       result.method,
        "url":          result.url,
        "passed":       result.passed,
        "error":        result.error,
        "summary":      result.summary,
        "checks": {
            "status": {
                "passed":   result.status.passed           if result.status   else None,
                "expected": result.status.expected_status  if result.status   else None,
                "actual":   result.status.actual_status    if result.status   else None,
                "message":  result.status.message          if result.status   else None,
            } if result.status else None,
            "latency": {
                "passed":       result.latency.passed      if result.latency else None,
                "latency_ms":   result.latency.latency_ms  if result.latency else None,
                "threshold_ms": result.latency.threshold_ms if result.latency else None,
                "tier":         result.latency.tier         if result.latency else None,
                "message":      result.latency.message      if result.latency else None,
            } if result.latency else None,
            "schema": {
                "passed":  result.schema.passed  if result.schema else None,
                "errors":  result.schema.errors  if result.schema else [],
                "message": result.schema.message if result.schema else None,
            } if result.schema else None,
            "payload": {
                "passed":     result.payload.passed            if result.payload else None,
                "size_bytes": result.payload.payload_size_bytes if result.payload else None,
                "issues":     result.payload.issues            if result.payload else [],
                "message":    result.payload.message           if result.payload else None,
            } if result.payload else None,
        }
    })


@app.route("/api/export/postman", methods=["GET"])
def api_export_postman():
    """Download the endpoint config as a Postman Collection v2.1 JSON."""
    config     = load_config()
    collection = export_postman_collection(config)
    filename   = f"postman_collection_{datetime.now().strftime('%Y%m%d')}.json"
    return Response(
        json.dumps(collection, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/api/report/markdown", methods=["POST"])
def api_report_markdown():
    """Run the test suite and return a Markdown report."""
    data   = request.get_json(silent=True) or {}
    config = load_config()
    suite  = run_suite(config, tag=data.get("tag"))
    report = generate_markdown_report(suite, analyst=data.get("analyst", "Sandrine Uwineza"))

    filename = f"api_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    return Response(
        report,
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/api/tags", methods=["GET"])
def api_tags():
    """Return all available tags from the configuration."""
    config = load_config()
    tags   = set()
    for ep in config.get("endpoints", []):
        tags.update(ep.get("tags", []))
    return jsonify(sorted(list(tags)))


if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
