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
 * Wire voice input to a <textarea>.
 * @param {{ textarea: HTMLTextAreaElement, btn: HTMLButtonElement,
 *            btnLabel: HTMLElement, statusEl: HTMLElement }} opts
 */
export function initVoiceInput({ textarea, btn, btnLabel, statusEl }) {
  if (!isVoiceSupported()) return;

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SR();
  recognition.lang = "ar-SA";
  recognition.continuous = false;
  recognition.interimResults = true;

  let listening = false;
  let finalText = "";

  btn.hidden = false;

  function setListening(active) {
    listening = active;
    btn.setAttribute("aria-pressed", String(active));
    btn.classList.toggle("voice-btn--active", active);
    btnLabel.textContent = active ? "جاري التسجيل…" : "تسجيل";
    statusEl.hidden = !active;
    if (active) statusEl.textContent = "🎙 تكلم الآن…";
  }

  recognition.addEventListener("start", () => setListening(true));

  recognition.addEventListener("result", (e) => {
    let interim = "";
    finalText = "";
    for (const res of e.results) {
      if (res.isFinal) {
        finalText += res[0].transcript;
      } else {
        interim += res[0].transcript;
      }
    }
    statusEl.textContent = interim ? `🎙 ${interim}` : "🎙 تكلم الآن…";
  });

  recognition.addEventListener("end", () => {
    setListening(false);
    statusEl.hidden = true;
    if (finalText.trim()) {
      const sep = textarea.value.trim() ? "\n" : "";
      textarea.value = textarea.value.trimEnd() + sep + finalText.trim();
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
      recognition.start();
    }
  });
}
