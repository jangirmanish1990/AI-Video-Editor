import { useRef, useState } from "react";
import { uploadAudio } from "../api";

// Compact control to attach a background-music track to the current job.
// Once attached, "add background music" becomes a usable command.
export default function MusicUploader({ jobId }) {
  const inputRef = useRef(null);
  const [music, setMusic] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function onPick(e) {
    const file = e.target.files?.[0];
    if (!file || !jobId) return;
    setBusy(true);
    setError(null);
    try {
      const res = await uploadAudio(jobId, file);
      setMusic(res.music);
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
        accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg,.flac"
        onChange={onPick}
        className="hidden"
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={busy || !jobId}
        className="rounded-lg border border-edge px-3 py-1.5 font-mono text-xs text-slate-300 transition-colors hover:border-slate-600 disabled:opacity-40"
      >
        {busy ? "attaching…" : music ? "♪ music attached" : "+ Music"}
      </button>
      {music && <span className="font-mono text-[11px] text-accent-soft">{music}</span>}
      {error && <span className="font-mono text-[11px] text-red-400">{error}</span>}
    </div>
  );
}
