import { downloadUrl } from "../api";

function relTime(ts) {
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function HistoryPanel({ history, onClear }) {
  if (!history || history.length === 0) {
    return (
      <div className="rounded-2xl border border-edge bg-panel/40 p-5">
        <h2 className="font-display text-sm font-semibold tracking-wide text-slate-300">HISTORY</h2>
        <p className="mt-3 text-sm text-slate-500">Your completed edits will appear here.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-edge bg-panel p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-display text-sm font-semibold tracking-wide text-slate-200">HISTORY</h2>
        <button
          onClick={onClear}
          className="font-mono text-[11px] text-slate-500 transition-colors hover:text-slate-300"
        >
          clear
        </button>
      </div>

      <div className="space-y-2.5">
        {history.map((entry) => (
          <div key={entry.id} className="rounded-lg border border-edge bg-surface p-3">
            <p className="text-sm text-slate-200">{entry.command}</p>
            {entry.ops?.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {entry.ops.map((op, i) => (
                  <span
                    key={i}
                    className="rounded font-mono text-[10px] text-accent-soft"
                  >
                    {op}
                    {i < entry.ops.length - 1 ? " ·" : ""}
                  </span>
                ))}
              </div>
            )}
            <div className="mt-2 flex items-center justify-between">
              <span className="font-mono text-[10px] text-slate-500">{relTime(entry.at)}</span>
              <a
                href={downloadUrl(entry.jobId)}
                className="font-mono text-[11px] text-accent-soft transition-colors hover:text-accent"
              >
                download ↓
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
