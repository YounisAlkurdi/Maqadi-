import { confirmPaste, createItem, listItems, previewPaste, setItemStatus, updateItem } from "../api.js";
import { CATEGORY_META, CATEGORY_ORDER } from "../components/categories.js";
import { renderCategoryGroup } from "../components/category-group.js";
import { suggestCategory } from "../components/keywords.js";
import { showToast } from "../components/toast.js";
import { requireAuth } from "../guard.js";
import { initShell } from "../shell.js";
import { initVoiceInput } from "../voice.js";

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
  pastePreviewItems: [],
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

// --- WhatsApp Paste Modal ---
const pasteOpenBtn = document.getElementById("paste-open-btn");
const pasteBackdrop = document.getElementById("paste-dialog-backdrop");
const pasteCloseBtn = document.getElementById("paste-dialog-close");
const pasteCancelBtn = document.getElementById("paste-cancel-btn");
const pasteTextarea = document.getElementById("paste-textarea");
const pasteError = document.getElementById("paste-error");
const pasteExtractBtn = document.getElementById("paste-extract-btn");
const pasteConfirmBtn = document.getElementById("paste-confirm-btn");
const pastePreviewSection = document.getElementById("paste-preview-section");
const pastePreviewList = document.getElementById("paste-preview-list");
const pastePreviewCount = document.getElementById("paste-preview-count");
const pasteEngineBadge = document.getElementById("paste-engine-badge");

// Voice input wiring
const voiceBtn = document.getElementById("voice-btn");
const voiceBtnLabel = document.getElementById("voice-btn-label");
const voiceStatusEl = document.getElementById("voice-status");
initVoiceInput({ textarea: pasteTextarea, btn: voiceBtn, btnLabel: voiceBtnLabel, statusEl: voiceStatusEl });

function openPasteModal() {
  state.pastePreviewItems = [];
  pasteTextarea.value = "";
  pasteError.hidden = true;
  pastePreviewSection.hidden = true;
  pastePreviewList.replaceChildren();
  pasteConfirmBtn.hidden = true;
  pasteBackdrop.hidden = false;
  pasteTextarea.focus();
}

function closePasteModal() {
  pasteBackdrop.hidden = true;
  state.pastePreviewItems = [];
}

function renderPastePreview(data) {
  pastePreviewList.replaceChildren();
  state.pastePreviewItems = (data.items || []).map((item) => ({ ...item, selected: true }));

  if (state.pastePreviewItems.length === 0) {
    pastePreviewSection.hidden = true;
    pasteConfirmBtn.hidden = true;
    pasteError.textContent = "ما لقينا أغراض واضحة في النص. جرّب صياغة ثانية.";
    pasteError.hidden = false;
    return;
  }

  pastePreviewCount.textContent = `الأغراض المستخرجة (${state.pastePreviewItems.length})`;
  pasteEngineBadge.textContent = data.engine === "llm" ? "ذكاء اصطناعي" : "استخراج سريع";

  state.pastePreviewItems.forEach((item, idx) => {
    const row = document.createElement("label");
    row.className = "paste-preview-row";

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = true;
    cb.addEventListener("change", () => {
      state.pastePreviewItems[idx].selected = cb.checked;
      const anySelected = state.pastePreviewItems.some((i) => i.selected);
      pasteConfirmBtn.disabled = !anySelected;
    });

    const info = document.createElement("div");
    info.className = "paste-preview-info";

    const title = document.createElement("div");
    title.className = "paste-preview-title";
    title.textContent = item.name;

    const meta = document.createElement("div");
    meta.className = "paste-preview-meta";

    if (item.quantity_text) {
      const qtySpan = document.createElement("span");
      qtySpan.textContent = item.quantity_text;
      meta.appendChild(qtySpan);
    }

    const catMeta = CATEGORY_META[item.category] || CATEGORY_META.other;
    const catSpan = document.createElement("span");
    catSpan.textContent = catMeta.label;
    meta.appendChild(catSpan);

    if (item.urgency === "urgent") {
      const urgSpan = document.createElement("span");
      urgSpan.textContent = "مستعجل";
      meta.appendChild(urgSpan);
    }

    if (item.merge_with_item_id) {
      const mergeBadge = document.createElement("span");
      mergeBadge.className = "badge-merge";
      mergeBadge.textContent = "موجود — سيتم دمجه";
      meta.appendChild(mergeBadge);
    }

    info.appendChild(title);
    info.appendChild(meta);
    row.appendChild(cb);
    row.appendChild(info);
    pastePreviewList.appendChild(row);
  });

  pastePreviewSection.hidden = false;
  pasteConfirmBtn.hidden = false;
  pasteConfirmBtn.disabled = false;
}

