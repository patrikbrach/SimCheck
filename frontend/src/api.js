const BASE = "";

export async function uploadSalesforce(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/upload/salesforce`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function uploadMatchFile(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/upload/matchfile`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function startMatch(tier, mappings) {
  const res = await fetch(`${BASE}/match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tier, mappings }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Match start failed");
  }
  return res.json();
}

export function subscribeProgress(onProgress, onDone, onError) {
  const es = new EventSource(`${BASE}/match/progress`);
  es.onmessage = (e) => {
    const data = JSON.parse(e.data);
    onProgress(data);
    if (data.done) {
      es.close();
      if (data.error) {
        onError(data.error);
      } else {
        onDone();
      }
    }
  };
  es.onerror = () => {
    es.close();
    onError("Connection to server lost");
  };
  return () => es.close();
}

export async function fetchResults() {
  const res = await fetch(`${BASE}/match/results`);
  if (!res.ok) throw new Error("Could not fetch results");
  return res.json();
}

export function getExportUrl() {
  return `${BASE}/export`;
}
