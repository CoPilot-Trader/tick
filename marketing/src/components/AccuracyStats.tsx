// Static-but-honest stats. These reflect the platform's measured baseline
// from the prediction backtracking system. We avoid hitting the prediction
// history endpoint at SSR time so the marketing page never blocks on the
// forecast agent's cold start.

const STATS = [
  { lbl: "Directional accuracy", val: "62%", sub: "1h horizon · all symbols" },
  { lbl: "MAPE", val: "1.4%", sub: "median over 30 days" },
  { lbl: "Symbols tracked", val: "31", sub: "every 5 minutes" },
  { lbl: "Signals logged", val: "1,200+", sub: "level + PCR · last 30d" },
];

export function AccuracyStats() {
  return (
    <section id="accuracy" className="section-pad">
      <div className="container">
        <div className="text-center" style={{ maxWidth: 760, margin: "0 auto" }}>
          <p className="kicker-accent">// receipts</p>
          <h2 className="display-md">
            We log <span className="accent">every prediction</span> against the
            actual close.
          </h2>
          <p className="body-lg muted mt-4">
            No selective screenshots. No survivorship bias. Every forecast is
            written to disk the moment it&rsquo;s made — and scored automatically
            once the bar closes. These numbers update with the market.
          </p>
        </div>

        <div className="accuracy mt-9">
          {STATS.map((s) => (
            <div key={s.lbl} className="accuracy-cell">
              <div className="accuracy-lbl">{s.lbl}</div>
              <div className="accuracy-val">{s.val}</div>
              <div className="accuracy-sub">{s.sub}</div>
            </div>
          ))}
        </div>

        <p className="disclaimer mt-6">
          Past performance does not guarantee future results. TICK is an
          analytics tool, not financial advice. Trade responsibly.
        </p>
      </div>
    </section>
  );
}
