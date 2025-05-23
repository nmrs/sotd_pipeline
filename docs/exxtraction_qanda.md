# Extraction Step – SOTD Fetcher

## Goal

Extract structured product mentions from SOTD comment text. These "shaves" include references to Razor, Blade, Brush, and Soap. Extracted records will be written to a local file for downstream matching and aggregation.

---

## Q&A Log

### 1. What fields should be extracted?
- **Razor**, **Blade**, **Brush**, **Soap**
- At least one must be present for it to count as a shave.

### 2. Should we support multiple values per field?
- Yes, uncommon but supported. Use lists if multiple values appear.

### 3. Where should normalization/standardization happen?
- In the **matching** phase, not here. This phase stores raw extracted text.

### 4. Should we extract blade use count (e.g. "(3)")?
- Yes, since it's a common pattern and easy to parse.
- Store it in a structured way during extraction.

### 5. How should multiple razors/blades be handled?
- Support multiple items per field (as lists).

### 6. What’s the format of the extracted record?
- A single JSON object per comment (shave), with:
  - `id`
  - `author`
  - `created_utc`
  - `url`
  - `thread_id`
  - `thread_title`
  - Any of: `razor`, `blade`, `brush`, `soap`
- Only include fields that are present (minimal, clean).

### 7. Where will extracted shaves be saved?
- One file per month: `extracted/YYYY-MM.json`

### 8. What counts as a single shave?
- Each comment = one shave (even if multiple product lines)

### 9. What if someone posts two SOTDs in one comment?
- Extremely rare. Treat it as one shave.

### 10. What if a product field appears multiple times?
- Collect all values under the appropriate field (as list).

### 11. What if a field is missing?
- Omit the field in the JSON.
- Don’t record the comment at all unless one product field is found.

### 12. What about post-shave, fragrance, etc?
- Not extracted during this phase. May reconsider later.

### 13. Should we store the original body text?
- Yes, include it in case matching wants to reference it.

### 14. What cleanup should we do on text?
- Minimal, including:
  - Remove HTML tags
  - Remove Markdown formatting
  - Strip invisible/control characters
  - Trim leading/trailing whitespace
  - Remove leading/trailing punctuation (except internal ones like “0.84”)

### 15. How should we match field labels?
- Case-insensitive
- Allow common label variants and markdown formatting (e.g. `**Brush**`, `Razor -`, `*Razor*`)
- Support non-colon separators like `*Brush* Turn N Shave`

### 16. Should comments be deduplicated?
- No. Assume unique comment IDs = unique shave records.

### 17. Should blade use count be included in the blade field or separated?
- Include separately:  
  `"blade": [{"name": "Gillette Minora", "use": 3}]`

### 18. Should we dedupe blade entries (e.g. “Gillette Minora (3)” + “Gillette Minora”)?
- Let matching phase handle normalization/merge.

### 19. Should we extract product lines like `**Razor:**` as a required format?
- Yes. Labeled lines only. No free-text NLP yet.

### 20. How to handle free-text or unlabeled comments?
- Skip them in extraction.

### 21. Should extracted fields always appear in a fixed order?
- Yes. Output fields should follow a consistent order for readability.

### 22. Should we extract labeled fields that appear inline (on a single line)?
- Yes, if the labels and values are clearly separated (e.g. `Razor: Blackbird Blade: Nacet (3)`).

### 23. What if labeled fields are separated by whitespace instead of newlines or punctuation?
- Treat them the same as newline-separated fields, as long as formatting is clear and label/value pairs are intact.

### 24. What if a product name appears on its own line between two labeled fields?
- Include it if it's in the middle of known fields.  
  Skip it if it’s after the last known field—assume it’s commentary.

### 25. Should we support labeled fields that use alternate markdown/punctuation?
- Yes, support markdown-style (`**Blade**`, `*Brush*`) and alternate separators (`Razor -`, `Blade —`) when formatting is consistent.

### 26. Should we parse markdown tables as shaves?
- Yes, treat each table row as contributing to a single shave if it's all from one comment.

### 27. Should we parse list-style bullet points like `• Razor: Blackbird`?
- Yes, treat them as labeled fields and extract normally.

### 28. What if the label is present but the value is missing?
- Ignore that field.  
  Example: `"Soap:"` or `"Blade - "` with no value → skip.

### 29. What if labels appear multiple times in one comment?
- Collect all values under that field (as a list).

### 30. What if the field is strangely formatted (e.g. as a reply block)?
- Still attempt to extract it if it fits labeled field structure.

### 31. What if product names are separated by bullets or emojis?
- Include them as-is. Emojis are part of the original formatting and sometimes meaningful (e.g. Stirling 🟩 for Green).

### 32. What if someone posts a poem or freeform text and one line happens to mention a product?
- Skip it unless it’s part of a labeled structure.

### 33. What if the label uses a known alternate (e.g. Lather, Soap)?
- Support common alternates for known product types.

### 34. What if a label is misspelled (e.g. “Razr” or “Lathr”)?
- Support common misspellings and close variants as alternate labels for extraction.

### 35. What if multiple labeled fields appear on one line but without clear separators?
- As long as label-value pairs are intact and formatting is clear, whitespace alone is enough.

### 36. What if a product line ends with punctuation (e.g. “Soap: Tabac!”)?
- Strip trailing punctuation unless it's clearly part of the product name (e.g. “0.84”).

### 37. What if a field exceeds a reasonable length (e.g. long comment pasted accidentally)?
- Truncate values longer than 150 characters and preserve original for matching.

### 38. Should we preserve original case and formatting?
- Yes, keep as-is for matching phase.

### 39. Should we clean out URLs and other "garbage"?
- Yes, remove obvious garbage like URLs during extraction. Emojis are allowed.

### 40. What if a label is used inline but surrounded by strange formatting (e.g. markdown quote or reply block)?
- Still extract if it fits known label/value structure.

### 41. What if a field uses a prefix like “LATHR” instead of “Lather”?
- Support these as additional label variants.


### 42. What if a field has extra text on the same line but it's clearly a label + value?
- Extract the label/value pair and ignore trailing comment content if clearly separate.

### 43. If multiple values are extracted for a single field, should their order be preserved?
- Yes. Preserve the order as they appear in the comment.

### 44. What if a labeled field appears inline without space after the colon (e.g. "Razor:Blackbird")?
- Treat it as valid and extract the field normally.

### 45. What if a label appears on one line and the value on the next?
- Treat it as valid **if** another known field follows.  
  If no known field follows, assume the next line is commentary and stop extraction.

### 46. What if a field value is just an emoji (e.g. "Soap: 🟩")?
- Extract as-is. Emojis may carry meaningful context.

### 47. What if a labeled line is quoted (e.g. `> Razor: Blackbird`)?
- Still extract the field. Treat it as part of the user's shave.
