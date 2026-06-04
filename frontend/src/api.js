// API surface for the backend. Base URL comes from VITE_API_URL in prod;
// defaults to the local FastAPI dev server.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function jsonOrThrow(resp) {
  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    try {
      const body = await resp.json();
      if (body.detail) detail = body.detail;
    } catch {
      // non-JSON error body — keep the generic message
    }
    throw new Error(detail);
  }
  return resp.json();
}

export async function uploadVideo(file) {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${API_URL}/upload`, { method: "POST", body: form });
  return jsonOrThrow(resp); // { job_id, filename, metadata }
}

export async function startEdit(jobId, command, region = null) {
  const resp = await fetch(`${API_URL}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, command, region }),
  });
  return jsonOrThrow(resp); // { job_id, status }
}

export async function uploadAudio(jobId, file) {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${API_URL}/audio/${jobId}`, { method: "POST", body: form });
  return jsonOrThrow(resp); // { job_id, music }
}

export async function submitBatch(jobIds, command) {
  const resp = await fetch(`${API_URL}/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_ids: jobIds, command }),
  });
  return jsonOrThrow(resp); // { batch_id, total, status }
}

export async function getBatch(batchId) {
  const resp = await fetch(`${API_URL}/batch/${batchId}`);
  return jsonOrThrow(resp); // { batch_id, command, status, total, completed, results }
}

export async function uploadBroll(jobId, file) {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${API_URL}/broll/${jobId}`, { method: "POST", body: form });
  return jsonOrThrow(resp); // { job_id, broll }
}

export async function getOps() {
  const resp = await fetch(`${API_URL}/ops`);
  return jsonOrThrow(resp); // [{ op, description, params_schema }]
}

export async function getSilences(jobId) {
  const resp = await fetch(`${API_URL}/silences/${jobId}`);
  return jsonOrThrow(resp); // { silences: [{start, end}], duration }
}

export function downloadUrl(jobId) {
  return `${API_URL}/download/${jobId}`;
}

export function openJobSocket(jobId) {
  const wsBase = API_URL.replace(/^http/, "ws");
  return new WebSocket(`${wsBase}/ws/${jobId}`);
}
