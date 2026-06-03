import { useEffect, useRef, useState } from "react";

// Side-by-side original vs edited preview. "Play both" starts the two videos
// from the top together; either ending pauses both. The original is muted so
// audio comes from the edited clip (which also keeps native controls).
export default function BeforeAfter({ job, resultUrl }) {
  const beforeRef = useRef(null);
  const afterRef = useRef(null);
  const [origUrl, setOrigUrl] = useState(null);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!job?.file) return undefined;
    const url = URL.createObjectURL(job.file);
    setOrigUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [job?.file]);

  const stopBoth = () => {
    beforeRef.current?.pause();
    afterRef.current?.pause();
    setPlaying(false);
  };

  const toggle = () => {
    const before = beforeRef.current;
    const after = afterRef.current;
    if (!before || !after) return;
    if (playing) {
      stopBoth();
      return;
    }
    before.currentTime = 0;
    after.currentTime = 0;
    before.play();
    after.play();
    setPlaying(true);
  };

  return (
    <div className="rounded-2xl border border-edge bg-panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wider text-slate-500">
          Before / After
        </span>
        <button
          onClick={toggle}
          className="rounded-lg border border-edge px-3 py-1.5 font-mono text-xs text-slate-300 transition-colors hover:border-slate-600"
        >
          {playing ? "pause both" : "play both"}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="mb-1.5 font-mono text-[11px] text-slate-500">original</p>
          <video
            ref={beforeRef}
            src={origUrl || undefined}
            onEnded={stopBoth}
            muted
            playsInline
            className="aspect-video w-full rounded-lg bg-black"
          />
        </div>
        <div>
          <p className="mb-1.5 font-mono text-[11px] text-accent-soft">edited</p>
          <video
            ref={afterRef}
            src={resultUrl || undefined}
            onEnded={stopBoth}
            controls
            playsInline
            className="aspect-video w-full rounded-lg bg-black"
          />
        </div>
      </div>
    </div>
  );
}
