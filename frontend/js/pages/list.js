import { listItems, setItemStatus } from "../api.js";
import { CATEGORY_META, CATEGORY_ORDER } from "../components/categories.js";
import { renderCategoryGroup } from "../components/category-group.js";
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
};

const subtitleEl = document.getElementById("list-subtitle");
const errorEl = document.getElementById("list-error");
const contentEl = document.getElementById("list-content");
const toastRoot = document.getElementById("toast-root");

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
      })
    );
  }
}

async function handleToggleItem(item) {
  const previousStatus = item.status;
  const nextStatus = previousStatus === "bought" ? "open" : "bought";

  // Optimistic update
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
    // Rollback on error
    state.items = state.items.map((i) =>
      i.id === item.id ? { ...i, status: previousStatus } : i
    );
    renderList();
    errorEl.textContent = err.message || "تعذر تحديث حالة الغرض.";
    errorEl.hidden = false;
  }
}

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
  const me = await initShell("list");
  if (me && Array.isArray(me.members)) {
    state.membersById = new Map(me.members.map((m) => [m.id, m]));
  }
  await fetchItems({ force: true });
  startPolling();
}

init();
