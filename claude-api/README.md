# claude-api

Examples for "Accessing Claude with the API" (Building with the Claude API course).
Each lesson is a standalone script; code is intentionally duplicated.

    uv sync
    cp .env.sample .env   # then set ANTHROPIC_API_KEY
    uv run lessons/03_making_a_request.py

# Prompt evaluation lessons (run in order)
    uv run lessons/09_eval_dataset.py    # writes lessons/dataset.json
    uv run lessons/10_eval_runner.py
    uv run lessons/11_eval_grading.py

# Prompt engineering techniques lessons
    uv run lessons/12_prompt_engineering.py   # iterate on a prompt
    uv run lessons/13_clear_and_direct.py
    uv run lessons/14_being_specific.py       # guidelines and steps
    uv run lessons/15_xml_tags.py
    uv run lessons/16_providing_examples.py   # multi-shot
