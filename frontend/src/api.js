const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export async function uploadPdf(file) {
  const formData = new FormData();
  formData.append("file", file);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    throw new Error(
      `Failed to connect to backend at ${API_BASE_URL}. ` +
        "If the API opens in the browser, set CORS on the server: CORS_ORIGINS (your Vercel URL) or CORS_ORIGIN_REGEX for *.vercel.app.",
    );
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Upload failed.");
  }
  return response.json();
}

export async function askQuestion(question) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
  } catch (error) {
    throw new Error(
      `Failed to connect to backend at ${API_BASE_URL}. ` +
        "If the API opens in the browser, set CORS on the server: CORS_ORIGINS (your Vercel URL) or CORS_ORIGIN_REGEX for *.vercel.app.",
    );
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Query failed.");
  }
  return response.json();
}
