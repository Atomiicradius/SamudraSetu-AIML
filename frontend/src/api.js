const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function readJson(response, fallbackMessage) {
  if (response.ok) return response.json();

  let message = `${fallbackMessage} (${response.status})`;
  try {
    const payload = await response.json();
    message = payload.detail?.[0]?.msg || payload.detail || message;
  } catch {
    // Keep the normalized status message for non-JSON failures.
  }
  throw new Error(message);
}

export async function getPipelineConfig() {
  const response = await fetch(`${API_BASE_URL}/api/v1/pipeline/config`);
  return readJson(response, 'Pipeline configuration request failed');
}

export async function runPipeline(requirement) {
  const response = await fetch(`${API_BASE_URL}/api/v1/pipeline/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requirement),
  });

  return readJson(response, 'Pipeline request failed');
}
