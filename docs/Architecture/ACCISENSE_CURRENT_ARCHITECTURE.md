                         ┌──────────────────┐
                         │ ACCISENSE SYSTEM │
                         │ Incident Source          │
                         └────────┬─────────┘
                                           │
                                          ▼
                         ┌──────────────────┐
                         │  Backend / API            │
                         │                                     │
                         │ • Create Incident        │ 
                         │ • Manage Status        │
                         │ • Escalation                │
                         └────────┬─────────┘
                                           │
                                          ▼
                          ┌──────────────────┐
                          │       n8n                       │
                          │  Automation Hub       │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
          ┌─────────────────┐          ┌─────────────────┐
          │    Telegram                │          │    Supabase              │
          │                                   │          │                                   │
          │ 🚨 ALERT                 │          │ Incident Record        │
          │                                   │          │                                   │
          │ [  ✅ ACK  ]              │          │ • acci_id                    │
          └────────┬────────┘          │ • message_id           │
                            │                            │ • status                     │
                           ▼                           │ • acknowledged       │
           ACK CALLBACK                   └─────────────────┘
                    │
                   ▼
          ┌─────────────────┐
          │    ACK n8n                │
          │    Workflow               │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Backend ACK API     │
          └────────┬────────┘
                            │
                           ▼
        ┌────────────────────────┐
        │ Update Telegram Alert          │
        │                                                 │
        │ Status: ACKNOWLEDGED     │
        │ ACK button removed             │
        └───────────┬────────────┘
                                │
                               ▼
          ┌───────────────────┐
          │ Update Supabase        │
          │                                       │
          │ ACKNOWLEDGED        │
          │ acknowledged_at        │
          └───────────────────┘