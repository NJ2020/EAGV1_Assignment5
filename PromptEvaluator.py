import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")

# Configure the Gemini API with the loaded key
genai.configure(api_key=api_key)

def evaluate_promt(prompt: str) -> str:

    system_prompt = f"""You are a PROMPT Evaluation Assistant.
    You will receive a PROMPT written by a student. Your job is to review this PROMPT
    and assess how well it supports structured, step-by-step reasoning in an LLM (e.g.,
    for math, logic, planning, or tool use).

    Evaluate the prompt on the following criteria:
    1. Explicit Reasoning Instructions
    - Does the prompt tell the model to reason step-by-step?
    - Does it include instructions like “explain your thinking” or “think before you answer”?
    2. Structured Output Format
    - Does the prompt enforce a predictable output format (e.g., FUNCTION_CALL, JSON, numbered steps)?
    - Is the output easy to parse or validate?
    3. Separation of Reasoning and Tools
    - Are reasoning steps clearly separated from computation or tool-use steps?
    - Is it clear when to calculate, when to verify, when to reason?
    4. Conversation Loop Support
    - Could this prompt work in a back-and-forth (multi-turn) setting?
    - Is there a way to update the context with results from previous steps?
    5. Instructional Framing
    - Are there examples of desired behavior or “formats” to follow?
    - Does the prompt define exactly how responses should look?
    6. Internal Self-Checks
    - Does the prompt instruct the model to self-verify or sanity-check intermediate steps?
    7. Reasoning Type Awareness
    - Does the prompt encourage the model to tag or identify the type of reasoning used (e.g., arithmetic, logic, lookup)?
    8. Error Handling or Fallbacks
    - Does the prompt specify what to do if an answer is uncertain, a tool fails, or the model is unsure?
    9. Overall Clarity and Robustness
    - Is the prompt easy to follow?
    - Is it likely to reduce hallucination and drift?

    Respond with a structured review in this format:
    ```json
    {{
    "explicit_reasoning": true,
    "structured_output": true,
    "tool_separation": true,
    "conversation_loop": true,
    "instructional_framing": true,
    "internal_self_checks": false,
    "reasoning_type_awareness": false,
    "fallbacks": false,
    "overall_clarity": "A custom message e.g. Excellent structure, but could improve with self-checks and error fallbacks."
    }}


    Evaluate the below PROMPT.

    """

    final_prompt = system_prompt + "PROMPT: " + prompt

    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    response = model.generate_content(final_prompt)

    return response.text

if __name__ == "__main__":


    query = """
    You are an agent working with Microsoft Paint in iterations. You have access to various Microsoft Paint tools.
    Your task is to follow the step-by-step plan below to accomplish the goal. Think carefully before each step, explain your reasoning, identify the type of reasoning being used, and use tools as needed.

    Goal:
    Step 1: Open Microsoft Paint.  
    Step 2: Add text 'INDIA' in Opened Paint App.

    Available tools:
    {tools_description}

    You must follow this reasoning and response format for each step:
    1. Step Reasoning: [Brief explanation of why and what you're doing]
    2. Reasoning Type: [e.g., lookup, tool-use, spatial reasoning, sequencing]
    3. Tool Decision: [if using a tool, state which one and what parameters it needs]
    4. Self-Check: [verify input/output validity or sanity check]
    5. Response Line (MUST be ONE line, NO other text):
    FUNCTION_CALL: function_name|param1|param2|...
    FINAL_ANSWER: [string value returned by the function call]
    6. If uncertain or if a tool fails (Error Handling or Fallbacks), use:
    - FUNCTION_CALL: report_error|[describe issue briefly]

    Examples:
    - FUNCTION_CALL: draw_rectangle|10|50|10|50
    - FUNCTION_CALL: add_text_in_paint|INDIA
    - FINAL_ANSWER: open_paint function called successfully....1111
    - FUNCTION_CALL: report_error|Unable to locate rectangle area

    Important Instructions:
    - Proceed step-by-step, one action per turn.
    - Do not skip steps or assume outcomes.
    - Do not include any explanation outside of the prescribed format.
    - Responses outside the "Response Line" will be ignored.
    """

    print(evaluate_promt(query))

    