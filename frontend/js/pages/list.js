import { createItem, listItems, setItemStatus, updateItem } from "../api.js";
import { CATEGORY_META, CATEGORY_ORDER } from "../components/categories.js";
import { renderCategoryGroup } from "../components/category-group.js";
import { suggestCategory } from "../components/keywords.js";
import { showToast } from "../components/toast.js";
import { requireAuth } from "../guard.js";
import { initShell } from "../shell.js";

const POLL_INTERVAL_MS = 5000;

const state = {
  items: [],
  etag: null,
  membersById: new Map(),
  collapsedGroups: new Set(["__bought__"]),
  pollTimer: null,
  quickUrgent: false,
  quickCategoryTouched: false,
  duplicateItemId: null,
  editingItem: null,
  editUrgent: false,
};

const subtitleEl = document.getElementById("list-subtitle");
const errorEl = document.getElementById("list-error");
const contentEl = document.getElementById("list-content");
const toastRoot = document.getElementById("toast-root");

// Quick-add elements
const quickForm = document.getElementById("quick-add-form");
const quickName = document.getElementById("quick-add-name");
const quickExtras = document.getElementById("quick-add-extras");
const quickQty = document.getElementById("quick-add-qty");
const quickCategory = document.getElementById("quick-add-category");
const quickUrgentBtn = document.getElementById("quick-add-urgent");
const quickMoreBtn = document.getElementById("quick-add-more");
const quickError = document.getElementById("quick-add-error");
const quickDup = document.getElementById("quick-add-dup");
const quickDupEdit = document.getElementById("quick-add-dup-edit");
const quickDupCancel = document.getElementById("quick-add-dup-cancel");
const fabAdd = document.getElementById("fab-add");

// Edit dialog elements
const editBackdrop = document.getElementById("edit-dialog-backdrop");
const editForm = document.getElementById("edit-dialog-form");
const editName = document.getElementById("edit-name");
const editQty = document.getElementById("edit-qty");
const editNote = document.getElementById("edit-note");
const editCategory = document.getElementById("edit-category");
const editUrgentBtn = document.getElementById("edit-urgent");
const editError = document.getElementById("edit-error");
const editDeleteBtn = document.getElementById("edit-delete");
const editCancelBtn = document.getElementById("edit-cancel");
const editCloseBtn = document.getElementById("edit-dialog-close");

function populateCategorySelect(selectEl) {
  selectEl.replaceChildren();
  for (const key of CATEGORY_ORDER) {
    const opt = document.createElement("option");
    opt.value = key;
    opt.textContent = CATEGORY_META[key].label;
    selectEl.appendChild(opt);
  }
}

function renderEmptyState() {
  const card = document.createElement("section");
  card.className = "card empty-state";

  const title = document.createElement("h2");
  title.className = "empty-state-title";
  title.textContent = "القائمة فاضية حالياً";

  const body = document.createElement("p");
  body.className = "empty-state-body";
  body.textContent =
    "ابدأ بإضافة غرض من شريط الإضافة السريعة، أو الصق رسائل العائلة من الواتساب لتحويلها لقائمة مرتبة.";

  card.appendChild(title);
  card.appendChild(body);
  return card;
}