pasteOpenBtn.addEventListener("click", openPasteModal);
pasteCloseBtn.addEventListener("click", closePasteModal);
pasteCancelBtn.addEventListener("click", closePasteModal);
pasteBackdrop.addEventListener("click", (e) => {
  if (e.target === pasteBackdrop) closePasteModal();
});

pasteExtractBtn.addEventListener("click", async () => {
  const text = pasteTextarea.value.trim();
  if (!text) {
    pasteError.textContent = "الصق نص الرسائل أولاً";
    pasteError.hidden = false;
    return;
  }
  pasteError.hidden = true;
  pasteExtractBtn.disabled = true;
  pasteExtractBtn.textContent = "جاري الاستخراج…";
  try {
    const data = await previewPaste(text);
    renderPastePreview(data);
  } catch (err) {
    pasteError.textContent = err.message || "تعذر استخراج الأغراض";
    pasteError.hidden = false;
  } finally {
    pasteExtractBtn.disabled = false;
    pasteExtractBtn.textContent = "استخرج الأغراض";
  }
});

pasteConfirmBtn.addEventListener("click", async () => {
  const selected = state.pastePreviewItems
    .filter((i) => i.selected)
    .map(({ selected: _s, source_snippet: _sn, confidence: _c, ...rest }) => rest);
  if (selected.length === 0) return;

  pasteError.hidden = true;
  pasteConfirmBtn.disabled = true;
  pasteConfirmBtn.textContent = "جاري الإضافة…";
  try {
    const res = await confirmPaste(selected);
    const count = (res.items || []).length;
    closePasteModal();
    await fetchItems({ force: true });
    showToast(`تمت إضافة ${count} غرض للقائمة`);
  } catch (err) {
    pasteError.textContent = err.message || "تعذر حفظ الأغراض";
    pasteError.hidden = false;
  } finally {
    pasteConfirmBtn.disabled = false;
    pasteConfirmBtn.textContent = "أضف المحدد";
  }
});

// --- WhatsApp Share ---
const shareListBtn = document.getElementById("share-list-btn");

function formatShareText(items) {
  const openItems = items.filter((i) => i.status === "open");
  if (openItems.length === 0) return "";

  const grouped = new Map();
  for (const cat of CATEGORY_ORDER) {
    grouped.set(cat, []);
  }
  for (const item of openItems) {
    const cat = grouped.has(item.category) ? item.category : "other";
    grouped.get(cat).push(item);
  }

  const lines = ["طلبات البيت:"];
  for (const cat of CATEGORY_ORDER) {
    const groupItems = grouped.get(cat);
    if (!groupItems || groupItems.length === 0) continue;
    const label = (CATEGORY_META[cat] || CATEGORY_META.other).label;
    lines.push(`\n*${label}*`);
    for (const item of groupItems) {
      const qty = item.quantity_text ? ` (${item.quantity_text})` : "";
      const urgent = item.urgency === "urgent" ? " [مستعجل]" : "";
      lines.push(`- ${item.name}${qty}${urgent}`);
    }
  }
  return lines.join("\n");
}

shareListBtn.addEventListener("click", async () => {
  const text = formatShareText(state.items);
  if (!text) {
    showToast("القائمة فاضية حالياً");
    return;
  }

  if (navigator.share) {
    try {
      await navigator.share({ title: "طلبات البيت", text });
      return;
    } catch (err) {
      if (err && err.name === "AbortError") return;
    }
  }

  try {
    await navigator.clipboard.writeText(text);
    showToast("تم نسخ القائمة للمشاركة");
  } catch {
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener,noreferrer");
  }
});
