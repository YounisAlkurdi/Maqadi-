import { ApiError, clearBoughtItems, createItem, getItemHistory } from "../api.js";
import { CATEGORY_META } from "../components/categories.js";
import { showToast } from "../components/toast.js";
import { requireAuth } from "../guard.js";
import { initShell } from "../shell.js";

const subtitleEl = document.getElementById("history-subtitle");
const errorEl = document.getElementById("history-error");
const listEl = document.getElementById("history-list");
const clearBoughtBtn = document.getElementById("clear-bought-btn");

let membersById = new Map();

function renderHistory(items) {
  listEl.replaceChildren();

  if (!items || items.length === 0) {
    subtitleEl.textContent = "لا توجد مشتريات سابقة";
    const card = document.createElement("div");
    card.className = "card shop-empty-card";
    const msg = document.createElement("p");
    msg.className = "page-subtitle";
    msg.textContent = "أي غرض تشتريه سيظهر هنا لتتمكن من إعادته للقائمة بسهولة.";
    card.appendChild(msg);
    listEl.appendChild(card);
    return;
  }

  subtitleEl.textContent = `آخر ${items.length} غرض تم شراؤه`;

  const card = document.createElement("div");
  card.className = "card history-card";

  for (const item of items) {
    const row = document.createElement("div");
    row.className = "history-row";

    const info = document.createElement("div");
    info.className = "history-info";

    const name = document.createElement("div");
    name.className = "history-name";
    name.textContent = item.name;

    const meta = document.createElement("div");
    meta.className = "history-meta";

    if (item.quantity_text) {
      const qty = document.createElement("span");
      qty.textContent = item.quantity_text;
      meta.appendChild(qty);
    }

    const catMeta = CATEGORY_META[item.category] || CATEGORY_META.other;
    const cat = document.createElement("span");
    cat.textContent = catMeta.label;
    meta.appendChild(cat);

    if (item.bought_by_member_id && membersById.has(item.bought_by_member_id)) {
      const buyer = document.createElement("span");
      buyer.textContent = `اشتراه ${membersById.get(item.bought_by_member_id).display_name}`;
      meta.appendChild(buyer);
    }

    info.appendChild(name);
    info.appendChild(meta);

    const readdBtn = document.createElement("button");
    readdBtn.type = "button";
    readdBtn.className = "btn btn-secondary";
    readdBtn.textContent = "أضف للقائمة";
    readdBtn.addEventListener("click", async () => {
      readdBtn.disabled = true;
      try {
        await createItem({
          name: item.name,
          quantity_text: item.quantity_text || null,
          category: item.category || "other",
          urgency: "normal",
        });
        showToast(`تمت إضافة "${item.name}" للقائمة`);
      } catch (err) {
        if (err instanceof ApiError && err.status === 409) {
          showToast(`"${item.name}" موجود أصلاً في القائمة`);
        } else {
          errorEl.textContent = err.message || "تعذر إضافة الغرض";
          errorEl.hidden = false;
        }
      } finally {
        readdBtn.disabled = false;
      }
    });

    row.appendChild(info);
    row.appendChild(readdBtn);
    card.appendChild(row);
  }

  listEl.appendChild(card);
}

clearBoughtBtn.addEventListener("click", async () => {
  errorEl.hidden = true;
  clearBoughtBtn.disabled = true;
  clearBoughtBtn.textContent = "جاري الأرشفة…";
  try {
    const res = await clearBoughtItems();
    const count = res.archived_count || 0;
    showToast(count > 0 ? `تمت أرشفة ${count} غرض` : "لا توجد أغراض مشتراة للأرشفة");
    await loadHistory();
  } catch (err) {
    errorEl.textContent = err.message || "تعذر أرشفة المشتراة";
    errorEl.hidden = false;
  } finally {
    clearBoughtBtn.disabled = false;
    clearBoughtBtn.textContent = "أرشفة المشتراة";
  }
});

async function loadHistory() {
  try {
    const data = await getItemHistory(50);
    errorEl.hidden = true;
    renderHistory(data.items || []);
  } catch (err) {
    errorEl.textContent = err.message || "تعذر تحميل السجل";
    errorEl.hidden = false;
  }
}

async function init() {
  if (!requireAuth()) return;
  const me = await initShell("history");
  if (me && Array.isArray(me.members)) {
    membersById = new Map(me.members.map((m) => [m.id, m]));
  }
  await loadHistory();
}

init();
