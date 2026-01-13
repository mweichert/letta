# Better Proxy Support

## Issue Summary

When using Letta with custom OpenAI-compatible proxies, the provider name is hardcoded to include "openai-proxy" which may not be desired for all proxy configurations.

## Root Cause

In `letta/schemas/providers/openai.py`, the code hardcodes the provider name construction when a custom `base_url` is provided.

## The Fix

Removed the hardcoded "openai-proxy" naming logic, allowing custom base URLs to work without forcing a specific naming convention.

## Files Modified

- `letta/schemas/providers/openai.py`

## Related

- This fix enables cleaner integration with custom LLM proxies (e.g., cli-proxy-api, LiteLLM, etc.)
