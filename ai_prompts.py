"""
Pollivu - AI Prompt Templates
Structured prompts for poll generation, option suggestions, and
poll improvement across all AI providers (Gemini, OpenAI, Claude, Ollama).
"""

from typing import List


def get_generation_prompt(topic: str, num_options: int, style: str) -> str:
    """Get the prompt for poll generation."""
    style_instructions = {
        'neutral': 'Keep the tone neutral and balanced.',
        'fun': 'Make it fun, casual, and engaging with emojis.',
        'professional': 'Use professional, formal language.',
        'educational': 'Make it educational and informative.'
    }
    
    return f"""Generate a poll based on this topic: "{topic}"

Requirements:
- Create exactly {num_options} answer options
- {style_instructions.get(style, style_instructions['neutral'])}
- Make the question clear and engaging
- Options should be distinct and cover different perspectives
- Keep options concise (under 100 characters each)

Return ONLY a JSON object in this exact format:
{{
    "question": "Your poll question here?",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"]
}}

Do not include any other text, only the JSON object."""


def get_new_options_prompt(question: str, existing_options: List[str], num_options: int = 4) -> str:
    """Get the prompt for suggesting new poll options that don't already exist."""
    existing_text = "\n".join(f"- {opt}" for opt in existing_options)
    
    return f"""Given this poll question: "{question}"

These options already exist:
{existing_text}

Suggest {num_options} NEW and DIFFERENT options that are NOT already in the list above.
- Make them relevant to the question
- Make them distinct from each other and from existing options
- Keep each option concise (under 100 characters)

Return ONLY a JSON object in this exact format:
{{
    "options": ["New Option 1", "New Option 2", "New Option 3", "New Option 4"]
}}

Do not include any other text, only the JSON object."""


def get_suggestion_prompt(question: str, options: List[str]) -> str:
    """Get the prompt for poll suggestions."""
    options_text = "\n".join(f"- {opt}" for opt in options)
    
    return f"""Analyze this poll and suggest improvements:

Question: {question}

Options:
{options_text}

Provide suggestions to make this poll better. Consider:
1. Is the question clear and unbiased?
2. Are the options balanced and distinct?
3. Are there any missing common options?
4. Any wording improvements?

Return ONLY a JSON object in this exact format:
{{
    "improved_question": "Improved question here",
    "improved_options": ["Option 1", "Option 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...]
}}

Do not include any other text, only the JSON object."""
