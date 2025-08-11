import ServiceStatus from '@/components/ServiceStatus'

export default function HealthPage() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold mb-4">🩺 System Health</h1>
      <div className="border rounded p-4">
        <ServiceStatus />
      </div>
    </main>
  )
}
