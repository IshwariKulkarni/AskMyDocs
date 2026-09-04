from judge import judge_answer

result = judge_answer(
    question="What was Apple's total revenue in Q3 fiscal 2025?",
    context="Apple today announced financial results... total revenue of $94.0 billion, up 10 percent year over year...",
    expected_answer="$94.0 billion (specifically $94,036 million)",
    answer="Apple's total revenue in Q3 fiscal 2025 was $94.0 billion.",
)
print(result)