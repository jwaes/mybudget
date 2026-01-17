# Implementation Plan: shadcn/ui Frontend Migration

**Branch**: `002-shadcn-ui-migration` | **Date**: 2026-01-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-shadcn-ui-migration/spec.md`

## Summary

Migrate MyBudget frontend from custom CSS styling to shadcn/ui components with Tailwind CSS. The primary change is adopting the sidebar-07 layout pattern (collapsible icon sidebar) with navigation for Budget, Accounts, and Transactions pages, plus a user menu at the bottom. All existing functionality must be preserved.

## Technical Context

**Language/Version**: TypeScript 5.8 (frontend)
**Primary Dependencies**: React 19, shadcn/ui (New York style), Tailwind CSS v3.x, Radix UI primitives, lucide-react (icons), React Router v7
**Storage**: N/A (frontend-only migration, no data model changes)
**Testing**: Vitest + React Testing Library (unit/component), Playwright (E2E)
**Target Platform**: Web browsers - Chrome, Firefox, Safari, Edge (latest 2 versions)
**Project Type**: Web application (frontend only)
**Performance Goals**: Sidebar animation < 300ms, page load increase < 20%
**Constraints**: Mobile breakpoint 768px, light theme only (dark theme out of scope)
**Scale/Scope**: 3 main pages (Budget, Accounts, Transactions), ~15 components to migrate

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | Component tests written before migrating components |
| II. Comprehensive Unit Testing | ✅ PASS | Vitest + RTL for component testing; target 90%+ coverage |
| III. Type Safety | ✅ PASS | TypeScript strict mode; shadcn components are fully typed |
| IV. Code Quality Standards | ✅ PASS | ESLint, Prettier; existing quality gates maintained |
| V. Simplicity First | ✅ PASS | Use shadcn primitives directly; no custom abstractions |
| VI. Consistent UI with shadcn/ui | ✅ PASS | This feature establishes shadcn/ui as the UI standard |
| VII. Responsive Design | ✅ PASS | Mobile breakpoint 768px; sidebar adapts to screen size |

**No violations requiring justification.**

## Project Structure

### Documentation (this feature)

```text
specs/002-shadcn-ui-migration/
├── plan.md              # This file
├── research.md          # Phase 0: shadcn setup, Tailwind integration patterns
├── data-model.md        # N/A (no data model changes)
├── quickstart.md        # Phase 1: Setup and migration guide
├── contracts/           # N/A (no API changes)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn primitive components (button, input, etc.)
│   │   ├── layout/          # App shell components
│   │   │   ├── AppSidebar.tsx       # Main sidebar component
│   │   │   ├── NavMain.tsx          # Main navigation items
│   │   │   ├── NavUser.tsx          # User menu at bottom
│   │   │   └── SidebarLayout.tsx    # Layout wrapper with SidebarProvider
│   │   └── [existing]/      # Migrated existing components
│   ├── pages/               # Page components (updated to use new layout)
│   ├── services/            # Unchanged - API services
│   ├── lib/
│   │   ├── utils.ts         # shadcn cn() utility
│   │   └── [existing]/      # Existing utilities
│   └── styles/
│       └── globals.css      # Tailwind directives + CSS variables
├── components.json          # shadcn configuration
├── tailwind.config.js       # Tailwind configuration
├── postcss.config.js        # PostCSS for Tailwind
└── tests/
    ├── components/          # Component tests
    │   └── layout/          # Layout component tests
    └── e2e/                 # E2E tests (verify no regression)
```

**Structure Decision**: Frontend-only changes. New `ui/` and `layout/` directories under components. Existing components migrated in-place to use shadcn primitives.

## Complexity Tracking

> No violations requiring justification - all principles satisfied.

## Phase 0: Research Summary

### Key Decisions

1. **shadcn Installation Method**: Use `npx shadcn@latest init` with Vite configuration
2. **Style Variant**: New York (cleaner, more professional for financial app)
3. **Base Color**: Neutral (zinc) - professional, works well with financial data
4. **CSS Variables**: Yes - enables easy theming if dark mode added later
5. **Component Installation**: Install sidebar-07 block, then individual components as needed

### Dependencies to Add

```json
{
  "dependencies": {
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    "lucide-react": "^0.400.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tooltip": "^1.0.7",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-collapsible": "^1.0.3"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

### Migration Strategy

**Incremental approach** (not big-bang):
1. Setup Tailwind + shadcn (non-breaking)
2. Add sidebar layout alongside existing layout
3. Migrate pages one-by-one to use new layout
4. Replace existing components with shadcn equivalents
5. Remove old CSS once migration complete

## Phase 1: Design Artifacts

### Components to Install from shadcn

| Component | Purpose | FR Mapping |
|-----------|---------|------------|
| sidebar | Main layout component | FR-001, FR-002, FR-009, FR-010 |
| button | Action buttons | FR-012 |
| input | Form text inputs | FR-013 |
| select | Dropdown selects | FR-013 |
| dialog | Modal dialogs | FR-014 |
| dropdown-menu | User menu dropdown | FR-007 |
| tooltip | Collapsed sidebar tooltips | FR-003 |
| card | Content containers | FR-012 |
| table | Data tables | FR-012 |

### Navigation Structure

```typescript
const navItems = [
  {
    title: "Budget",
    url: "/budget",
    icon: LayoutGrid,
    isActive: (path) => path === "/" || path === "/budget"
  },
  {
    title: "Accounts",
    url: "/accounts",
    icon: Wallet,
  },
  {
    title: "Transactions",
    url: "/transactions",
    icon: ArrowLeftRight,
  }
]
```

### Layout Component Hierarchy

```
<SidebarProvider>
  <AppSidebar>
    <SidebarHeader>
      <AppLogo />
    </SidebarHeader>
    <SidebarContent>
      <NavMain items={navItems} />
    </SidebarContent>
    <SidebarFooter>
      <NavUser user={currentUser} onLogout={handleLogout} />
    </SidebarFooter>
    <SidebarRail />
  </AppSidebar>
  <SidebarInset>
    <header>
      <SidebarTrigger />
      <Breadcrumb />
    </header>
    <main>
      {children}
    </main>
  </SidebarInset>
</SidebarProvider>
```

### File Changes Summary

| File | Action | Notes |
|------|--------|-------|
| `tailwind.config.js` | CREATE | Tailwind configuration |
| `postcss.config.js` | CREATE | PostCSS configuration |
| `components.json` | CREATE | shadcn configuration |
| `src/styles/globals.css` | CREATE | CSS variables + Tailwind |
| `src/lib/utils.ts` | CREATE | cn() utility |
| `src/components/ui/*` | CREATE | shadcn primitives |
| `src/components/layout/*` | CREATE | Layout components |
| `src/components/AppLayout.tsx` | MODIFY | Use new sidebar layout |
| `src/pages/*.tsx` | MODIFY | Update to use shadcn components |
| `src/index.css` | DELETE | Replace with globals.css |

## Next Steps

Run `/speckit.tasks` to generate the task breakdown for implementation.
