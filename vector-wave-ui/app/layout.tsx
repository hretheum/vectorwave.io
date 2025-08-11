import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import NavBar from "@/components/NavBar";
import Breadcrumbs from "@/components/Breadcrumbs";
import ServiceStatus from "@/components/ServiceStatus";
import { Toaster } from "react-hot-toast";

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
          <NavBar />
          <div className="container mx-auto px-4 flex items-center justify-between">
            <Breadcrumbs />
            <ServiceStatus />
          </div>
          <div className="flex-1">{children}</div>
          <Toaster position="bottom-right" />
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