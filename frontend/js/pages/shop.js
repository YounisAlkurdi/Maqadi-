import { listItems, setItemStatus } from "../api.js";
import { CATEGORY_ORDER } from "../components/categories.js";
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

const subtitleEl = document.getElementById("shop-subtitle");
const errorEl = document.getElementById("shop-error");
const contentEl = document.getElementById("shop-content");
const progressCard = document.getElementById("shop-progress-card");
const progressText = document.getElementById("shop-progress-text");
const progressPct = document.getElementById("shop-progress-pct");
const progressFill = document.getElementById("shop-progress-fill");
const progressTrack = document.querySelector(".shop-progress-track");

function updateProgress(openCount, boughtCount) {
  const total = openCount + boughtCount;
  if (total === 0) {
    progressCard.hidden = true;
    return;
  }
  const pct = Math.round((boughtCount / total) * 100);
  progressCard.hidden = false;
  progressText.textContent = `تم شراء ${boughtCount} من ${total}`;
  progressPct.textContent = `${pct}%`;
  progressFill.style.width = `${pct}%`;
  if (progressTrack) {
    progressTrack.setAttribute("aria-valuenow", String(pct));
  }
}

function renderShop() {
  contentEl.replaceChildren();

  const openItems = state.items.filter((i) => i.status === "open");
  const boughtItems = state.items.filter((i) => i.status === "bought");

  updateProgress(openItems.length, boughtItems.length);

  if (openItems.length === 0 && boughtItems.length === 0) {
    subtitleEl.textContent = "لا توجد أغراض في القائمة";
    const card = document.createElement("div");
    card.className = "card shop-empty-card";
    const msg = document.createElement("p");
    msg.className = "page-subtitle";
    msg.textContent = "كل شيء تمام! ما في أغراض مفتوحة للتسوق.";
    const link = document.createElement("a");
    link.href = "list.html";
    link.className = "btn btn-primary";
    link.textContent = "أضف أغراض من القائمة";
    card.appendChild(msg);
    card.appendChild(link);
    contentEl.appendChild(card);
    return;
  }

  if (openItems.length === 0) {
    subtitleEl.textContent = "خلصت كل الأغراض! 🎉";
  } else {
    subtitleEl.textContent = `باقي ${openItems.length} غرض في السلة`;
  }

  const byCategory = new Map();
  for (const cat of CATEGORY_ORDER) {
    byCategory.set(cat, []);
  }
  for (const item of openItems) {
    const cat = byCategory.has(item.category) ? item.category : "other";
    byCategory.get(cat).push(item);
  }

  for (const cat of CATEGORY_ORDER) {
    const groupItems = byCategory.get(cat);
    if (!groupItems || groupItems.length === 0) continue;
    contentEl.appendChild(
      renderCategoryGroup({
        category: cat,
        items: groupItems,
        membersById: state.membersById,
        collapsed: state.collapsedGroups.has(cat),
        onToggleCollapse: (key) => {
          if (state.collapsedGroups.has(key)) {
            state.collapsedGroups.delete(key);
          } else {
            state.collapsedGroups.add(key);
          }
          renderShop();
        },
        onToggleItem: handleToggleItem,
        onEditItem: null,
      })
    );
  }

  if (boughtItems.length > 0) {
    contentEl.appendChild(
      renderCategoryGroup({
        category: "__bought__",
        title: "تم شراؤها",
        items: boughtItems,
        membersById: state.membersById,
        collapsed: state.collapsedGroups.has("__bought__"),
        onToggleCollapse: (key) => {
          if (state.collapsedGroups.has(key)) {
            state.collapsedGroups.delete(key);
          } else {
            state.collapsedGroups.add(key);
          }
          renderShop();
        },
        onToggleItem: handleToggleItem,
        onEditItem: null,
      })
    );
  }
}

async function handleToggleItem(item) {
  const nextStatus = item.status === "open" ? "bought" : "open";
  const prevStatus = item.status;

  // Optimistic update
  state.items = state.items.map((i) => (i.id === item.id ? { ...i, status: nextStatus } : i));
  renderShop();

  try {
    const updated = await setItemStatus(item.id, nextStatus);
    state.items = state.items.map((i) => (i.id === item.id ? updated : i));
    state.etag = null;
    renderShop();

    if (nextStatus === "bought") {
      showToast(`تم شراء "${item.name}"`, {
        actionLabel: "تراجع",
        onAction: async () => {
          await setItemStatus(item.id, "open");
          await fetchItems({ force: true });
        },
      });
    }
  } catch (err) {
    state.items = state.items.map((i) => (i.id === item.id ? { ...i, status: prevStatus } : i));
    renderShop();
    errorEl.textContent = err.message || "تعذر تحديث الغرض";
    errorEl.hidden = false;
  }
}

async function fetchItems({ force = false } = {}) {
  try {
    const res = await listItems(force ? null : state.etag);
    if (res.notModified) return;
    state.items = res.data.items || [];
    state.etag = res.etag;
    errorEl.hidden = true;
    renderShop();
  } catch (err) {
    errorEl.textContent = err.message || "تعذر تحميل القائمة";
    errorEl.hidden = false;
  }
}

function startPolling() {
  stopPolling();
  state.pollTimer = window.setInterval(() => {
    if (!document.hidden) {
      fetchItems();
    }
  }, POLL_INTERVAL_MS);
}

function stopPolling() {
  if (state.pollTimer !== null) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) {
    fetchItems();
  }
});

window.addEventListener("pagehide", stopPolling);
window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    fetchItems({ force: true });
    startPolling();
  }
});

async function init() {
  if (!requireAuth()) return;
  const me = await initShell("shop");
  if (me && Array.isArray(me.members)) {
    state.membersById = new Map(me.members.map((m) => [m.id, m]));
  }
  await fetchItems({ force: true });
  startPolling();
}

init();
