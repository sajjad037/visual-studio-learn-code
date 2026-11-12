"""Build your own coding agent — one file, three tools, one approval gate.

The agent can read files and run the test suite on its own. It can NEVER
write a file until a human approves the exact change in the terminal.
Every tool is confined to the demo project folder, and the loop stops
after MAX_STEPS model turns no matter what.

Setup:
    pip install google-genai==3.0.0 pytest==9.2.0
    export GEMINI_API_KEY=...        # free key from Google AI Studio
    python agent.py
"""

import os
import subprocess
import sys
from pathlib import Path

from google import genai
from google.genai import types

PROJECT_DIR = Path(__file__).parent / "demo"
MODEL = "gemini-3.8-flash"
MAX_STEPS = 12
# Rate card for the cost printout (USD per 1M tokens) — re-verify at build.
PRICE_IN, PRICE_OUT = 0.75, 3.75

TASK = (
    "Run the test suite in this project. If a test fails, read the test and "
    "the code it tests, find the bug, and fix the source file so the whole "
    "suite passes. Do not edit the tests. When every test passes, stop and "
    "summarise what the bug was and what you changed."
)


def confine(path_text):
    """Resolve a model-supplied path and refuse anything outside the project."""
    path = (PROJECT_DIR / path_text).resolve()
    if not path.is_relative_to(PROJECT_DIR.resolve()):
        return None
    return path


def tool_read_file(path):
    target = confine(path)
    if target is None or not target.is_file():
        return {"error": f"cannot read {path}"}
    return {"content": target.read_text()[:8000]}


def tool_run_tests():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120,
    )
    return {"exit_code": proc.returncode, "output": (proc.stdout + proc.stderr)[-3000:]}


def tool_write_file(path, content):
    """THE GATE: the model only ever PROPOSES. A human decides."""
    target = confine(path)
    if target is None:
        return {"error": f"refused: {path} is outside the project folder"}
    print(f"\n--- The agent wants to write {path} ---")
    print(content)
    answer = input("Apply this change? [y/N] ").strip().lower()
    if answer != "y":
        print("--- Denied by the human. The file was NOT changed. ---")
        return {"result": "DENIED by the human approver. Do not retry this write; "
                          "explain in your summary what you wanted to change."}
    target.write_text(content)
    print("--- Approved and written. ---")
    return {"result": f"{path} written"}


TOOLS = {"read_file": tool_read_file, "run_tests": tool_run_tests,
         "write_file": tool_write_file}

DECLARATIONS = [
    types.FunctionDeclaration(
        name="read_file", description="Read a file inside the project folder.",
        parameters=types.Schema(type="OBJECT", properties={
            "path": types.Schema(type="STRING", description="File name, e.g. cart.py")},
            required=["path"])),
    types.FunctionDeclaration(
        name="run_tests", description="Run the project's pytest suite and return the result.",
        parameters=types.Schema(type="OBJECT", properties={})),
    types.FunctionDeclaration(
        name="write_file",
        description="Propose writing a whole file. A human must approve before anything is saved.",
        parameters=types.Schema(type="OBJECT", properties={
            "path": types.Schema(type="STRING"),
            "content": types.Schema(type="STRING", description="The full new file content")},
            required=["path", "content"])),
]


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("Set GEMINI_API_KEY first (free key from Google AI Studio).")
    client = genai.Client()
    config = types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=DECLARATIONS)])
    contents = [types.Content(role="user", parts=[types.Part(text=TASK)])]
    in_tokens = out_tokens = 0

    for step in range(1, MAX_STEPS + 1):
        response = client.models.generate_content(
            model=MODEL, contents=contents, config=config)
        if response.usage_metadata:
            in_tokens += response.usage_metadata.prompt_token_count or 0
            # The rate card bills thinking tokens as output — count them too,
            # or the cost printout understates the real bill.
            out_tokens += response.usage_metadata.candidates_token_count or 0
            out_tokens += response.usage_metadata.thoughts_token_count or 0
        model_content = response.candidates[0].content
        contents.append(model_content)

        calls = [p.function_call for p in model_content.parts if p.function_call]
        if not calls:  # the model answered in words — the task is done
            print("\nAGENT:", response.text)
            break
        replies = []
        for call in calls:
            print(f"[step {step}] tool: {call.name} {dict(call.args or {})}")
            result = TOOLS[call.name](**dict(call.args or {}))
            replies.append(types.Part.from_function_response(
                name=call.name, response=result))
        # Function responses go back with role "user" — the manual
        # function-calling pattern this API accepts (verified live
        # 2026-11-11: role "tool" is rejected with a 400 on this surface).
        contents.append(types.Content(role="user", parts=replies))
    else:
        print(f"\nStopped: step cap ({MAX_STEPS}) reached.")

    cost = in_tokens / 1e6 * PRICE_IN + out_tokens / 1e6 * PRICE_OUT
    print(f"\nTokens: {in_tokens} in / {out_tokens} out — this run cost about ${cost:.4f}")


if __name__ == "__main__":
    main()
