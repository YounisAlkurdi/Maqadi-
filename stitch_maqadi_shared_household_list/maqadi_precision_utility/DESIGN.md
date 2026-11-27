---
name: Maqadi Precision Utility
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#3f493f'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#6f7a6e'
  outline-variant: '#becabc'
  surface-tint: '#006d30'
  primary: '#00652c'
  on-primary: '#ffffff'
  primary-container: '#15803d'
  on-primary-container: '#d3ffd5'
  inverse-primary: '#79db8d'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3fd'
  on-secondary-container: '#57657b'
  tertiary: '#4f576d'
  on-tertiary: '#ffffff'
  tertiary-container: '#676f86'
  on-tertiary-container: '#f2f3ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#95f8a7'
  primary-fixed-dim: '#79db8d'
  on-primary-fixed: '#00210a'
  on-primary-fixed-variant: '#005323'
  secondary-fixed: '#d5e3fd'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2f'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-xl:
    fontFamily: IBM Plex Sans
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: IBM Plex Sans
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: IBM Plex Sans
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: IBM Plex Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.005em
  headline-sm:
    fontFamily: IBM Plex Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  title-md:
    fontFamily: IBM Plex Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
  title-sm:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  body-lg:
    fontFamily: IBM Plex Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: IBM Plex Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-md:
    fontFamily: IBM Plex Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  label-sm:
    fontFamily: IBM Plex Sans
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
  code:
    fontFamily: IBM Plex Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-md: 1.5rem
  gutter-lg: 2rem
  margin: 1rem
  margin-md: 2rem
  margin-lg: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

The design system establishes a high-performance, calm, and hyper-structured digital workspace tailored for collaborative Arabic household operations. Balancing the utilitarian precision of contemporary software (such as Linear and Notion) with the domestic warmth of home management, the aesthetic is pristine, intentional, and clutter-free. 

Key attributes:
- **Tone:** Authoritative, understated, disciplined, and frictionless.
- **Audience:** Contemporary Arabic households, multi-generational families, and busy domestic organizers requiring immediate clarity and speed.
- **Visual Stance:** Ultra-refined light minimalism with tactile clarity. The layout relies on crisp 1px borders, subtle tonal variations, generous white space, and balanced density to render lists, chores, and pantry inventories readable at a glance without visual fatigue. Native Right-to-Left (RTL) mechanics drive reading flow and spatial interactions.

## Colors

The color architecture creates crisp contrast, immediate status recognition, and serene organization across data-dense screens.

### Palette Architecture
- **Primary Brand Base:** Deep Forest Emerald (`#15803D`) with dynamic state variants (`#16A34A` for interactive hovers, `#DCFCE7` for positive completion badges). It conveys stability, freshness, and accomplishment.
- **Canvas & Neutral Foundation:** The application canvas runs on Slate 50 (`#F8FAFC`) with structural structural dividers and inset wells in Slate 100 (`#F1F5F9`). Active interactable surfaces rest on Pure White (`#FFFFFF`).
- **High-Contrast Typography Scale:** Headings and critical copy deploy Slate 900 (`#0F172A`), sustained body copy anchors on Slate 700 (`#334155`), and supportive metadata/hints utilize Slate 500 (`#64748B`). Border structures conform systematically to Slate 200 (`#E2E8F0`).
- **Functional Semantics:**
  - *Urgent / Out of Stock:* Rose 600 (`#EF4444`) on Rose 50 (`#FEE2E2`).
  - *Duplicate Warning / Pending Verification:* Amber 600 (`#F59E0B`) on Amber 50 (`#FEF3C7`).
- **Family Identification Tokens:** Distinct member assignments utilize muted, sophisticated avatar tokens: Teal (`#0D9488`), Indigo (`#4F46E5`), Amber (`#D97706`), Emerald (`#059669`), Violet (`#7C3AED`), and Rose (`#E11D48`).

## Typography

The type system prioritizes IBM Plex Sans (and its Arabic variant) for its engineering clarity, open counterforms, and balanced vertical metrics. Arabic and Latin copy integrate smoothly within single task runs.

### Hierarchical Guidelines
- **Headings (Semibold 600):** Controlled vertical rhythm with reduced letter spacing to maintain visual authority without taking excessive canvas room.
- **Labels & Interactive Affordances (Medium 500):** Applied across filtering chips, inputs, table heads, and status indicators to maintain legibility when compact.
- **Body & Secondary Copy (Regular 400):** Generous line height relative to font size ensures long item titles, notes, and nutritional details remain comfortable across high-density checklists.

## Layout & Spacing

A mathematical 8px base rhythm orchestrates layout and density across all device breakpoints. The system relies on a fluid grid bounded by structured max-widths (`1280px` for operations dashboards, `640px` for mobile list views).

