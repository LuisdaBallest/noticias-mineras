import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import re
import streamlit as st
from src.summarizer.openai_summarizer import OpenAISummarizer

def send_email_report(recipient_emails, articles, keywords_text):
    """
    Envía un informe por correo electrónico con los artículos encontrados
    """
    try:
        # Configuración del servidor de correo
        smtp_server = st.secrets.get("EMAIL_SERVER", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("EMAIL_PORT", 587))
        sender_email = st.secrets.get("EMAIL_SENDER")
        password = st.secrets.get("EMAIL_PASSWORD")
        
        if not sender_email or not password:
            return False, "Falta configuración de correo electrónico en los secretos de la aplicación."
            
        # Validar direcciones de correo
        valid_emails = []
        invalid_emails = []
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in recipient_emails:
            email = email.strip()
            if re.match(email_pattern, email):
                valid_emails.append(email)
            else:
                invalid_emails.append(email)
        
        if not valid_emails:
            return False, "No se proporcionaron direcciones de correo válidas."
            
        # Fecha actual para el asunto
        today_date = datetime.now().strftime("%d/%m/%Y")
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Informe de Noticias Mineras México - {today_date}'
        msg['From'] = sender_email
        msg['To'] = ", ".join(valid_emails)
        
        # Crear versión HTML del correo
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    background-color: #fc6603;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    border: 1px solid #eee;
                    border-radius: 5px;
                }}
                .content {{
                    padding: 20px;
                }}
                .article {{
                    margin-bottom: 30px;
                    border-left: 4px solid #C99D45;
                    padding-left: 15px;
                }}
                .article h3 {{
                    margin: 0 0 10px 0;
                    color: #303030;
                }}
                .article-link {{
                    color: #fc6603;
                    text-decoration: none;
                }}
                .article-link:hover {{
                    text-decoration: underline;
                }}
                .summary {{
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 10px;
                }}
                .footer {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                    border-radius: 0 0 5px 5px;
                }}
                .keywords {{
                    background-color: #f5f5f5;
                    padding: 10px 15px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                    font-style: italic;
                    color: #666;
                }}
                .highlighted {{
                    color: #C99D45;
                    font-weight: bold;
                }}
                .article-image {{
                    width: 100%;
                    max-height: 250px;
                    object-fit: cover;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .image-container {{
                    width: 100%;
                    height: auto;
                    max-height: 250px;
                    overflow: hidden;
                    border-radius: 5px;
                    margin: 10px 0;
                    text-align: center;
                    background-color: #f8f8f8;
                    position: relative;
                }}
                .no-image {{
                    padding: 15px;
                    background-color: #f8f8f8;
                    text-align: center;
                    color: #999;
                    font-style: italic;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Noticias Mineras México</h1>
                    <p>Informe generado el {today_date}</p>
                </div>
                <div class="content">
                    <p>A continuación se presenta un resumen de las últimas noticias relevantes para el sector minero en México: </p>
                    
                    <h2>Artículos ({len(articles)})</h2>
                    <p> Solo se mostrarán los primeros 20</p
        """
        
        # Crear el objeto summarizer
        summarizer = OpenAISummarizer()
        
        # Añadir artículos (máximo 10 para no hacer el correo demasiado grande)
        for i, article in enumerate(articles[:20]):
            try:
                summary = summarizer.summarize(article['text'])
                
                # Iniciar el HTML del artículo
                article_html = f"""
                <div class="article">
                    <h3>{i+1}. {article['title']}</h3>
                """
                
                # Añadir imagen si está disponible
                if article.get('image') and article['image'].get('url'):
                    img_url = article['image']['url']
                    img_alt = article['image'].get('alt', article['title'])
                    
                    # Verificar que la URL de la imagen sea válida
                    if img_url and img_url.strip():
                        article_html += f"""
                        <div class="image-container">
                            <img src="{img_url}" alt="{img_alt}" class="article-image">
                        </div>
                        """
                
                fecha_display = article.get('formatted_date', article.get('date', ''))
                if fecha_display:
                    article_html += f"""
                    <h3>{i+1}. {article['title']}</h3>
                    <p style="margin-top: -5px; font-size: 0.85em; color: #666;">
                        <em>Publicado: {fecha_display}</em>
                    </p>
                    """
                else:
                    article_html += f"""
                    <h3>{i+1}. {article['title']}</h3>
                    """
                
                # Añadir enlace y resumen
                article_html += f"""
                    <p><a href="{article['link']}" class="article-link">Ver artículo original</a></p>
                    <div class="summary">
                        <p><span class="highlighted">Resumen:</span> {summary}</p>
                    </div>
                </div>
                """
                
                # Añadir el artículo al contenido HTML
                html_content += article_html
                
            except Exception as e:
                print(f"Error al procesar artículo para correo: {str(e)}")
                # Añadir el artículo sin resumen
                html_content += f"""
                <div class="article">
                    <h3>{i+1}. {article['title']}</h3>
                """
                
                # Añadir imagen si está disponible (incluso para artículos con error)
                if article.get('image') and article['image'].get('url'):
                    img_url = article['image']['url']
                    img_alt = article['image'].get('alt', article['title'])
                    
                    # Verificar que la URL de la imagen sea válida
                    if img_url and img_url.strip():
                        html_content += f"""
                        <div class="image-container">
                            <img src="{img_url}" alt="{img_alt}" class="article-image">
                        </div>
                        """
                
                # Completar el HTML del artículo
                html_content += f"""
                    <p><a href="{article['link']}" class="article-link">Ver artículo original</a></p>
                    <div class="summary">
                        <p><span class="highlighted">Nota:</span> No se pudo generar un resumen para este artículo.</p>
                    </div>
                </div>
                """
        
        # Añadir pie de correo
        html_content += """
                    <p>Para ver más detalles y acceder a todos los artículos, visite la plataforma completa.</p>
                </div>
                <div class="footer">
                    <p>Este es un correo automatizado. Por favor, no responda a este mensaje.</p>
                    <p>© 2025 Monitor de Noticias Mineras México</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Adjuntar contenido HTML al mensaje
        msg.attach(MIMEText(html_content, 'html'))
        
        # Conectar al servidor SMTP y enviar el correo
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Establecer conexión segura
            server.login(sender_email, password)
            server.send_message(msg)
        
        # Mensaje de éxito
        success_message = f"Informe enviado correctamente a {len(valid_emails)} destinatarios."
        if invalid_emails:
            success_message += f" Se omitieron {len(invalid_emails)} direcciones inválidas: {', '.join(invalid_emails)}"
            
        return True, success_message
        
    except Exception as e:
        return False, f"Error al enviar correo: {str(e)}"