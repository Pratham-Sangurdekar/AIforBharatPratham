// API base URL — uses env var for AWS deployment, falls back to /api for local proxy
const API_BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api`
  : "/api";

export async function analyzeContent(formData: FormData) {
  const controller = new AbortController();
  // Video/audio analysis can take 2+ minutes for model loading + processing
  const timeout = setTimeout(() => controller.abort(), 180_000);

  try {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(body?.detail || "Analysis failed");
    }
    return res.json();
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "Analysis timed out. Video/image processing can take a while on first run — please try again."
      );
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export async function getHistory(limit = 20, offset = 0, contentType?: string) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (contentType) params.set("content_type", contentType);
  const res = await fetch(`${API_BASE}/history?${params}`);
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}

export async function getAnalysisDetail(id: number) {
  const res = await fetch(`${API_BASE}/history/${id}`);
  if (!res.ok) throw new Error("Failed to fetch analysis");
  return res.json();
}

export async function getTrends() {
  const res = await fetch(`${API_BASE}/trends`);
  if (!res.ok) throw new Error("Failed to fetch trends");
  return res.json();
}

export async function getPlatformTrends() {
  const res = await fetch(`${API_BASE}/trends/platforms`);
  if (!res.ok) throw new Error("Failed to fetch platform trends");
  return res.json();
}

export async function getProfile() {
  const res = await fetch(`${API_BASE}/profile`);
  if (!res.ok) throw new Error("Failed to fetch profile");
  return res.json();
}

export async function updateProfile(data: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}/profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update profile");
  return res.json();
}

export async function getGallery(contentType?: string, limit = 30, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (contentType) params.set("content_type", contentType);
  const res = await fetch(`${API_BASE}/gallery?${params}`);
  if (!res.ok) throw new Error("Failed to fetch gallery");
  return res.json();
}

export async function getMetrics() {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}
