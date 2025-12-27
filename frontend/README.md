# Frontend - TICK Rapid Prototype

Next.js/TypeScript frontend for the TICK multi-agent stock prediction system.

**Status**: 🚀 Rapid Prototype (Milestone 0)  
**Developer**: Lead Developer

## Features

- 📊 **Interactive Price Charts**: Real-time and predicted prices with support/resistance levels
- 🎯 **5-Minute Predictions**: Clickable prediction dots showing detailed insights
- 📈 **10 S&P 500 Stocks**: Pre-configured with top stocks (AAPL, MSFT, GOOGL, etc.)
- 💡 **Prediction Details**: Modal showing price predictions, trend classification, sentiment, and fused signals
- 🎨 **Modern UI**: Built with Tailwind CSS and Recharts
- 🔌 **Backend Ready**: API client structure ready for backend integration

## Structure

```
frontend/
├── src/
│   ├── app/              # Next.js app directory
│   ├── components/      # React components
│   ├── lib/             # Utilities and helpers
│   ├── types/           # TypeScript type definitions
│   ├── hooks/           # Custom React hooks
│   └── styles/          # Global styles
├── public/              # Static assets
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── next.config.js       # Next.js config
└── README.md           # This file
```

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Run development server**:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open browser**:
   Navigate to `http://localhost:3000`

## Development

### Code Style

- Use TypeScript for all files
- Follow React best practices
- Use functional components with hooks
- Follow Next.js 13+ App Router conventions

### Project Structure

- `src/app/` - Next.js app router pages and layouts
- `src/components/` - Reusable React components
- `src/lib/` - Utility functions and API clients
- `src/types/` - TypeScript interfaces and types
- `src/hooks/` - Custom React hooks

## Components

- **StockSelector**: Dropdown to select from 10 S&P 500 stocks
- **PriceChart**: Interactive chart with actual prices, predictions, and support/resistance levels
- **PredictionDetail**: Modal showing detailed prediction insights (price, trend, sentiment, levels)
- **StockOverview**: Overview card with current price, change, and key metrics

## API Integration

The frontend currently uses mock data but is ready for backend integration. See `src/lib/api/client.ts` for API client setup. To connect to backend:

1. Update `NEXT_PUBLIC_API_URL` in `.env.local`
2. Uncomment API calls in `src/lib/api/client.ts`
3. Remove mock data imports

## Building for Production

```bash
npm run build
npm start
```

## Environment Variables

See `.env.example` for required environment variables.

## Questions?

Contact Lead Developer for frontend architecture questions.

