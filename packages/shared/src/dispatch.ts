export const SEVERITIES = ['LOW','MEDIUM','HIGH','CRITICAL'] as const;
export type Severity = typeof SEVERITIES[number];

export const DISPATCH_POLICY: Record<Severity, {wave:number; radius_m:number; timeout_s:number}[]> = {
  CRITICAL: [
    { wave: 1, radius_m: 3000,  timeout_s: 20 },
    { wave: 2, radius_m: 8000,  timeout_s: 30 },
    { wave: 3, radius_m: 15000, timeout_s: 60 },
  ],
  HIGH: [
    { wave: 1, radius_m: 5000,  timeout_s: 45 },
    { wave: 2, radius_m: 12000, timeout_s: 60 },
  ],
  MEDIUM: [
    { wave: 1, radius_m: 8000,  timeout_s: 90 },
    { wave: 2, radius_m: 20000, timeout_s: 120 },
  ],
  LOW: [
    { wave: 1, radius_m: 10000, timeout_s: 180 },
  ],
};