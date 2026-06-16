/** Client-side helper for talking to the workspace copilot proxy. */

import type { CopilotAnswer } from "@/lib/types";

export async function askCopilot(question: string): Promise<CopilotAnswer> {
  const response = await fetch("/api/copilot", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`Copilot request failed with status ${response.status}.`);
  }

  return (await response.json()) as CopilotAnswer;
}

