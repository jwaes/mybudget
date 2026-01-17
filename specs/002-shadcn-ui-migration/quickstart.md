# Quickstart: shadcn/ui Frontend Migration

**Feature**: 002-shadcn-ui-migration
**Time to Setup**: ~10 minutes

## Prerequisites

- Node.js 18+ installed
- MyBudget frontend running (`cd frontend && npm install && npm run dev`)
- Familiarity with React and TypeScript

## Setup Steps

### 1. Initialize Tailwind CSS

```bash
cd frontend

# Install Tailwind and dependencies
npm install -D tailwindcss postcss autoprefixer

# Initialize Tailwind
npx tailwindcss init -p
```

### 2. Configure Tailwind

Update `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### 3. Initialize shadcn/ui

```bash
npx shadcn@latest init
```

When prompted:
- Style: **New York**
- Base color: **Zinc**
- CSS variables: **Yes**
- Tailwind CSS config: `tailwind.config.js`
- Components: `@/components`
- Utils: `@/lib/utils`
- React Server Components: **No** (Vite doesn't use RSC)

### 4. Install Sidebar Components

```bash
# Install the sidebar block (includes all sidebar primitives)
npx shadcn@latest add sidebar

# Install additional components we'll need
npx shadcn@latest add button dropdown-menu tooltip dialog input card table
```

### 5. Update CSS Entry Point

Replace `src/index.css` content with `src/styles/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 240 5.9% 10%;
    --radius: 0.5rem;
    --sidebar-background: 0 0% 98%;
    --sidebar-foreground: 240 5.3% 26.1%;
    --sidebar-primary: 240 5.9% 10%;
    --sidebar-primary-foreground: 0 0% 98%;
    --sidebar-accent: 240 4.8% 95.9%;
    --sidebar-accent-foreground: 240 5.9% 10%;
    --sidebar-border: 220 13% 91%;
    --sidebar-ring: 240 5.9% 10%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### 6. Update main.tsx

```tsx
import './styles/globals.css'  // Changed from './index.css'
```

### 7. Verify Setup

```bash
npm run dev
```

The application should still work (existing CSS still applies).

## Development Workflow

### Adding New Components

```bash
# Search for a component
npx shadcn@latest search button

# Add a component
npx shadcn@latest add [component-name]
```

### Using Components

```tsx
import { Button } from "@/components/ui/button"

function MyComponent() {
  return <Button variant="outline">Click me</Button>
}
```

### Running Tests

```bash
# Unit tests
npm test

# E2E tests (verify no regressions)
npm run test:e2e
```

## Verification Checklist

After setup, verify:

- [ ] `npm run dev` starts without errors
- [ ] Existing pages render correctly
- [ ] No TypeScript errors in IDE
- [ ] `components.json` exists in frontend root
- [ ] `tailwind.config.js` is configured
- [ ] `src/lib/utils.ts` contains `cn()` function

## Troubleshooting

### "Cannot find module '@/components/ui/button'"

Ensure `tsconfig.json` has path alias:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Styles not applying

1. Check `globals.css` is imported in `main.tsx`
2. Verify Tailwind content paths in `tailwind.config.js`
3. Restart dev server after config changes

### Component not found after install

Run `npx shadcn@latest add [component]` again - it's idempotent.

## Next Steps

After setup is complete:
1. Create layout components (AppSidebar, NavMain, NavUser)
2. Update App.tsx to use new layout
3. Migrate existing components to use shadcn primitives
4. Remove old CSS once migration complete
