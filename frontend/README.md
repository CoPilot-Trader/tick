# Frontend - Multi-Agent Stock Prediction System

Next.js/TypeScript frontend for the multi-agent stock prediction system.

**Developer**: Lead Developer

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

## API Integration

The frontend communicates with the backend API. See `src/lib/api/` for API client setup.

## Building for Production

```bash
npm run build
npm start
```

## Environment Variables

See `.env.example` for required environment variables.

## Questions?

Contact Lead Developer for frontend architecture questions.