### Breakpoints & Fluid Scaling
- **Mobile (< 768px):** Single-column layout. Margin set to `1rem` (16px), gutters set to `1rem` (16px). Bottom sheets and sticky task bars replace hover panels.
- **Tablet (768px – 1024px):** 8-column layout. Margin set to `2rem` (32px), gutters set to `1.5rem` (24px). Sidebar navigations collapse into iconography rails.
- **Desktop (> 1024px):** 12-column layout. Margin set to `3rem` (48px), gutters set to `2rem` (32px). Persistent navigation drawer on the right side (RTL), dual-column master-detail views for active lists and item specifications.

### RTL Spacing Axioms
- Start padding and margin map to physical right; end padding and margin map to physical left.
- Numeric counters, drag handles, and status indicators align flush right with copy reading naturally toward the left.

## Elevation & Depth

Visual hierarchy does not rely on heavy dropped shadows. Instead, it uses structural 1px borders, subtle surface offsets, and soft diffused ambient shadows.

### Elevation Hierarchy
1. **Base Surface (Level 0):** Canvas `#F8FAFC`. Zero elevation, non-interactive foundation.
2. **Resting Interactive Surface (Level 1):** Solid `#FFFFFF`, bordered by 1px solid `#E2E8F0`, with `box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.05)`. Used for item list cards, pantry bins, and category buckets.
3. **Hover & Active Surface (Level 2):** Solid `#FFFFFF`, bordered by 1px solid `#CBD5E1`, with `box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.04)`. Applied to active dragging items, dropdowns, and focused cards.
4. **Modal & Floating Dialogs (Level 3):** Solid `#FFFFFF`, bordered by 1px solid `#E2E8F0`, with `box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04)`. Used for quick item additions, filter drawers, and confirmation dialogues.

## Shapes

The shape scale relies on a calibrated `Rounded` baseline (`roundedness: 2`). This avoids cold industrial sharpness while keeping list layouts crisp and organized.

### Scale Application
- **Default (0.5rem / 8px):** Checkboxes, form fields, action buttons, small avatars, and metadata chips.
- **Medium / Large (1rem / 16px):** Core cards, list containers, actionable modules, and persistent quick-entry headers.
- **Extra-Large (1.5rem / 24px):** Dialog modals, bottom action sheets, and family management panels.
- **Pill (Fully Rounded):** Member assignment avatars, quick-filter tag toggles, and status badges.

## Components

### Buttons
- **Primary:** Solid `#15803D` background, `#FFFFFF` text, `0.5rem` radius, 1px transparent border. Hover shifts to `#16A34A`. Focus ring creates a 2px offset in `#15803D`.
- **Secondary:** Surface `#FFFFFF`, 1px border `#E2E8F0`, text `#334155`. Hover shifts to `#F1F5F9` and text to `#0F172A`.
- **Ghost / Destructive:** No background in rest state; text `#EF4444`. Hover shifts background to `#FEE2E2`.

### Chips & Filter Tags
- **Default Filter:** Height `32px`, padding `0 12px`, border 1px solid `#E2E8F0`, background `#FFFFFF`, text `#64748B`.
- **Selected Filter:** Background `#DCFCE7`, border 1px solid `#86EFAC`, text `#15803D`, font weight `500`.

### Lists & Shopping Rows
- **Container Structure:** Rows have a uniform height of `56px`, 1px border-bottom `#F1F5F9`, flex layout with right-aligned interactive checkboxes.
- **Completed Item State:** Text style switches to `line-through`, color dims to `#94A3B8`, checkbox fills with `#15803D`.
- **Drag Handle:** Subtle 6-dot indicator in `#CBD5E1` positioned at the outer right margin for quick reordering.

### Checkboxes & Radios
- **Geometry:** 20px x 20px square with a `6px` radius. 
- **Resting:** 1.5px border `#CBD5E1`, background `#FFFFFF`.
- **Checked:** Background `#15803D`, border `#15803D`, displaying a clean `#FFFFFF` checkmark.

### Input Fields & Quick Add Bar
- **Field Anatomy:** Height `44px`, background `#FFFFFF`, border 1px solid `#E2E8F0`, text `#0F172A`, placeholder text `#94A3B8`.
- **Focused State:** 1px border `#15803D`, with `0 0 0 3px rgba(21, 128, 61, 0.1)`.
- **RTL Prefix & Suffix:** Quantities and category pickers nest cleanly at the left edge (LTR end / RTL visual left), allowing unobstructed RTL typing from the right.

### Cards & Grouping Buckets
- Crisp white background (`#FFFFFF`), 16px corner radius, 1px border `#E2E8F0`, 16px to 24px inner padding. Headers include title, badge counter, and action dropdown.

### Family Member Avatars & Tooltips
- Circular (full pill) 32px or 28px diameter elements displaying localized initial glyphs. 2px white border offset for stacked avatar clusters. Clicking opens a tooltip with member details and errand responsibilities.