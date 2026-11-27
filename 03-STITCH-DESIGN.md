# Google Stitch — Design Brief v2: Maqadi (طلبات البيت)

**What changed from v1:**
1. **Laptop-first.** Every screen is designed at 1440×900 first, then adapted to tablet (820) and phone (390). Same product, responsive layout, not a separate mobile app.
2. **Conventional style.** The look follows what people already expect from shopping-list and household apps (AnyList, Bring!, OurGroceries, Cozi): light neutral background, white cards, one fresh green accent, sidebar navigation on desktop, always-visible "add item" bar, category groups, round checkboxes. No custom "paper slip" concept, no unusual palette. Users should understand it in 5 seconds without learning anything.

**How to use with Stitch**
1. Paste **Section 1 (Design System)** as the project context.
2. For each screen, paste the **Desktop prompt** first (generate at 1440×900).
3. Then paste that screen's **Responsive prompt** to get the tablet and phone versions of the *same* screen.
4. Export screenshots as a visual reference only. The real frontend is hand-built vanilla HTML/CSS/JS.

---

## 1. Design System (paste first)

**Product:** A shared household errands/shopping list for Arabic-speaking families in Jordan. Main differentiator: paste messy WhatsApp messages and get a clean categorized list to confirm.

**Users:** Family members aged 15 to 65, 3 to 6 per home, mixed tech comfort. Used on a laptop at home (planning, pasting messages) and on a phone in the supermarket (checking off).

**Language & direction:** Arabic, **right-to-left everywhere** (sidebar on the right, content flows from right). Western digits. Simple everyday Arabic copy.

**Style reference:** Clean, friendly, utilitarian productivity app. Familiar patterns from popular list apps. Light mode only for v1.

**Color tokens**
| Token | Hex | Use |
|---|---|---|
| `primary` | `#1F8A5B` | primary buttons, active nav, checkbox fill, progress |
| `primary-dark` | `#166A45` | hover/pressed, links |
| `primary-tint` | `#E8F4EE` | selected nav item, soft highlights, AI-suggestion backgrounds |
| `bg` | `#F6F8F7` | page background |
| `surface` | `#FFFFFF` | cards, sidebar, dialogs |
| `border` | `#E3E8E5` | 1px card/input borders, dividers |
| `text` | `#1B2420` | main text |
| `text-muted` | `#5F6C66` | secondary text, placeholders (must stay ≥ 4.5:1 on surface) |
| `urgent` | `#D64545` | "مستعجل" marker, destructive actions |
| `warning` | `#F2B544` | "موجود أصلاً" tag, attention badges (dark text on it) |

**Member colors** (small filled dot or avatar circle + name; never color alone): `#2A7F85` teal, `#7A4A7D` plum, `#B5622F` rust, `#4A5AA8` indigo, `#6E8B3D` moss, `#B84A6B` rose.

**Typography:** one family, **IBM Plex Sans Arabic** (Arabic + Latin digits), weights 400/500/600.
Scale desktop: page title 28/600 · section title 20/600 · item name 17/500 · body 16/400 · secondary 14/400.
Scale phone: page title 24 · item name 18 · body 16 (never below 14). Line-height 1.6. Sentence case.

**Shape & spacing:** 8px grid. Cards radius 12px, inputs and buttons 10px, pills and avatars 999px. Cards: white with 1px `border` and a very subtle shadow (`0 1px 2px rgba(0,0,0,.04)`); dialogs get a stronger shadow plus a dimmed backdrop. No gradients.

**Icons:** simple outline icon set (Lucide/Material Symbols Outlined style), 20–24px, 1.75px stroke. Each category has one icon: خضار وفواكه (carrot), ألبان وبيض (milk bottle), لحوم ودجاج (drumstick), مخبوزات (bread), معلبات وجافة (jar), منظفات (spray bottle), صيدلية (pill), أخرى (tag).

