# Arc Payroll Frontend

This is the frontend management interface for the Arc Payroll system, built with Next.js 15.

## Features

- 📊 **Dashboard Overview**: Display current month batches, amounts, success rates, anomaly statistics
- 📋 **Batch Management**: View batch list, details, transaction status
- 📈 **Report Downloads**: Download reconciliation reports (CSV)
- ⚙️ **System Settings**: Configure RPC, caps and other parameters
- 🎨 **Modern UI**: Uses Tailwind CSS, responsive design

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **UI Styling**: Tailwind CSS
- **State Management**: React Query (TanStack Query)
- **Data Validation**: Zod
- **Charts**: Recharts
- **HTTP Client**: Axios

## Environment Setup

1. **Copy environment variable template**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file**
   ```bash
   # Set backend API URL
   NEXT_PUBLIC_BACKEND_BASE_URL=http://localhost:8080
   ```

3. **Install dependencies**
   ```bash
   npm install
   ```

## Development

### Start Development Server
```bash
npm run dev
```

Open browser and visit [http://localhost:3000](http://localhost:3000)

### Build Production Version
```bash
npm run build
npm start
```

### Type Check
```bash
npm run type-check
```

### Lint Check
```bash
npm run lint
```

## Docker Deployment

### Build Image
```bash
docker build -t arc-payroll-frontend .
```

### Run Container
```bash
docker run -d \
  -p 3000:3000 \
  --env-file .env \
  --name arc-payroll-frontend \
  arc-payroll-frontend
```

## Page Structure

```
src/app/
├── layout.tsx           # Root layout (navigation bar)
├── page.tsx             # Home page - Dashboard
├── globals.css          # Global styles
├── batches/
│   ├── page.tsx         # Batch list page
│   └── [batchId]/
│       └── page.tsx     # Batch detail page
└── settings/
    └── page.tsx         # Settings page
```

## API Integration

Frontend communicates with backend API via Axios:

```typescript
// Example: Get batch list
const response = await axios.get(
  `${process.env.NEXT_PUBLIC_BACKEND_BASE_URL}/batches`
)
```

### Main API Endpoints

- `GET /healthz` - Health check
- `GET /batches` - Get batch list
- `GET /batches/:batchId` - Get batch details
- `POST /admin/trigger` - Manually trigger batch
- `GET /reports/:month/reconcile` - Download reconciliation report

## Development Guidelines

### Component Naming Convention

- **Page Components**: Use PascalCase (e.g. `BatchListPage`)
- **UI Components**: Use PascalCase (e.g. `StatCard`)
- **File Names**: Use kebab-case (e.g. `stat-card.tsx`)

### Styling Guidelines

- Prefer Tailwind CSS utility classes
- Avoid custom CSS (unless necessary)
- Use predefined Design Tokens (defined in `tailwind.config.ts`)

### Code Style

- Use TypeScript strict mode
- Follow ESLint rules
- Every function should have JSDoc comments (in English)

## Directory Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # Shared components (to be created)
│   ├── lib/              # Utility functions (to be created)
│   └── types/            # TypeScript type definitions (to be created)
├── public/               # Static assets
├── .env.example          # Environment variable template
├── Dockerfile            # Docker build file
├── next.config.js        # Next.js configuration
├── tailwind.config.ts    # Tailwind CSS configuration
├── tsconfig.json         # TypeScript configuration
├── package.json          # Dependency management
└── README.md             # This file
```

## TODOs

- [ ] Complete batch list page
- [ ] Batch detail page (with transaction records)
- [ ] Report download functionality
- [ ] Settings page
- [ ] Authentication (NextAuth)
- [ ] Error handling & Toast notifications
- [ ] Loading states
- [ ] Dark mode

## License

MIT
