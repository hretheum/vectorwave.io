import { fetchJSON } from '@/lib/api'

async function publishSample() {
  'use server'
  const payload = {
    topic: { title: 'Test', description: 'Desc' },
    platforms: {
      linkedin: { enabled: true, account_id: 'a' },
      twitter: { enabled: true, account_id: 'b' },
    },
  }
  const res = await fetchJSON<any>('http://localhost:8080/publish', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return res
}

export default async function PublishingPage() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold mb-4">🚀 Publishing Planner</h1>
      <form action={publishSample}>
        <button className="px-4 py-2 bg-blue-600 text-white rounded">Publish sample</button>
      </form>
      <p className="text-sm text-gray-500 mt-3">Calls orchestrator at localhost:8080</p>
    </main>
  )
}
