# Citizen (PWA):

US-1: As a citizen, I can open the app and report an incident in under 15 seconds without typing an address.

US-2: As a citizen, the app automatically attaches my GPS and a live photo to the report.

US-3: As a citizen, I get a confirmation with an incident ID and can see status updates in real time.

# Agency Dispatcher (dashboard):

US-4: As an agency dispatcher, I receive a live offer card with countdown, photo, distance, and one-tap accept.

US-5: As a dispatcher, if another agency accepts first, my card is revoked within 1 second.

US-6: As a dispatcher, I can abort an accepted dispatch with a reason and the incident re-broadcasts.

# Platform Admin (supervisor):

US-7: As a supervisor, I see every active incident on a live map with severity color-coding.

US-8: As a supervisor, I can manually re-broadcast or override any incident.

US-9: As a supervisor, I'm notified when an incident reaches unassigned after all waves.

# Acceptance criteria (Phase 1 exit):

Time-to-first-offer < 3s

Time-to-accept (CRITICAL) < 30s

Realtime revocation fan-out < 1s

Zero double-dispatch under 20× concurrent accepts (race test passes)