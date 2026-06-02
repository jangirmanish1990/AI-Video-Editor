import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";
import { getSilences } from "../api";

function fmt(t) {
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

// Waveform with: silence-gap overlays (orange, read-only) and a draggable
// selection region (blue). The selection is lifted to App so a command like
// "trim to selection" can send the chosen {start, end} to the agent.
export default function WaveformTimeline({ job, onSelect }) {
  const containerRef = useRef(null);
  const wsRef = useRef(null);
  const regionsRef = useRef(null);
  const selectionRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  const [ready, setReady] = useState(false);
  const [silenceCount, setSilenceCount] = useState(null);
  const [selection, setSelection] = useState(null);

  useEffect(() => {
    if (!job?.file || !containerRef.current) return undefined;
    setReady(false);
    setSilenceCount(null);
    setSelection(null);
    selectionRef.current = null;
    if (onSelectRef.current) onSelectRef.current(null);

    const ws = WaveSurfer.create({
      container: containerRef.current,
      height: 72,
      waveColor: "#475569",
      progressColor: "#64748b",
      cursorColor: "#fb923c",
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
    });
    const regions = ws.registerPlugin(RegionsPlugin.create());
    wsRef.current = ws;
    regionsRef.current = regions;
    ws.loadBlob(job.file);
    ws.on("ready", () => setReady(true));

    const isSilence = (r) => r.id && String(r.id).startsWith("silence");
    const apply = (r) => {
      const range = { start: r.start, end: r.end };
      setSelection(range);
      if (onSelectRef.current) onSelectRef.current(range);
    };

    regions.on("region-created", (r) => {
      if (isSilence(r)) return;
      if (selectionRef.current && selectionRef.current.id !== r.id) {
        selectionRef.current.remove();
      }
      selectionRef.current = r;
      apply(r);
    });
    regions.on("region-updated", (r) => {
      if (isSilence(r) || !selectionRef.current || r.id !== selectionRef.current.id) return;
      apply(r);
    });

    return () => {
      ws.destroy();
      wsRef.current = null;
      regionsRef.current = null;
      selectionRef.current = null;
    };
  }, [job?.file]);

  useEffect(() => {
    if (!ready || !job?.job_id || !regionsRef.current) return undefined;
    let cancelled = false;

    regionsRef.current.enableDragSelection({ color: "rgba(96, 165, 250, 0.28)" });

    getSilences(job.job_id)
      .then((data) => {
        if (cancelled || !regionsRef.current) return;
        const gaps = data.silences || [];
        gaps.forEach((s, i) =>
          regionsRef.current.addRegion({
            id: `silence-${i}`,
            start: s.start,
            end: s.end,
            color: "rgba(249, 115, 22, 0.18)",
            drag: false,
            resize: false,
          }),
        );
        setSilenceCount(gaps.length);
      })
      .catch(() => setSilenceCount(0));

    return () => {
      cancelled = true;
    };
  }, [ready, job?.job_id]);

  const clearSelection = () => {
    if (selectionRef.current) {
      selectionRef.current.remove();
      selectionRef.current = null;
    }
    setSelection(null);
    if (onSelectRef.current) onSelectRef.current(null);
  };

  return (
    <div className="rounded-2xl border border-edge bg-panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wider text-slate-500">
          Waveform
        </span>
        <div className="flex items-center gap-3">
          {silenceCount > 0 && (
            <span className="font-mono text-[11px] text-accent-soft">
              {silenceCount} silent {silenceCount === 1 ? "gap" : "gaps"}
            </span>
          )}
          {selection && (
            <span className="font-mono text-[11px] text-sky-400">
              selection {fmt(selection.start)}–{fmt(selection.end)}
              <button
                onClick={clearSelection}
                className="ml-2 text-slate-500 transition-colors hover:text-slate-300"
              >
                clear
              </button>
            </span>
          )}
        </div>
      </div>
      <div ref={containerRef} className="w-full" />
      <p className="mt-3 font-mono text-[11px] text-slate-500">
        {!ready
          ? "decoding audio…"
          : "drag on the waveform to select a range, then try \u201ctrim to selection\u201d"}
      </p>
    </div>
  );
}
