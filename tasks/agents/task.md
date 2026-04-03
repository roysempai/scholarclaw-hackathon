# Block: AGENTS
## Status: PENDING BUILD
## Pentest findings will be written here after the block is built.

### Overview
AI agents powered by Anthropic Claude for eligibility checking and draft generation.

### Agents
1. **EligibilityAgent** - Checks user eligibility for schemes
2. **DraftAgent** - Generates application drafts
3. **ReminderAgent** - Manages deadline reminders

### Technologies
- Anthropic Claude API
- LangGraph for orchestration
- Instructor for structured outputs

### Security Requirements
- Input sanitization before sending to LLM
- Output validation
- Prompt injection protection via ArmorIQ
- Token usage monitoring
- All calls logged to audit chain
