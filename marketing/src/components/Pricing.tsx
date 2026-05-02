import { DASHBOARD_URL } from "@/lib/links";

type Tier = {
  tier: string;
  price: string;
  per: string;
  pitch: string;
  feats: string[];
  cta: string;
  feat?: boolean;
};

const TIERS: Tier[] = [
  {
    tier: "Open",
    price: "$0",
    per: "/ forever",
    pitch: "Live charts, three core agents, public watchlist.",
    feats: [
      "5 tracked tickers",
      "Price forecast (1h, 1d)",
      "Sentiment overlay",
      "Daily prediction backtracking",
      "Public dashboard",
    ],
    cta: "Open the dashboard",
  },
  {
    tier: "Trader",
    price: "$49",
    per: "/ month",
    pitch: "Full agent suite, unlimited symbols, live signal stream.",
    feats: [
      "Unlimited tickers",
      "All 7 agents (forecast, levels, PCR, fusion)",
      "Walk-forward backtester",
      "Signal alerts (email + webhook)",
      "Strategy export & API access",
    ],
    cta: "Start 14-day trial",
    feat: true,
  },
  {
    tier: "Desk",
    price: "Custom",
    per: "/ for teams",
    pitch: "Private deployment, custom strategies, white-glove onboarding.",
    feats: [
      "Self-hosted or private cloud",
      "Custom agents on your data",
      "Broker integrations",
      "Dedicated support engineer",
      "SOC2 + audit logging",
    ],
    cta: "Talk to us",
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="section-pad">
      <div className="container">
        <div className="text-center" style={{ maxWidth: 760, margin: "0 auto" }}>
          <p className="kicker-accent">// pricing</p>
          <h2 className="display-md">
            Priced for traders. <span className="accent">Not for funds.</span>
          </h2>
          <p className="body-lg muted mt-4">
            Start free. Upgrade when you&rsquo;re ready to act on signals at
            scale. No per-seat enterprise tax.
          </p>
        </div>

        <div className="grid grid-3 mt-9">
          {TIERS.map((t) => (
            <div
              key={t.tier}
              className={`price-card${t.feat ? " is-feat" : ""}`}
            >
              <div className="price-tier">{t.tier}</div>
              <div className="price-amount">
                <span className="num">{t.price}</span>
                <span className="per">{t.per}</span>
              </div>
              <p className="price-pitch">{t.pitch}</p>
              <ul className="price-list">
                {t.feats.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
              <div className="price-cta">
                <a
                  href={t.tier === "Desk" ? "mailto:hello@tick.trade" : DASHBOARD_URL}
                  target={t.tier === "Desk" ? undefined : "_blank"}
                  rel="noreferrer"
                  className={`btn ${t.feat ? "btn-solid" : "btn-line"} btn-lg`}
                  style={{ width: "100%", justifyContent: "center" }}
                >
                  {t.cta} →
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
