import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

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
        <CopilotKit 
          runtimeUrl="/api/copilotkit"
          publicApiKey={process.env.NEXT_PUBLIC_COPILOT_PUBLIC_KEY}
        >
          <CopilotSidebar
            defaultOpen={true}
            labels={{
              title: "Vector Wave AI Assistant",
              initial: `Cześć! 👋 Jestem asystentem redakcyjnym Vector Wave.

📂 Dostępne tematy do analizy:
• 2025-07-31-adhd-ideas-overflow (8 plików) - pomysły o ADHD
• 2025-07-31-brainstorm (14 plików) - sesja burzy mózgów

Kliknij "Pokaż dostępne tematy" aby zobaczyć pełną listę.`,
            }}
            clickOutsideToClose={false}
            showSuggestions={true}
          >
            {children}
          </CopilotSidebar>
        </CopilotKit>
      </body>
    </html>
  );
}