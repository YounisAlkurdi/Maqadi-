/**
 * Voice input helper using the Web Speech API (SpeechRecognition).
 * Falls back gracefully when the browser does not support it.
 *
 * Usage:
 *   import { initVoiceInput } from "./voice.js";
 *   initVoiceInput({ textarea, btn, btnLabel, statusEl });
 */

export function isVoiceSupported() {
  return typeof window !== "undefined" &&
    !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

/**
 * Wire voice input to a field or callback.
 * @param {{ textarea?: HTMLTextAreaElement|HTMLInputElement, btn: HTMLButtonElement,
 *            statusEl: HTMLElement, onTranscript?: (text: string) => Promise<void>|void }} opts
 */
export function initVoiceInput({ textarea, btn, statusEl, onTranscript }) {
  if (!btn || (!textarea && !onTranscript)) return;

  if (!isVoiceSupported()) {
    btn.addEventListener("click", () => {
      statusEl.hidden = false;
      statusEl.textContent = "الإدخال الصوتي غير مدعوم في هذا المتصفح (جرّب Chrome أو Edge).";
    });
    return;
  }

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SR();
  recognition.lang = "ar-SA";
  recognition.continuous = true;
  recognition.interimResults = true;

  let listening = false;
  let finalText = "";
  let latestInterim = "";

  function setListening(active) {
    listening = active;
    btn.setAttribute("aria-pressed", String(active));
    btn.setAttribute("aria-label", active ? "إيقاف الإدخال الصوتي" : "إدخال صوتي");
    btn.classList.toggle("voice-btn--active", active);
    statusEl.hidden = !active;
    if (active) statusEl.textContent = "جاري الاستماع… اضغط المايك للإيقاف";
  }

  recognition.addEventListener("start", () => setListening(true));

  recognition.addEventListener("result", (e) => {
    let f = "";
    let interim = "";
    for (const res of e.results) {
      const t = res[0].transcript;
      if (res.isFinal) {
        f += (f ? " " : "") + t.trim();
      } else {
        interim += (interim ? " " : "") + t.trim();
      }
    }
    finalText = f;
    latestInterim = interim;
    const combined = [finalText, latestInterim].filter(Boolean).join(" ");
    statusEl.textContent = combined || "جاري الاستماع… اضغط المايك للإيقاف";
  });

  recognition.addEventListener("end", async () => {
    const wasListening = listening;
    setListening(false);
    const spoken = [finalText, latestInterim].filter(Boolean).join(" ").trim();
    finalText = "";
    latestInterim = "";
    if (!wasListening) return;

    if (!spoken) {
      statusEl.hidden = false;
      statusEl.textContent = "لم يُكتشف أي كلام، حاول مرة أخرى.";
      return;
    }

    if (onTranscript) {
      await onTranscript(spoken);
    } else if (textarea) {
      const sep = textarea.value.trim()
        ? textarea.tagName === "TEXTAREA" ? "\n" : " "
        : "";
      textarea.value = textarea.value.trimEnd() + sep + spoken;
      textarea.dispatchEvent(new Event("input", { bubbles: true }));
      textarea.focus();
    }
  });

  recognition.addEventListener("error", (e) => {
    setListening(false);
    statusEl.hidden = false;
    const msgs = {
      "not-allowed": "الرجاء السماح بالوصول إلى الميكروفون.",
      "no-speech": "لم يُكتشف أي كلام، حاول مرة أخرى.",
      "network": "تعذر الاتصال، تحقق من الإنترنت.",
    };
    statusEl.textContent = msgs[e.error] || `خطأ في التسجيل (${e.error}).`;
  });

  btn.addEventListener("click", () => {
    if (listening) {
      recognition.stop();
    } else {
      finalText = "";
      latestInterim = "";
      recognition.start();
    }
  });
}
