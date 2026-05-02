type Card = {
  num: string;
  title: string;
  body: string;
  they: string;
  you: string;
};

const CARDS: Card[] = [
  {
    num: "P1",
    title: "Speed asymmetry",
    body: "Bloomberg terminals push real-time signals into trading desks in milliseconds. You refresh Yahoo Finance.",
    they: "Sub-second feeds, co-located",
    you: "15-min delayed quotes",
  },
  {
    num: "P2",
    title: "Signal asymmetry",
    body: "Quant funds run dozens of orthogonal strategies in parallel. You read a Reddit thread and hope.",
    they: "200+ live strategies",
    you: "1 gut feeling",
  },
  {
    num: "P3",
    title: "Backtest asymmetry",
    body: "Institutions stress-test every idea across 20 years of tick data before risking a dollar. You learn live, with real money.",
    they: "Decades of backtesting",
    you: "Hope it works tomorrow",
  },
];

export function Problem() {
  return (
    <section className="section-pad">
      <div className="container">
        <div className="text-center" style={{ maxWidth: 760, margin: "0 auto" }}>
          <p className="kicker-accent">// the gap</p>
          <h2 className="display-md">
            Retail trades blind. <span className="accent">Institutions don&rsquo;t.</span>
          </h2>
          <p className="body-lg muted mt-4">
            Every retail loss is, in part, an information loss. The professionals
            see further, faster, and with more rigor. TICK closes that gap.
          </p>
        </div>

        <div className="grid grid-3 mt-9">
          {CARDS.map((c) => (
            <article key={c.num} className="problem-card">
              <div className="problem-num">{c.num}</div>
              <h3 className="problem-title">{c.title}</h3>
              <p className="problem-body">{c.body}</p>
              <div className="problem-vs">
                <div className="col vs-they">
                  <strong>They get</strong>
                  {c.they}
                </div>
                <div className="col vs-you">
                  <strong>You get</strong>
                  {c.you}
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
