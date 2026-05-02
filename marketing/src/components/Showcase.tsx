import { LiveChart } from "./LiveChart";
import type { Candle } from "@/lib/api";

type Props = { symbol: string; initialCandles: Candle[] };

export function Showcase({ symbol, initialCandles }: Props) {
  return (
    <section id="platform" className="section-pad">
      <div className="container">
        <div className="text-center" style={{ maxWidth: 800, margin: "0 auto" }}>
          <p className="kicker-accent">// the platform</p>
          <h2 className="display-md">
            One chart. Every signal. <span className="accent">Live.</span>
          </h2>
          <p className="body-lg muted mt-4">
            Predictions, support &amp; resistance, news markers, and
            level-rejection signals — overlaid on a real candlestick stream
            and updated every few minutes. The same view our backend agents
            see.
          </p>
        </div>

        <div className="showcase mt-8">
          <div className="showcase-bar">
            <div className="showcase-dots">
              <span className="showcase-dot is-accent" />
              <span className="showcase-dot" />
              <span className="showcase-dot" />
            </div>
            <span className="showcase-title">tick.dashboard / {symbol} · 1D · 5M</span>
            <div className="showcase-tabs">
              <button className="showcase-tab is-on" type="button">Predictions</button>
              <button className="showcase-tab" type="button">Levels</button>
              <button className="showcase-tab" type="button">News</button>
              <button className="showcase-tab" type="button">Signals</button>
            </div>
          </div>

          <div className="showcase-body">
            <div className="annot-chart">
              <LiveChart
                symbol={symbol}
                initialCandles={initialCandles}
                variant="showcase"
              />
              {/* Decorative annotation pills — purely visual storytelling */}
              <div className="annot-overlay" style={{ top: 26, left: 24 }}>
                <span className="annot-pill is-pred">
                  <span className="dot" /> 1H Forecast +0.42%
                </span>
              </div>
              <div className="annot-overlay" style={{ top: 26, right: 24 }}>
                <span className="annot-pill is-news">
                  <span className="dot" /> Earnings · 7d
                </span>
              </div>
              <div className="annot-overlay" style={{ bottom: 70, left: 24 }}>
                <span className="annot-pill is-signal">
                  <span className="dot" /> PML rejection · target +1.8%
                </span>
              </div>
              <div className="annot-overlay" style={{ bottom: 70, right: 24 }}>
                <span className="annot-pill is-pred">
                  <span className="dot" /> 1D band 91% conf
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
