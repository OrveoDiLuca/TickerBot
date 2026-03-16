# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev       # Start dev server with HMR
npm run build     # Type-check + production build (tsc -b && vite build)
npm run lint      # Run ESLint
npm run preview   # Preview production build
```

No test framework is configured.

## Architecture

**TickerBot** is a multi-agent financial analysis chatbot — React/TypeScript frontend, FastAPI Python backend, and an orchestrated AI agent system.

### Layout

Two-panel layout defined in `App.tsx`:
- **`SideBar.tsx`** — branding, "New Analysis" button, hardcoded recent analyses, navigation links, user profile
- **`Chat.tsx`** — main chat interface; manages `Message[]` state, renders user/bot messages, handles input

### Data flow

`Chat.tsx` owns all state. `Message` type (`src/types/index.ts`) has `{ id: string, role: 'user' | 'bot', text: string }`. IDs are generated with `uuid`. Bot responses are currently stubbed/placeholder.

### Styling

Tailwind CSS v4 (via `@tailwindcss/vite` plugin — no `tailwind.config.js` needed). Custom colors are applied via inline styles. Dark theme throughout.
- Primary blue: `#2b6cee`
- Background: `#101622` / `#151d2e`
- Border: `#222f47`

### SVG Icons

`src/helpers/Icons.tsx` exports `BotIcon` and `SendIcon` as React components.
