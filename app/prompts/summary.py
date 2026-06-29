SUMMARY_PROMPT_TEMPLATE = """You are a senior academic researcher. Summarize the following educational text.
Format the summary according to the '{format}' style.

Follow these specific instructions for the format:
- Concise: Write a single, dense, high-impact paragraph capturing the main thesis and key findings.
- Detailed: Write a multi-paragraph, structured summary including major topics, supporting details, secondary arguments, and key terms.
- Bullet-point: Write a bulleted list of the most critical takeaways, key terms, and arguments.

Text to summarize:
{text}

Summary:"""
