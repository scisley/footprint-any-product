# Footprint Any Product - Frontend

A modern, minimalistic Next.js application for analyzing the carbon footprint of any product based on its URL or name.

## Features

- Clean, responsive design with light and dark mode support
- Product URL/name input with real-time validation
- WebSocket-based streaming text component for live analysis results
- Built with Next.js, React 19, and TailwindCSS

## Getting Started

### Prerequisites

- Node.js 18.0.0 or later
- PNPM package manager

### Installation

```bash
# Install dependencies
pnpm install
```

### Development

```bash
# Start the development server
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

### Build

```bash
# Build for production
pnpm build

# Start the production server
pnpm start
```

## Project Structure

```
frontend/
├── public/             # Static assets
├── src/
│   ├── app/            # Next.js app router
│   │   ├── globals.css # Global styles
│   │   ├── layout.tsx  # Root layout
│   │   └── page.tsx    # Home page
│   └── components/     # Reusable components
│       ├── ProductInput.tsx  # URL/product name input
│       └── StreamingText.tsx # WebSocket streaming component
├── tailwind.config.js  # TailwindCSS configuration
└── ...                 # Configuration files
```

## WebSocket Integration

The frontend connects to a WebSocket server (by default at `ws://localhost:3001`) to receive streaming analysis results. You can configure the WebSocket URL in the `StreamingText` component.

## Carbon Footprint Analysis

This application provides a user-friendly interface for analyzing the environmental impact of products. Enter a product URL or name to receive a detailed lifecycle carbon analysis powered by AI, covering:

- Materials footprint
- Manufacturing processes
- Packaging analysis
- Transportation impacts
- Usage lifecycle
- End-of-life handling

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.
