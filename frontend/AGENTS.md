# Frontend Codebase Guide

## Overview

A Next.js 16 Kanban board app using React 19, TypeScript, Tailwind CSS 4, and @dnd-kit for drag-and-drop. Currently a client-side-only demo with no backend integration.

## Directory Structure

```
frontend/
  src/
    app/
      globals.css          # CSS custom properties (colors, fonts, surfaces)
      layout.tsx           # Root layout, loads Space Grotesk + Manrope fonts
      page.tsx             # Home page, renders KanbanBoard
    components/
      KanbanBoard.tsx      # Main board: state, drag-drop context, column rendering
      KanbanBoard.test.tsx # Unit tests for board (renders columns, rename, add/delete cards)
      KanbanColumn.tsx     # Column: editable title, droppable zone, card list, empty state
      KanbanCard.tsx       # Draggable card with title, details, delete button
      KanbanCardPreview.tsx # Ghost card shown during drag
      NewCardForm.tsx      # Toggle form for adding cards (title required, details optional)
    lib/
      kanban.ts            # Types (Board, Column, Card), moveCard logic, initialData, createId
      kanban.test.ts       # Unit tests for moveCard (reorder, cross-column, empty column)
    test/
      setup.ts             # Vitest setup
      vitest.d.ts          # Type definitions for test matchers
  tests/
    kanban.spec.ts         # Playwright E2E tests (board loads, add card, drag card)
  package.json             # Dependencies and scripts
  vitest.config.ts         # Vitest config (jsdom, coverage)
  playwright.config.ts     # Playwright config
  next.config.ts           # Next.js config (minimal)
  tsconfig.json            # TypeScript config
  postcss.config.mjs       # PostCSS with Tailwind plugin
  eslint.config.mjs        # ESLint config
```

## Key Concepts

### State Model

All state lives in `KanbanBoard.tsx` via `useState`:
- `board: { columns: Column[], cards: Record<string, Card> }` -- columns hold ordered card ID arrays; cards stored in a flat map for O(1) lookup.
- `activeCardId: string | null` -- tracks which card is being dragged.

No persistence. State resets on page reload.

### Columns

Five fixed columns: Backlog, Discovery, In Progress, Review, Done. Titles are editable inline. Columns cannot be added or removed.

### Cards

Each card has `id`, `title`, `details`. Cards can be added (via NewCardForm), deleted, dragged within a column (reorder), or dragged between columns (move).

### Drag-and-Drop

Uses @dnd-kit with PointerSensor (6px activation distance), closestCorners collision detection:
- Cards use `useSortable()` hook
- Columns use `useDroppable()` hook
- `DragOverlay` renders `KanbanCardPreview` during drag
- `moveCard()` in `kanban.ts` handles the array manipulation

### ID Generation

`createId(prefix)` returns `${prefix}-${random}${timestamp}` for unique IDs.

### Styling

Tailwind CSS 4 utility classes. CSS custom properties in `globals.css` define the color scheme, fonts, surfaces, and shadows. No CSS modules. Responsive grid (single column on small screens, 5-column on lg+).

## Dependencies

- next 16.1.6, react 19.2.3, typescript 5
- @dnd-kit/core 6.3.1, @dnd-kit/sortable 10.0.0, @dnd-kit/utilities 3.2.2
- tailwindcss 4, @tailwindcss/postcss 4, clsx 2.1.1
- vitest 3.2.4, @testing-library/react 16.3.2, playwright 1.58.0

## Scripts (from package.json)

- `npm run dev` -- dev server
- `npm run build` -- production build
- `npm run start` -- start production server
- `npm test` -- run vitest
- `npm run test:e2e` -- run playwright tests
