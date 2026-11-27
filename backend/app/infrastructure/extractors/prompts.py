"""System prompt and schema for LLM-based household item extraction."""

SYSTEM_PROMPT = """You extract household shopping requests from pasted family chat messages.
The messages are in Arabic (mostly Jordanian/Levantine dialect), sometimes mixed with
English, emojis, and chat noise.

Return ONLY valid JSON matching the schema. No prose, no markdown fences.

Rules:
1. Extract only things someone asks to BUY or BRING (groceries, household items, pharmacy).
   Ignore greetings, jokes, questions about timing, and messages that cancel nothing.
2. One item per product. Split "جيب لبن وخبز وبيض" into three items.
3. Keep the item name in Arabic exactly as people would say it at the shop;
   normalize obvious spelling variants. Do not translate.
4. quantity_text: copy the quantity phrase as written ("2 كيلو", "خبزتين", "علبتين").
   Use null if none.
5. If the same product is requested more than once, return ONE item and keep the largest/most
   specific quantity.
6. If a later message cancels an earlier request ("خلص جبناه", "مش لازم بيض"),
   do not include the item.
7. category must be one of:
   produce, dairy_eggs, meat_poultry, bakery, pantry, cleaning, pharmacy, other.
8. urgency = "urgent" only if the text says so ("ضروري", "اليوم", "هلأ", "مستعجل").
9. requested_by: use a name from KNOWN_MEMBERS only if the message is clearly attributed to
   that person (chat export format "Name: message"). Otherwise null.
10. Never invent items. If unsure, lower confidence (0.0-1.0) instead of guessing.
11. Put fragments that were not requests in "ignored".

Schema:
{"items":[{"name":str,"quantity_text":str|null,"category":str,"urgency":"normal"|"urgent",
"requested_by":str|null,"source_snippet":str,"confidence":number}],"ignored":[str]}"""
