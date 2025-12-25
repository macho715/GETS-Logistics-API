"""
GETS Logistics API - Streamlined for Vercel Deployment
"""
from flask import Flask, jsonify
import os

app = Flask(__name__)

# Check if Airtable is configured
AIRTABLE_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
AIRTABLE_CONFIGURED = bool(AIRTABLE_TOKEN)

@app.route("/")
def home():
    """API home endpoint"""
    return jsonify({
        "message": "GETS Logistics API - Production Ready",
        "status": "online",
        "version": "2.0.0",
        "airtable_configured": AIRTABLE_CONFIGURED,
        "endpoints": {
            "/": "API home",
            "/health": "Health check",
            "/status/summary": "Global shipment status summary",
            "/document/status/<shptNo>": "Document status for specific shipment",
            "/approval/status/<shptNo>": "Approval status for specific shipment",
            "/approval/summary": "Global approval summary with SLA tracking",
            "/bottleneck/summary": "Bottleneck analysis with aging distribution",
            "/document/events/<shptNo>": "Document event history"
        }
    })

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "airtable": {
            "configured": AIRTABLE_CONFIGURED,
            "connected": AIRTABLE_CONFIGURED  # Simplified for now
        },
        "version": "2.0.0"
    })

# Import full functionality if available
try:
    # Try absolute import for Vercel
    from api.document_status import (
        get_status_summary,
        get_document_status,
        get_approval_status_by_shpt,
        get_approval_summary,
        get_bottleneck_summary,
        get_document_events
    )
    
    # Register routes
    app.add_url_rule("/status/summary", "status_summary", get_status_summary, methods=["GET"])
    app.add_url_rule("/document/status/<shpt_no>", "document_status", get_document_status, methods=["GET"])
    app.add_url_rule("/approval/status/<shpt_no>", "approval_status", get_approval_status_by_shpt, methods=["GET"])
    app.add_url_rule("/approval/summary", "approval_summary", get_approval_summary, methods=["GET"])
    app.add_url_rule("/bottleneck/summary", "bottleneck_summary", get_bottleneck_summary, methods=["GET"])
    app.add_url_rule("/document/events/<shpt_no>", "document_events", get_document_events, methods=["GET"])
    
except ImportError as e:
    print(f"Warning: Could not import full API functionality: {e}")
    # Gracefully degrade to basic endpoints only
    
    @app.route("/status/summary")
    def status_summary_fallback():
        return jsonify({"error": "Full API not available", "message": str(e)}), 503
    
    @app.route("/document/status/<shpt_no>")
    def document_status_fallback(shpt_no):
        return jsonify({"error": "Full API not available", "shptNo": shpt_no}), 503
    
    @app.route("/approval/status/<shpt_no>")
    def approval_status_fallback(shpt_no):
        return jsonify({"error": "Full API not available", "shptNo": shpt_no}), 503
    
    @app.route("/approval/summary")
    def approval_summary_fallback():
        return jsonify({"error": "Full API not available"}), 503
    
    @app.route("/bottleneck/summary")
    def bottleneck_summary_fallback():
        return jsonify({"error": "Full API not available"}), 503
    
    @app.route("/document/events/<shpt_no>")
    def document_events_fallback(shpt_no):
        return jsonify({"error": "Full API not available", "shptNo": shpt_no}), 503

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

