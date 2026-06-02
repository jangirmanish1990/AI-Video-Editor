import { useEffect, useRef, useState } from "react";
import { downloadUrl } from "../api";

const STAGES = ["planning", "executing", "done"];

function fmtElapsed(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function StatusDot({ status }) {
  const color =
    status === "error"
      ? "bg-red-500"
      : status === "done"
        ? "bg-emerald-500"
        : "bg-accent animate-pulse";
  return <span className={`inline-block h-2 w-2 rounded-full ${color}`} />;
}

function OpIcon({ state }) {
  if (state === "done") {
    return (
      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-accent text-[10px] text-slate-950">
        ✓
      </span>
    );
  }
  if (state === "failed") {
    return (
      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-slate-950">
        ✕
      </span>
    );
  }
  if (state === "running") {
    return (
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
    );
  }
  return <span className="h-4 w-4 rounded-full border border-edge" />;
}

export default function JobStatus({ jobId, socket }) {
  const { status, plan, progress, result, error } = socket;
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(null);

  const active = Boolean(status) && status !== "done" && !error && !result;

  useEffect(() => {
    if (!status) {
      startRef.current = null;
      setElapsed(0);
    } else if (active && startRef.current === null) {
      startRef.current = Date.now();
    }
  }, [status, active]);

  useEffect(() => {
    if (!active) return undefined;
    const id = setInterval(() => {
      if (startRef.current !== null) {
        setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
      }
    }, 250);
    return () => clearInterval(id);
  }, [active]);

  if (!status && !error) {
    return (
      <div className="rounded-2xl border border-edge bg-panel/40 p-5">
        <h2 className="font-display text-sm font-semibold tracking-wide text-slate-300">STATUS</h2>
        <p className="mt-3 text-sm text-slate-500">Run a command to watch the agent work.</p>
      </div>
    );
  }

  const runningIndex = progress ? progress.index : 0;

  const opState = (i) => {
    if (result) return "done";
    if (error) {
      if (i < runningIndex) return "done";
      return i === runningIndex ? "failed" : "pending";
    }
    if (runningIndex === 0) return "pending";
    if (i < runningIndex) return "done";
    return i === runningIndex ? "running" : "pending";
  };

  return (
    <div className="rounded-2xl border border-edge bg-panel p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusDot status={error ? "error" : status} />
          <h2 className="font-display text-sm font-semibold tracking-wide text-slate-200">
            {error ? "ERROR" : (status || "").toUpperCase()}
          </h2>
        </div>
        <span className="font-mono text-xs text-slate-500">{fmtElapsed(elapsed)}</span>
      </div>

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

      {plan && (
        <div className="mt-4 space-y-2">
          <p className="font-mono text-[11px] uppercase tracking-wider text-slate-500">
            Plan{plan.length > 1 ? ` · ${plan.length} steps` : ""}
          </p>
          {plan.map((step, idx) => {
            const state = opState(idx + 1);
            const textColor =
              state === "done"
                ? "text-slate-300"
                : state === "running"
                  ? "text-slate-100"
                  : state === "failed"
                    ? "text-red-400"
                    : "text-slate-500";
            return (
              <div key={idx} className="flex animate-rise items-center gap-2.5">
                <OpIcon state={state} />
                <span className={`font-mono text-xs ${textColor}`}>{step.op}</span>
                {state === "running" && (
                  <span className="font-mono text-[11px] text-slate-500">
                    running… ({runningIndex}/{progress?.total ?? plan.length})
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

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
