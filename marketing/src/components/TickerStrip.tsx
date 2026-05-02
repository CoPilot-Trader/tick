"use client";

import { useEffect, useState } from "react";
import type { Snapshot } from "@/lib/api";

type Props = { snapshots: Snapshot[] };

function fmtPx(n: number) {
  return n.toFixed(2);
}
function fmtChg(n: number) {
  const s = n >= 0 ? "+" : "";
  return `${s}${n.toFixed(2)}`;
}
function fmtPct(n: number) {
  const s = n >= 0 ? "+" : "";
  return `${s}${n.toFixed(2)}%`;
}
function dirClass(n: number) {
  if (n > 0.001) return "up";
  if (n < -0.001) return "down";
  return "flat";
}

export function TickerStrip({ snapshots: initial }: Props) {
  const [snapshots, setSnapshots] = useState<Snapshot[]>(initial);

  // Refresh every 20s. Doubled-up rendering below means the marquee animation
  // never visibly resets.
  useEffect(() => {
    const symbols = initial.map((s) => s.symbol).join(",");
    if (!symbols) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const res = await fetch(`/api/snapshot?symbols=${symbols}`, {
          cache: "no-store",
        });
        if (!res.ok) return;
        const data = (await res.json()) as { snapshots: Snapshot[] };
        if (!cancelled && Array.isArray(data.snapshots)) {
          setSnapshots(data.snapshots);
        }
      } catch {
        // swallow — keep last good snapshot
      }
    };
    const id = setInterval(tick, 20_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [initial]);

  const items = [...snapshots, ...snapshots]; // doubled for seamless scroll

  return (
    <div className="ticker" aria-label="Live market ticker">
      <div className="ticker-track">
        {items.map((s, i) => (
          <span key={`${s.symbol}-${i}`} className="ticker-item">
            <span className="ticker-sym">{s.symbol}</span>
            <span className="ticker-px">{fmtPx(s.price)}</span>
            <span className={`ticker-chg ${dirClass(s.change)}`}>
              {fmtChg(s.change)} ({fmtPct(s.changePct)})
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