function renderList() {
  const openItems = state.items.filter((i) => i.status === "open");
  const boughtItems = state.items.filter((i) => i.status === "bought");

  subtitleEl.textContent =
    openItems.length === 0
      ? "لا توجد أغراض مطلوبة"
      : `${openItems.length} أغراض مطلوبة`;

  contentEl.replaceChildren();

  if (openItems.length === 0 && boughtItems.length === 0) {
    contentEl.appendChild(renderEmptyState());
    return;
  }

  for (const catKey of CATEGORY_ORDER) {
    const groupItems = openItems.filter((i) => i.category === catKey);
    if (groupItems.length === 0) continue;

    const meta = CATEGORY_META[catKey] || { label: "أخرى" };
    contentEl.appendChild(
      renderCategoryGroup({
        title: meta.label,
        items: groupItems,
        membersById: state.membersById,
        collapsed: state.collapsedGroups.has(catKey),
        onToggleCollapse: () => {
          if (state.collapsedGroups.has(catKey)) {
            state.collapsedGroups.delete(catKey);
          } else {
            state.collapsedGroups.add(catKey);
          }
          renderList();
        },
        onToggleItem: handleToggleItem,
        onEditItem: openEditDialog,
      })
    );
  }

  if (boughtItems.length > 0) {
    contentEl.appendChild(
      renderCategoryGroup({
        title: "تم شراؤه",
        items: boughtItems,
        membersById: state.membersById,
        collapsed: state.collapsedGroups.has("__bought__"),
        onToggleCollapse: () => {
          if (state.collapsedGroups.has("__bought__")) {
            state.collapsedGroups.delete("__bought__");
          } else {
            state.collapsedGroups.add("__bought__");
          }
          renderList();
        },
        onToggleItem: handleToggleItem,
        onEditItem: openEditDialog,
      })
    );
  }
}

async function handleToggleItem(item) {
  const previousStatus = item.status;
  const nextStatus = previousStatus === "bought" ? "open" : "bought";

  state.items = state.items.map((i) =>
    i.id === item.id ? { ...i, status: nextStatus } : i
  );
  renderList();

  try {
    const updated = await setItemStatus(item.id, nextStatus);
    state.items = state.items.map((i) => (i.id === item.id ? updated : i));
    state.etag = null;
    renderList();

    if (nextStatus === "bought") {
      showToast(toastRoot, `تم شراؤه: ${item.name}`, {
        actionLabel: "تراجع",
        onAction: () => handleToggleItem(updated),
      });
    }
  } catch (err) {
    state.items = state.items.map((i) =>
      i.id === item.id ? { ...i, status: previousStatus } : i
    );
    renderList();
    errorEl.textContent = err.message || "تعذر تحديث حالة الغرض.";
    errorEl.hidden = false;
  }
}

async function submitQuickAdd({ keepOpen = false } = {}) {
  quickError.hidden = true;
  quickDup.hidden = true;

  const name = quickName.value.trim();
  if (!name) {
    quickError.textContent = "اكتب اسم الغرض أولاً.";
    quickError.hidden = false;
    quickName.focus();
    return;
  }

  try {
    const created = await createItem({
      name,
      quantity_text: quickQty.value.trim() || null,
      category: quickCategory.value || "other",
      urgency: state.quickUrgent ? "urgent" : "normal",
    });
    state.items = [created, ...state.items];
    state.etag = null;
    renderList();

    quickName.value = "";
    quickQty.value = "";
    state.quickUrgent = false;
    state.quickCategoryTouched = false;
    quickUrgentBtn.setAttribute("aria-pressed", "false");
    quickCategory.value = "other";

    if (keepOpen) {
      quickExtras.hidden = false;
      quickName.focus();
    } else {
      quickExtras.hidden = true;
    }
  } catch (err) {
    if (err.status === 409 && err.existingItemId) {
      state.duplicateItemId = err.existingItemId;
      quickDup.hidden = false;
    } else {
      quickError.textContent = err.message || "تعذر إضافة الغرض.";
      quickError.hidden = false;
    }
  }
}

function openEditDialog(item) {
  state.editingItem = item;
  editName.value = item.name;
  editQty.value = item.quantity_text || "";
  editNote.value = item.note || "";
  editCategory.value = item.category || "other";
  state.editUrgent = item.urgency === "urgent";
  editUrgentBtn.setAttribute("aria-pressed", String(state.editUrgent));
  editError.hidden = true;
  editBackdrop.hidden = false;
  editName.focus();
}

function closeEditDialog() {
  editBackdrop.hidden = true;
  state.editingItem = null;
}

quickName.addEventListener("input", () => {
  const val = quickName.value.trim();
  quickExtras.hidden = val.length === 0;
  quickDup.hidden = true;
  quickError.hidden = true;
  if (!state.quickCategoryTouched) {
    quickCategory.value = suggestCategory(val);
  }
});

quickCategory.addEventListener("change", () => {
  state.quickCategoryTouched = true;
});

