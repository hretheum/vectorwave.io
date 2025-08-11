"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Breadcrumbs() {
  const pathname = usePathname() || '/'
  const parts = pathname.split('/').filter(Boolean)
  const crumbs = parts.map((p, i) => ({
    label: decodeURIComponent(p),
    href: '/' + parts.slice(0, i + 1).join('/'),
  }))

  return (
    <div className="text-sm text-gray-600 py-2">
      <Link href="/" className="hover:underline">Home</Link>
      {crumbs.map((c, i) => (
        <span key={c.href}>
          <span className="mx-2">/</span>
          {i < crumbs.length - 1 ? (
            <Link href={c.href} className="hover:underline">{c.label}</Link>
          ) : (
            <span className="font-medium text-gray-900">{c.label}</span>
          )}
        </span>
      ))}
    </div>
  )
}
