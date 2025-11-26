import os
from docx import Document
from pypdf import PdfReader
from huggingface_hub import InferenceClient

API_TOKEN ="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"
client = InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", api_key=API_TOKEN )


def load_file(path):
    if path.endswith(".txt"):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            raise ValueError("Can't read file")
    elif path.endswith(".pdf"):
        try:
            reader = PdfReader(path)
            return "\n".join(page.extract_text() for page in reader.pages)
        except:
            raise ValueError("Can't read file")
    elif path.endswith(".docx"):
        try:
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        except:
            raise ValueError("Can't read file")        
    else:
        raise ValueError("Unsupported file type")




def compare_cv_to_job(cv_file,job=None):
    try:
        cv_text =load_file(cv_file)
        job_text =job if job else " There is no job description"
        prompt = f"""
                        Compare the CV and Job Description.

                        Return:
                        - match_score (0-100)
                        - strengths
                        - missing_skills
                        - recommendation

                        CV:
                        {cv_text[:3000]}

                        Job Description:
                        {job_text}
                """

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content
    except:
         raise ValueError(f"Error during comparison")