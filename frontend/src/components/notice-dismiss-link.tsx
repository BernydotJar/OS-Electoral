"use client";

import type { Route } from "next";
import { useRouter } from "next/navigation";

export function NoticeDismissLink({
  fallbackHref,
  label,
}: Readonly<{
  fallbackHref: string;
  label: string;
}>) {
  const router = useRouter();

  function dismiss(event: React.MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    const current = new URL(window.location.href);
    current.searchParams.delete("notice");
    const query = current.searchParams.toString();
    const nextHref = `${current.pathname}${query ? `?${query}` : ""}${current.hash}`;
    router.replace(nextHref as Route, { scroll: false });
  }

  return (
    <a href={fallbackHref} onClick={dismiss}>
      {label}
    </a>
  );
}
