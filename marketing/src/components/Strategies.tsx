type Strat = {
  name: string;
  glyph: string;
  blurb: string;
  metaLeft: string;
  metaRight: string;
};

const STRATS: Strat[] = [
  {
    name: "Price Forecast",
    glyph: "◭",
    blurb: "Multi-horizon price targets — 1h, 4h, 1d, 1w — with confidence bands and a live backtracking log of past predictions vs. the actual close.",
    metaLeft: "1h · 4h · 1d · 1w",
    metaRight: "MAPE ~1.4%",
  },
  {
    name: "Trend Classification",
    glyph: "◢",
    blurb: "Regime classifier that tags every bar as bull, bear, or range — so position sizing matches the market state, not the ticker.",
    metaLeft: "3-state regime",
    metaRight: "Live tag",
  },
  {
    name: "Sentiment Fusion",
    glyph: "◉",
    blurb: "News, headlines and earnings sentiment scored, decayed, and fused into a single directional bias — overlaid on the chart as event markers.",
    metaLeft: "NewsAPI · Finnhub",
    metaRight: "Real-time",
  },
  {
    name: "Level Rejection",
    glyph: "▣",
    blurb: "Detects rejection at OR Low, prior-day levels and VWAP — emits CALL signals with entry, stop, and two targets, ready to execute.",
    metaLeft: "PML · OR_LOW · PREV_VWAP",
    metaRight: "~71% win",
  },
  {
    name: "PCR Shock",
    glyph: "◈",
    blurb: "Put/call ratio shocks projected forward at 15m, 30m, 1h, 2h, close, and 1d — historical accuracy logged per signal.",
    metaLeft: "15m → 1d",
    metaRight: "59% acc",
  },
  {
    name: "Backtest Engine",
    glyph: "▥",
    blurb: "Replay any strategy across years of tick data — equity curve, drawdown, Sharpe, win rate. Validate before you risk a dollar.",
    metaLeft: "Tick-level",
    metaRight: "Walk-forward",
  },
];

export function Strategies() {
  return (
    <section id="strategies" className="section-pad">
      <div className="container">
        <div className="text-center" style={{ maxWidth: 760, margin: "0 auto" }}>
          <p className="kicker-accent">// the agents</p>
          <h2 className="display-md">
            Six strategies, one bar at a time.
          </h2>
          <p className="body-lg muted mt-4">
            Each agent is an independent specialist. They run in parallel on
            every tick and write their conclusions to the same chart — so you
            see consensus, divergence, and edge in one view.
          </p>
        </div>

        <div className="grid grid-3 mt-9">
          {STRATS.map((s) => (
            <article key={s.name} className="strat-card">
              <div className="stripe" aria-hidden />
              <div className="strat-icon" aria-hidden>{s.glyph}</div>
              <h3 className="strat-name">{s.name}</h3>
              <p className="strat-blurb">{s.blurb}</p>
              <div className="strat-meta">
                <span>{s.metaLeft}</span>
                <span className="stat">{s.metaRight}</span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
