import os
import fitz  # PyMuPDF
import tempfile
from openai import OpenAI, RateLimitError, APIError
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type((RateLimitError, APIError)))
def ask_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)

def extract_logo_image(pdf_path):
    doc = fitz.open(pdf_path)
    largest_image = None
    max_area = 0

    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            temp_path = os.path.join(tempfile.gettempdir(), f"logo_{xref}.{image_ext}")

            with open(temp_path, "wb") as f:
                f.write(image_bytes)

            width = base_image.get("width", 0)
            height = base_image.get("height", 0)
            area = width * height
            if area > max_area:
                max_area = area
                largest_image = temp_path

    return largest_image

def summarize_audit(text, filename):
    prompt = f"""
You are a senior auditor. Provide a short, structured summary (max 1 page) of the following audit report.

Format it with these sections:
1. Audit Topic
2. Main Findings (2–3 bullets)
3. Measures Proposed (2–3 bullets)
4. Future Steps (2–3 bullets)

Audit Text from file {filename}:
{text[:8000]}
"""
    return ask_openai(prompt)

def extract_theme_keywords(summary_text):
    prompt = f"""
Extract 4–6 key audit themes or topic keywords from the following summary. Return a comma-separated list only.

Text:
{summary_text}
"""
    keywords = ask_openai(prompt)
    return [kw.strip() for kw in keywords.split(",") if kw.strip()]

def compare_audits(summaries):
    prompt = "Compare the following audit summaries and outline key similarities and differences:\n\n" + "\n\n".join(summaries)
    return ask_openai(prompt)

def extract_learnings(summaries):
    prompt = "From these audit summaries, extract 3–5 practical audit insights or lessons for future audits:\n\n" + "\n\n".join(summaries)
    return ask_openai(prompt)

def analyze_audits(pdf_paths, filenames):
    summaries = []
    logos = []
    themes = []

    for path, name in zip(pdf_paths, filenames):
        text = extract_text(path)
        summary = summarize_audit(text, name)
        summaries.append(summary)

        logo_path = extract_logo_image(path)
        logos.append(logo_path)

        keywords = extract_theme_keywords(summary)
        themes.append(keywords)

    comparison = compare_audits(summaries)
    learnings = extract_learnings(summaries)

    return {
        "summaries": summaries,
        "logos": logos,
        "themes": themes,
        "comparison": comparison,
        "learnings": learnings
    }
