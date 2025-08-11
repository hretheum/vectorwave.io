import Link from 'next/link'
import { fetchTopicSuggestions } from '@/lib/api'

export default async function TopicsPage() {
  const suggestions = await fetchTopicSuggestions(12)
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold mb-4">🎯 AI-Suggested Topics</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {suggestions.map((s) => (
          <div key={s.topic_id} className="border rounded-lg p-4 shadow-sm">
            <div className="text-lg font-medium">{s.title}</div>
            <div className="text-sm text-gray-500 mt-1">{s.description}</div>
            <div className="text-xs text-gray-400 mt-2">Fit: {(s.platform_fit||[]).join(', ')}</div>
            <Link href={`/topics/${encodeURIComponent(s.topic_id||s.title)}`} className="text-blue-600 text-sm mt-3 inline-block">Details →</Link>
          </div>
        ))}
      </div>
    </main>
  )
}
