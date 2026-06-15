"use client";

import { useMemo, useState } from "react";
import type { FormEvent } from "react";

import { useSearchParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { ROLE_OPTIONS, sanitizeNextPath, type WorkspaceRole } from "@/lib/auth";
import { cn } from "@/lib/utils";

interface AccessFormProps {
  mode: "login" | "signup";
}

interface FormState {
  displayName: string;
  email: string;
  workspaceName: string;
  role: WorkspaceRole;
}

const initialState: FormState = {
  displayName: "",
  email: "",
  workspaceName: "",
  role: "incident_commander",
};

function labelForMode(mode: "login" | "signup"): string {
  return mode === "login" ? "Resume workspace" : "Create workspace";
}

export function AccessForm({ mode }: AccessFormProps) {
  const searchParams = useSearchParams();
  const nextPath = sanitizeNextPath(searchParams.get("next"), "/");
  const [formState, setFormState] = useState<FormState>(initialState);
  const [selectedRole, setSelectedRole] = useState<WorkspaceRole>(initialState.role);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fieldLabel = mode === "login" ? "Workspace ID" : "Workspace name";
  const fieldHint =
    mode === "login"
      ? "Use the tenant identifier you were given."
      : "This becomes the name of the workspace and its tenant key.";

  const workspacePlaceholder = mode === "login" ? "acme-operations" : "Acme Operations";
  const roleInfo = useMemo(() => ROLE_OPTIONS.find((option) => option.value === selectedRole) ?? ROLE_OPTIONS[0], [selectedRole]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const payload =
        mode === "login"
          ? {
              displayName: formState.displayName.trim(),
              email: formState.email.trim(),
              workspaceId: formState.workspaceName.trim(),
              role: selectedRole,
              next: nextPath,
            }
          : {
              displayName: formState.displayName.trim(),
              email: formState.email.trim(),
              workspaceName: formState.workspaceName.trim(),
              role: selectedRole,
              next: nextPath,
            };

      const response = await fetch(mode === "login" ? "/api/auth/login" : "/api/auth/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = (await response.json().catch(() => null)) as { next?: string; error?: string } | null;

      if (!response.ok) {
        throw new Error(data?.error ?? "We could not complete access right now.");
      }

      window.location.assign(data?.next ?? nextPath);
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "We could not complete access right now.");
      setSubmitting(false);
    }
  }

  return (
    <Card className="w-full max-w-3xl border-white/10 bg-white/6">
      <CardHeader className="gap-4 border-b border-white/8 bg-black/15 px-6 py-6 sm:px-8">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="info">Tenant aware</Badge>
          <Badge tone={roleInfo.tone}>{roleInfo.label}</Badge>
        </div>
        <div className="space-y-2">
          <CardTitle className="text-2xl sm:text-3xl">
            {mode === "login" ? "Welcome back" : "Start a new workspace"}
          </CardTitle>
          <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
            {mode === "login"
              ? "Return to your workspace, keep your role, and continue the review from the same view."
              : "Create a tenant-scoped workspace and choose the role that matches how you work."}
          </p>
        </div>
      </CardHeader>

      <CardBody className="space-y-6 px-6 py-6 sm:px-8">
        <form className="space-y-5" onSubmit={handleSubmit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-white">Your name</span>
              <input
                required
                value={formState.displayName}
                onChange={(event) => setFormState((state) => ({ ...state, displayName: event.target.value }))}
                placeholder="Jordan Lee"
                className="h-12 w-full rounded-2xl border border-white/10 bg-black/20 px-4 text-sm text-white outline-none placeholder:text-muted-foreground focus:border-primary/40 focus:ring-2 focus:ring-primary/20"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-white">Email</span>
              <input
                required
                type="email"
                value={formState.email}
                onChange={(event) => setFormState((state) => ({ ...state, email: event.target.value }))}
                placeholder="jordan@acme.com"
                className="h-12 w-full rounded-2xl border border-white/10 bg-black/20 px-4 text-sm text-white outline-none placeholder:text-muted-foreground focus:border-primary/40 focus:ring-2 focus:ring-primary/20"
              />
            </label>
          </div>

          <label className="space-y-2">
            <span className="text-sm font-medium text-white">{fieldLabel}</span>
            <input
              required
              value={formState.workspaceName}
              onChange={(event) => setFormState((state) => ({ ...state, workspaceName: event.target.value }))}
              placeholder={workspacePlaceholder}
              className="h-12 w-full rounded-2xl border border-white/10 bg-black/20 px-4 text-sm text-white outline-none placeholder:text-muted-foreground focus:border-primary/40 focus:ring-2 focus:ring-primary/20"
            />
            <span className="block text-xs leading-5 text-muted-foreground">{fieldHint}</span>
          </label>

          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <span className="text-sm font-medium text-white">Workspace role</span>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">This sets the default surfaces you see first.</p>
              </div>
              <Badge tone={roleInfo.tone}>{roleInfo.label}</Badge>
            </div>

            <div className="grid gap-3 lg:grid-cols-2">
              {ROLE_OPTIONS.map((option) => {
                const selected = option.value === selectedRole;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setSelectedRole(option.value)}
                    className={cn(
                      "rounded-2xl border p-4 text-left transition-all",
                      selected ? "border-primary/40 bg-primary/10 shadow-[0_0_0_1px_rgba(45,212,191,0.14)]" : "border-white/8 bg-white/5 hover:bg-white/8",
                    )}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-semibold text-white">{option.label}</span>
                      <span className="h-2.5 w-2.5 rounded-full bg-primary" style={{ opacity: selected ? 1 : 0.35 }} />
                    </div>
                    <p className="mt-2 text-xs leading-5 text-muted-foreground">{option.summary}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {error ? (
            <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm leading-6 text-rose-100">
              {error}
            </div>
          ) : null}

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button type="submit" className="sm:flex-1" disabled={submitting}>
              {submitting ? "Working..." : labelForMode(mode)}
            </Button>
            <Button href={mode === "login" ? "/signup" : "/login"} variant="secondary" className="sm:flex-1">
              {mode === "login" ? "Create a workspace" : "Resume access"}
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
