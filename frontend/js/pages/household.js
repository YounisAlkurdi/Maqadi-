import { clearToken, removeMember, rotateInviteCode } from "../api.js";
import { showToast } from "../components/toast.js";
import { requireAuth } from "../guard.js";
import { initShell } from "../shell.js";

const titleEl = document.getElementById("household-title");
const subtitleEl = document.getElementById("household-subtitle");
const errorEl = document.getElementById("household-error");
const inviteCodeEl = document.getElementById("invite-code-value");
const copyInviteBtn = document.getElementById("copy-invite-btn");
const rotateInviteBtn = document.getElementById("rotate-invite-btn");
const membersListEl = document.getElementById("members-list");
const logoutBtn = document.getElementById("logout-btn");

let currentInviteCode = "";
let currentMembers = [];
let currentActorId = "";

function renderMembers(members, currentMemberId) {
  currentMembers = members;
  currentActorId = currentMemberId;
  subtitleEl.textContent = `${members.length} أعضاء في البيت`;
  membersListEl.replaceChildren();
  for (const member of members) {
    const li = document.createElement("li");
    li.className = "member-row";

    const dot = document.createElement("span");
    dot.className = "member-dot";
    dot.style.backgroundColor = member.color || "#2B7A78";

    const name = document.createElement("span");
    name.className = "member-name";
    name.textContent = member.display_name;

    li.appendChild(dot);
    li.appendChild(name);

    if (member.id === currentMemberId) {
      const badge = document.createElement("span");
      badge.className = "badge-muted";
      badge.textContent = "أنت";
      li.appendChild(badge);
    } else {
      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "btn btn-text member-remove-btn";
      removeBtn.textContent = "إزالة";
      removeBtn.addEventListener("click", async () => {
        if (!window.confirm(`إزالة "${member.display_name}" من البيت؟`)) return;
        errorEl.hidden = true;
        removeBtn.disabled = true;
        try {
          await removeMember(member.id);
          const next = currentMembers.filter((m) => m.id !== member.id);
          renderMembers(next, currentActorId);
          showToast(`تمت إزالة ${member.display_name}`);
        } catch (err) {
          errorEl.textContent = err.message || "تعذر إزالة العضو";
          errorEl.hidden = false;
          removeBtn.disabled = false;
        }
      });
      li.appendChild(removeBtn);
    }

    membersListEl.appendChild(li);
  }
}

copyInviteBtn.addEventListener("click", async () => {
  if (!currentInviteCode) return;
  try {
    await navigator.clipboard.writeText(currentInviteCode);
    showToast("تم نسخ رمز الدعوة");
  } catch {
    showToast(`رمز الدعوة: ${currentInviteCode}`);
  }
});

rotateInviteBtn.addEventListener("click", async () => {
  errorEl.hidden = true;
  rotateInviteBtn.disabled = true;
  rotateInviteBtn.textContent = "جاري التجديد…";
  try {
    const res = await rotateInviteCode();
    currentInviteCode = res.invite_code || "";
    inviteCodeEl.textContent = currentInviteCode || "------";
    showToast("تم تجديد رمز الدعوة");
  } catch (err) {
    errorEl.textContent = err.message || "تعذر تجديد رمز الدعوة";
    errorEl.hidden = false;
  } finally {
    rotateInviteBtn.disabled = false;
    rotateInviteBtn.textContent = "تجديد الرمز";
  }
});

logoutBtn.addEventListener("click", () => {
  clearToken();
  window.location.href = "index.html";
});

async function init() {
  if (!requireAuth()) return;
  const me = await initShell("household");
  if (!me) {
    errorEl.textContent = "تعذر تحميل بيانات البيت";
    errorEl.hidden = false;
    return;
  }

  titleEl.textContent = me.household.name;
  const count = Array.isArray(me.members) ? me.members.length : 0;
  subtitleEl.textContent = `${count} أعضاء في البيت`;

  currentInviteCode = me.household.invite_code || "";
  inviteCodeEl.textContent = currentInviteCode || "------";
  renderMembers(me.members || [], me.member.id);
}

init();
