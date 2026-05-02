import { DASHBOARD_URL } from "@/lib/links";

export function CTA() {
  return (
    <section id="cta" className="section-pad cta-sec">
      <div className="container container-narrow text-center cta-inner">
        <p className="kicker-accent">// the next bar</p>
        <h2 className="display-md">
          The market opens at 9:30. <br />
          <span className="accent">You should already be ready.</span>
        </h2>
        <p className="body-lg muted mt-4">
          Open the dashboard now — live charts, every agent firing on real
          tickers, no signup wall. Bring a watchlist; leave with a thesis.
        </p>
        <div className="row hero-cta mt-7 justify-center">
          <a
            href={DASHBOARD_URL}
            target="_blank"
            rel="noreferrer"
            className="btn btn-solid btn-lg"
          >
            Open the dashboard →
          </a>
          <a href="#strategies" className="btn btn-line btn-lg">
            Read the strategies
          </a>
        </div>
        <p className="label-mono muted mt-5">
          → no credit card · live data · cancel anytime
        </p>
      </div>
    </section>
  );
}
