"""Build Your First AI Agent in Python (Tool-Calling, Step by Step).

Companion code for the Visual Studio Learn post and video:
- Post:  https://visualstudiolearn.blogspot.com/2026/10/build-your-first-ai-agent-in-python.html
- Video: https://www.youtube.com/watch?v=r0nY3zq9YfE

A small command-line agent with two tools (weather lookup + a safe
calculator) and a manual agent loop. No framework, no LangChain.

Requires: Python 3.12, google-genai 1.35.0, and a Gemini API key in the
GEMINI_API_KEY environment variable. See README.md in this folder.
"""

import ast
import json
import operator
import urllib.parse
import urllib.request


def get_weather(city: str) -> dict:
    """Get the current weather for a city.

    Args:
        city: City name, for example "Ottawa" or "Toronto".
    Returns:
        Temperature in Celsius, wind speed, and a condition code.
    """
    query = urllib.parse.quote(city)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1"
    with urllib.request.urlopen(geo_url, timeout=10) as response:
        places = json.load(response).get("results")
    if not places:
        return {"error": f"No location found for {city}"}

    place = places[0]
    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={place['latitude']}&longitude={place['longitude']}"
        "&current=temperature_2m,wind_speed_10m,weather_code"
    )
    with urllib.request.urlopen(weather_url, timeout=10) as response:
        current = json.load(response)["current"]
    return {
        "city": place["name"],
        "temperature_c": current["temperature_2m"],
        "wind_kmh": current["wind_speed_10m"],
        "weather_code": current["weather_code"],
    }


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Expression contains something the calculator does not allow")


def calculate(expression: str) -> dict:
    """Calculate a basic arithmetic expression.

    Args:
        expression: Arithmetic only, for example "18.5 - 16.0" or "(4 + 6) * 2".
    Returns:
        The numeric result, or an error message if the expression is not allowed.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        return {"expression": expression, "result": _eval_node(tree.body)}
    except Exception as exc:
        return {"error": f"Could not calculate '{expression}': {exc}"}


import os

from google import genai
from google.genai import types

TOOLS = {"get_weather": get_weather, "calculate": calculate}
MAX_STEPS = 6


def run_agent(question: str) -> str:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    config = types.GenerateContentConfig(
        tools=list(TOOLS.values()),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        system_instruction=(
            "Use the tools when you need live weather or arithmetic. "
            "Do not guess temperatures or do maths in your head."
        ),
    )
    contents = [question]

    for step in range(1, MAX_STEPS + 1):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )
        if not response.function_calls:
            return response.text

        contents.append(response.candidates[0].content)
        for call in response.function_calls:
            tool = TOOLS.get(call.name)
            if tool is None:
                result = {"error": f"Unknown tool: {call.name}"}
            else:
                result = tool(**call.args)
            print(f"  step {step}: {call.name}({call.args}) -> {result}")
            contents.append(
                types.Part.from_function_response(name=call.name, response=result)
            )

    return "Stopped: the agent used all of its steps without finishing."


if __name__ == "__main__":
    answer = run_agent(
        "Is it warmer in Ottawa or Toronto right now, "
        "and what is the temperature difference times two?"
    )
    print("\nAnswer:", answer)
