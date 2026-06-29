QUIZ_PROMPT_TEMPLATE = """You are a professional examiner. Create a multiple-choice quiz on the topic "{topic}" with a difficulty level of "{difficulty}".
You must generate exactly {num_questions} questions.

You must respond ONLY with a raw JSON array matching the structure below.
Do not include any greeting, conversational text, or explanations outside the JSON array structure.

JSON Schema:
[
  {{
    "questionText": "What is the primary function of a database index?",
    "options": [
      "To compress files on disk",
      "To speed up data retrieval operations",
      "To enforce database security",
      "To store backup records"
    ],
    "correctAnswer": "To speed up data retrieval operations",
    "explanation": "An index is a data structure that improves the speed of data retrieval operations on a database table at the cost of additional writes and storage space."
  }}
]

Make sure:
1. The options list has between 2 and 6 entries.
2. The 'correctAnswer' matches one of the options EXACTLY.
3. The quiz has exactly {num_questions} questions.
4. If you include code blocks, escape quotes properly.

Return the JSON array:"""
