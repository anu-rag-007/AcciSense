                    Accident Image
                          ↓
                 /incident/from-image
                          ↓
                     Vision AI
                          ↓
                    Create Incident
                          ↓
                       Supabase
                          ↓
               ┌───────────────────┐
               │   n8n Webhook     │
               │ accisense-alert    │
               └─────────┬─────────┘
                         ↓
                 Severity Router
                  ↙    ↓    ↓    ↘
                P0    P1    P2    P3
                 ↓     ↓     ↓     ↓
               Telegram / Email
                         ↓
                       Wait
                         ↓
                    Check Status
                      ↙     ↘
                    ACK      NO ACK
                    ↓          ↓
                   END      Escalate
                               ↓
                         Telegram + Twilio