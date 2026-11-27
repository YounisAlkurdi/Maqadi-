import { renderItemRow } from "./item-row.js";

export function renderCategoryGroup({
  title,
  items,
  membersById,
  collapsed = false,
  onToggleCollapse,
  onToggleItem,
  onEditItem,
}) {
  const section = document.createElement("section");
  section.className = "card category-group";

  const headerBtn = document.createElement("button");
  headerBtn.type = "button";
  headerBtn.className = "category-header";
  headerBtn.setAttribute("aria-expanded", String(!collapsed));

  const titleWrap = document.createElement("span");
  titleWrap.className = "category-title-wrap";

  const titleEl = document.createElement("span");
  titleEl.className = "category-title";
  titleEl.textContent = title;

  const countEl = document.createElement("span");
  countEl.className = "category-count";
  countEl.textContent = `(${items.length})`;

  titleWrap.appendChild(titleEl);
  titleWrap.appendChild(countEl);

  const chevron = document.createElement("span");
  chevron.className = "category-chevron";
  chevron.setAttribute("aria-hidden", "true");
  chevron.textContent = collapsed ? "▾" : "▴";

  headerBtn.appendChild(titleWrap);
  headerBtn.appendChild(chevron);
  headerBtn.addEventListener("click", onToggleCollapse);

  section.appendChild(headerBtn);

  if (!collapsed) {
    const ul = document.createElement("ul");
    ul.className = "item-list";
    for (const item of items) {
      ul.appendChild(
        renderItemRow(item, membersById, { onToggle: onToggleItem, onEdit: onEditItem })
      );
    }
    section.appendChild(ul);
  }

  return section;
}
