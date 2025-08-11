"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'

function cx(...classes: (string | false | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}

export default function NavBar() {
  const pathname = usePathname()
  const isActive = (href: string) => pathname === href || pathname?.startsWith(href + '/')

  const linkCls = (href: string) =>
    cx(
      'text-sm px-2 py-1 rounded',
      isActive(href) ? 'text-indigo-700 bg-indigo-50' : 'text-gray-600 hover:text-gray-900'
    )

  return (
    <nav className="border-b bg-white/80 backdrop-blur sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3 flex items-center gap-6">
        <Link href="/" className="font-semibold">Vector Wave</Link>
        <Link href="/topics" className={linkCls('/topics')}>Topics</Link>
        <Link href="/editor" className={linkCls('/editor')}>Editor</Link>
        <Link href="/publishing" className={linkCls('/publishing')}>Publishing</Link>
        <Link href="/publishing/recent" className={linkCls('/publishing/recent')}>Recent</Link>
        <Link href="/queue" className={linkCls('/queue')}>Queue</Link>
        <Link href="/system/health" className={linkCls('/system/health')}>Health</Link>
      </div>
    </nav>
  )
}
