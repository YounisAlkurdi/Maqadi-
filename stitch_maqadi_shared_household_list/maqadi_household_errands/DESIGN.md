---
name: Maqadi Household Errands
colors:
  surface: '#f2fcf5'
  surface-dim: '#d2dcd6'
  surface-bright: '#f2fcf5'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#ecf6ef'
  surface-container: '#e6f0ea'
  surface-container-high: '#e1ebe4'
  surface-container-highest: '#dbe5de'
  on-surface: '#151d1a'
  on-surface-variant: '#3e4941'
  inverse-surface: '#29322e'
  inverse-on-surface: '#e9f3ec'
  outline: '#6e7a71'
  outline-variant: '#bdcabf'
  surface-tint: '#006d44'
  primary: '#006a42'
  on-primary: '#ffffff'
  primary-container: '#168556'
  on-primary-container: '#f6fff6'
  inverse-primary: '#77daa4'
  secondary: '#00696f'
  on-secondary: '#ffffff'
  secondary-container: '#9eedf3'
  on-secondary-container: '#0c6d73'
  tertiary: '#7b5500'
  on-tertiary: '#ffffff'
  tertiary-container: '#9a6c00'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#93f7be'
  primary-fixed-dim: '#77daa4'
  on-primary-fixed: '#002111'
  on-primary-fixed-variant: '#005232'
  secondary-fixed: '#a1f0f6'
  secondary-fixed-dim: '#85d3da'
  on-secondary-fixed: '#002022'
  on-secondary-fixed-variant: '#004f54'
  tertiary-fixed: '#ffdeab'
  tertiary-fixed-dim: '#fabc4a'
  on-tertiary-fixed: '#271900'
  on-tertiary-fixed-variant: '#5f4100'
  background: '#f2fcf5'
  on-background: '#151d1a'
  surface-variant: '#dbe5de'
typography:
  headline-lg:
    fontFamily: IBM Plex Sans
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 44px
  headline-lg-mobile:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 38px
  headline-md:
    fontFamily: IBM Plex Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 32px
  title-md:
    fontFamily: IBM Plex Sans
    fontSize: 17px
    fontWeight: '500'
    lineHeight: 28px
  body-md:
    fontFamily: IBM Plex Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-sm:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  label-md:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-sm:
    fontFamily: IBM Plex Sans
    fontSize: 12px
    fontWeight: '500'
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
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

The design system is engineered for shared domestic utility, centered around the daily rhythms of Arabic-speaking families in Jordan. It prioritizes clarity, speed of capture, and collective coordination across multi-generational households. The emotional tone is dependable, warm, and distinctly pragmatic—avoiding decorative tech cliches in favor of an interface that feels like an organized physical kitchen chalkboard or a well-kept ledger.

The design style combines **Functional Utilitarianism** with **Modern Domestic Minimalism**:
- **Strict RTL-First Architecture:** Visual balance, logical flow, and iconography mirror natural Arabic reading and scanning habits.
- **Utilitarian Speed:** Immediate touch-targets, frictionless check-off micro-actions, and clear priority indicators.
- **Zero Decorative Fluff:** No gradients, ornate 3D illustrations, or visual noise. Structure and typography guide attention directly to what needs to be bought or done.
- **Family Differentiation:** Subtle, distinct member color tokens allow quick identification of who added or claimed an errand without overpowering the list hierarchy.

## Colors

The palette is tuned for high daylight legibility, rapid grocery aisle referencing, and clear contextual feedback under light-mode operations.

### Key Palettes
- **Primary (`#1F8A5B`):** The operational core. Used for completion states, primary action buttons, focused controls, active navigation markers, and checklist fills.
- **Primary Dark (`#166A45`):** Hover, pressed, and active link states.
- **Primary Tint (`#E8F4EE`):** Low-contrast fills for selected list items, soft category headers, and proactive smart suggestions.
- **Background (`#F6F8F7`):** Soft, neutral off-white backing that reduces glare during outdoor shopping trips.
- **Surface (`#FFFFFF`):** High-clarity white for cards, persistent sheets, modals, and input fields.
- **Border (`#E3E8E5`):** Crisp 1px structural framing for containers and segment dividers.
- **Text Dominant (`#1B2420`):** High-contrast deep slate-charcoal for Arabic titles, item names, and critical counts.
- **Text Muted (`#5F6C66`):** Secondary metadata, notes, timestamps, and input placeholders, verified for minimum WCAG AA 4.5:1 contrast against `#FFFFFF` and `#F6F8F7`.

