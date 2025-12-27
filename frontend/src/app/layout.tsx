import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'TICK - Time-Indexed Composite Knowledge for Markets',
  description: 'Multi-agent AI system for stock market analysis, prediction, and trading signal generation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

