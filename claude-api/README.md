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

# Tool use with Claude lessons
    uv run lessons/17_intro_tool_use.py            # Claude requests a tool
    uv run lessons/18_project_overview.py          # baseline: no tools
    uv run lessons/19_tool_functions.py            # offline, no API call
    uv run lessons/20_tool_schemas.py
    uv run lessons/21_message_blocks.py
    uv run lessons/22_tool_results.py
    uv run lessons/23_multi_turn_with_tools.py
    uv run lessons/24_multiple_turns.py            # loop until no tool_use
    uv run lessons/25_multiple_tools.py
    uv run lessons/26_fine_grained_tool_calling.py
    uv run lessons/27_text_edit_tool.py            # runs in a temp dir
    uv run lessons/28_web_search_tool.py

# RAG and agentic search lessons
    uv run lessons/29_intro_rag.py                 # whole doc vs retrieved chunk
    uv run lessons/30_text_chunking.py             # offline
    uv run lessons/31_text_embeddings.py           # offline (toy embeddings)
    uv run lessons/32_rag_flow.py                  # offline, prints the prompt
    uv run lessons/33_implementing_rag.py
    uv run lessons/34_bm25_lexical_search.py       # offline
    uv run lessons/35_multi_index_rag_pipeline.py  # vector + BM25 + RRF + rerank
