export async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export type TopicSuggestion = {
  topic_id?: string;
  title: string;
  description?: string;
  score?: number;
  platform_fit?: string[];
};

export async function fetchTopicSuggestions(limit = 12): Promise<TopicSuggestion[]> {
  // Best-effort suggestions via Topic Manager vector search
  const q = encodeURIComponent("AI");
  try {
    const data = await fetchJSON<any>(`http://localhost:8041/topics/search?q=${q}&limit=${limit}`);
    const items = (data.items || []) as any[];
    return items.map((it) => ({
      topic_id: it.topic_id || it.id,
      title: it.title || it.document || "Suggested Topic",
      description: (it.metadata && it.metadata.summary) || "",
      score: typeof it.score === "number" ? it.score : undefined,
      platform_fit: ["linkedin", "twitter", "ghost"],
    }));
  } catch {
    // Fallback mock
    return Array.from({ length: limit }).map((_, i) => ({
      topic_id: `mock_${i}`,
      title: `AI Suggestion #${i + 1}`,
      description: "Placeholder suggestion",
      score: Math.round(70 + Math.random() * 30),
      platform_fit: ["linkedin", "twitter"],
    }));
  }
}
