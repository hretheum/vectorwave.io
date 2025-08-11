import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Vector Wave Editorial AI",
  description: "AI-powered content editorial system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl">
      <body className={inter.className} suppressHydrationWarning>
        <div className="min-h-screen flex flex-col">
          <nav className="border-b bg-white/80 backdrop-blur sticky top-0 z-50">
            <div className="container mx-auto px-4 py-3 flex items-center gap-6">
              <a href="/" className="font-semibold">Vector Wave</a>
              <a href="/topics" className="text-sm text-gray-600 hover:text-gray-900">Topics</a>
              <a href="/editor" className="text-sm text-gray-600 hover:text-gray-900">Editor</a>
              <a href="/publishing" className="text-sm text-gray-600 hover:text-gray-900">Publishing</a>
            </div>
          </nav>
          <div className="flex-1">{children}</div>
          <footer className="border-t bg-white text-sm text-gray-600">
            <div className="container mx-auto px-4 py-3 flex items-center justify-between">
              <span>Vector Wave Editorial UI</span>
              <span>v0.1 (scaffold)</span>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}