### Semantic Signals
- **Urgent (`#D64545`):** Reserved exclusively for "مستعجل" (urgent) errand flags, deletion dialogues, and stock-out alerts.
- **Warning (`#F2B544`):** Soft amber for duplicate detection ("موجود أصلاً") and gentle attention states, always paired with `#1B2420` text for contrast.

### Household Member Palette
Used for avatar chips, assignment dots, and item ownership indicators:
- **Teal:** `#2A7F85`
- **Plum:** `#7A4A7D`
- **Rust:** `#B5622F`
- **Indigo:** `#4A5AA8`
- **Moss:** `#6E8B3D`
- **Rose:** `#B84A6B`

## Typography

Typography uses `IBM Plex Sans Arabic` to ensure authentic baseline balance, fluid letter connections, and clear visibility of diacritics.

### Directional & Numeric Rules
- **Text Direction:** Strict Right-to-Left (`dir="rtl"`). All layout alignments originate from the right canvas edge.
- **Numerals:** Standard Western Arabic numerals (`0-9`) must be used for quantities, prices (JOD), and item counts (e.g., `2 كيلو`, `0.75 دينار`, `3 علب`) for quick legibility on mobile devices.
- **Line Heights:** Arabic typography requires slightly expanded vertical clearance (`line-height: ~1.6`) to prevent ascenders and descenders from clipping into surrounding containers.
- **Font Scale Roles:**
  - `headline-lg` (28px/600 desktop, 24px/600 mobile): Major page and list titles ("قائمة المؤونة الأسبوعية").
  - `headline-md` (20px/600): Category dividers ("خضار وفواكه", "منظفات منزلية").
  - `title-md` (17px/500): Core list item names ("حليب كامل الدسم").
  - `body-md` (16px/400): Standard informational body, descriptions, and modal content.
  - `body-sm` (14px/400): Secondary details, quantity specs ("2 كغم من الدكان"), and store locations.
  - `label-md` / `label-sm`: Badges, status chips, member identity tokens, and utility metadata.

## Layout & Spacing

The system is built on an **8px base grid** optimized for swift one-handed mobile interactions while shopping and structured desktop views for weekly household management.

### Responsive Breakpoints & Containers
- **Mobile (< 768px):** Single-column stacked layout. Gutters: `12px` (`0.75rem`), outer margins: `16px` (`1rem`). Sticky bottom action bars ensure instant list item entry without requiring reach to the top.
- **Tablet (768px - 1024px):** 8-column layout. Gutters: `16px` (`1rem`), outer margins: `24px` (`1.5rem`). Split-view: category navigation on the right (RTL), active checklist on the left.
- **Desktop (> 1024px):** 12-column layout max-width `1280px` centered. Gutters: `16px` (`1rem`), margins: `32px` (`2rem`). Fixed right-hand household sidebar (`280px`), main list container spanning remaining width.

### Spacing Tokens
- `space-xs` (4px): Micro-spacing between paired icons and text labels.
- `space-sm` (8px): Internal tag padding, gap between checklist checkbox and text.
- `space-md` (16px): Standard card interior padding, vertical gap between distinct list items.
- `space-lg` (24px): Gap between discrete category blocks and section headers.
- `space-xl` (32px): Structural spacing around page header complexes and canvas boundaries.

## Elevation & Depth

To prevent visual clutter on fast-paced mobile devices, the system avoids heavy multi-layered shadows and dramatic skeuomorphism. It utilizes **flat structural framing** combined with a single **ambient micro-shadow**.

### Surface Layers
- **Base Canvas:** `#F6F8F7` (Lowest depth level).
- **Default Surface (Cards, Modules):** `#FFFFFF` bordered with `1px solid #E3E8E5` and resting on an ambient micro-shadow: `0 1px 2px rgba(0, 0, 0, 0.04)`.
- **Raised Interactive (Dropdowns, Floating Add Buttons):** `#FFFFFF` bordered with `1px solid #E3E8E5` and elevated via `0 4px 12px rgba(27, 36, 32, 0.08)`.
- **Modals & Overlays:** Solid white cards centered over a backdrop overlay of `#1B2420` at `40% opacity` with no background blur.

