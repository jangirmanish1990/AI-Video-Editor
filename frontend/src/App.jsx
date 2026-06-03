import { useEffect, useRef, useState } from "react";
import Uploader from "./components/Uploader";
import VideoPlayer from "./components/VideoPlayer";
import BeforeAfter from "./components/BeforeAfter";
import WaveformTimeline from "./components/WaveformTimeline";
import CommandBar from "./components/CommandBar";
import MusicUploader from "./components/MusicUploader";
import JobStatus from "./components/JobStatus";
import HistoryPanel from "./components/HistoryPanel";
import OpsReference from "./components/OpsReference";
import { useJobSocket } from "./hooks/useJobSocket";
import { startEdit, downloadUrl } from "./api";

const HISTORY_KEY = "ave_history";

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch {
    return [];
  }
}

export default function App() {
  const [currentJob, setCurrentJob] = useState(null);
  const [run, setRun] = useState({ jobId: null, token: 0, command: "" });
  const [runError, setRunError] = useState(null);
  const [history, setHistory] = useState(loadHistory);
  const [selection, setSelection] = useState(null);
  const [lastResultUrl, setLastResultUrl] = useState(null);
  const recordedRef = useRef(null);

  const socket = useJobSocket(run.jobId, run.token);
  const running = socket.status && socket.status !== "done" && !socket.error;

  // Loading a different clip clears everything tied to the previous one.
  function loadJob(job) {
    setCurrentJob(job);
    setLastResultUrl(null);
    setSelection(null);
    setRunError(null);
    recordedRef.current = null;
  }

  // Return to the upload screen for a fresh clip (history is preserved).
  function startOver() {
    setCurrentJob(null);
    setRun({ jobId: null, token: 0, command: "" });
    setLastResultUrl(null);
    setSelection(null);
    setRunError(null);
    recordedRef.current = null;
  }

  // Persist history whenever it changes.
  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch {
      // storage full / unavailable — non-fatal
    }
  }, [history]);

  // Record a completed run once (keyed on the run token).
  useEffect(() => {
    if (!socket.result || !currentJob || recordedRef.current === run.token) return;
    recordedRef.current = run.token;
    const entry = {
      id: `${currentJob.job_id}-${run.token}`,
      jobId: currentJob.job_id,
      command: run.command,
      ops: (socket.plan || []).map((p) => p.op),
      at: Date.now(),
    };
    setHistory((prev) => [entry, ...prev].slice(0, 20));
  }, [socket.result, currentJob, run.token, run.command, socket.plan]);

  // Keep the edited preview URL fresh (cache-busted per run).
  useEffect(() => {
    if (socket.result && currentJob) {
      setLastResultUrl(`${downloadUrl(currentJob.job_id)}?v=${run.token}`);
    }
  }, [socket.result, currentJob, run.token]);

  async function handleRun(command) {
    if (!currentJob) return;
    setRunError(null);
    try {
      await startEdit(currentJob.job_id, command, selection);
      setRun((prev) => ({ jobId: currentJob.job_id, token: prev.token + 1, command }));
    } catch (err) {
      setRunError(err.message);
    }
  }

  return (
    <div className="mx-auto flex min-h-full max-w-6xl flex-col px-5 py-8">
      <header className="sticky top-0 z-10 -mx-5 mb-8 flex items-center justify-between gap-3 border-b border-edge/60 bg-surface/85 px-5 py-4 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent font-display text-lg font-bold text-slate-950">
            ▶
          </div>
          <div>
            <h1 className="font-display text-xl font-bold leading-none text-slate-100">
              AI Video Editor
            </h1>
            <p className="mt-1 font-mono text-[11px] text-slate-500">
              describe an edit — the agent does the rest
            </p>
          </div>
        </div>
        {currentJob && (
          <div className="flex items-center gap-3">
            <span className="hidden max-w-[180px] truncate font-mono text-[11px] text-slate-500 sm:inline">
              {currentJob.filename}
            </span>
            <button
              onClick={startOver}
              className="rounded-lg border border-edge px-3 py-1.5 font-mono text-xs text-slate-300 transition-colors hover:border-slate-600 hover:text-slate-100"
            >
              + New video
            </button>
          </div>
        )}
      </header>

      {!currentJob ? (
        <Uploader onUploaded={loadJob} />
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_340px]">
          <div className="flex flex-col gap-4">
            {lastResultUrl ? (
              <BeforeAfter job={currentJob} resultUrl={lastResultUrl} />
            ) : (
              <VideoPlayer job={currentJob} />
            )}
            <WaveformTimeline job={currentJob} onSelect={setSelection} />
            <MusicUploader jobId={currentJob.job_id} />
            <CommandBar onRun={handleRun} disabled={!currentJob} running={running} />
            {runError && <p className="text-sm text-red-400">{runError}</p>}
          </div>
          <aside className="flex flex-col gap-5">
            <JobStatus jobId={run.jobId} socket={socket} />
            <HistoryPanel history={history} onClear={() => setHistory([])} />
            <OpsReference onTry={handleRun} canTry={Boolean(currentJob) && !running} />
          </aside>
        </div>
      )}
    </div>
  );
}
