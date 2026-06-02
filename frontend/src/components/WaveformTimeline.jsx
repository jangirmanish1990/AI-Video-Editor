import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";
import { getSilences } from "../api";

// Display-only waveform: renders the uploaded clip's audio and highlights the
// silent gaps that "remove silences" would cut. Interactive region selection
// arrives on Day 16.
export default function WaveformTimeline({ job }) {
  const containerRef = useRef(null);
  const wsRef = useRef(null);
  const regionsRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [silenceCount, setSilenceCount] = useState(null);

  useEffect(() => {
    if (!job?.file || !containerRef.current) return undefined;
    setReady(false);
    setSilenceCount(null);

    const ws = WaveSurfer.create({
      container: containerRef.current,
      height: 72,
      waveColor: "#475569", // slate-600
      progressColor: "#64748b", // slate-500 (display-only, subtle)
      cursorColor: "transparent",
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      interact: false,
    });
    const regions = ws.registerPlugin(RegionsPlugin.create());
    wsRef.current = ws;
    regionsRef.current = regions;

    ws.loadBlob(job.file);
    ws.on("ready", () => setReady(true));

    return () => {
      ws.destroy();
      wsRef.current = null;
      regionsRef.current = null;
    };
  }, [job?.file]);

  // Once decoded, fetch + overlay silence regions from the backend.
  useEffect(() => {
    if (!ready || !job?.job_id || !regionsRef.current) return undefined;
    let cancelled = false;

    getSilences(job.job_id)
      .then((data) => {
        if (cancelled || !regionsRef.current) return;
        regionsRef.current.clearRegions();
        const gaps = data.silences || [];
        gaps.forEach((s) => {
          regionsRef.current.addRegion({
            start: s.start,
            end: s.end,
            color: "rgba(249, 115, 22, 0.18)", // accent, translucent
            drag: false,
            resize: false,
          });
        });
        setSilenceCount(gaps.length);
      })
      .catch(() => setSilenceCount(0));

    return () => {
      cancelled = true;
    };
  }, [ready, job?.job_id]);

  return (
    <div className="rounded-2xl border border-edge bg-panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wider text-slate-500">
          Waveform
        </span>
        {silenceCount !== null && silenceCount > 0 && (
          <span className="font-mono text-[11px] text-accent-soft">
            {silenceCount} silent {silenceCount === 1 ? "gap" : "gaps"} highlighted
          </span>
        )}
      </div>
      <div ref={containerRef} className="w-full" />
      {!ready && (
        <p className="mt-3 font-mono text-[11px] text-slate-500">decoding audio…</p>
      )}
    </div>
  );
}
