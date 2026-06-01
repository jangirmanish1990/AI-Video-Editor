import { downloadUrl } from "../api";

const STAGES = ["planning", "executing", "done"];

function StatusDot({ status }) {
  const color =
    status === "error"
      ? "bg-red-500"
      : status === "done"
        ? "bg-emerald-500"
        : "bg-accent animate-pulse";
  return <span className={`inline-block h-2 w-2 rounded-full ${color}`} />;
}

export default function JobStatus({ jobId, socket }) {
  const { status, plan, progress, result, error } = socket;

  if (!status && !error) {
    return (
      <div className="rounded-2xl border border-edge bg-panel/40 p-5">
        <h2 className="font-display text-sm font-semibold tracking-wide text-slate-300">
          STATUS
        </h2>
        <p className="mt-3 text-sm text-slate-500">
          Run a command to watch the agent work.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-edge bg-panel p-5">
      <div className="flex items-center gap-2">
        <StatusDot status={error ? "error" : status} />
        <h2 className="font-display text-sm font-semibold tracking-wide text-slate-200">
          {error ? "ERROR" : (status || "").toUpperCase()}
        </h2>
      </div>

      {/* Stage rail */}
      {!error && (
        <div className="mt-4 flex items-center gap-1.5">
          {STAGES.map((stage) => {
            const reached = STAGES.indexOf(stage) <= STAGES.indexOf(status);
            return (
              <div
                key={stage}
                className={`h-1 flex-1 rounded-full ${reached ? "bg-accent" : "bg-edge"}`}
                title={stage}
              />
            );
          })}
        </div>
      )}

      {/* Parsed plan */}
      {plan && (
        <div className="mt-4">
          <p className="mb-2 font-mono text-[11px] uppercase tracking-wider text-slate-500">
            Plan
          </p>
          <div className="flex flex-wrap gap-1.5">
            {plan.map((step, i) => (
              <span
                key={i}
                className="animate-rise rounded-md border border-edge bg-surface px-2 py-1 font-mono text-xs text-accent-soft"
              >
                {step.op}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Per-op progress */}
      {progress && !result && (
        <p className="mt-4 animate-rise font-mono text-sm text-slate-300">
          Executing {progress.op} — {progress.index}/{progress.total}
        </p>
      )}

      {/* Error detail */}
      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

      {/* Result */}
      {result && (
        <a
          href={downloadUrl(jobId)}
          className="mt-5 flex animate-rise items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-slate-950 transition-opacity hover:bg-accent-soft"
        >
          Download result
        </a>
      )}
    </div>
  );
}
