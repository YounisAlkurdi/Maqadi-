import { clearToken, getMe } from "./api.js";

const NAV_ITEMS = [
  { id: "list", href: "list.html", label: "القائمة", icon: "M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2m-6 9 2 2 4-4" },
  { id: "shop", href: "shop.html", label: "وضع السوق", icon: "M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4ZM3 6h18M16 10a4 4 0 0 1-8 0" },
  { id: "history", href: "history.html", label: "السجل", icon: "M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" },
  { id: "household", href: "household.html", label: "البيت", icon: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" },
];

function createSvgIcon(pathD, className = "") {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("width", "22");
  svg.setAttribute("height", "22");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "1.75");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  if (className) svg.className.baseVal = className;

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", pathD);
  svg.appendChild(path);
  return svg;
}

function formatInviteCode(code) {
  if (!code || code.length !== 8) return code || "";
  return `${code.slice(0, 4)}-${code.slice(4)}`;
}

export async function initShell(activePage) {
  const sidebarEl = document.getElementById("app-sidebar");
  const tabBarEl = document.getElementById("app-tabbar");
  if (!sidebarEl || !tabBarEl) return null;

  let meData = null;
  try {
    meData = await getMe();
  } catch (err) {
    if (err.status === 401) {
      clearToken();
      window.location.replace("index.html");
      return null;
    }
  }

  sidebarEl.replaceChildren();
  tabBarEl.replaceChildren();

  // Brand wordmark
  const brand = document.createElement("div");
  brand.className = "brand-wordmark";
  brand.appendChild(
    createSvgIcon("M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11", "brand-icon")
  );
  const brandLabel = document.createElement("span");
  brandLabel.className = "brand-label";
  brandLabel.textContent = "طلبات البيت";
  brand.appendChild(brandLabel);
  sidebarEl.appendChild(brand);

  // Household badge
  if (meData) {
    const badge = document.createElement("div");
    badge.className = "household-badge";
    const avatar = document.createElement("span");
    avatar.className = "avatar";
    avatar.style.backgroundColor = meData.member.color;
    avatar.textContent = meData.member.display_name.slice(0, 1);
    const hhName = document.createElement("span");
    hhName.textContent = meData.household.name;
    badge.appendChild(avatar);
    badge.appendChild(hhName);
    sidebarEl.appendChild(badge);
  }

  // Nav list
  const nav = document.createElement("nav");
  nav.setAttribute("aria-label", "التنقل الرئيسي");
  const ul = document.createElement("ul");
  ul.className = "nav-list";

  for (const item of NAV_ITEMS) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.className = "nav-link";
    a.href = item.href;
    if (item.id === activePage) {
      a.setAttribute("aria-current", "page");
    }
    a.appendChild(createSvgIcon(item.icon));
    const label = document.createElement("span");
    label.className = "nav-label";
    label.textContent = item.label;
    a.appendChild(label);
    li.appendChild(a);
    ul.appendChild(li);

    // Bottom tab bar item
    const tabA = document.createElement("a");
    tabA.className = "tab-link";
    tabA.href = item.href;
    if (item.id === activePage) {
      tabA.setAttribute("aria-current", "page");
    }
    tabA.appendChild(createSvgIcon(item.icon));
    const tabLabel = document.createElement("span");
    tabLabel.textContent = item.label;
    tabA.appendChild(tabLabel);
    tabBarEl.appendChild(tabA);
  }
  nav.appendChild(ul);
  sidebarEl.appendChild(nav);

  // Invite code mini card
  if (meData) {
    const card = document.createElement("div");
    card.className = "invite-mini-card";
    const title = document.createElement("span");
    title.className = "field-label";
    title.textContent = "كود البيت";
    const row = document.createElement("div");
    row.className = "invite-mini-row";
    const codeSpan = document.createElement("span");
    codeSpan.className = "invite-code-text";
    codeSpan.textContent = formatInviteCode(meData.household.invite_code);

    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "btn btn-text";
    copyBtn.textContent = "نسخ";
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(meData.household.invite_code);
        copyBtn.textContent = "تم";
        setTimeout(() => {
          copyBtn.textContent = "نسخ";
        }, 1500);
      } catch {
        copyBtn.textContent = "نسخ";
      }
    });

    row.appendChild(codeSpan);
    row.appendChild(copyBtn);
    card.appendChild(title);
    card.appendChild(row);
    sidebarEl.appendChild(card);
  }

  return meData;
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}