**Responsive layout system**
| Breakpoint | Layout |
|---|---|
| **Desktop ≥ 1200px** (design here first) | 3 zones: **right sidebar 248px** (logo, household name, nav, invite code card) · **main column** (list, max 760px) · **left side panel 340px** (the persistent "الصق رسائل" paste card + "آخر ما انشرى"). Dialogs centered, 720–880px wide. |
| **Tablet 768–1199px** | Sidebar collapses to a **72px icon rail**. Side panel moves into a collapsible section above the list or opens as a drawer. Main column fills the rest. |
| **Phone < 768px** | Sidebar and side panel disappear. **Bottom tab bar** (القائمة · وضع السوق · السجل · البيت). A **floating "+" button** (bottom-left in RTL) opens the add sheet; a second small action opens paste. Dialogs become **bottom sheets** (full width, rounded top, drag handle). Rows 56px+, touch targets ≥ 44px. |

Content must reflow, not shrink: no horizontal scroll at 360px, no hover-only actions (every hover action has a visible control or tap equivalent on touch).

**Components (shared across breakpoints)**
- **Quick-add bar:** a wide input at the top of the list: placeholder "أضف غرض… مثلاً: لبن، 2 كيلو بندورة". Enter adds. Right-side category auto-chip appears as the user types. Always visible on desktop; on phone it is the "+" sheet.
- **Item row:** round checkbox at the start (right), item name 17/500, quantity as muted text, member avatar + name, optional `مستعجل` pill (urgent color + text), overflow menu (⋮) with تعديل / حذف. Hover (desktop) highlights the row with `primary-tint`. Bought rows: struck through, muted, moved to a collapsed group "تم شراؤه (N)" at the bottom.
- **Category group:** header with category icon, name, count, collapse chevron. Rows inside one card.
- **Buttons:** primary (filled `primary`, white text, 44px desktop / 52px phone), secondary (white, 1px border), text button. One primary button per view area.
- **Toast:** bottom center, one line, with "تراجع" (undo) action.
- **Tags:** "موجود أصلاً" (warning bg), "مستعجل" (urgent), "جديد" (primary-tint).

**Interaction principles**
1. One main screen. Two always-available actions: **add** and **paste**.
2. Checking an item is one click/tap; undo is one click/tap.
3. AI results are always a **preview the user confirms**. Never auto-add.
4. Never lose typed or pasted text on error.
5. Motion only for feedback (checkbox, row moving to "bought", dialog open). Respect reduced motion.
6. Visible keyboard focus: 2px `primary-dark` outline with 2px offset. Full keyboard flow on desktop (Enter adds, Esc closes dialogs).

---

## 2. Content bank (use real Arabic, never lorem ipsum)

Household: بيت أبو أحمد. Members: أمي، أبو أحمد، سارة، يونس.
Items: خبز (خبزتين) · لبن · بيض (طبقة) · بندورة (كيلو) · خيار · دجاج (كيلو ونص) · شامبو · كاسات للضيوف · مناديل · حفاضات · بنادول.
Categories: خضار وفواكه · ألبان وبيض · لحوم ودجاج · مخبوزات · معلبات وجافة · منظفات · صيدلية · أخرى.
Nav: القائمة · وضع السوق · السجل · البيت.
Sample paste text:
```
أمي: يا يونس لا تنسى تجيب خبزتين ولبن
أبو أحمد: وجيب بيض كمان، ضروري اليوم
أمي: وكيلو بندورة
سارة: بدي شامبو وكاسات للضيوف
😂😂 مين أكل الشوكولاتة؟
```

---

## 3. Screens

### Screen A — Join / Create household

