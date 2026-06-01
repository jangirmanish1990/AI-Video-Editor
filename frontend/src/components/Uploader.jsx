import { useRef, useState } from "react";
import { uploadVideo } from "../api";

const ACCEPT = ".mp4,.mov,.mkv,.webm";

export default function Uploader({ onUploaded }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function handleFile(file) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const result = await uploadVideo(file);
      onUploaded({ ...result, file });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-8 py-20 text-center transition-colors ${
        dragging
          ? "border-accent bg-accent/5"
          : "border-edge bg-panel/40 hover:border-slate-600"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-accent/10 text-accent">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 16V4M12 4L7 9M12 4l5 5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" strokeLinecap="round" />
        </svg>
      </div>
      <p className="font-display text-lg font-semibold text-slate-100">
        {busy ? "Uploading…" : "Drop a video here"}
      </p>
      <p className="mt-1 text-sm text-slate-400">
        or click to browse · mp4, mov, mkv, webm
      </p>
      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
    </div>
  );
}
