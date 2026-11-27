let activeTimer = null;

export function showToast(container, message, { actionLabel = null, onAction = null, durationMs = 5000 } = {}) {
  if (activeTimer) {
    clearTimeout(activeTimer);
    activeTimer = null;
  }

  container.replaceChildren();
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.setAttribute("role", "status");
  toast.setAttribute("aria-live", "polite");

  const text = document.createElement("span");
  text.textContent = message;
  toast.appendChild(text);

  if (actionLabel && onAction) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-text toast-action";
    btn.textContent = actionLabel;
    btn.addEventListener("click", () => {
      if (activeTimer) clearTimeout(activeTimer);
      container.replaceChildren();
      onAction();
    });
    toast.appendChild(btn);
  }

  container.appendChild(toast);

  activeTimer = setTimeout(() => {
    container.replaceChildren();
    activeTimer = null;
  }, durationMs);
}
