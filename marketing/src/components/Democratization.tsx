export function Democratization() {
  return (
    <section className="section-pad demo-band">
      <div className="container demo-grid">
        <div>
          <p className="kicker-accent">// the principle</p>
          <h2 className="display-md mt-3">
            The same edge.<br />
            <span className="accent">For everyone with a browser.</span>
          </h2>
          <p className="body-lg muted mt-5">
            For thirty years, the gap between professional and retail traders
            was a distribution problem — institutions had the data, the models,
            and the time. We&rsquo;re closing that gap with an open product:
            transparent accuracy, no black boxes, and a price tag that doesn&rsquo;t
            assume you&rsquo;re a hedge fund.
          </p>
          <ul className="demo-list mt-7">
            <li>
              <span className="demo-bullet">●</span>
              <div>
                <div className="demo-bullet-title">Institutional rigor, retail price</div>
                <div className="demo-bullet-body">
                  Multi-agent forecasts, walk-forward backtests and signal
                  attribution — the workflow that costs $24k/year on a
                  Bloomberg terminal.
                </div>
              </div>
            </li>
            <li>
              <span className="demo-bullet">●</span>
              <div>
                <div className="demo-bullet-title">Accuracy in the open</div>
                <div className="demo-bullet-body">
                  Every prediction is logged with the actual outcome. MAPE and
                  directional accuracy are visible on the chart — not buried in
                  a brochure.
                </div>
              </div>
            </li>
            <li>
              <span className="demo-bullet">●</span>
              <div>
                <div className="demo-bullet-title">Transparent strategies</div>
                <div className="demo-bullet-body">
                  Each agent&rsquo;s logic is documented. You see why a signal
                  fired, where the level was, and what the historical hit rate
                  has been.
                </div>
              </div>
            </li>
            <li>
              <span className="demo-bullet">●</span>
              <div>
                <div className="demo-bullet-title">No advice, just edge</div>
                <div className="demo-bullet-body">
                  TICK doesn&rsquo;t tell you what to trade. It hands you the
                  same view a quant desk has — and trusts you to act on it.
                </div>
              </div>
            </li>
          </ul>
        </div>

        <div>
          <div className="compare">
            <div className="compare-head">
              <div>Capability</div>
              <div>Bloomberg / TT</div>
              <div>TICK</div>
            </div>
            <div className="compare-row">
              <div>Live multi-horizon forecast</div>
              <div>$$$</div>
              <div>Included</div>
            </div>
            <div className="compare-row">
              <div>Sentiment fusion overlay</div>
              <div>Add-on</div>
              <div>Included</div>
            </div>
            <div className="compare-row">
              <div>Level-rejection signals</div>
              <div>Quant desk</div>
              <div>Included</div>
            </div>
            <div className="compare-row">
              <div>Walk-forward backtester</div>
              <div>Quant desk</div>
              <div>Included</div>
            </div>
            <div className="compare-row">
              <div>Logged accuracy in UI</div>
              <div>—</div>
              <div>Always on</div>
            </div>
            <div className="compare-row">
              <div>Cost per seat / year</div>
              <div>~$24,000</div>
              <div>$0 — $49</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
