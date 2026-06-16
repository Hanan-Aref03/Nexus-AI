export const dynamic = "force-dynamic";

import { FinOpsBoard } from "@/components/finops/finops-board";
import { loadFinOpsInsights } from "@/lib/backend";
import { requireCurrentSession } from "@/lib/session";

export default async function FinOpsPage() {
  const session = await requireCurrentSession("/finops");
  const insights = await loadFinOpsInsights(session);

  return <FinOpsBoard insights={insights} />;
}
