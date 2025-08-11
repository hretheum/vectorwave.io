import { fetchJSON } from '@/lib/api'
import toast from 'react-hot-toast'

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
  async function fetchMetrics() {
    'use server'
    try {
      const m = await fetchJSON<any>('http://localhost:8080/metrics', { cache: 'no-store' as any })
      return m
    } catch {
      return null
    }
  }
  const metrics = await fetchMetrics()
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold mb-4">🚀 Publishing Planner</h1>
      <form action={async () => {
        'use server'
        const res = await publishSample()
        // Note: toasts are client-side; we keep server action returning data
        return res
      }}>
        <button className="px-4 py-2 bg-blue-600 text-white rounded" formAction={async () => {
          'use server'
          const res = await publishSample()
          // client toast trigger is not available here; rely on UI reading response in future enhancement
          return res
        }}>Publish sample</button>
      </form>
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
          <div className="border rounded p-3">
            <div className="text-xs text-gray-500">Total Publications</div>
            <div className="text-xl font-semibold">{metrics.total_publications}</div>
          </div>
          <div className="border rounded p-3">
            <div className="text-xs text-gray-500">Presentor Ready</div>
            <div className="text-xl font-semibold">{metrics.presentor_ready ? 'Yes' : 'No'}</div>
          </div>
          <div className="border rounded p-3">
            <div className="text-xs text-gray-500">Analytics Events</div>
            <div className="text-xl font-semibold">{metrics.analytics_events}</div>
          </div>
        </div>
      )}
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
