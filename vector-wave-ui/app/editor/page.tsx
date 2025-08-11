'use client'

import { useState } from 'react'

export default function EditorPage() {
  const [content, setContent] = useState('')
  const [preview, setPreview] = useState('')

  return (
    <main className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
      <section>
        <h1 className="text-xl font-semibold mb-2">📝 Content Editor</h1>
        <textarea
          className="w-full h-64 border rounded p-2"
          value={content}
          onChange={(e) => {
            setContent(e.target.value)
            setPreview(e.target.value)
          }}
          placeholder="Start writing your LinkedIn article..."
        />
        <div className="text-sm text-gray-500 mt-2">Characters: {content.length}</div>
      </section>
      <section>
        <h2 className="text-lg font-medium mb-2">💼 LinkedIn Preview</h2>
        <article className="border rounded p-3 bg-white">
          {preview || 'Your preview will appear here'}
        </article>
      </section>
    </main>
  )
}
