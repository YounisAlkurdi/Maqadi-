import { requireAuth } from "../guard.js";
import { initShell } from "../shell.js";

if (requireAuth()) {
  initShell("shop");
}
