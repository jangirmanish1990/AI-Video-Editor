import { useEffect, useState } from "react";
import { getOps } from "../api";

// Example phrasings per op. Sourced from the op name returned by /ops, so if the
// backend gains an op without an example here, it still lists (just no example).
const EXAMPLES = {
  trim: "trim to the first 30 seconds",
  cut: "cut from 0:05 to 0:10",
  remove_silence: "remove all silences",
  speed: "speed up 1.5x",
  caption: "add captions",
  extract_audio: "extract the audio as mp3",
};

export default function OpsReference({ onTry, canTry }) {
  const [ops, setOps] = useState([]);
  const [open, setOpen] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    getOps()
      .then(setOps)
      .catch(() => setError(true));
  }, []);

  return (
    <div className="rounded-2xl border border-edge bg-panel p-5">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between"
      >
        <h2 className="font-display text-sm font-semibold tracking-wide text-slate-200">
          WHAT YOU CAN ASK
        </h2>
        <span className="font-mono text-sm text-slate-500">{open ? "–" : "+"}</span>
      </button>

      {open && (
        <div className="mt-4 space-y-3">
          {error && <p className="text-sm text-slate-500">Couldn't load operations.</p>}
          {ops.map((o) => {
            const example = EXAMPLES[o.op];
            return (
              <div key={o.op} className="border-l-2 border-edge pl-3">
                <p className="font-mono text-xs text-accent-soft">{o.op}</p>
                <p className="mt-0.5 text-xs text-slate-400">{o.description}</p>
                {example &&
                  (canTry ? (
                    <button
                      onClick={() => onTry(example)}
                      className="mt-1 font-mono text-[11px] text-slate-500 transition-colors hover:text-accent-soft"
                    >
                      try: “{example}” →
                    </button>
                  ) : (
                    <p className="mt-1 font-mono text-[11px] text-slate-500">e.g. “{example}”</p>
                  ))}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
