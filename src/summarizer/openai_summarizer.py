from openai import OpenAI
import streamlit as st

class OpenAISummarizer:
    def __init__(self):
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)

    def summarize(self, article_text):
        try:
            if not article_text or len(article_text.strip()) < 50:
                return "No hay suficiente texto en el artículo para generar un resumen."

            # Truncate to avoid token limits
            max_chars = 15000  # Adjust based on your API tier
            truncated_text = article_text[:max_chars] if len(article_text) > max_chars else article_text
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un periodista profesional especializado en minería."},
                    {"role": "user", "content": f"Tu tarea es resumir la siguiente nota a 4 o 5 líneas. Se objetivo y no omitas nada importante:\n\n{truncated_text}"}
                ]
            )
            
            summary = response.choices[0].message.content
            return summary.strip()
        except Exception as e:
            print(f"Error al summarizar: {e}")
            return f"No se pudo generar un resumen para este artículo. Error: {str(e)}"