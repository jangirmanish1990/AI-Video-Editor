import { useRef, useState } from "react";
import { submitBatch, getBatch, uploadVideo } from "../api";

// Batch mode: pick several clips, type one command, process all.
// Files are uploaded one by one, then POST /batch runs them sequentially.
// GET /batch/{id} is polled every 2s until all jobs complete.
export default function BatchPanel() {
  const inputRef = useRef(null);
  const pollRef = useRef(null);

  const [files, setFiles] = useState([]);
  const [command, setCommand] = useState("");
  const [phase, setPhase] = useState("idle"); // idle | uploading | processing | done | error
  const [uploadProgress, setUploadProgress] = useState(0); // 0-files.length
  const [batch, setBatch] = useState(null); // GET /batch response
  const [error, setError] = useState(null);

  function onFilePick(e) {
    const picked = Array.from(e.target.files || []);
    setFiles(picked);
    setPhase("idle");
    setBatch(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  async function runBatch() {
    if (!files.length || !command.trim()) return;
    setPhase("uploading");
    setUploadProgress(0);
    setError(null);
    setBatch(null);

    const jobIds = [];
    try {
      for (const file of files) {
        const result = await uploadVideo(file);
        jobIds.push(result.job_id);
        setUploadProgress((n) => n + 1);
      }
    } catch (err) {
      setError(`Upload failed: ${err.message}`);
      setPhase("error");
      return;
    }

    let batchData;
    try {
      batchData = await submitBatch(jobIds, command.trim());
    } catch (err) {
      setError(`Batch submit failed: ${err.message}`);
      setPhase("error");
      return;
    }

    setPhase("processing");
    setBatch({ ...batchData, results: [] });

    pollRef.current = setInterval(async () => {
      try {
        const data = await getBatch(batchData.batch_id);
        setBatch(data);
        if (data.status !== "processing") {
          stopPolling();
          setPhase("done");
        }
      } catch {
        stopPolling();
        setError("Lost contact with the batch — check the server.");
        setPhase("error");
      }
    }, 2000);
  }

  function reset() {
    stopPolling();
    setFiles([]);
    setCommand("");
    setPhase("idle");
    setBatch(null);
    setError(null);
    setUploadProgress(0);
  }

  const busy = phase === "uploading" || phase === "processing";

  return (
    <div className="rounded-2xl border border-edge bg-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-sm font-semibold tracking-wide text-slate-200">
          BATCH
        </h2>
        {phase !== "idle" && (
          <button onClick={reset} className="font-mono text-[11px] text-slate-500 hover:text-slate-300">
            reset
          </button>
        )}
      </div>

      {/* File picker */}
      <input ref={inputRef} type="file" accept="video/*,.mp4,.mov,.mkv,.webm"
        multiple onChange={onFilePick} className="hidden" />
      <button onClick={() => inputRef.current?.click()} disabled={busy}
        className="w-full rounded-lg border border-dashed border-edge py-3 font-mono text-xs text-slate-500 transition-colors hover:border-slate-600 hover:text-slate-300 disabled:opacity-40">
        {files.length ? `${files.length} clip${files.length > 1 ? "s" : ""} selected — click to change` : "+ pick clips (multi-select)"}
      </button>

      {/* Command */}
      <input
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        disabled={busy}
        placeholder="e.g. trim to 30 seconds"
        className="mt-3 w-full rounded-lg border border-edge bg-surface px-3 py-2 font-mono text-xs text-slate-200 placeholder-slate-600 outline-none focus:border-slate-500 disabled:opacity-40"
      />

      {/* Run button */}
      <button onClick={runBatch} disabled={busy || !files.length || !command.trim()}
        className="mt-3 w-full rounded-lg bg-accent py-2 font-mono text-xs font-semibold text-slate-950 transition-opacity hover:bg-accent-soft disabled:opacity-40">
        {phase === "uploading" ? `uploading ${uploadProgress}/${files.length}…`
          : phase === "processing" ? `processing ${batch?.completed ?? 0}/${batch?.total ?? files.length}…`
          : "run batch"}
      </button>

      {/* Results */}
      {batch?.results?.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="font-mono text-[11px] uppercase tracking-wider text-slate-500">Results</p>
          {batch.results.map((r, i) => (
            <div key={i} className="flex items-center justify-between rounded-lg border border-edge bg-surface px-3 py-2">
              <span className={`font-mono text-xs ${r.status === "done" ? "text-emerald-400" : "text-red-400"}`}>
                {r.status === "done" ? "✓" : "✕"} clip {i + 1}
              </span>
              {r.status === "done" && r.output_url ? (
                <a href={`http://localhost:8000${r.output_url}`}
                  className="font-mono text-[11px] text-accent-soft hover:underline">
                  download ↓
                </a>
              ) : (
                <span className="font-mono text-[11px] text-red-400">{r.error}</span>
              )}
            </div>
          ))}
          {phase === "processing" && batch.completed < batch.total && (
            <p className="font-mono text-[11px] text-slate-500 animate-pulse">
              running clip {batch.completed + 1} of {batch.total}…
            </p>
          )}
        </div>
      )}

      {error && <p className="mt-3 font-mono text-[11px] text-red-400">{error}</p>}
    </div>
  );
}
