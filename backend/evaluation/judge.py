import json
import re
import ollama

JUDGE_MODEL = "gemma3:4b"

JUDGE_PROMPT_TEMPLATE = """You are an evaluation judge for a RAG system. You will be shown a question, the retrieved context, the expected answer, and a model's actual answer.

Question: {question}

Retrieved context:
{context}

Expected answer: {expected_answer}

Model's answer: {answer}

Classify the model's answer into EXACTLY ONE of these categories:

- "correct" = the answer matches the expected answer and every factual claim in it is directly supported by the retrieved context
- "correct_decline" = the model said it could not find the answer, AND the retrieved context genuinely does not contain enough information to answer the question
- "incomplete_decline" = the model said it could not find the answer, BUT the retrieved context actually does contain enough information to answer it
- "hallucinated" = the model made a specific factual claim (a number, name, date, or fact) that does NOT appear anywhere in the retrieved context

Important:
- Ignore generic conversational filler (e.g. "feel free to ask more questions") — only judge FACTUAL claims.
- For any specific number the model states, check character-by-character whether that exact number appears in the retrieved context. If it doesn't appear, that is a hallucination, even if the model's reasoning sounds confident and well-structured.

Respond with ONLY valid JSON in this exact format, nothing else:
{{"category": "<one of the four categories above>", "reasoning": "<one sentence, quote the specific number or claim you checked>"}}
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

    valid_categories = {"correct", "correct_decline", "incomplete_decline", "hallucinated"}

    try:
        parsed = json.loads(raw)
        category = parsed.get("category")
        if category not in valid_categories:
            return {
                "judge_category": None,
                "judge_reasoning": f"Invalid category returned: {category!r}",
                "judge_parse_error": True,
            }
        return {
            "judge_category": category,
            "judge_reasoning": parsed.get("reasoning", ""),
            "judge_parse_error": False,
        }
    except json.JSONDecodeError:
        return {
            "judge_category": None,
            "judge_reasoning": raw[:200],
            "judge_parse_error": True,
        }