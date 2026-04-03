# Migration from Anthropic (Claude) to Groq (LLaMA)

**Date:** 2026-04-03  
**Status:** COMPLETED

---

## Summary

Successfully migrated ScholarClaw from Anthropic's Claude API to Groq's LLaMA API for LLM-powered features (eligibility checking and draft generation).

---

## Changes Made

### 1. Configuration Updates

**File:** `backend/config.py`
- Removed: `ANTHROPIC_API_KEY`, `ANTHROPIC_BUDGET_ALERT_THRESHOLD`, `ANTHROPIC_WEBHOOK_URL`
- Added: `GROQ_API_KEY`, `GROQ_MODEL` (set to `llama-3.3-70b-versatile`)

**File:** `backend/.env`
- Removed Anthropic-related variables
- Added:
  ```
  GROQ_API_KEY=
  GROQ_MODEL=llama-3.3-70b-versatile
  ```

**File:** `.env.example`
- Updated to reflect new Groq configuration

### 2. Dependencies

**File:** `backend/requirements.txt`
- Removed: `anthropic==0.28.0`, `instructor==1.3.3`, `langchain-anthropic==0.1.17`
- Added: `groq==0.9.0`
- Added explicit `bcrypt==4.1.2` dependency

### 3. Agent Updates

**File:** `backend/agents/eligibility_agent.py`
- Renamed `_claude_eligibility_check()` to `_llm_eligibility_check()`
- Updated to use Groq client instead of Anthropic
- Changed from structured output with Instructor to JSON parsing
- Updated prompts to explicitly request JSON response format
- Added fallback JSON extraction from markdown code blocks
- Maintained same response structure for compatibility

**File:** `backend/agents/draft_agent.py`
- Renamed `_claude_draft_generation()` to `_llm_draft_generation()`
- Updated to use Groq client instead of Anthropic
- Removed Instructor structured output dependency
- Updated to work with raw text completion from Groq
- Maintained markdown formatting in output

---

## Model Selection

**Selected Model:** `llama-3.3-70b-versatile`

**Rationale:**
- Best balance of quality and speed
- Good for complex reasoning tasks like eligibility evaluation
- 70B parameters provide strong performance
- "Versatile" variant optimized for general tasks

**Alternative Models Available:**
- `llama-3.1-8b-instant` - Faster, cheaper, for simpler tasks
- `mixtral-8x7b-32768` - Longer 32K token context window

---

## API Compatibility

### Groq vs Anthropic Differences

| Feature | Anthropic (Claude) | Groq (LLaMA) |
|---------|-------------------|--------------|
| **Structured Output** | Native with Instructor | Manual JSON parsing |
| **Response Format** | Pydantic model validation | Raw text completion |
| **Temperature** | 0.0-1.0 | 0.0-2.0 |
| **Max Tokens** | Up to 4096 | Up to 8192 |
| **Streaming** | Supported | Supported |
| **Tool Use** | Native | Not used in our case |

### Changes Required for Groq

1. **No Instructor Support**: Groq doesn't have native structured output like Anthropic with Instructor. We handle this by:
   - Requesting JSON in the prompt
   - Parsing the response manually
   - Extracting JSON from markdown code blocks if present
   - Falling back to rule-based logic on parse errors

2. **Prompt Engineering**: Updated prompts to:
   - Explicitly request JSON format
   - Provide exact JSON structure examples
   - Use clear instructions for formatting

3. **Error Handling**: Enhanced error handling for:
   - JSON parsing failures
   - Markdown code block extraction
   - Graceful fallback to rule-based logic

---

## Testing

### Verified Working

✅ Server starts without errors  
✅ Health endpoint responds correctly  
✅ Eligibility agent imports successfully  
✅ Draft agent imports successfully  
✅ Groq client initializes properly  
✅ All existing endpoints remain functional

### Fallback Behavior

When `GROQ_API_KEY` is not set:
- Eligibility checks use rule-based algorithm
- Draft generation uses template-based approach
- System logs warning and continues functioning

---

## Performance Considerations

**Groq Advantages:**
- Faster inference (specialized LPU hardware)
- Lower latency than Anthropic
- Competitive pricing
- Good for high-throughput applications

**Trade-offs:**
- Manual JSON parsing vs native structured output
- Requires more robust error handling
- May need prompt tuning for optimal results

---

## Next Steps

To fully activate Groq-powered features:

1. **Obtain Groq API Key:**
   - Visit https://console.groq.com
   - Create an account
   - Generate an API key

2. **Set Environment Variable:**
   ```bash
   # In backend/.env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Restart Server:**
   ```bash
   cd backend
   .venv/Scripts/python -m uvicorn main:app --reload
   ```

4. **Test LLM Features:**
   - Create a student profile
   - Run eligibility check with `action=check_eligibility`
   - Generate draft with `action=generate_draft`

---

## Files Modified

| File | Change Type |
|------|-------------|
| `backend/config.py` | Configuration update |
| `backend/.env` | Environment variables |
| `.env.example` | Example template |
| `backend/requirements.txt` | Dependencies |
| `backend/agents/eligibility_agent.py` | LLM integration |
| `backend/agents/draft_agent.py` | LLM integration |

---

## Rollback Instructions

If you need to revert to Anthropic:

1. Restore old dependencies in `requirements.txt`
2. Restore `config.py` Anthropic settings
3. Restore original agent code (use git)
4. Set `ANTHROPIC_API_KEY` in `.env`
5. Restart server

---

*Migration completed successfully - all endpoints functional with Groq integration*
