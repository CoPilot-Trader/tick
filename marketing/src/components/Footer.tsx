import { CONTACT_EMAIL } from "@/lib/links";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="footer">
      <div className="container footer-row">
        <div className="footer-brand">
          <span className="appbar-mark" aria-hidden>T</span>
          <span className="footer-word">TICK</span>
          <span className="footer-tag muted">// markets, decoded</span>
        </div>
        <div className="footer-links">
          <a href="#platform">Platform</a>
          <a href="#strategies">Strategies</a>
          <a href="#how">How it works</a>
          <a href="#accuracy">Accuracy</a>
          <a href="#pricing">Pricing</a>
          <a href={`mailto:${CONTACT_EMAIL}`}>Contact</a>
        </div>
        <div className="footer-meta muted mono">
          © {year} TICK · built by DashGen Solutions
        </div>
      </div>
    </footer>
  );
}