**Desktop prompt (1440×900)**
```
Design a desktop sign-in screen in Arabic, RTL, for "طلبات البيت", a shared household shopping list. Light, clean, familiar app style. Background #F6F8F7.
Split layout: right half = a centered white card (max 440px, radius 12px, 1px border #E3E8E5). Left half = brand panel with soft tint #E8F4EE: the logo wordmark "طلبات البيت" with a small green (#1F8A5B) cart-check icon, the headline "قائمة وحدة لكل البيت", and three short points with outline icons: "الصق رسائل الواتساب وخلّي الذكاء الاصطناعي يرتبها" · "كل العيلة تشوف نفس القائمة لحظياً" · "بدون تسجيل ولا باسورد". No people illustrations.
Card content: segmented control with two tabs "أنشئ بيت جديد" and "عندي كود البيت". The second tab shows: input "كود البيت" (8 characters, letter-spaced, centered), input "اسمك", and "اختر لونك" as a row of 6 colored circles with a check on the selected one. Primary full-width button "ادخل" (#1F8A5B, white text, 44px). Under it a muted note: "أي شخص معه الكود يقدر يدخل. ممكن تغيّر الكود من إعدادات البيت."
Font: IBM Plex Sans Arabic only. No gradients.
```
**Responsive prompt**
```
Adapt the previous sign-in screen to tablet (820px) and phone (390×844). Remove the brand panel on phone and keep only the logo, headline and the form card full-width with 16px margins. On tablet keep the card centered at 480px with the brand points shown under the form. Primary button becomes 52px tall on phone. Keep all copy and colors identical.
```

### Screen B — Main list (the core page)

**Desktop prompt (1440×900)**
```
Design the main page of a shared household shopping list web app, Arabic RTL, desktop 1440×900, background #F6F8F7. Familiar app-shell style like AnyList or Bring.
Three zones:
1) Right sidebar 248px, white, 1px left border: logo "طلبات البيت"; household name "بيت أبو أحمد" with a small avatar; nav items with outline icons: "القائمة" (active, tint #E8F4EE with green text and a 3px green bar at the start), "وضع السوق", "السجل", "البيت"; at the bottom a small card "كود البيت" showing "K7M2-9QXP" with a copy icon button.
2) Main column (max 760px, centered in the remaining space): page title "قائمة المقاضي" with a muted subtitle "7 أغراض مطلوبة"; below it a wide quick-add input (white, 1px border, 48px high, placeholder "أضف غرض… مثلاً: لبن، 2 كيلو بندورة") with a green "أضف" button inside its end. Below: category groups, each a white card with header (category outline icon, name, count, chevron): "خضار وفواكه (3)", "ألبان وبيض (2)", "مخبوزات (1)", "منظفات (1)". Each item row 56px: round checkbox at the start, name 17px "بندورة", muted quantity "كيلو", member avatar circle + name "أمي" at the end, one row with a red "مستعجل" pill, a ⋮ menu shown on hover. One row is being hovered (tint #E8F4EE). At the bottom a collapsed group "تم شراؤه (4)". A toast at the bottom center: "تم شراؤه: لبن — تراجع".
3) Left side panel 340px: a white card titled "الصق رسائل الواتساب" with a short multiline textarea (placeholder "الصق هنا رسائل العيلة…"), a muted line "ما بنحفظ النص، بنحفظ الأغراض اللي تأكدها بس", and a primary button "حوّل لقائمة". Under it a second card "آخر ما انشرى" with 3 lines: "لبن — يونس — قبل ساعتين".
Tokens: primary #1F8A5B, text #1B2420, muted #5F6C66, border #E3E8E5, urgent #D64545. Font IBM Plex Sans Arabic. Cards radius 12px, subtle shadow. No gradients, no illustrations inside the list.
```
**Responsive prompt**
```
Adapt the main list page.
Tablet (820px): collapse the sidebar into a 72px right icon rail (icons only, active one tinted). Remove the left side panel; show a single full-width "الصق رسائل الواتساب" button next to the quick-add input that opens the paste dialog. Main column fills the width.
Phone (390×844): remove the sidebar and side panel. Top app bar: household name on the right, member avatars (stacked circles) on the left. Quick-add input stays at the top of the list. Item rows are 56px with the checkbox at the right and the ⋮ menu always visible. Bottom tab bar (white, 1px top border) with 4 tabs: القائمة (active, green), وضع السوق, السجل, البيت. A floating green circular "+" button above the tab bar at the bottom-left (RTL) and a smaller secondary round button for paste. Toast sits above the tab bar.
```

