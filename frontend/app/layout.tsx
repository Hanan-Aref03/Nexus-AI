import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { getCurrentSession } from "@/lib/session";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "NexusAI Workspace",
    template: "%s | NexusAI",
  },
  description: "A tenant-aware workspace for evidence, incidents, impact maps, and concise summaries.",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default async function RootLayout({ children }: RootLayoutProps) {
  const session = await getCurrentSession();

  return (
    <html lang="en">
      <body>
        <AppShell session={session}>{children}</AppShell>
      </body>
    </html>
  );
}
