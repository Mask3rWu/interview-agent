/**
 * SSE client for streaming interview responses.
 * Uses fetch with ReadableStream since the SSE endpoint is POST.
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SSECallbacks {
  onToken?: (token: string) => void;
  onMessageEnd?: (fullText: string) => void;
  onAssessment?: (data: unknown) => void;
  onError?: (error: string) => void;
}

export async function streamAnswer(
  sessionId: string,
  answer: string,
  callbacks: SSECallbacks
): Promise<void> {
  const res = await fetch(`${API_BASE}/interviews/${sessionId}/answer/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer }),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    callbacks.onError?.(
      (detail as { detail?: string }).detail || `HTTP ${res.status}`
    );
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    callbacks.onError?.("No response body");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let eventType = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        eventType = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const data = line.slice(6);
        try {
          const parsed = JSON.parse(data);
          if (eventType === "token") {
            callbacks.onToken?.(parsed.token);
          } else if (eventType === "message_end") {
            callbacks.onMessageEnd?.(parsed.full_text);
          } else if (eventType === "assessment") {
            callbacks.onAssessment?.(parsed);
          } else if (eventType === "error") {
            callbacks.onError?.(parsed);
          }
        } catch {
          // non-JSON data, ignore
        }
        eventType = "";
      }
    }
  }
}
