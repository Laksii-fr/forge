"use client";

import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { API_URL, getCurrentUser, logout, type User } from "@/lib/api";

export default function LoginForm() {
  const searchParams = useSearchParams();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(searchParams.get("error"));
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    let active = true;

    getCurrentUser()
      .then((currentUser) => {
        if (active) {
          setUser(currentUser);
        }
      })
      .catch(() => {
        if (active) {
          setMessage("Could not reach the server.");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  async function handleLogout() {
    setLoggingOut(true);
    setMessage(null);
    try {
      await logout();
      setUser(null);
    } catch {
      setMessage("Could not log out.");
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16 font-sans">
      <section className="w-full max-w-md rounded-2xl border border-black/10 bg-white p-8 shadow-sm dark:border-white/10 dark:bg-zinc-950">
        <p className="text-sm font-medium tracking-wide text-zinc-500">Forge</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">
          {user ? "You're signed in" : "Sign in"}
        </h1>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          {user
            ? "This session is connected to your GitHub account."
            : "Use your GitHub account to continue."}
        </p>

        {loading ? (
          <p className="mt-8 text-sm text-zinc-500">Checking your session…</p>
        ) : user ? (
          <SignedIn user={user} loggingOut={loggingOut} onLogout={handleLogout} />
        ) : (
          <a
            href={`${API_URL}/api/auth/github`}
            className="mt-8 flex h-12 items-center justify-center gap-3 rounded-full bg-black px-5 text-sm font-medium text-white transition-colors hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200"
          >
            <GitHubIcon />
            Continue with GitHub
          </a>
        )}

        {message ? <p className="mt-4 text-sm text-red-600 dark:text-red-400">{message}</p> : null}
      </section>
    </main>
  );
}

function SignedIn({
  user,
  loggingOut,
  onLogout,
}: {
  user: User;
  loggingOut: boolean;
  onLogout: () => void;
}) {
  const displayName = user.name || user.login;

  return (
    <div className="mt-8">
      <div className="flex items-center gap-4">
        {user.avatar_url ? (
          <Image
            src={user.avatar_url}
            alt=""
            width={56}
            height={56}
            className="h-14 w-14 rounded-full"
          />
        ) : (
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-zinc-200 text-lg font-medium dark:bg-zinc-800">
            {displayName.slice(0, 1).toUpperCase()}
          </div>
        )}
        <div>
          <p className="font-medium">{displayName}</p>
          <p className="text-sm text-zinc-500">@{user.login}</p>
          {user.email ? <p className="text-sm text-zinc-500">{user.email}</p> : null}
        </div>
      </div>
      <button
        type="button"
        onClick={onLogout}
        disabled={loggingOut}
        className="mt-6 flex h-12 w-full items-center justify-center rounded-full border border-black/10 px-5 text-sm font-medium transition-colors hover:bg-zinc-100 disabled:opacity-60 dark:border-white/15 dark:hover:bg-zinc-900"
      >
        {loggingOut ? "Signing out…" : "Log out"}
      </button>
    </div>
  );
}

function GitHubIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" className="h-4 w-4 fill-current">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82A7.7 7.7 0 0 1 8 4.77c.68.003 1.36.092 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
    </svg>
  );
}
