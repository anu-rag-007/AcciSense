# AcciSense – Current System Specification

## Version
Prototype v1.0

## Core Purpose
AcciSense detects or receives an abnormal incident and initiates
a closed-loop emergency response workflow.

The system:
1. Creates an incident.
2. Sends an alert to a responder.
3. Requires acknowledgement.
4. Tracks the acknowledgement.
5. Escalates if no acknowledgement is received.

---

# COMPONENTS

## 1. Backend

Responsibilities:
- Create incident
- Generate incident ID
- Manage incident status
- Handle acknowledgement
- Handle escalation timeout

Main endpoints:
- [Add your endpoints here]

---

## 2. n8n – Alert Workflow

Workflow name:
AcciSense_alert

Flow:

Create Incident
↓
Send Alert
↓
Supabase Create Row
↓
Send Confirmation / Log

---

## 3. Telegram

Purpose:
Send incident alerts to responders.

Alert format:

🚨 ACCISENSE ALERT

Severity: HIGH

Alert ID: AC-XXXXXXXX

Please acknowledge this alert.

[ ✅ ACK ]

Callback data format:

ack:AC-XXXXXXXX

---

## 4. Supabase

Table:
cards

Columns:

| Column | Purpose |
|---|---|
| id | Database primary ID |
| message_id | Telegram alert message ID |
| acci_id | AcciSense incident ID |
| status | Current incident status |
| acknowledged_at | ACK timestamp |

---

## 5. ACK Workflow

Flow:

Telegram Callback
↓
Extract AcciSense ID
↓
Acknowledge Incident
↓
Get many rows
↓
Update Telegram Message
↓
Update Supabase

Supabase update condition:

acci_id =
{{ $('Extract AcciSense ID').first().json.acci_id }}

Updated fields:

status = ACKNOWLEDGED

acknowledged_at = {{ $now }}


# 1. Backend — AcciSense API

## Technology
- FastAPI
- Python
- Supabase Python Client

## Purpose

The AcciSense backend acts as the core incident gateway.

It is responsible for:

1. Creating AcciSense incident IDs.
2. Receiving incident information.
3. Managing acknowledgement requests.
4. Updating incident acknowledgement status.
5. Retrieving incident records from Supabase.

---

# API Endpoints

## 1. Create Incident

Method:

POST

Endpoint:

/incident

### Request Body

{
  "incident_type": "string",
  "location": "string",
  "severity_indicator": "string"
}

### Response

{
  "incident_id": "AC-XXXXXXXX",
  "incident_type": "string",
  "location": "string",
  "severity_indicator": "string",
  "status": "OPEN",
  "created_at": "timestamp"
}

The backend generates a unique AcciSense incident ID in the format:

AC-XXXXXXXX

---

## 2. Acknowledge Incident

Method:

POST

Endpoint:

/incident/{incident_id}/acknowledge

Example:

POST /incident/AC-CB31585D/acknowledge

### Function

When an incident is acknowledged, the backend:

1. Receives the incident ID.
2. Finds the corresponding record in the Supabase `cards` table.
3. Matches the record using:

acci_id = incident_id

4. Updates:

status = Acknowledged

acknowledged_at = current UTC timestamp

### Response

{
  "incident_id": "AC-XXXXXXXX",
  "status": "Acknowledged",
  "acknowledged_at": "timestamp"
}

If no matching incident exists, the API returns:

404 — Incident not found

---

## 3. Get All Incident Cards

Method:

GET

Endpoint:

/cards

### Function

Retrieves all records from the Supabase `cards` table.

---

## 4. Root Diagnostic

Method:

GET

Endpoint:

/

### Response

{
  "system_status": "ONLINE",
  "service": "AcciSense Core Gateway Engine"
}