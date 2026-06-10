import { redirect } from "next/navigation";

import { AccessForm } from "@/components/auth/access-form";
import { getCurrentSession } from "@/lib/session";

export default async function SignupPage() {
  const session = await getCurrentSession();
  if (session) {
    redirect("/");
  }

  return (
    <div className="mx-auto flex w-full max-w-4xl items-center justify-center py-6">
      <AccessForm mode="signup" />
    </div>
  );
}