quickUrgentBtn.addEventListener("click", () => {
  state.quickUrgent = !state.quickUrgent;
  quickUrgentBtn.setAttribute("aria-pressed", String(state.quickUrgent));
});

quickForm.addEventListener("submit", (e) => {
  e.preventDefault();
  submitQuickAdd({ keepOpen: false });
});

quickMoreBtn.addEventListener("click", () => {
  submitQuickAdd({ keepOpen: true });
});

quickDupEdit.addEventListener("click", () => {
  const existing = state.items.find((i) => i.id === state.duplicateItemId);
  quickDup.hidden = true;
  if (existing) {
    openEditDialog(existing);
  }
});

quickDupCancel.addEventListener("click", () => {
  quickDup.hidden = true;
  state.duplicateItemId = null;
});

fabAdd.addEventListener("click", () => {
  quickExtras.hidden = false;
  quickName.focus();
  quickForm.scrollIntoView({ behavior: "smooth", block: "center" });
});

editUrgentBtn.addEventListener("click", () => {
  state.editUrgent = !state.editUrgent;
  editUrgentBtn.setAttribute("aria-pressed", String(state.editUrgent));
});

editCancelBtn.addEventListener("click", closeEditDialog);
editCloseBtn.addEventListener("click", closeEditDialog);
editBackdrop.addEventListener("click", (e) => {
  if (e.target === editBackdrop) closeEditDialog();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !editBackdrop.hidden) {
    closeEditDialog();
  }
});

editForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!state.editingItem) return;

  const name = editName.value.trim();
  if (!name) {
    editError.textContent = "اكتب اسم الغرض.";
    editError.hidden = false;
    editName.focus();
    return;
  }

  try {
    const updated = await updateItem(state.editingItem.id, {
      name,
      quantity_text: editQty.value.trim() || null,
      note: editNote.value.trim() || null,
      category: editCategory.value,
      urgency: state.editUrgent ? "urgent" : "normal",
    });
    state.items = state.items.map((i) => (i.id === updated.id ? updated : i));
    state.etag = null;
    closeEditDialog();
    renderList();
  } catch (err) {
    editError.textContent = err.message || "تعذر حفظ التعديلات.";
    editError.hidden = false;
  }
});

editDeleteBtn.addEventListener("click", async () => {
  if (!state.editingItem) return;
  const target = state.editingItem;
  closeEditDialog();

  try {
    await setItemStatus(target.id, "cancelled");
    state.items = state.items.filter((i) => i.id !== target.id);
    state.etag = null;
    renderList();

    showToast(toastRoot, `تم حذف: ${target.name}`, {
      actionLabel: "تراجع",
      onAction: async () => {
        const restored = await setItemStatus(target.id, "open");
        state.items = [restored, ...state.items];
        state.etag = null;
        renderList();
      },
    });
  } catch (err) {
    errorEl.textContent = err.message || "تعذر حذف الغرض.";
    errorEl.hidden = false;
  }
});

async function fetchItems({ force = false } = {}) {
  try {
    errorEl.hidden = true;
    const res = await listItems(force ? null : state.etag);
    if (res.notModified) return;
    state.items = res.data.items;
    state.etag = res.etag;
    renderList();
  } catch (err) {
    errorEl.textContent = err.message || "تعذر تحميل القائمة.";
    errorEl.hidden = false;
  }
}

function startPolling() {
  stopPolling();
  if (document.hidden) return;
  state.pollTimer = setInterval(() => {
    if (!document.hidden) {
      fetchItems();
    }
  }, POLL_INTERVAL_MS);
}

function stopPolling() {
  if (state.pollTimer) {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopPolling();
  } else {
    fetchItems();
    startPolling();
  }
});

window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    fetchItems({ force: true });
    startPolling();
  }
});

async function init() {
  if (!requireAuth()) return;
  populateCategorySelect(quickCategory);
  populateCategorySelect(editCategory);
  const me = await initShell("list");
  if (me && Array.isArray(me.members)) {
    state.membersById = new Map(me.members.map((m) => [m.id, m]));
  }
  await fetchItems({ force: true });
  startPolling();
}

init();
