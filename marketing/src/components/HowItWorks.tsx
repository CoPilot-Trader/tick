import { Fragment } from "react";

const STEPS = [
  {
    num: "01",
    title: "Ingest",
    body: "Pulls OHLCV, news, sentiment, options flow and macro context across 30+ tickers — every five minutes, into a TimescaleDB hypertable.",
  },
  {
    num: "02",
    title: "Reason",
    body: "Seven specialist agents reason in parallel: price, trend, sentiment, levels, options shock, support/resistance and a fusion layer.",
  },
  {
    num: "03",
    title: "Forecast",
    body: "Each agent emits a typed signal — direction, confidence, target, stop. The fusion layer composes them into a single trade-ready view.",
  },
  {
    num: "04",
    title: "Backtest",
    body: "Every signal is logged with the actual outcome. Accuracy is measured continuously and visible — no marketing math, just realised P&L.",
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="section-pad how">
      <div className="container">
        <div className="text-center" style={{ maxWidth: 760, margin: "0 auto" }}>
          <p className="kicker-accent">// the flow</p>
          <h2 className="display-md">
            From raw ticks to traded edge in one pipeline.
          </h2>
        </div>

        <div className="flow mt-9">
          {STEPS.map((s, i) => (
            <Fragment key={s.num}>
              <div className="flow-node">
                <div className="flow-node-num mono">STEP {s.num}</div>
                <div className="flow-node-title">{s.title}</div>
                <div className="flow-node-body">{s.body}</div>
              </div>
              {i < STEPS.length - 1 && (
                <div className="flow-arrow" aria-hidden>
                  <span className="flow-line" />
                  <span className="flow-arrowhead">→</span>
                </div>
              )}
            </Fragment>
          ))}
        </div>
      </div>
    </section>
  );
}
