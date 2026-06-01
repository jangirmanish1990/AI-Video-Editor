import { useState } from "react";

const SUGGESTIONS = ["remove all silences", "add captions", "trim to 60 seconds", "speed up 1.5x"];

export default function CommandBar({ onRun, disabled, running }) {
  const [value, setValue] = useState("");

  function submit() {
    const command = value.trim();
    if (!command || disabled || running) return;
    onRun(command);
  }

  return (
    <div className="rounded-2xl border border-edge bg-panel p-3">
      <div className="flex items-center gap-2">
        <span className="pl-2 font-mono text-accent">›</span>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          disabled={disabled}
          placeholder={disabled ? "Upload a video first…" : "Describe an edit…"}
          className="flex-1 bg-transparent py-2 text-slate-100 placeholder:text-slate-500 focus:outline-none disabled:cursor-not-allowed"
        />
        <button
          onClick={submit}
          disabled={disabled || running || !value.trim()}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-slate-950 transition-opacity hover:bg-accent-soft disabled:opacity-40"
        >
          {running ? "Running…" : "Run"}
        </button>
      </div>
      {!disabled && (
        <div className="mt-2.5 flex flex-wrap gap-1.5 pl-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setValue(s)}
              className="rounded-md border border-edge px-2 py-1 font-mono text-[11px] text-slate-400 transition-colors hover:border-slate-600 hover:text-slate-200"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
