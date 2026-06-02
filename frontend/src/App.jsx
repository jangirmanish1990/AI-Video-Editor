import { useState } from "react";
import Uploader from "./components/Uploader";
import VideoPlayer from "./components/VideoPlayer";
import WaveformTimeline from "./components/WaveformTimeline";
import CommandBar from "./components/CommandBar";
import JobStatus from "./components/JobStatus";
import { useJobSocket } from "./hooks/useJobSocket";
import { startEdit } from "./api";

export default function App() {
  const [currentJob, setCurrentJob] = useState(null); // { job_id, filename, metadata, file }
  const [run, setRun] = useState({ jobId: null, token: 0 }); // bump token to re-run
  const [runError, setRunError] = useState(null);

  const socket = useJobSocket(run.jobId, run.token);
  const running = socket.status && socket.status !== "done" && !socket.error;

  async function handleRun(command) {
    if (!currentJob) return;
    setRunError(null);
    try {
      await startEdit(currentJob.job_id, command);
      setRun((prev) => ({ jobId: currentJob.job_id, token: prev.token + 1 }));
    } catch (err) {
      setRunError(err.message);
    }
  }

  return (
    <div className="mx-auto flex min-h-full max-w-6xl flex-col px-5 py-8">
      {/* Header */}
      <header className="mb-8 flex items-center gap-3">
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
      </header>

      {/* Main */}
      {!currentJob ? (
        <Uploader onUploaded={setCurrentJob} />
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_340px]">
          <div className="flex flex-col gap-4">
            <VideoPlayer job={currentJob} />
            <WaveformTimeline job={currentJob} />
            <CommandBar onRun={handleRun} disabled={!currentJob} running={running} />
            {runError && <p className="text-sm text-red-400">{runError}</p>}
          </div>
          <aside className="flex flex-col gap-5">
            <JobStatus jobId={run.jobId} socket={socket} />
            {/* Day 15: <HistoryPanel /> · Day 18: <OpsReference /> mount here */}
          </aside>
        </div>
      )}
    </div>
  );
}
