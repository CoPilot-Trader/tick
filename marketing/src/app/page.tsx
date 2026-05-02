import { AppBar } from "@/components/AppBar";
import { TickerStrip } from "@/components/TickerStrip";
import { Hero } from "@/components/Hero";
import { Problem } from "@/components/Problem";
import { Showcase } from "@/components/Showcase";
import { Strategies } from "@/components/Strategies";
import { HowItWorks } from "@/components/HowItWorks";
import { Democratization } from "@/components/Democratization";
import { AccuracyStats } from "@/components/AccuracyStats";
import { Pricing } from "@/components/Pricing";
import { CTA } from "@/components/CTA";
import { Footer } from "@/components/Footer";
import { getSnapshot } from "@/lib/api";

// Always render fresh — the hero chart should reflect the most recent
// 5-minute candles. Edge revalidation is tight (30s) inside fetch().
export const dynamic = "force-dynamic";

const TICKER_SYMBOLS = [
  "AAPL", "MSFT", "GOOGL", "AMZN", "META",
  "NVDA", "TSLA", "NFLX", "SPY", "JPM",
  "V", "WMT",
];

const HERO_SYMBOL = "AAPL";

export default async function Home() {
  const [heroSnap, ...tickerSnaps] = await Promise.all([
    getSnapshot(HERO_SYMBOL),
    ...TICKER_SYMBOLS.map((s) => getSnapshot(s)),
  ]);

  return (
    <>
      <AppBar />
      <TickerStrip snapshots={tickerSnaps} />
      <main>
        <Hero snapshot={heroSnap} />
        <Problem />
        <Showcase symbol={HERO_SYMBOL} initialCandles={heroSnap.candles} />
        <Strategies />
        <HowItWorks />
        <Democratization />
        <AccuracyStats />
        <Pricing />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
