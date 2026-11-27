export function renderItemRow(item, membersById, { onToggle }) {
  const isBought = item.status === "bought";
  const row = document.createElement("li");
  row.className = isBought ? "item-row item-row--bought" : "item-row";
  row.dataset.itemId = item.id;

  const checkBtn = document.createElement("button");
  checkBtn.type = "button";
  checkBtn.className = isBought ? "item-check item-check--checked" : "item-check";
  checkBtn.setAttribute("role", "checkbox");
  checkBtn.setAttribute("aria-checked", String(isBought));
  checkBtn.setAttribute(
    "aria-label",
    isBought ? `إلغاء شراء ${item.name}` : `تحديد ${item.name} كمُشترى`
  );
  if (isBought) {
    checkBtn.textContent = "✓";
  }
  checkBtn.addEventListener("click", () => onToggle(item));

  const main = document.createElement("div");
  main.className = "item-main";

  const nameSpan = document.createElement("span");
  nameSpan.className = "item-name";
  nameSpan.textContent = item.name;
  main.appendChild(nameSpan);

  if (item.quantity_text) {
    const qtySpan = document.createElement("span");
    qtySpan.className = "item-qty";
    qtySpan.textContent = item.quantity_text;
    main.appendChild(qtySpan);
  }

  if (item.urgency === "urgent" && !isBought) {
    const urgentChip = document.createElement("span");
    urgentChip.className = "chip chip-urgent";
    urgentChip.textContent = "مستعجل";
    main.appendChild(urgentChip);
  }

  const meta = document.createElement("div");
  meta.className = "item-meta";

  const requester = item.requested_by_member_id
    ? membersById.get(item.requested_by_member_id)
    : null;
  if (requester) {
    const memberWrap = document.createElement("span");
    memberWrap.className = "item-member";

    const dot = document.createElement("span");
    dot.className = "member-dot";
    dot.style.backgroundColor = requester.color;
    dot.setAttribute("aria-hidden", "true");

    const memberName = document.createElement("span");
    memberName.textContent = requester.display_name;

    memberWrap.appendChild(dot);
    memberWrap.appendChild(memberName);
    meta.appendChild(memberWrap);
  }

  row.appendChild(checkBtn);
  row.appendChild(main);
  row.appendChild(meta);
  return row;
}
