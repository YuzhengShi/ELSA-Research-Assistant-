import ollama
import json
import re
from config import LLM_MODEL, DOMAINS, DOMAIN_SECTIONS, ALL_MARKERS

# === Natural Language Intent Detection ===
REMEMBER_PATTERNS = [
    # Direct commands
    r"^remember\s+(?:that\s+)?(.+)",
    r"^add\s+(?:this|that|the\s+following)?[:\s]*(.+)",
    r"^save\s+(?:this|that)?[:\s]*(.+)",
    r"^note\s+(?:that|this|down)?[:\s]*(.+)",
    r"^record\s+(?:that|this)?[:\s]*(.+)",
    r"^store\s+(?:this|that)?[:\s]*(.+)",
    r"^put\s+(?:this|that)\s+(?:in|into|down)[:\s]*(.+)",
    r"^write\s+(?:this|that|down)?[:\s]*(.+)",
    r"^log\s+(?:this|that)?[:\s]*(.+)",
    r"^keep\s+(?:this|that|track)?[:\s]*(.+)",
    r"^insert\s+(?:this|that)?[:\s]*(.+)",
    
    # Conversational
    r"^(?:please\s+)?(?:can you\s+)?(?:add|save|remember|note|record|store|put|write|log|insert)\s+(?:this|that)?[:\s]*(.+)",
    r"^i\s+(?:want|need)\s+(?:to|you\s+to)\s+(?:add|save|remember|note|record)\s+(?:this|that)?[:\s]*(.+)",
    r"^(?:let's|let me)\s+(?:add|save|note|record)\s+(?:this|that)?[:\s]*(.+)",
    r"^don'?t\s+forget\s+(?:that\s+)?(.+)",
    r"^make\s+(?:a\s+)?note\s+(?:of\s+)?(?:that\s+)?(.+)",
    r"^jot\s+(?:this\s+)?down[:\s]*(.+)",
]

def extract_remember_content(message: str) -> str | None:
    """
    Check if message is a remember/add intent and extract the content.
    Returns the content to remember, or None if not a remember intent.
    """
    lower_msg = message.lower().strip()
    
    for pattern in REMEMBER_PATTERNS:
        match = re.match(pattern, lower_msg, re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            if content:
                # Return original case version
                # Find where the content starts in original message
                lower_content_start = lower_msg.find(content.lower())
                if lower_content_start != -1:
                    return message[lower_content_start:].strip()
                return content
    
    return None

def is_remember_intent(message: str) -> bool:
    """Quick check if message looks like a remember intent."""
    return extract_remember_content(message) is not None

SYSTEM_PROMPT = """You are a research assistant helping manage an academic document about the ELSA (Emotive-Limbic Symbolic Attunement) framework for internalizing psychopathology.

The document has 6 domains:
- D1: Somatic/Interoceptive Regulation
- D2: Affective/Emotion Regulation
- D3: Cognitive Regulation/Repetitive Thought
- D4: Meaning/Coherence/Identity Integration
- D5: Relational Attunement/Mentalization
- D6: Moral-Evaluative Integration

Each domain has sections: Definition, Mechanistic Explanation, Adaptive Functioning, Maladaptive Functioning, Clinical Relevance, Clinical Examples (Maladaptive/Adaptive), Cross-Domain Interactions, Summary Table, and References.

There's also an Introduction, Conclusion sections, and Table 7.

You help the user:
1. QUERY: Answer questions about the document content
2. REMEMBER: Identify which section new information belongs to
3. GAPS: Analyze what's missing in the document

Always be concise and precise. When classifying content to sections, explain your reasoning briefly."""

def chat(user_message: str, context: str = "", history: list = None) -> str:
    """Send a message to the LLM with optional context."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if history:
        messages.extend(history)
    
    if context:
        full_message = f"""Relevant document context:
---
{context}
---

User question: {user_message}"""
    else:
        full_message = user_message
    
    messages.append({"role": "user", "content": full_message})
    
    response = ollama.chat(model=LLM_MODEL, messages=messages)
    return response["message"]["content"]

def classify_section(content: str) -> dict:
    """Determine which section a piece of content belongs to.
    
    Returns:
        {
            "marker": "[D2:CLINICAL EXAMPLE: ADAPTIVE]",
            "domain": "D2",
            "section_type": "CLINICAL EXAMPLE: ADAPTIVE",
            "confidence": "high|medium|low",
            "reasoning": "..."
        }
    """
    prompt = f"""Classify this research note into the appropriate section of the ELSA document.

Content to classify:
"{content}"

Available markers:
{json.dumps(ALL_MARKERS, indent=2)}

Respond in JSON format:
{{
    "marker": "[exact marker from list]",
    "domain": "D1-D6 or null",
    "section_type": "section name",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation"
}}

Return ONLY valid JSON, no other text."""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a precise classifier. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        # Try to parse JSON from response
        text = response["message"]["content"]
        # Handle markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {
            "marker": None,
            "error": "Failed to parse classification",
            "raw_response": response["message"]["content"]
        }

def analyze_gaps(sections_summary: str) -> str:
    """Analyze document completeness and suggest what's missing."""
    prompt = f"""Analyze this ELSA document status and identify gaps:

{sections_summary}

For each empty or incomplete section, explain:
1. What content is expected there
2. Why it matters for the framework
3. Suggested priority (high/medium/low)

Be specific and actionable."""

    return chat(prompt)

def generate_summary(content: str, section_type: str) -> str:
    """Generate a concise summary of section content."""
    prompt = f"""Summarize this {section_type} section content concisely:

{content}

Provide a 2-3 sentence summary capturing the key points."""

    return chat(prompt)


# Test
if __name__ == "__main__":
    # Test classification
    test_content = "Patients with anxiety often show heightened interoceptive sensitivity, misinterpreting normal bodily sensations as threatening."
    
    result = classify_section(test_content)
    print("Classification result:")
    print(json.dumps(result, indent=2))
