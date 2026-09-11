# AcciSense 🚨

### Autonomous Emergency Response & Escalation Engine

AcciSense is an event-driven emergency response and escalation system
designed to reduce coordination delays during traffic accidents. It
combines accident-image analysis, structured incident creation, workflow
orchestration, real-time Telegram alerts, acknowledgement tracking,
escalation logic, email notifications, and automated voice calling.

## 🚀 Project Overview

Traditional emergency monitoring can suffer from fragmented accident
information, manual responder coordination, unacknowledged alerts,
delayed escalation, and weak incident-state tracking.

AcciSense addresses these problems through an automated, state-aware
dispatch pipeline.

``` text
Accident Image
      ↓
AcciSense Backend
      ↓
AI Accident Analysis
      ↓
Incident Creation
      ↓
n8n Event Orchestration
      ↓
Priority / Severity Routing
      ↓
Telegram Alert
      ↓
      ├── ACK → Incident Acknowledged
      │
      └── No ACK → Escalation
                         ↓
                    Voice Call
```

For higher-priority incidents, email notification is also dispatched.

## ✨ Features

### Accident Image Input

The dashboard accepts an accident image and sends it to:

``` text
POST /incident/from-image
```

### AI Accident Analysis

The analysis extracts structured information including:

-   Incident type
-   Severity
-   Severity score
-   Priority
-   People affected
-   Description
-   AI confidence

### FastAPI Backend

The backend acts as the AcciSense Core Gateway Engine and provides REST
APIs for incident creation, retrieval, acknowledgement, escalation,
image analysis, and dashboard data.

### n8n Automation

n8n is the event-driven orchestration layer responsible for:

1.  Receiving incidents
2.  Parsing alerts
3.  Retrieving incident state
4.  Normalizing AI triage
5.  Routing by priority
6.  Dispatching notifications
7.  Waiting for acknowledgement
8.  Checking status
9.  Escalating unacknowledged incidents
10. Triggering voice-call fallback

## 🔌 API Endpoints

  ---------------------------------------------------------------------------------------
  Endpoint                                Method                  Purpose
  --------------------------------------- ----------------------- -----------------------
  `/`                                     GET                     Backend health/status

  `/incident`                             POST                    Create an incident

  `/incident/{incident_id}`               GET                     Retrieve latest
                                                                  incident state

  `/incident/{incident_id}/acknowledge`   POST                    Acknowledge an incident

  `/incident/{incident_id}/escalate`      POST                    Escalate an
                                                                  unacknowledged incident

  `/cards`                                GET                     Retrieve incident/card
                                                                  records

  `/analyze-image`                        POST                    Analyze an accident
                                                                  image

  `/incident/from-image`                  POST                    Analyze image and
                                                                  create incident
  ---------------------------------------------------------------------------------------

## 🧠 Incident State Management

Typical lifecycle:

``` text
WAITING_FOR_ACK
       ↓
   ACKNOWLEDGED
```

or:

``` text
WAITING_FOR_ACK
       ↓
   ESCALATED
```

If an incident is already acknowledged, escalation is cancelled.

## 🎯 Priority Routing

  Severity   Priority
  ---------- ----------
  CRITICAL   P0
  HIGH       P1
  MEDIUM     P2
  LOW        P3

P0/P1 incidents use:

``` text
Telegram + Email
```

P2/P3 incidents use:

``` text
Telegram
```

## 🤖 AI Triage & Fallback

The workflow normalizes AI output into:

``` text
ai_severity
ai_priority
ai_confidence
triage_source
ai_reason
```

If AI output cannot be parsed, the workflow falls back to
severity-score/priority-based classification:

``` text
CRITICAL → P0
HIGH     → P1
MEDIUM   → P2
LOW      → P3
```

## 📱 Telegram Alerts

Telegram is the primary real-time responder notification channel.

Each alert contains an interactive ACK button. The callback data
includes the incident ID:

``` text
ack:AC-XXXXXXXX
```

This allows the acknowledgement workflow to identify the correct
incident.

## ✅ Acknowledgement Workflow

The ACK workflow follows:

``` text
Telegram ACK Button
        ↓
On ACK Button
        ↓
Parse ACK
        ↓
Acknowledge Incident
        ↓
Update Telegram
```

The callback is read from:

``` text
callback_query.data
```

and the incident ID is extracted before calling:

``` text
POST /incident/{incident_id}/acknowledge
```

The backend updates the incident to:

``` text
Acknowledged
```

and the Telegram notification is updated with the acknowledgement
confirmation.

## ⏱️ Automatic Escalation

If the responder does not acknowledge within the configured waiting
period:

``` text
WAITING_FOR_ACK
       ↓
ESCALATED
```

The escalation endpoint records the escalation timestamp and prevents
escalation if the incident has already been acknowledged.

## 📧 Email Alerts

P0 and P1 incidents also generate email notifications through n8n SMTP
email delivery.

## 📞 Voice Call Escalation

Twilio is used as an automated voice-call fallback after escalation.

The implementation was tested using a Twilio trial account. Trial
limitations mean the current implementation uses the trial-compatible
voice template rather than relying on unrestricted custom TwiML.

## 🗄️ Supabase Database

Supabase provides persistent incident storage.

Incident records include fields such as:

``` text
id
acci_id
status
acknowledged_at
escalated_at
created_at
incident_type
location
priority
severity
people_affected
latitude
longitude
severity_score
ai_confidence
event_time
description
```

## 🖥️ Dispatch Dashboard

The dark-themed web dashboard provides:

-   Accident image upload
-   Live incident feed
-   Incident creation
-   Severity and priority display
-   AI confidence
-   Incident status
-   Statistics
-   Leaflet map
-   Toast notifications
-   Live clock
-   Dispatch interface

Technologies include HTML, CSS, JavaScript, and Leaflet.

## 🌐 System Architecture

``` text
┌──────────────────────────────┐
│       AcciSense Frontend     │
│  Image Upload / Dashboard    │
│  Incident Feed / Map         │
└──────────────┬───────────────┘
               │ HTTP
               ▼
┌──────────────────────────────┐
│       FastAPI Backend        │
│ Image Analysis / Incident DB │
│ ACK / Escalation APIs        │
└───────┬───────────────┬──────┘
        │               │
        ▼               ▼
┌──────────────┐  ┌──────────────────┐
│   Supabase   │  │       n8n        │
│ Incident DB  │  │ Event Automation │
└──────────────┘  └───────┬──────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
         Telegram       Email       Twilio
          Alerts        Alerts       Voice
             │
             ▼
        ACK Workflow
             │
             ▼
       FastAPI ACK API
```

## 🐳 Local Deployment

The current development environment uses:

``` text
Windows Host
│
├── FastAPI
│   └── localhost:8000
│
└── Docker
    └── n8n
        └── localhost:5678
```

From the n8n Docker container, the FastAPI host is accessed through:

``` text
http://host.docker.internal:8000
```

n8n data is persisted using:

``` text
D:\AcciSense\n8n:/home/node/.n8n
```

## 🌍 Webhook Integration

ngrok exposes the local n8n instance for Telegram and backend-to-n8n
communication.

Example:

``` text
https://<your-ngrok-domain>/webhook/accisense-alert
```

Private webhook URLs and credentials should not be committed to GitHub.

## 🔐 Secrets

Store secrets in `.env` and keep `.env` in `.gitignore`.

Typical sensitive configuration includes:

``` env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

Other credentials may include Gemini/API credentials, Telegram bot
credentials, SMTP credentials, Twilio credentials, and ngrok
configuration.

**Never commit real secrets to the repository.**

## 🧪 End-to-End Demonstration

### Scenario 1 --- Acknowledged

``` text
Upload accident image
        ↓