### RTL Visual Balance
- Border treatments, selection accent bars, and nested markers sit consistently on the right edge of list containers.
- Checked-off items collapse visual weight: the background transitions to `#F6F8F7`, the border becomes translucent, text shifts to `#5F6C66` with strikethrough, and elevation drops to `none`.

## Shapes

The design system implements a defined hierarchy of rounded corners to reinforce domestic comfort while maintaining clean UI structure.

- **Cards & Content Blocks:** `12px` border radius (`rounded-lg`), establishing clear visual compartments for shopping categories and receipt summaries.
- **Interactive Controls (Buttons, Inputs, Selectors):** `10px` border radius, creating comfortable, tap-friendly touch targets that align with mobile finger ergonomics.
- **Tags, Badges, Status Pills & Member Avatars:** `999px` fully rounded pills (`rounded-full`) to contrast against rectangular cards.
- **Checkboxes:** `6px` border radius to maintain a functional square profile with soft, friendly corners.

## Components

### 1. Buttons
- **Primary Action:** Solid `#1F8A5B` fill with `#FFFFFF` text, `10px` border radius, minimum height `44px` (mobile tap target `48px`). Hover state: `#166A45`. Active/Pressed: scale down by 1% with `#166A45`.
- **Secondary Action:** Outlined with `1px solid #E3E8E5`, background `#FFFFFF`, text `#1B2420`. Hover: `#F6F8F7`.
- **Destructive Action:** Low-contrast background `#FDEDED`, text `#D64545`, border `1px solid #FACDCD`.
- **RTL Icon Placement:** Action icons (e.g., plus icon for adding items) appear to the right of the text label.

### 2. Shopping List Items & Checkboxes
- **List Item Card:** White container (`#FFFFFF`), `12px` radius, `1px solid #E3E8E5`, `space-md` padding. Arranged horizontally with RTL alignment: Checkbox on the right, item name and details in the center, and metadata (urgency badge, quantity, member avatar) on the left.
- **Checkbox:** `22px x 22px` box with `6px` radius. Unchecked: `1.5px solid #5F6C66`, background `#FFFFFF`. Checked: solid `#1F8A5B` background with a crisp white checkmark SVG. Triggers a clean strikethrough on the adjacent item text.

### 3. Badges & Chips
- **Urgent Badge ("مستعجل"):** Full pill (`999px`), background `#D64545`, text `#FFFFFF`, typography `label-sm`.
- **Warning Badge ("موجود أصلاً"):** Full pill (`999px`), background `#F2B544`, text `#1B2420`, typography `label-sm`.
- **Category Filter Chips:** Horizontal scrolling pill strip. Inactive: `#FFFFFF` with `1px solid #E3E8E5`, text `#5F6C66`. Active: `#1F8A5B` with white text.

### 4. Input Fields
- **Item Quick-Add Input:** Large single-line text field, `10px` radius, `1px solid #E3E8E5`, background `#FFFFFF`. Focused state: `1.5px solid #1F8A5B` with zero ring glow.
- **Placeholder Text:** Light gray (`#5F6C66`) set in right-aligned Arabic (e.g., "أضف غرض جديد...").
- **Integrated Unit Selector:** Embedded right/left numeric counters for quantity selection with Western Arabic numerals (`0-9`).

### 5. Cards & Category Sections
- **Category Group Card:** Encased within `12px` rounded cards or framed as a clean list bordered by a bottom hairline divider (`#E3E8E5`).
- **Section Headers:** Include a category icon on the far right, bold text (`headline-md`), and a numerical item counter pill (`label-sm`) on the far left.

### 6. Member Avatars & Ownership
- **Avatar Circles:** `28px` diameter circles with `999px` radius, filled with one of the assigned Member Colors (Teal, Plum, Rust, Indigo, Moss, Rose).
- **Initials:** Display the first letter of the Arabic name in white bold type (`label-sm`) centered in the circle.

### 7. Iconography Rules
- Use clean, single-weight outline SVG icons (`1.5px` stroke) matching the text color.
- Directional icons (arrows, chevrons, return back buttons) must be mirrored automatically for RTL contexts.