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
const removeBackdrop = document.getElementById("remove-dialog-backdrop");
const removeMessageEl = document.getElementById("remove-dialog-message");
const removeErrorEl = document.getElementById("remove-dialog-error");
const removeCloseBtn = document.getElementById("remove-dialog-close");
const removeCancelBtn = document.getElementById("remove-dialog-cancel");
const removeConfirmBtn = document.getElementById("remove-dialog-confirm");
const logoutBackdrop = document.getElementById("logout-dialog-backdrop");
const logoutInviteCodeEl = document.getElementById("logout-invite-code");
const logoutCopyCodeBtn = document.getElementById("logout-copy-code");
const logoutCloseBtn = document.getElementById("logout-dialog-close");
const logoutCancelBtn = document.getElementById("logout-dialog-cancel");
const logoutConfirmBtn = document.getElementById("logout-dialog-confirm");

let currentInviteCode = "";
let currentMembers = [];
let currentActorId = "";
let pendingRemoveMember = null;

function openRemoveDialog(member) {
  pendingRemoveMember = member;
  removeMessageEl.textContent = `هل أنت متأكد من إزالة «${member.display_name}» من البيت؟`;
  removeErrorEl.hidden = true;
  removeConfirmBtn.disabled = false;
  removeConfirmBtn.textContent = "نعم، إزالة العضو";
  removeBackdrop.hidden = false;
  removeCancelBtn.focus();
}

function closeRemoveDialog() {
  removeBackdrop.hidden = true;
  pendingRemoveMember = null;
}

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
      removeBtn.addEventListener("click", () => openRemoveDialog(member));
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

function openLogoutDialog() {
  logoutInviteCodeEl.textContent = formatCode(currentInviteCode) || "----";
  logoutBackdrop.hidden = false;
  logoutCancelBtn.focus();
}

function closeLogoutDialog() {
  logoutBackdrop.hidden = true;
}

logoutBtn.addEventListener("click", openLogoutDialog);
logoutCloseBtn.addEventListener("click", closeLogoutDialog);
logoutCancelBtn.addEventListener("click", closeLogoutDialog);
logoutBackdrop.addEventListener("click", (e) => {
  if (e.target === logoutBackdrop) closeLogoutDialog();
});
logoutCopyCodeBtn.addEventListener("click", async () => {
  if (!currentInviteCode) return;
  try {
    await navigator.clipboard.writeText(currentInviteCode);
    showToast("تم نسخ كود البيت");
  } catch {
    showToast("انسخ الكود يدوياً: " + currentInviteCode);
  }
});
logoutConfirmBtn.addEventListener("click", () => {
  clearToken();
  window.location.href = "index.html";
});

removeCloseBtn.addEventListener("click", closeRemoveDialog);
removeCancelBtn.addEventListener("click", closeRemoveDialog);
removeBackdrop.addEventListener("click", (e) => {
  if (e.target === removeBackdrop) closeRemoveDialog();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (!removeBackdrop.hidden) closeRemoveDialog();
    if (!logoutBackdrop.hidden) closeLogoutDialog();
  }
});

removeConfirmBtn.addEventListener("click", async () => {
  if (!pendingRemoveMember) return;
  const target = pendingRemoveMember;
  removeErrorEl.hidden = true;
  removeConfirmBtn.disabled = true;
  removeConfirmBtn.textContent = "جاري الإزالة…";
  try {
    await removeMember(target.id);
    const next = currentMembers.filter((m) => m.id !== target.id);
    closeRemoveDialog();
    renderMembers(next, currentActorId);
    showToast(`تمت إزالة ${target.display_name}`);
  } catch (err) {
    removeErrorEl.textContent = err.message || "تعذر إزالة العضو";
    removeErrorEl.hidden = false;
    removeConfirmBtn.disabled = false;
    removeConfirmBtn.textContent = "نعم، إزالة العضو";
  }
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
