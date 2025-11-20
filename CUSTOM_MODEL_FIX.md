# Custom Model Name Issue

## Problem

Your API provider (`https://api.bltcy.ai`) supports the model `gpt-5-nano-2025-08-07`, but LlamaIndex's OpenAI wrapper validates model names against the official OpenAI model list, causing this error:

```
Unknown model 'gpt-5-nano-2025-08-07'. Please provide a valid OpenAI model name...
```

## Verified

✅ Your API provider DOES support `gpt-5-nano-2025-08-07`  
✅ Direct OpenAI SDK calls work fine  
❌ LlamaIndex's OpenAI wrapper blocks it

## Solutions

### Option 1: Use a Standard Model Name (RECOMMENDED)

The easiest solution is to use a standard OpenAI model name that your API provider also supports:

**In Railway, set**:
```bash
CHAT_MODEL=gpt-4o-mini
```

Your API provider supports this model and it will work without any code changes.

### Option 2: Monkey Patch LlamaIndex (Complex)

We could monkey-patch the validation in LlamaIndex, but this is fragile and may break with updates.

### Option 3: Fork LlamaIndex (Not Recommended)

Fork and modify LlamaIndex to disable validation - too much maintenance overhead.

### Option 4: Use Raw OpenAI SDK (Requires Refactoring)

Bypass LlamaIndex's OpenAI wrapper and use the OpenAI SDK directly - requires significant code changes.

## Recommendation

**Use Option 1**: Set `CHAT_MODEL=gpt-4o-mini` in Railway.

This model:
- ✅ Is supported by your API provider (verified)
- ✅ Works with LlamaIndex without modifications
- ✅ Is cost-effective
- ✅ Has good performance

## Steps

1. Go to Railway dashboard
2. Select your API service
3. Go to "Variables" tab
4. Change `CHAT_MODEL` from `gpt-5-nano-2025-08-07` to `gpt-4o-mini`
5. Railway will automatically restart
6. Run `python test_production.py` to verify

## Alternative Models

If `gpt-4o-mini` doesn't work, try these (in order):
1. `gpt-4o`
2. `gpt-4-turbo`
3. `gpt-3.5-turbo`

All of these should be supported by both your API provider and LlamaIndex.

## Future Fix

If you really need to use `gpt-5-nano-2025-08-07`, we would need to:
1. Create a custom LLM wrapper that bypasses validation
2. Replace all OpenAI LLM instances with the custom wrapper
3. Test thoroughly

This is doable but adds complexity. The standard model name approach is much simpler and more maintainable.
