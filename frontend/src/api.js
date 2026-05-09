async function requestJson(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    throw new Error(data?.detail || `Request failed with status ${response.status}`);
  }

  return data;
}

export function getHealth() {
  return requestJson("/api/health");
}

export function getSamples() {
  return requestJson("/api/samples");
}

export function generateSamples() {
  return requestJson("/api/samples/generate", { method: "POST" });
}

export function extractSample(name) {
  return requestJson("/api/extract/sample", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export function extractUpload(file) {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson("/api/extract/upload", {
    method: "POST",
    body: formData,
  });
}

export function evaluateCv({ cvText, protectedMode, model, temperature, forceDemo }) {
  return requestJson("/api/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cv_text: cvText,
      protected: protectedMode,
      model,
      temperature,
      force_demo: forceDemo,
    }),
  });
}

export function compareCv({ cvText, model, temperature, forceDemo }) {
  return requestJson("/api/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cv_text: cvText,
      model,
      temperature,
      force_demo: forceDemo,
    }),
  });
}
