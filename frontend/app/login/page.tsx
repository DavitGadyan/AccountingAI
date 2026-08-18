"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { BrandMark } from "@/components/architecture/product-mark";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      router.push("/");
    } catch (err) {
      // The API returns the same message for unknown email and wrong password, and this
      // surface must not add a distinction the server deliberately withheld.
      setError((err as Error).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <Card className="w-full max-w-sm">
        <CardHeader
          title={
            <span className="flex items-center gap-2">
              <BrandMark size={20} /> AccountingAI
            </span>
          }
          subtitle="Cross-border syndication compliance"
        />
        <CardBody>
          <form onSubmit={submit} className="space-y-3">
            <div>
              <label htmlFor="email" className="text-xs text-tertiary">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                className="mt-1 w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-primary"
              />
            </div>
            <div>
              <label htmlFor="password" className="text-xs text-tertiary">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                className="mt-1 w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-primary"
              />
            </div>
            {error ? <p className="text-xs text-blocking">{error}</p> : null}
            <Button type="submit" className="w-full" disabled={pending}>
              {pending ? "Signing in…" : "Sign in"}
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
