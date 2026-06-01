import { useEffect, useRef, useState } from "react";
import { openJobSocket } from "../api";

const EMPTY = {
  status: null, // planning | executing | done | error
  plan: null, // [{ op, params }]
  progress: null, // { op, index, total }
  result: null, // { output_url, duration_s }
  error: null, // string
  events: [], // raw event log, newest last
};

/**
 * Opens a WebSocket to /ws/{jobId} when (jobId, runToken) are set, and
 * accumulates the server event stream defined in specs/api.md.
 * Bump runToken to re-run the same job (reopens a fresh socket).
 */
export function useJobSocket(jobId, runToken) {
  const [state, setState] = useState(EMPTY);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!jobId || !runToken) return undefined;

    setState({ ...EMPTY });
    const socket = openJobSocket(jobId);
    socketRef.current = socket;

    socket.onmessage = (event) => {
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }
      setState((prev) => {
        const next = { ...prev, events: [...prev.events, msg] };
        switch (msg.type) {
          case "status":
            next.status = msg.status;
            break;
          case "plan":
            next.plan = msg.plan;
            break;
          case "progress":
            next.progress = { op: msg.op, index: msg.index, total: msg.total };
            break;
          case "result":
            next.result = { output_url: msg.output_url, duration_s: msg.duration_s };
            break;
          case "error":
            next.error = msg.message;
            break;
          default:
            break;
        }
        return next;
      });
    };

    socket.onerror = () => {
      setState((prev) => ({
        ...prev,
        error: prev.error || "Connection to the server was interrupted.",
      }));
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [jobId, runToken]);

  return state;
}
