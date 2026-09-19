'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

type Phase = 'init' | 'ready' | 'capturing' | 'uploading' | 'done' | 'error';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://127.0.0.1:8000';

type SubmitResult = {
  incident_id: string;
  media_url: string;
  severity: string | null;
  category: string | null;
  dispatch_status: string;
};

async function sha256Hex(buf: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', buf);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function getPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported'));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10_000,
      maximumAge: 0,
    });
  });
}

export default function ReportPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [phase, setPhase] = useState<Phase>('init');
  const [error, setError] = useState<string | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lng: number; accuracy: number } | null>(null);
  const [result, setResult] = useState<SubmitResult | null>(null);

  // ── Start camera + GPS on mount
  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => {});
        }

        const pos = await getPosition();
        if (cancelled) return;
        setCoords({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
        setPhase('ready');
      } catch (e: any) {
        if (cancelled) return;
        setError(e?.message ?? 'Failed to initialize camera or GPS');
        setPhase('error');
      }
    })();

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const capture = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !coords) return;

    setPhase('capturing');
    try {
      // Draw current frame to canvas, downscale to 1280px wide max
      const maxW = 1280;
      const scale = Math.min(1, maxW / video.videoWidth);
      const w = Math.round(video.videoWidth * scale);
      const h = Math.round(video.videoHeight * scale);
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(video, 0, 0, w, h);

      const blob: Blob = await new Promise((resolve, reject) =>
        canvas.toBlob(
          (b) => (b ? resolve(b) : reject(new Error('toBlob failed'))),
          'image/jpeg',
          0.85,
        ),
      );

      const arrayBuf = await blob.arrayBuffer();
      const clientHash = await sha256Hex(arrayBuf);

      setPhase('uploading');

      const fd = new FormData();
      fd.append('photo', blob, 'report.jpg');
      fd.append('latitude', coords.lat.toString());
      fd.append('longitude', coords.lng.toString());
      fd.append('captured_at', new Date().toISOString());
      fd.append('client_hash', clientHash);
      fd.append('description', '');

      const res = await fetch(`${API_BASE}/api/incidents/realtime`, {
        method: 'POST',
        body: fd,
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Upload failed (${res.status}): ${txt}`);
      }

      const json: SubmitResult = await res.json();
      setResult(json);
      setPhase('done');
    } catch (e: any) {
      setError(e?.message ?? 'Capture failed');
      setPhase('error');
    }
  }, [coords]);

  return (
    <main className="min-h-screen bg-black text-white flex flex-col">
      <div className="flex-1 relative">
        <video
          ref={videoRef}
          playsInline
          muted
          className="absolute inset-0 w-full h-full object-cover"
        />
        <canvas ref={canvasRef} className="hidden" />

        {/* Status pill */}
        <div className="absolute top-4 left-4 right-4 flex justify-between items-start text-xs">
          <div className="bg-black/60 px-3 py-1.5 rounded-full">
            {coords
              ? `📍 ±${Math.round(coords.accuracy)}m`
              : phase === 'init'
              ? '📍 locating…'
              : '📍 unavailable'}
          </div>
          <div className="bg-black/60 px-3 py-1.5 rounded-full">
            {phase === 'ready' && '✓ ready'}
            {phase === 'capturing' && '📷 capturing…'}
            {phase === 'uploading' && '☁ uploading…'}
            {phase === 'done' && '✓ sent'}
            {phase === 'error' && '⚠ error'}
          </div>
        </div>
      </div>

      {/* Bottom control */}
      <div className="p-6 pb-10 bg-black">
        {phase === 'error' && (
          <div className="text-red-400 text-center mb-4 text-sm">{error}</div>
        )}

        {phase === 'done' && result ? (
          <div className="text-center space-y-2">
            <div className="text-emerald-400 text-lg font-semibold">
              Report received
            </div>
            <div className="text-slate-300 text-xs">
              #{result.incident_id.slice(0, 8)}
            </div>
            <div className="text-slate-400 text-sm">
              {result.severity ?? '—'} · {result.category ?? '—'}
            </div>
            <div className="text-slate-500 text-xs">
              Status: {result.dispatch_status}
            </div>
          </div>
        ) : (
          <button
            onClick={capture}
            disabled={phase !== 'ready'}
            className="w-full py-5 rounded-2xl bg-red-600 text-white text-xl font-bold
                       disabled:opacity-40 active:scale-95 transition"
          >
            {phase === 'capturing' && 'Capturing…'}
            {phase === 'uploading' && 'Uploading…'}
            {(phase === 'ready' || phase === 'init') && 'REPORT INCIDENT'}
            {phase === 'error' && 'Retry'}
          </button>
        )}
      </div>
    </main>
  );
}