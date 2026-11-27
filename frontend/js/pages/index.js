import { createHousehold, getToken, joinHousehold, setToken } from "../api.js";

const MEMBER_COLORS = [
  "#2A7F85",
  "#7A4A7D",
  "#B5622F",
  "#4A5AA8",
  "#6E8B3D",
  "#B84A6B",
];

if (getToken()) {
  window.location.replace("list.html");
}

let mode = "join"; // "join" | "create"
let selectedColor = MEMBER_COLORS[0];

const tabCreate = document.getElementById("tab-create");
const tabJoin = document.getElementById("tab-join");
const householdField = document.getElementById("field-household-name");
const householdInput = document.getElementById("input-household-name");
const codeField = document.getElementById("field-invite-code");
const codeInput = document.getElementById("input-invite-code");
const nameInput = document.getElementById("input-display-name");
const colorPicker = document.getElementById("color-picker");
const submitBtn = document.getElementById("submit-btn");
const errorBox = document.getElementById("auth-error");
const form = document.getElementById("auth-form");

function renderColors() {
  colorPicker.replaceChildren();
  for (const color of MEMBER_COLORS) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "color-dot";
    btn.style.backgroundColor = color;
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-checked", String(color === selectedColor));
    btn.setAttribute("aria-label", `اختيار اللون ${color}`);
    if (color === selectedColor) {
      btn.textContent = "✓";
    }
    btn.addEventListener("click", () => {
      selectedColor = color;
      renderColors();
    });
    colorPicker.appendChild(btn);
  }
}

function setMode(nextMode) {
  mode = nextMode;
  const isCreate = mode === "create";
  tabCreate.setAttribute("aria-selected", String(isCreate));
  tabJoin.setAttribute("aria-selected", String(!isCreate));
  householdField.hidden = !isCreate;
  householdInput.required = isCreate;
  codeField.hidden = isCreate;
  codeInput.required = !isCreate;
  submitBtn.textContent = isCreate ? "أنشئ البيت" : "ادخل";
  errorBox.hidden = true;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

tabCreate.addEventListener("click", () => setMode("create"));
tabJoin.addEventListener("click", () => setMode("join"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  submitBtn.disabled = true;

  try {
    const displayName = nameInput.value.trim();
    if (!displayName) {
      showError("اكتب اسمك أولاً.");
      return;
    }

    if (mode === "create") {
      const householdName = householdInput.value.trim();
      if (!householdName) {
        showError("اكتب اسم البيت.");
        return;
      }
      const res = await createHousehold({
        household_name: householdName,
        display_name: displayName,
        color: selectedColor,
      });
      setToken(res.member_token);
    } else {
      const inviteCode = codeInput.value.trim();
      if (!inviteCode) {
        showError("اكتب كود البيت.");
        return;
      }
      const res = await joinHousehold({
        invite_code: inviteCode,
        display_name: displayName,
        color: selectedColor,
      });
      setToken(res.member_token);
    }

    window.location.replace("list.html");
  } catch (err) {
    if (err.status === 404) {
      showError("كود البيت غير صحيح. تأكد منه وجرب مرة ثانية.");
    } else if (err.status === 429) {
      showError("محاولات كثيرة خاطئة. انتظر 15 دقيقة وجرب مرة ثانية.");
    } else {
      showError(err.message || "تعذر إتمام الطلب.");
    }
  } finally {
    submitBtn.disabled = false;
  }
});

renderColors();
setMode("join");
