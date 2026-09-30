from flask import Flask, jsonify, request
from datetime import datetime, timezone
import boto3
import uuid

app = Flask(__name__)

# Connect to DynamoDB in the same AWS region as our table
dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
table = dynamodb.Table("SecurityEvents")


@app.route("/")
def home():
    return jsonify({
        "project": "AWS Cloud Security API",
        "status": "running",
        "database": "Amazon DynamoDB",
        "message": "Cloud security service is online"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/events", methods=["POST"])
def create_event():
    data = request.get_json() or {}

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": data.get("event_type", "unknown"),
        "source_ip": data.get("source_ip", "unknown"),
        "severity": data.get("severity", "low"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    table.put_item(Item=event)

    return jsonify({
        "message": "Security event stored in DynamoDB",
        "event": event
    }), 201


@app.route("/events", methods=["GET"])
def get_events():
    response = table.scan()
    events = response.get("Items", [])

    return jsonify({
        "total_events": len(events),
        "events": events
    })


if __name__ == "__main__":
    app.run(debug=True)