# Maqadi — طلبات البيت

موقع ويب عربي (RTL) لمشاركة قائمة طلبات البيت بين أفراد العائلة، مع استخراج ذكي للطلبات من رسائل الواتساب.

## التشغيل المحلي

```bash
cd backend && uv sync --extra dev
cp ../.env.example ../.env
cd backend && uv run uvicorn app.main:app --reload
```

افتح `http://localhost:8000` في المتصفح، و`http://localhost:8000/api/v1/healthz` للتحقق من الخادم.
