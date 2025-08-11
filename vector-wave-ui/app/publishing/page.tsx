import { fetchJSON } from '@/lib/api'

async function trackAnalytics(payload: any) {
  'use server'
  try {
    await fetchJSON<any>('http://localhost:8080/analytics/track', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch {}
}

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
  // Fire-and-forget analytics track
  await trackAnalytics({ request_id: res.request_id || res.publication_id, platform: 'linkedin', status: res.status })
  return res
}

export default async function PublishingPage() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold mb-4">🚀 Publishing Planner</h1>
      <form action={publishSample}>
        <button className="px-4 py-2 bg-blue-600 text-white rounded">Publish sample</button>
      </form>
      <div className="mt-6">
        <h2 className="text-lg font-medium mb-2">Preferences</h2>
        <form action={async (formData) => {
          'use server'
          const user = 'demo'
          const platform = String(formData.get('platform')||'linkedin')
          const hour = String(formData.get('hour')||'11:00')
          const score = Number(formData.get('score')||0.8)
          await fetchJSON<any>(`http://localhost:8080/preferences/${user}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform, hour, score }),
          })
        }} className="flex items-end gap-2">
          <div>
            <label className="block text-sm text-gray-600">Platform</label>
            <select name="platform" className="border rounded px-2 py-1">
              <option>linkedin</option>
              <option>twitter</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600">Hour</label>
            <input name="hour" defaultValue="11:00" className="border rounded px-2 py-1" />
          </div>
          <div>
            <label className="block text-sm text-gray-600">Score</label>
            <input name="score" defaultValue="0.8" className="border rounded px-2 py-1" />
          </div>
          <button className="px-3 py-1.5 bg-gray-800 text-white rounded">Save</button>
        </form>
      </div>
      <p className="text-sm text-gray-500 mt-3">Calls orchestrator at localhost:8080</p>
    </main>
  )
}
