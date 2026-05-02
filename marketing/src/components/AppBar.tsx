import { DASHBOARD_URL } from "@/lib/links";

export function AppBar() {
  return (
    <header className="appbar">
      <div className="container appbar-row">
        <a href="#top" className="appbar-brand" aria-label="TICK home">
          <span className="appbar-mark" aria-hidden>T</span>
          <span>TICK</span>
        </a>
        <nav className="appbar-nav" aria-label="Primary">
          <a href="#platform">Platform</a>
          <a href="#strategies">Strategies</a>
          <a href="#how">How it works</a>
          <a href="#accuracy">Accuracy</a>
          <a href="#pricing">Pricing</a>
          <span className="appbar-status" aria-label="Markets live">
            <span className="dot" /> NYSE LIVE
          </span>
          <a
            href={DASHBOARD_URL}
            target="_blank"
            rel="noreferrer"
            className="btn btn-line btn-sm"
          >
            Open dashboard →
          </a>
        </nav>
      </div>
    </header>
  );
}
