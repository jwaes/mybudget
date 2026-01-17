# Tasks: shadcn/ui Frontend Migration

**Input**: Design documents from `/specs/002-shadcn-ui-migration/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: Component tests included per constitution (Principle I: Test-First Development)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/`, `frontend/tests/`
- shadcn components: `frontend/src/components/ui/`
- Layout components: `frontend/src/components/layout/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize Tailwind CSS and shadcn/ui in the frontend project

- [ ] T001 Install Tailwind CSS dependencies (tailwindcss, postcss, autoprefixer) in frontend/package.json
- [ ] T002 Create Tailwind configuration in frontend/tailwind.config.js per quickstart.md
- [ ] T003 Create PostCSS configuration in frontend/postcss.config.js
- [ ] T004 Initialize shadcn/ui with New York style (creates frontend/components.json)
- [ ] T005 Create CSS variables and Tailwind directives in frontend/src/styles/globals.css
- [ ] T006 Update frontend/src/main.tsx to import styles/globals.css instead of index.css
- [ ] T007 [P] Verify path alias @/ is configured in frontend/tsconfig.json
- [ ] T008 [P] Install shadcn sidebar component (npx shadcn@latest add sidebar)
- [ ] T009 [P] Install shadcn button component (npx shadcn@latest add button)
- [ ] T010 [P] Install shadcn tooltip component (npx shadcn@latest add tooltip)
- [ ] T011 [P] Install shadcn dropdown-menu component (npx shadcn@latest add dropdown-menu)
- [ ] T012 Verify cn() utility exists in frontend/src/lib/utils.ts
- [ ] T013 Verify dev server starts without errors (npm run dev)

**Checkpoint**: shadcn/ui infrastructure ready - layout components can now be created

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create base layout infrastructure that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T014 Write test for SidebarLayout wrapper component in frontend/tests/components/layout/SidebarLayout.test.tsx
- [ ] T015 Create SidebarLayout wrapper component with SidebarProvider in frontend/src/components/layout/SidebarLayout.tsx
- [ ] T016 Write test for sidebar state persistence hook in frontend/tests/hooks/useSidebarState.test.ts
- [ ] T017 Create useSidebarState hook for session-based sidebar state in frontend/src/hooks/useSidebarState.ts
- [ ] T018 Update frontend/src/App.tsx to wrap routes with SidebarLayout

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Application Shell with Collapsible Sidebar (Priority: P1) 🎯 MVP

**Goal**: Create the main application layout with a collapsible sidebar containing navigation for Budget, Accounts, and Transactions pages

**Independent Test**: User can log in, see the sidebar with navigation items (Budget, Accounts, Transactions), collapse/expand the sidebar, and navigate between pages using the sidebar links

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T019 [P] [US1] Write test for AppSidebar component in frontend/tests/components/layout/AppSidebar.test.tsx
- [ ] T020 [P] [US1] Write test for NavMain navigation component in frontend/tests/components/layout/NavMain.test.tsx
- [ ] T021 [P] [US1] Write test for sidebar collapse/expand behavior in frontend/tests/components/layout/SidebarCollapse.test.tsx
- [ ] T022 [P] [US1] Write test for tooltip display on collapsed icons in frontend/tests/components/layout/SidebarTooltip.test.tsx
- [ ] T023 [P] [US1] Write test for active navigation highlighting in frontend/tests/components/layout/NavActive.test.tsx

### Implementation for User Story 1

- [ ] T024 [US1] Create AppSidebar component with header, content, footer sections in frontend/src/components/layout/AppSidebar.tsx
- [ ] T025 [US1] Create NavMain component with Budget, Accounts, Transactions nav items in frontend/src/components/layout/NavMain.tsx
- [ ] T026 [US1] Add lucide-react icons (LayoutGrid, Wallet, ArrowLeftRight) to navigation items
- [ ] T027 [US1] Implement sidebar collapse/expand with SidebarRail trigger in AppSidebar
- [ ] T028 [US1] Add tooltip wrapper for collapsed sidebar navigation items using shadcn Tooltip
- [ ] T029 [US1] Implement active route highlighting using React Router's useLocation
- [ ] T030 [US1] Add SidebarTrigger to page header for manual collapse toggle
- [ ] T031 [US1] Style sidebar collapse animation to complete in <300ms (SC-002)
- [ ] T032 [US1] Integrate AppSidebar into SidebarLayout in frontend/src/components/layout/SidebarLayout.tsx

**Checkpoint**: User Story 1 complete - sidebar navigation is fully functional and testable independently

---

## Phase 4: User Story 2 - User Menu with Profile and Logout (Priority: P2)

**Goal**: Add user information display and logout functionality to the sidebar footer

**Independent Test**: User can see their email in the sidebar user menu, click to open a dropdown, and successfully log out

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T033 [P] [US2] Write test for NavUser component in frontend/tests/components/layout/NavUser.test.tsx
- [ ] T034 [P] [US2] Write test for user dropdown menu behavior in frontend/tests/components/layout/UserDropdown.test.tsx
- [ ] T035 [P] [US2] Write test for logout flow in frontend/tests/components/layout/Logout.test.tsx

### Implementation for User Story 2

- [ ] T036 [US2] Create NavUser component displaying user email in frontend/src/components/layout/NavUser.tsx
- [ ] T037 [US2] Add DropdownMenu with "Log out" option to NavUser component
- [ ] T038 [US2] Integrate NavUser into AppSidebar footer section
- [ ] T039 [US2] Connect logout action to existing auth service (frontend/src/services/auth.ts)
- [ ] T040 [US2] Handle logout redirect to login page
- [ ] T041 [US2] Truncate long email addresses with ellipsis in collapsed sidebar (edge case)
- [ ] T042 [US2] Clear sidebar state preference on logout (edge case per spec)

**Checkpoint**: User Story 2 complete - user menu and logout work independently

---

## Phase 5: User Story 3 - Responsive Mobile Layout (Priority: P3)

**Goal**: Make the sidebar responsive for mobile devices (<768px viewport)

**Independent Test**: User can access the application on a mobile device, use a hamburger menu to access navigation, and navigate with auto-close behavior

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T043 [P] [US3] Write test for mobile sidebar trigger visibility in frontend/tests/components/layout/MobileSidebar.test.tsx
- [ ] T044 [P] [US3] Write test for sidebar overlay behavior on mobile in frontend/tests/components/layout/SidebarOverlay.test.tsx
- [ ] T045 [P] [US3] Write test for auto-close after navigation on mobile in frontend/tests/components/layout/MobileNavClose.test.tsx
- [ ] T046 [P] [US3] Write test for viewport transition behavior in frontend/tests/components/layout/ViewportTransition.test.tsx

### Implementation for User Story 3

- [ ] T047 [US3] Configure sidebar to hide on mobile (<768px) using Tailwind responsive classes
- [ ] T048 [US3] Add mobile menu trigger button visible only on mobile viewports
- [ ] T049 [US3] Implement sidebar as Sheet/overlay on mobile using shadcn Sheet component
- [ ] T050 [US3] Add auto-close behavior when navigation item is clicked on mobile
- [ ] T051 [US3] Handle viewport transition: reset to expanded on desktop, hidden on mobile (edge case)
- [ ] T052 [US3] Ensure touch targets are at least 44x44px on mobile (Constitution Principle VII)
- [ ] T053 [US3] Test layout renders correctly from 320px to 2560px width (SC-004)

**Checkpoint**: User Story 3 complete - mobile layout is fully responsive and testable

---

## Phase 6: User Story 4 - Consistent Component Styling (Priority: P4)

**Goal**: Migrate existing UI components to use shadcn/ui primitives for visual consistency

**Independent Test**: User can interact with buttons, form inputs, modals, and dropdowns across different pages and observe consistent styling

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T054 [P] [US4] Write test for Button component variants in frontend/tests/components/ui/Button.test.tsx
- [ ] T055 [P] [US4] Write test for Input component with validation states in frontend/tests/components/ui/Input.test.tsx
- [ ] T056 [P] [US4] Write test for Dialog component styling in frontend/tests/components/ui/Dialog.test.tsx
- [ ] T057 [P] [US4] Write test for focus states on all interactive elements in frontend/tests/components/ui/FocusStates.test.tsx

### Implementation for User Story 4

- [ ] T058 [P] [US4] Install remaining shadcn components: input, dialog, card, table, select (npx shadcn@latest add)
- [ ] T059 [US4] Migrate existing buttons to shadcn Button with primary/secondary/destructive variants
- [ ] T060 [US4] Migrate form inputs to shadcn Input component in all forms
- [ ] T061 [US4] Migrate modals/dialogs to shadcn Dialog component (AddTransaction, SetTarget, etc.)
- [ ] T062 [US4] Migrate data tables to shadcn Table component
- [ ] T063 [US4] Migrate select dropdowns to shadcn Select component
- [ ] T064 [US4] Ensure all interactive elements have visible focus states (SC-003)
- [ ] T065 [US4] Remove old component CSS classes that are now replaced by shadcn styling

**Checkpoint**: User Story 4 complete - all components have consistent shadcn styling

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, verification, and cross-cutting improvements

- [ ] T066 [P] Run all existing E2E tests to verify no regression (SC-005)
- [ ] T067 [P] Verify page load time increase is <20% (SC-006)
- [ ] T068 Delete frontend/src/index.css (replaced by globals.css)
- [ ] T069 Remove unused CSS classes from migrated components
- [ ] T070 Update frontend component imports to use @/ path alias consistently
- [ ] T071 Run quickstart.md verification checklist
- [ ] T072 Final code cleanup and unused import removal

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (sidebar) → US2 (user menu) → US3 (mobile) can proceed in sequence
  - US4 (component styling) can proceed in parallel with US2/US3 after US1 is done
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (sidebar must exist to add user menu to footer)
- **User Story 3 (P3)**: Depends on US1 (sidebar must exist to make responsive)
- **User Story 4 (P4)**: Can start after US1, no dependency on US2/US3

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Core component before dependent features
- Story complete before moving to next priority
- Constitution Principle I (TDD) must be followed

### Parallel Opportunities

- All Setup tasks T007-T011 marked [P] can run in parallel
- All tests for a user story marked [P] can run in parallel
- US4 (component styling) can run in parallel with US2/US3 after US1 completes

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all tests for User Story 1 together:
Task: "Write test for AppSidebar component in frontend/tests/components/layout/AppSidebar.test.tsx"
Task: "Write test for NavMain navigation component in frontend/tests/components/layout/NavMain.test.tsx"
Task: "Write test for sidebar collapse/expand behavior in frontend/tests/components/layout/SidebarCollapse.test.tsx"
Task: "Write test for tooltip display on collapsed icons in frontend/tests/components/layout/SidebarTooltip.test.tsx"
Task: "Write test for active navigation highlighting in frontend/tests/components/layout/NavActive.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T013)
2. Complete Phase 2: Foundational (T014-T018)
3. Complete Phase 3: User Story 1 (T019-T032)
4. **STOP and VALIDATE**: Test sidebar navigation independently
5. Deploy/demo if ready - basic sidebar layout functional

### Incremental Delivery

1. Complete Setup + Foundational → Infrastructure ready
2. Add User Story 1 → Test independently → Deploy (MVP - sidebar layout)
3. Add User Story 2 → Test independently → Deploy (user menu + logout)
4. Add User Story 3 → Test independently → Deploy (mobile responsive)
5. Add User Story 4 → Test independently → Deploy (full component consistency)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once US1 is done:
   - Developer A: User Story 2 (user menu)
   - Developer B: User Story 3 (mobile)
   - Developer C: User Story 4 (component styling)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow Constitution Principles VI (shadcn) and VII (responsive) throughout
