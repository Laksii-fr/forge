import { Suspense } from "react";

import LoginForm from "./login-form";

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginForm />
    </Suspense>
  );
}

function LoginFallback() {
  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16 font-sans">
      <p className="text-sm text-zinc-500">Checking your session…</p>
    </main>
  );
}
