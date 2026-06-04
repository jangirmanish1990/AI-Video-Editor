import { useRef, useState } from "react";
import { uploadBroll } from "../api";

// Compact control to attach a B-roll clip to the current job. Once attached,
// "add the b-roll as an intro" / "at the end" become usable commands.
export default function BrollUploader({ jobId }) {
  const inputRef = useRef(null);
  const [clip, setClip] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function onPick(e) {
    const file = e.target.files?.[0];
    if (!file || !jobId) return;
    setBusy(true);
    setError(null);
    try {
      const res = await uploadBroll(jobId, file);
      setClip(res.broll);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="flex items-center gap-2">
      <input
        ref={inputRef}
        type="file"
        accept="video/*,.mp4,.mov,.mkv,.webm"
        onChange={onPick}
        className="hidden"
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={busy || !jobId}
        className="rounded-lg border border-edge px-3 py-1.5 font-mono text-xs text-slate-300 transition-colors hover:border-slate-600 disabled:opacity-40"
      >
        {busy ? "attaching…" : clip ? "▣ b-roll attached" : "+ B-roll"}
      </button>
      {clip && <span className="font-mono text-[11px] text-accent-soft">{clip}</span>}
      {error && <span className="font-mono text-[11px] text-red-400">{error}</span>}
    </div>
  );
}
