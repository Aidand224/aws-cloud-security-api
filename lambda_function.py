import json
import boto3
import uuid
from collections import Counter
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("SecurityEvents")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):

    # Lambda Function URL provides request information here
    request_context = event.get("requestContext", {})
    http = request_context.get("http", {})

    method = http.get("method", "GET")
    path = event.get("rawPath", "/")

    # Home endpoint
    if method == "GET" and path == "/":
        return response(200, {
            "project": "AWS Cloud Security API",
            "status": "running",
            "database": "Amazon DynamoDB",
            "compute": "AWS Lambda",
            "message": "Cloud security service is online"
        })

    # Health endpoint
    if method == "GET" and path == "/health":
        return response(200, {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # Create security event
    if method == "POST" and path == "/events":

        try:
            body = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return response(400, {
                "error": "Invalid JSON"
            })

        event_type = body.get("event_type", "unknown")

        severity_rules = {
            "brute_force_attempt": "critical",
            "unauthorized_access": "high",
            "suspicious_login": "high",
            "failed_login": "medium"
        }

        severity = severity_rules.get(event_type, "low")

        security_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "source_ip": body.get("source_ip", "unknown"),
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        table.put_item(Item=security_event)

        return response(201, {
            "message": "Security event stored in DynamoDB",
            "event": security_event
        })

    # Retrieve security events
    if method == "GET" and path == "/events":

        result = table.scan()
        events = result.get("Items", [])

        return response(200, {
            "total_events": len(events),
            "events": events
        })

    # Security event statistics
    if method == "GET" and path == "/stats":

        result = table.scan()
        events = result.get("Items", [])

        severity_counts = Counter(
            event.get("severity", "unknown") for event in events
        )

        event_type_counts = Counter(
            event.get("event_type", "unknown") for event in events
        )

        source_ip_counts = Counter(
            event.get("source_ip", "unknown") for event in events
        )

        return response(200, {
            "total_events": len(events),
            "severity_counts": dict(severity_counts),
            "most_common_event_type":
                event_type_counts.most_common(1)[0][0]
                if event_type_counts else None,
            "most_common_source_ip":
                source_ip_counts.most_common(1)[0][0]
                if source_ip_counts else None
        })

    return response(404, {
        "error": "Route not found"
    })