AI analyzes image
        ↓
Incident created
        ↓
n8n receives incident
        ↓
Priority calculated
        ↓
Telegram alert
        ↓
Responder presses ACK
        ↓
Backend status = Acknowledged
        ↓
Telegram confirmation/update
        ↓
Escalation cancelled
```

### Scenario 2 --- Unacknowledged

``` text
Upload accident image
        ↓
AI analyzes image
        ↓
Incident created
        ↓
Telegram alert
        ↓
No ACK
        ↓
Status check
        ↓
Incident escalated
        ↓
Escalation notification
        ↓
Automated Twilio voice call
```

## 🛠️ Technologies Used

  Technology             Purpose
  ---------------------- -------------------------------------
  Python                 Backend and automation
  FastAPI                REST API / core gateway
  Supabase               Incident persistence
  n8n                    Event-driven workflow orchestration
  Telegram Bot API       Real-time alerts and ACK
  Gemini / AI analysis   Accident image understanding
  Twilio                 Voice-call escalation
  SMTP / Gmail           Email alerts
  HTML/CSS/JavaScript    Dispatch dashboard
  Leaflet                Map visualization
  Docker                 n8n deployment
  ngrok                  Public webhook exposure

## 🎯 Hackathon Objective

AcciSense transforms emergency response from a manually coordinated
process into an automated, event-driven lifecycle:

``` text
DETECT
  ↓
ANALYZE
  ↓
PRIORITIZE
  ↓
DISPATCH
  ↓
ACKNOWLEDGE
  ↓
OR ESCALATE
  ↓
AUDIT / TRACK
```

The core value is not simply sending an alert; it is managing the
incident state from detection through acknowledgement or escalation.

## 👥 Team

### RUNTIME TERROR

**HACKINDIA AI & WEB3 BUILDERS HACKATHON 2026**

## 📌 Current Project Status

### Completed

-   Accident image upload
-   AI accident analysis
-   Structured incident creation
-   FastAPI backend
-   Supabase persistence
-   n8n event orchestration
-   Severity/priority routing
-   Telegram emergency alerts
-   Interactive Telegram ACK
-   ACK backend endpoint
-   ACK workflow
-   Automatic escalation
-   Escalation state tracking
-   Email notifications
-   Twilio voice-call fallback
-   Frontend dispatch dashboard
-   Leaflet map interface
-   End-to-end pipeline testing
-   Dockerized n8n environment
-   ngrok webhook integration

The MVP has been tested across the complete flow from accident-image
input through notification, acknowledgement, escalation, and voice-call
fallback.

## ⚠️ MVP / Production Considerations

This is a hackathon MVP and should not be used as a production
emergency-dispatch system without additional engineering.

Production deployment would require secure authentication,
authorization, HTTPS, production secrets management, resilient queues,
GPS validation, retries, dead-letter handling, monitoring, rate
limiting, database policies, high availability, formal AI evaluation,
emergency-service integrations, and privacy/compliance review.

## 🔮 Future Scope

-   Real-time GPS incident coordinates
-   Multi-agency responder routing
-   Advanced computer vision
-   Dedicated responder mobile application
-   WebSocket-based dashboard updates
-   Immutable audit trails
-   Blockchain-backed incident verification
-   Multi-level escalation chains
-   Nearest-responder selection
-   Voice-based responder interaction
-   Incident analytics

## 🏁 Conclusion

AcciSense demonstrates a complete automated emergency-response pipeline:

``` text
Accident → Analysis → Priority → Alert → ACK → Resolution
                                      │
                                      └── No ACK → Escalation → Voice Call
```

The result is a working hackathon MVP focused on **speed,
accountability, state awareness, and automated escalation**.

------------------------------------------------------------------------

## Developed by Team RUNTIME TERROR

### HACKINDIA AI & WEB3 BUILDERS HACKATHON 2026
