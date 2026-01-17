# Research: shadcn/ui Frontend Migration

**Feature**: 002-shadcn-ui-migration
**Date**: 2026-01-17

## Research Questions Resolved

### 1. shadcn/ui Installation with Vite

**Decision**: Use `npx shadcn@latest init` with manual Vite configuration

**Rationale**:
- shadcn/ui officially supports Vite as of 2024
- The CLI handles most configuration automatically
- Vite's fast HMR works well with Tailwind CSS

**Alternatives Considered**:
- Manual setup: More control but error-prone
- Create React App migration: Would require additional tooling changes

### 2. Style Variant Selection

**Decision**: New York style

**Rationale**:
- Cleaner, more compact design suitable for data-heavy financial applications
- Professional appearance for financial software
- Works well with tables and forms (common in budget apps)

**Alternatives Considered**:
- Default style: More spacious, better for marketing sites
- Custom theme: Would require additional design work

### 3. Base Color Palette

**Decision**: Neutral (zinc)

**Rationale**:
- Professional, business-appropriate color
- Works well with positive/negative financial indicators (green/red)
- Not distracting when viewing financial data
- Good contrast for accessibility

**Alternatives Considered**:
- Slate: Similar but cooler tone
- Stone: Warmer but less professional
- Gray: Too plain, lacks character

### 4. CSS Variables vs Direct Colors

**Decision**: Use CSS variables

**Rationale**:
- Enables future dark mode implementation without code changes
- Easier theme customization
- Better integration with shadcn/ui's theming system
- Follows shadcn/ui best practices

**Alternatives Considered**:
- Direct Tailwind colors: Simpler but harder to theme later

### 5. Migration Strategy

**Decision**: Incremental migration (not big-bang)

**Rationale**:
- Lower risk - can catch issues early
- Maintains working application throughout migration
- Easier to roll back specific changes
- Allows testing at each stage
- Follows constitution's simplicity principle

**Alternatives Considered**:
- Big-bang rewrite: Faster but higher risk of regressions
- Parallel development: More complex, harder to maintain

### 6. Sidebar Implementation

**Decision**: Use sidebar-07 block as base

**Rationale**:
- Matches exact requirements (collapsible to icons)
- Includes all needed sub-components (nav, user menu, rail)
- Mobile-responsive out of the box
- Well-tested by shadcn/ui community

**Alternatives Considered**:
- sidebar-01: Simpler but doesn't collapse to icons
- Custom implementation: More work, less reliable

### 7. Component Installation Order

**Decision**: Install sidebar block first, then primitives as needed

**Rationale**:
- Sidebar block installs many dependencies automatically
- Avoids duplicate installations
- Establishes layout foundation before styling details

**Installation Sequence**:
1. `npx shadcn@latest init` - Initialize project
2. `npx shadcn@latest add sidebar` - Sidebar primitives
3. Install remaining components as needed during migration

### 8. Existing CSS Handling

**Decision**: Keep existing CSS during migration, remove after completion

**Rationale**:
- Non-migrated components continue to work
- Prevents visual regressions during migration
- Clean removal once all components migrated

**Migration Pattern**:
1. Add Tailwind/shadcn styles
2. Migrate component to use new styles
3. Verify component works
4. Remove old CSS for that component
5. Repeat until complete
6. Remove index.css entirely

## Dependencies Analysis

### Core Dependencies (Required)

| Package | Version | Purpose |
|---------|---------|---------|
| tailwindcss | ^3.4.0 | Utility-first CSS framework |
| postcss | ^8.4.0 | CSS processing |
| autoprefixer | ^10.4.0 | CSS vendor prefixes |
| class-variance-authority | ^0.7.0 | Component variants |
| clsx | ^2.1.0 | Conditional classes |
| tailwind-merge | ^2.2.0 | Merge Tailwind classes |
| lucide-react | ^0.400.0 | Icons |

### Radix UI Primitives (Installed by shadcn)

| Package | Purpose | Used By |
|---------|---------|---------|
| @radix-ui/react-slot | Slot composition | Button |
| @radix-ui/react-tooltip | Tooltips | Sidebar collapse |
| @radix-ui/react-dropdown-menu | Dropdowns | User menu |
| @radix-ui/react-dialog | Modals | All dialogs |
| @radix-ui/react-collapsible | Collapse | Sidebar sections |
| @radix-ui/react-separator | Dividers | Visual separation |

### No Backend Changes

This migration is frontend-only. No API contract changes required.

## Performance Considerations

### Bundle Size Impact

- Tailwind CSS: ~10KB (gzipped) with PurgeCSS
- Radix UI primitives: ~5-15KB per component (tree-shaken)
- lucide-react: Only used icons included

**Mitigation**:
- Tree-shaking removes unused code
- Dynamic imports for larger components if needed

### Animation Performance

- Sidebar collapse uses CSS transforms (GPU accelerated)
- Target: < 300ms animation duration
- Uses `will-change` for smooth transitions

## Accessibility Notes

From shadcn/ui's Radix UI foundation:
- Full keyboard navigation support
- ARIA attributes automatically applied
- Focus management handled
- Screen reader announcements

## Browser Compatibility

Tailwind CSS v3.4 supports:
- Chrome 88+
- Firefox 78+
- Safari 14+
- Edge 88+

All within spec requirement (latest 2 versions).