### Screen C — Paste & preview (the signature feature)

**Desktop prompt**
```
Design a large centered dialog (880px wide, radius 12px, strong soft shadow, dimmed backdrop) over the main list page, Arabic RTL, desktop 1440×900. Title "حوّل الرسائل لقائمة".
Two-column layout inside the dialog with a thin divider:
Right column "الرسائل" (the source): a read-only-looking textarea containing the sample paste text from the content bank (messy chat with names, an emoji line), with a link "عدّل النص" above it.
Left column "الأغراض اللي لقيناها (5)" (the result): items grouped by category with outline icons. Each row has a checked green checkbox, editable name, editable quantity, a requester chip with member avatar + name ("أمي"), and a category dropdown. One row shows a yellow (#F2B544) tag "موجود أصلاً — ضم؟" with two small buttons "ضم" and "أضف مستقل". Below the list a collapsed section "تجاهلنا 1 رسالة" that expands to show the ignored chat noise.
Footer: secondary button "إلغاء" and primary button "أضف 5 أغراض" (#1F8A5B). A small muted line: "راجع النتيجة قبل ما تضيفها."
Also design the loading state (skeleton rows with the text "عم نرتب الرسائل…") and the error state (inline red message "ما قدرنا نفهم الرسائل. نصك محفوظ، جرّب مرة ثانية." with a "حاول مرة ثانية" button; the pasted text stays visible).
Make the relationship between the messy source on one side and the clean result on the other the clearest thing on the screen.
```
**Responsive prompt**
```
Adapt the paste dialog.
Tablet (820px): dialog 90% width, keep two columns if space allows, otherwise stack source above result.
Phone (390×844): turn it into a full-height bottom sheet with a drag handle and a 3-step flow: step 1 "الصق الرسائل" (large textarea + primary button "حوّل لقائمة"), step 2 "راجع الأغراض" (the grouped editable list with sticky footer button "أضف 5 أغراض"), step 3 error state. A small segmented toggle "النص | النتيجة" lets the user peek at the source while reviewing. Rows are 56px with 44px touch targets.
```

### Screen D — Shop mode

**Desktop prompt**
```
Design a "shop mode" page, Arabic RTL, desktop 1440×900, same app shell (sidebar "وضع السوق" active). Main column is narrower (560px) and centered with larger rows (64px), 20px item text and 28px round checkboxes. Header: title "وضع السوق", progress text "باقي 7 من 12" and a thin green progress bar. Only open items, grouped by category in supermarket-walk order: خضار وفواكه، لحوم ودجاج، ألبان وبيض، مخبوزات، معلبات وجافة، منظفات. A primary button "خلصت التسوق" appears at the bottom only when everything is checked (show it disabled with the hint "بقي أغراض"). High contrast, no side panel.
```
**Responsive prompt**
```
Adapt shop mode to phone (390×844): this is the main phone use case, standing in the supermarket with one hand. Remove the sidebar, show the bottom tab bar with "وضع السوق" active, rows 72px, text 20px, checkbox 32px at the right, sticky progress header, and the "خلصت التسوق" button docked above the tab bar. Keep screen layout minimal and high contrast.
```

### Screen E — Add / edit item

**Desktop prompt**
```
Design the expanded state of the quick-add bar and the edit dialog, Arabic RTL, desktop.
Expanded quick-add: while typing "بندورة كيلو" under the input a small panel shows an auto-detected category chip "خضار وفواكه" (tinted green), a quantity field filled with "كيلو", an urgency toggle "مستعجل", and buttons "أضف" (primary) and "أضف وكمّل". Show the duplicate state too: an inline yellow notice "بندورة موجودة أصلاً في القائمة" with buttons "عدّل الموجود" and "أضف مع ذلك".
Edit dialog (480px, centered): fields الاسم, الكمية, ملاحظة, التصنيف (dropdown with category icons), toggle مستعجل; buttons "احفظ" (primary), "إلغاء", and a red text button "احذف الغرض".
```
**Responsive prompt**
```
Adapt to phone (390×844): the "+" floating button opens a bottom sheet titled "أضف غرض" with the name input autofocused, quantity input, category chips in a horizontal scroll row (auto-suggested one highlighted), the urgency switch, primary button "أضف" and a text button "أضف وكمّل". Controls are in the lower half of the screen for one-hand use. The edit dialog also becomes a bottom sheet.
```

