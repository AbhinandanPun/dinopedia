"""Prompt templates for Gemini content generation."""

def get_article_prompt(dinosaur):
    """Generate prompt for full dinosaur article."""
    return f"""
You are a paleontology educator writing for a general audience. Write about the following dinosaur:

**Dinosaur**: {dinosaur['common_name']} ({dinosaur['scientific_name']})
**Period**: {dinosaur['period']} ({dinosaur['period_years']})
**Diet**: {dinosaur['diet']}
**Habitat**: {dinosaur['habitat']}
**Length**: {dinosaur['length_m']}m
**Weight**: {dinosaur['weight_kg']}kg
**Key Facts**: {', '.join(dinosaur['key_facts'])}

Create a response in JSON format with these fields:
- "article": 800-1200 word educational article about this dinosaur
- "social_snippet": 180-200 character summary suitable for social media
- "hashtags": array of 5-7 relevant hashtags (e.g., ["#dinosaurs", "#paleontology"])

Ensure the article is factually accurate and engaging. Use the key facts provided above.

Format your response as valid JSON only (no markdown, no extra text).
"""

def get_short_prompt(dinosaur):
    """Generate prompt for social media snippet."""
    return f"""
Write a 1-2 sentence social media post about {dinosaur['common_name']}.
Make it engaging and include one interesting fact.
Keep it under 280 characters.
"""
