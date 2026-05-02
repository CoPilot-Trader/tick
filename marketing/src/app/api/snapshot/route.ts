import { NextRequest, NextResponse } from "next/server";
import { getSnapshot } from "@/lib/api";

// Browser-safe proxy used by the ticker strip / hero badge for periodic
// updates. Avoids CORS friction (this route is same-origin) and lets us
// share the same fallback shape used at SSR.

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const symbolsParam = searchParams.get("symbols") ?? "";
  const symbols = symbolsParam
    .split(",")
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean)
    .slice(0, 16);

  if (symbols.length === 0) {
    return NextResponse.json({ snapshots: [] });
  }

  const snapshots = await Promise.all(symbols.map((s) => getSnapshot(s)));
  return NextResponse.json({ snapshots });
}
