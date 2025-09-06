"""
Constants used across the investigator modules.
"""

# Expected number of base prompts in base_prompts.json
# This should be updated when base prompts are added or removed
EXPECTED_BASE_PROMPT_COUNT = 17

# Test tolerance for future-proofing
# Tests will accept counts >= EXPECTED_BASE_PROMPT_COUNT
# This allows for adding new prompts without breaking tests
BASE_PROMPT_COUNT_TOLERANCE = 5
