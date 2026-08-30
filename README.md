#  AcciSense

### AI-Assisted Incident Detection, Alerting & Escalation System

AcciSense is an incident-response automation system designed to detect critical incidents, immediately notify responders, track acknowledgements, and automatically escalate incidents when no acknowledgement is received within the defined response window.

The current MVP uses **n8n**, **Telegram**, and an AcciSense backend/API to demonstrate the complete incident lifecycle.

---

##  Problem

In critical environments, delayed incident acknowledgement can result in delayed response and increased risk.

Traditional alert systems often:

- Notify responders but do not verify acknowledgement
- Require manual escalation
- Provide limited visibility into response status
- Make it difficult to track the complete incident lifecycle

AcciSense addresses this by connecting **incident detection → notification → acknowledgement → escalation** into one automated workflow.

---

---

## 📊 Quick Links & Assets
- **💻 Live Backend API (Swagger UI):** `http://127.0.0.1:8000/docs` *(If applicable)*
- **🎥 2-Minute Project Demonstration Video:** [Watch our Walkthrough on YouTube]
[![Youtube] (https://youtu.be/badge/Rc4Uodzkcj4?si=wqEoUBcJ2y78Z1MY)](https://youtu.be/Rc4Uodzkcj4?si=wqEoUBcJ2y78Z1MY)
- **📈 Pitch Presentation Deck:** [View Our Presentation Slides](YOUR_GOOGLE_SLIDES_OR_CANVA_LINK_HERE)

---

##  Solution

AcciSense provides an automated incident-response pipeline:

```text
Incident Detected
       │
       ▼
 AcciSense API
       │
       ▼
    n8n
       │
       ▼
 Telegram Alert
       │
       ├───────────────┐
       │                               │
     ACK                   No ACK
       │                               │
       ▼                            ▼
Acknowledged       Escalation
       │
       ▼
Telegram Updated

⚙️ Current MVP

The current MVP demonstrates:

Incident creation
Unique AcciSense Alert IDs
Automated Telegram notifications
Interactive ACK button
Telegram callback handling
AcciSense acknowledgement API
Telegram message updates
Timeout-based escalation
Error handling for already-escalated incidents

Example Alert ID: AC-F3AEA840

🔄 Incident Lifecycle

1. Incident Detection
An incident is sent to the AcciSense webhook.
POST /accisense-alert
Example payload:

JSON
{
  "acci_id": "AC-47207EDD",
  "severity": "HIGH",
  "incident": "Critical incident detected",
  "location": "Zone A"
}

2. Alert Generation
n8n processes the incident and generates a structured Telegram notification.
Example:
🚨 ACCISENSE — INCIDENT ALERT

Alert ID: AC-47207EDD
Severity: HIGH
Incident: Critical incident detected
Location: Zone A
⚠️ Acknowledgement required.


3. Responder Acknowledgement
The responder presses the ACK button in Telegram.
The callback contains:
ack:AC-47207EDD

The ACK workflow extracts:
AcciSense ID
Chat ID
Telegram Message ID
Callback Data

4. Backend Acknowledgement
n8n sends the acknowledgement to the AcciSense backend.
POST /incidents/{acci_id}/acknowledge

If successful, the incident status becomes:
ACKNOWLEDGED

5. Telegram Update
The original Telegram alert is updated instead of sending a duplicate notification.
Example:

✅ ACCISENSE — ACKNOWLEDGED

Alert ID: AC-47207EDD
Status: ACKNOWLEDGED

6. Automatic Escalation
If the responder does not acknowledge the incident within the configured response window, AcciSense escalates the incident.

Example backend response:
409 Conflict

Incident has already been escalated because no acknowledgement was received.

This prevents a late acknowledgement from incorrectly being treated as a normal acknowledgement.

🧩 Architecture

┌──────────────────────┐
│  Incident Detection            │
└──────────┬───────────┘
                      │
                     ▼
┌──────────────────────┐
│    AcciSense API                 │
└──────────┬───────────┘
                      │
                     ▼
┌──────────────────────┐
│         n8n                             │
│   Automation Layer            │
└──────────┬───────────┘
                      │
                     ▼
┌──────────────────────┐
│       Telegram                      │
│    Responder Alert              │
└──────────┬───────────┘
                      │
              ┌───┴───┐
              │                │
           ACK     Timeout
             │                    │
            ▼                  ▼
 Acknowledge  Escalate
            │
           ▼
Update Alert


📁 Repository Structure

Accisense/
│
├── n8n/
│   ├── accisense-alert.json
│   └── accisense-ack.json
│
├── docs/
│   └── screenshots/
│
├── README.md
├── .gitignore
└── LICENSE


🛠️ Technology Stack

| Technology           | Purpose                 |
| -------------------- | ----------------------- |
| Python / Backend API | Incident processing     |
| n8n                  | Workflow automation     |
| Telegram Bot API     | Responder notifications |
| REST API             | Backend communication   |
| Webhooks             | Event communication     |
| GitHub               | Source control          |


### Clone the repository
\`\`\`bash
git clone https://github.com/anu-rag-007
cd accisense
\`\`\`

### Spin Up the Backend API
\`\`\`bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
\`\`\`
Visit \`http://127.0.0\` to access the interactive Swagger UI interface.
