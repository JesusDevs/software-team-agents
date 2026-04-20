# UX Design Principles

## Core Principles
1. **User-centered** — every decision justified by user need
2. **Consistency** — same patterns for same actions across all screens
3. **Feedback** — every action gets immediate visual response
4. **Error prevention** — design to make errors impossible before correcting them
5. **Accessibility** — WCAG 2.1 AA minimum compliance

## Layout Patterns
### Dashboard Layout
- Sidebar navigation (64px collapsed, 240px expanded)
- Top bar: breadcrumb + user avatar + notifications
- Main content: 12-column grid, 24px gutters
- Cards: 16px padding, 8px border-radius, subtle shadow

### Form Layout
- Single column for mobile, 2-column max for desktop
- Labels above inputs (not inline)
- Real-time validation (on blur, not on change)
- Primary CTA always visible without scroll

## Navigation Patterns
- Max 2 levels of hierarchy in nav
- Current location always visible (breadcrumb)
- Back navigation always available
- No dead ends

## Interaction Patterns
- Loading states: skeleton screens (not spinners) for content
- Empty states: always provide CTA to fill the empty state
- Confirmation dialogs: only for destructive or irreversible actions
- Toasts: success (3s), error (persistent until dismissed)

## Design Tokens (Base)
```
Colors:
  primary: #2563EB     (blue-600)
  secondary: #7C3AED   (violet-600)
  success: #16A34A     (green-600)
  warning: #D97706     (amber-600)
  error: #DC2626       (red-600)
  neutral-50: #F9FAFB
  neutral-900: #111827

Typography:
  font-family: Inter, system-ui, sans-serif
  size-xs: 12px
  size-sm: 14px
  size-base: 16px
  size-lg: 18px
  size-xl: 20px
  size-2xl: 24px

Spacing (4px grid):
  xs: 4px | sm: 8px | md: 16px | lg: 24px | xl: 32px | 2xl: 48px

Border radius:
  sm: 4px | md: 8px | lg: 12px | full: 9999px
```
