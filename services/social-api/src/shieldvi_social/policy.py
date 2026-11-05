"""Active shadow policy shared by the worker and offline evaluation.

Scores and lexical/repeated candidates request review, never HIGH or auto-hold.
"""


def policy_outcome(response):
    review = (response.toxicity_score >= .41 or response.ai_label == "TOXIC" or
        response.lexical_review_recommended or response.directed_insult_candidate or
        response.suspected_repeated_harassment or response.suggested_action == "needs_review" or
        any(signal.category in {"profanity", "directed_insult"} for signal in response.lexical_signals))
    return ("REVIEW", "PUBLISHED_FLAGGED", "QUEUED") if review else ("LOW", "PUBLISHED", "NOT_REQUIRED")