### Screen F — Share to WhatsApp

**Desktop prompt**
```
Design a small centered dialog (520px), Arabic RTL, titled "شارك القائمة". Inside: a light grey chat-bubble style box showing the exact message that will be sent:
"قائمة المقاضي 🛒
- بندورة (كيلو)
- لبن (مستعجل)
- خبز (خبزتين)"
Buttons: primary "افتح الواتساب" (use a neutral green button with a chat icon, not the WhatsApp logo) and secondary "انسخ النص" with a copied confirmation state "تم النسخ".
```
**Responsive prompt**
```
Adapt to phone as a bottom sheet with the same content; both buttons full width, stacked, 52px tall.
```

### Screen G — History page

**Desktop prompt**
```
Design a page "السجل", Arabic RTL, desktop 1440×900, same app shell with "السجل" active. Main column (760px): title "آخر ما انشرى" and a segmented filter "اليوم | هذا الأسبوع | الكل". A white card containing rows grouped by day ("اليوم", "أمس", "الخميس"). Each row: item name, quantity, member avatar + name of who bought it, relative time "قبل ساعتين", and a text button "أضفه مرة ثانية". Empty state text: "لسا ما انشرى شي. لما تشيّك غرض بيظهر هون." with a small outline icon and no illustration.
```
**Responsive prompt**
```
Adapt to tablet and phone: full-width card, rows 56px, the "أضفه مرة ثانية" action becomes an icon button (+) with an accessible label, bottom tab bar with "السجل" active on phone.
```

### Screen H — Household (members & invite code)

**Desktop prompt**
```
Design a page "البيت", Arabic RTL, desktop 1440×900, same app shell with "البيت" active. Main column 760px with two white cards.
Card 1 "أفراد البيت": list of 4 members, each with a colored avatar circle, name, "انضم قبل 3 أيام", and a "أنت" tag on the current member.
Card 2 "كود البيت": the code "K7M2-9QXP" in a large letter-spaced box with a copy button, a muted explanation "أي شخص معه الكود يقدر يدخل البيت.", and a secondary button "غيّر الكود" that opens a confirmation dialog: "الكود القديم رح يتوقف. الأعضاء الحاليين ما رح يتأثروا." with buttons "غيّر الكود" (red) and "إلغاء".
```
**Responsive prompt**
```
Adapt to phone (390×844): stack the cards full-width, bottom tab bar with "البيت" active, copy button and "غيّر الكود" at least 44px tall.
```

---

## 4. Reject rules (check Stitch output before using it)

Reject or regenerate if the output has: left-to-right layout, hard-coded left/right alignment, Latin-only fonts, more than one primary button in the same area, gradients, hover-only actions with no touch alternative, a phone version that is just a scaled-down desktop, text under 14px, or contrast below 4.5:1.

## 5. Hand-off to the agents

1. Save exports to `docs/design/` as `a-join-desktop.png`, `a-join-phone.png`, `b-list-desktop.png`, `b-list-tablet.png`, `b-list-phone.png`, and so on (screen letter, then breakpoint).
2. Agent task F4 turns Section 1 into `frontend/css/tokens.css`, including the three breakpoints (`--bp-tablet: 768px`, `--bp-desktop: 1200px`) and the layout rules in the "Responsive layout system" table.
3. Build order for the UI: desktop layout first, then add the tablet and phone rules with CSS media queries. The same HTML serves all sizes (no separate mobile pages).
