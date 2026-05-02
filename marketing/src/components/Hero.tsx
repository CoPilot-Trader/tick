import { LiveChart } from "./LiveChart";
import { DASHBOARD_URL } from "@/lib/links";
import type { Snapshot } from "@/lib/api";

const COMPANY_NAMES: Record<string, string> = {
  AAPL: "Apple Inc.",
  MSFT: "Microsoft Corp.",
  GOOGL: "Alphabet Inc.",
  AMZN: "Amazon.com",
  META: "Meta Platforms",
  NVDA: "NVIDIA Corp.",
  TSLA: "Tesla Inc.",
  SPY: "S&P 500 ETF",
};

function fmtPx(n: number) {
  return n.toFixed(2);
}
function fmtPct(n: number) {
  const s = n >= 0 ? "+" : "";
  return `${s}${n.toFixed(2)}%`;
}
function fmtVol(n: number) {
  if (n >= 1e9) return (n / 1e9).toFixed(2) + "B";
  if (n >= 1e6) return (n / 1e6).toFixed(2) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return n.toString();
}

export function Hero({ snapshot }: { snapshot: Snapshot }) {
  const dir = snapshot.change >= 0 ? "up" : "down";
  const high = snapshot.candles.reduce(
    (m, c) => Math.max(m, c.high),
    -Infinity,
  );
  const low = snapshot.candles.reduce((m, c) => Math.min(m, c.low), Infinity);

  return (
    <section id="top" className="hero">
      <div className="hero-grid" aria-hidden />
      <div className="hero-glow" aria-hidden />
      <div className="container hero-inner">
        <div className="hero-copy">
          <p className="kicker-accent">// multi-agent market intelligence</p>
          <h1 className="display-xl">
            Markets don&rsquo;t keep secrets.
            <br />
            <span className="accent">Code does.</span>
          </h1>
          <p className="body-lg muted">
            TICK is a multi-agent prediction engine — price forecasts,
            sentiment fusion, level-rejection signals and a full backtest
            workbench, all running on live market data. The same edge
            institutions buy, finally available to everyone.
          </p>
          <div className="hero-cta row">
            <a
              href={DASHBOARD_URL}
              target="_blank"
              rel="noreferrer"
              className="btn btn-solid btn-lg"
            >
              Open the dashboard →
            </a>
            <a href="#platform" className="btn btn-line btn-lg">
              See it in motion
            </a>
          </div>
          <div className="hero-meta">
            <span className="hero-meta-item">7 specialist agents</span>
            <span className="hero-meta-item">31 tickers, 5-min cadence</span>
            <span className="hero-meta-item">backtested, not back-fit</span>
          </div>
        </div>

        <div className="hero-visual">
          <div className="hero-chart">
            <div className="hero-chart-head">
              <div className="hero-chart-sym">
                <span className="sym">{snapshot.symbol}</span>
                <span className="name">
                  {COMPANY_NAMES[snapshot.symbol] ?? snapshot.symbol}
                </span>
              </div>
              <div className="hero-chart-px">
                <span className="px">{fmtPx(snapshot.price)}</span>
                <span className={`chg ${dir}`}>
                  {snapshot.change >= 0 ? "▲" : "▼"} {fmtPct(snapshot.changePct)}
                </span>
              </div>
              <div className="hero-chart-meta">
                <span>5M · 1D</span>
                <span className="hero-chart-live">
                  <span className="dot" /> LIVE
                </span>
              </div>
            </div>
            <div className="hero-chart-body">
              <LiveChart
                symbol={snapshot.symbol}
                initialCandles={snapshot.candles}
              />
            </div>
            <div className="hero-chart-foot">
              <div className="hero-chart-stat">
                <div className="lbl">Open</div>
                <div className="val">
                  {fmtPx(snapshot.candles[0]?.open ?? snapshot.price)}
                </div>
              </div>
              <div className="hero-chart-stat">
                <div className="lbl">High</div>
                <div className="val">{fmtPx(high)}</div>
              </div>
              <div className="hero-chart-stat">
                <div className="lbl">Low</div>
                <div className="val">{fmtPx(low)}</div>
              </div>
              <div className="hero-chart-stat">
                <div className="lbl">Vol</div>
                <div className="val">{fmtVol(snapshot.volume)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
