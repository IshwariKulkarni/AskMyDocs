import json
import re
import ollama

JUDGE_MODEL = "gemma3:4b"

JUDGE_PROMPT_TEMPLATE = """You are an evaluation judge. You will be shown a question, 
the context that was retrieved to answer it, the expected (ground truth) answer, and a 
model's actual answer. Score the model's answer.

Question: {question}

Retrieved context:
{context}

Expected answer: {expected_answer}

Model's answer: {answer}

Score the model's answer using this rubric:
- 2 = Correct and fully supported by the retrieved context
- 1 = Partially correct, or correct but missing key detail
- 0 = Incorrect, OR the answer states information not present in the retrieved context (hallucination)

Also determine: is this answer grounded in the retrieved context (true), or does it include claims 
not supported by the context (false)?

Respond with ONLY valid JSON in this exact format, nothing else:
{{"score": <0, 1, or 2>, "grounded": <true or false>, "reasoning": "<one sentence>"}}
"""


def judge_answer(question, context, expected_answer, answer):
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=question,
        context=context,
        expected_answer=expected_answer,
        answer=answer,
    )

    response = ollama.generate(
        model=JUDGE_MODEL,
        prompt=prompt,
        options={"temperature": 0},
    )

    raw = response["response"].strip()
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(raw)
        return {
            "judge_score": parsed.get("score"),
            "judge_grounded": parsed.get("grounded"),
            "judge_reasoning": parsed.get("reasoning", ""),
            "judge_parse_error": False,
        }
    except json.JSONDecodeError:
        return {
            "judge_score": None,
            "judge_grounded": None,
            "judge_reasoning": raw[:200],
            "judge_parse_error": True,
        }