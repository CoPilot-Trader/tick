import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TICK — markets don't keep secrets. Code does.",
  description:
    "TICK is a multi-agent market intelligence platform. Real-time predictions, live signal overlays, and full-strategy backtests — built so the same edge that institutions buy is finally available to everyone.",
  metadataBase: new URL("https://tick.trade"),
  openGraph: {
    title: "TICK — multi-agent market intelligence",
    description:
      "Live multi-horizon price forecasts, sentiment fusion, level-rejection signals, and a backtest engine. Open the dashboard.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
