RECOMMEND_PROMPT_TEMPLATE = """You are a highly experienced academic advisor and technical mentor. 
Generate a personalized study roadmap, resource list, and practice guide for a student learning "{topic}".

Student Profile:
- Current Skill Level: {skill_level}
- Personal Goals: {goals}

You must respond ONLY with a raw JSON object matching the schema below. 
Do not include any conversational intro, outro, or markdown code fence blocks if possible. If you use markdown, format it as ```json ... ```.

JSON Schema:
{{
  "roadmap": [
    {{
      "phase": "Phase 1: Foundations",
      "title": "Introduction to Core Concepts",
      "description": "Understand variables, basic data types, and syntax rules.",
      "duration": "1 week (5 hours)"
    }}
  ],
  "resources": [
    {{
      "name": "Python Crash Course Book by Eric Matthes",
      "type": "Book",
      "description": "An excellent hands-on project-based introduction to Python."
    }}
  ],
  "practice_suggestions": [
    "Build a CLI calculator that handles addition, subtraction, multiplication, and division.",
    "Write a script that processes a CSV file of student grades and calculates averages."
  ]
}}

Make sure the roadmap contains at least 3 distinct phases, the resources contain at least 3 recommendations (with varied types like Book, Video, Course, or Article), and there are at least 3 actionable practice suggestions.

Return the JSON object:"""
