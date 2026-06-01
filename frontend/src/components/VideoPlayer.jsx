import { useEffect, useState } from "react";

function fmtDuration(seconds) {
  if (!seconds || seconds <= 0) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function VideoPlayer({ job }) {
  const [src, setSrc] = useState(null);

  // Preview the local file directly (no round-trip to the server needed).
  useEffect(() => {
    if (!job?.file) {
      setSrc(null);
      return undefined;
    }
    const url = URL.createObjectURL(job.file);
    setSrc(url);
    return () => URL.revokeObjectURL(url);
  }, [job?.file]);

  return (
    <div className="overflow-hidden rounded-2xl border border-edge bg-black">
      <div className="aspect-video w-full">
        {src ? (
          <video src={src} controls className="h-full w-full" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-slate-600">
            No preview
          </div>
        )}
      </div>
      <div className="flex items-center justify-between border-t border-edge bg-panel px-4 py-2.5">
        <span className="truncate font-mono text-xs text-slate-400">{job?.filename}</span>
        <span className="font-mono text-xs text-slate-500">
          {fmtDuration(job?.metadata?.duration_s)}
        </span>
      </div>
    </div>
  );
}
