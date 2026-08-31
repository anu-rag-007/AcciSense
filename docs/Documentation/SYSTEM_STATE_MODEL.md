INCIDENT CREATED
                     │
                    ▼
             ALERT DISPATCHED
                               │
           ┌─────────┴─────────┐
           │                                       │
          ▼                                     ▼
     ACKNOWLEDGED         NO RESPONSE
                                                   │
                                                  ▼
                                          ESCALATED
                                          

DATABASE/BACKEND:

Status                                                          Meaning   
---------------------------------------------------------------------------
CREATED                                                     Incident created
ALERT_DISPATCHED                                  Alert sent to responder
ACKNOWLEDGED                                       Responder clicked ACK
ESCALATED                                                 No ACK within timeout
RESOLVED                                                   Incident completely handled