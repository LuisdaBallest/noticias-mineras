import streamlit as st
import streamlit as st
from src.scrapers.website_one_scraper import WebsiteOneScraper
from src.scrapers.website_two_scraper import WebsiteTwoScraper
from src.scrapers.website_three_scraper import WebsiteThreeScraper
from src.scrapers.website_four_scraper import WebsiteFourScraper
from src.summarizer.openai_summarizer import OpenAISummarizer
import concurrent.futures
from src.utils.email_service import send_email_report

st.set_page_config(
    page_title="Noticias Mineras México",
    page_icon="📰",
    layout="centered",
    initial_sidebar_state="collapsed",
)



# Colores
PRIMARY = "#fc6603"    # Naranja
SECONDARY = "#C99D45"    # Oro
DARK = "#303030"         # Casi negro
MEDIUM = "#6C757D"       # Gris
LIGHT = "#F5F5F5"        # Gris claro
ACCENT = "#BF7930"       # Cobre

# Define default keywords - hardcoded for consistency
DEFAULT_KEYWORDS = "oro, cobre, plata, zinc, litio, abrir, acero, aluminio, cemento, cementera, cantera, canteras, apertura, inaugurar, inauguración, inauguran, inaugura, inauguro, cerrar, cierre, cierran, clausurar, clausura, clausuran, clausuro, clausurado, clausurada, quiebra, bancarrota, crecimiento, incremento, crece, incrementa, disminuye, reduce, reducen, disminución, reducción, Sandvik, sandvik, CAT, Caterpillar, komatsu, expandir, expansión, expande, expanden, expandirse, comienza, comenzar, inicia, inician, Minera México, Peñoles, Coeur, First Majestic, Fresnillo, Newmont, Goldcorp, Pan American, Panamericana, Argonaut, Frisco, Endeavour, colorada, chispas, filos, gatos, san julian, palmarejo, parral, santa elena, tayoltita, saucito, san dimas, san francisco, san josé, san luis, san martin, san nicolas, san patricio, san rafael, san vicente, santa cruz, santa maria, santa rosa, santa rita, media luna, Torex, Pinnacle, Silver Wolf, copalquin, Bear Creek, mercedes, cananea, aumenta, aumentar, aumentará, aumentan, aumentó, durango, nuevo"

# Define keyword tags to display (can be the same as DEFAULT_KEYWORDS but split into a list)
KEYWORD_TAGS = ["minería", "oro", "plata", "cobre", "proyecto", "exploración", "inversión"]

# Custom CSS to style the application with professional colors
st.markdown("""
<style>
    /* General page setup */
    .reportview-container {
        background-color: """+LIGHT+""";
    }
    
    /* Main title styling */
    .main-title {
        color: white;
        background: linear-gradient(140deg, """+PRIMARY+""" 0%, """+DARK+""" 130%);
        padding: 1.5rem;
        border-radius: 4px;
        font-size: 2rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Subtitle styling */
    .subtitle {
        color: """+PRIMARY+""";
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        border-bottom: 2px solid """+SECONDARY+""";
        padding-bottom: 0.5rem;
    }
    
    /* Card styling for articles */
    .article-card {
        border-left: 5px solid """+SECONDARY+""";
        background-color: white;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Source link styling */
    .source-link {
        color: """+PRIMARY+""" !important;
        font-weight: 600;
        text-decoration: none;
        transition: color 0.2s;
    }
    
    .source-link:hover {
        color: """+SECONDARY+""" !important;
        text-decoration: underline;
    }
    
    /* Summary section styling */
    .summary-section {
        background-color: """+LIGHT+""";
        padding: 1rem;
        border-radius: 4px;
        margin: 0.8rem 0;
        border: 1px solid #eaeaea;
    }
    
    /* Buttons styling */
    .stButton>button {
        background: linear-gradient(140deg, """+PRIMARY+""" 0%, """+DARK+""" 130%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 4px;
        transition: opacity 0.2s;
    }
    
    .stButton>button:hover {
        opacity: 0.9;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: """+MEDIUM+""";
        color: white !important;
        font-weight: 600;
        border-radius: 4px;
        padding: 0.7rem !important;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #eaeaea;
        color: """+MEDIUM+""";
        font-size: 0.8rem;
    }
    
    /* Custom info box */
    .info-box {
        background-color: """+LIGHT+""";
        padding: 0.8rem;
        border-radius: 4px;
        margin: 0.8rem 0;
        border-left: 4px solid """+PRIMARY+""";
    }
    
    /* Warning box */
    .warning-box {
        background-color: #FFF8E1;
        color: #856404;
        padding: 0.8rem;
        border-radius: 4px;
        margin: 0.8rem 0;
        border-left: 4px solid #FFD54F;
    }
    
    /* Success box */
    .success-box {
        background-color: #E8F5E9;
        color: #1B5E20;
        padding: 0.8rem;
        border-radius: 4px;
        margin: 0.8rem 0;
        border-left: 4px solid #4CAF50;
    }
    
    /* Label styles */
    .label {
        font-weight: 600;
        color: """+DARK+""";
    }
    
    /* Highlight text */
    .highlight {
        color: """+SECONDARY+""";
        font-weight: 600;
    }
    
    /* Section dividers */
    .divider {
        margin: 1.5rem 0;
        border-top: 1px solid #eaeaea;
    }
    
    /* Keyword tags */
    .keyword-tag {
        display: inline-block;
        background-color: """+PRIMARY+""";
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 1rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
    }
    
    /* Image container - tamaño fijo y uniforme */
    .image-container {
        width: 100%;
        height: 180px; /* Altura fija para todas las imágenes */
        overflow: hidden; 
        margin-bottom: 1rem; 
        text-align: center; 
        background-color: #f8f8f8; 
        border-radius: 4px;
        position: relative; /* Para posicionamiento interno */
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Estilo para la imagen dentro del contenedor */
    .image-container img {
        width: 100%;
        height: 100%;
        object-fit: cover; /* Mantiene la proporción y cubre el contenedor */
        object-position: center; /* Centra la imagen */
    }
    
    /* Image fallback message */
    .image-fallback {
        padding: 1rem; 
        background-color: #f8f8f8; 
        text-align: center; 
        border-radius: 4px; 
        margin-bottom: 1rem;
        color: """+MEDIUM+""";
        font-style: italic;
    }
    /* Estilo específico para el botón de reset */
    button[data-testid="baseButton-secondary"] {
        background-color: """+LIGHT+""" !important;
        background-image: none !important;
        color: """+MEDIUM+""" !important;
        border: 1px solid #ddd !important;
        padding: 0.4rem 0.8rem !important;
        font-size: 0.8rem !important;
        border-radius: 4px !important;
        transition: all 0.2s;
        margin-top: 1.5rem;
        font-weight: normal !important;
    }

    button[data-testid="baseButton-secondary"]:hover {
        background-color: #eeeeee !important;
        border-color: """+MEDIUM+""" !important;
    }

    /* Container for keywords text area and reset button */
    .keywords-container {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Función para restaurar los keywords predeterminados
def reset_keywords():
    st.session_state.keywords = DEFAULT_KEYWORDS

# Función para eliminar artículos duplicados
def deduplicate_articles(articles_list):
    """
    Elimina artículos duplicados basados en el título
    Preserva el primer artículo encontrado con cada título
    """
    unique_articles = []
    seen_titles = set()
    
    # Itera por la lista de artículos
    for article in articles_list:
        # Normaliza el título (minúsculas, sin espacios extra)
        title = article['title'].lower().strip()
        
        # Si este título no ha sido visto antes, agrégalo
        if title not in seen_titles:
            seen_titles.add(title)
            unique_articles.append(article)
            
    # Reporta cuántos duplicados se eliminaron
    duplicates_removed = len(articles_list) - len(unique_articles)
    if duplicates_removed > 0:
        print(f"Se eliminaron {duplicates_removed} artículos duplicados")
        
    return unique_articles

def main():
    # Variables de estado para mantener la aplicación entre recargas
    if 'articles' not in st.session_state:
        st.session_state.articles = []  # Para guardar los artículos
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False  # Para saber si se realizó una búsqueda
    if 'email_status' not in st.session_state:
        st.session_state.email_status = None  # Para mostrar estado del envío de correo
    if 'summarizer' not in st.session_state:
        st.session_state.summarizer = OpenAISummarizer()  # Inicializar el summarizer una sola vez

    # Custom title with HTML
    st.markdown('<div class="main-title">Noticias Mineras México</div>', unsafe_allow_html=True)
    
    # Add a small description
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem; color: """+MEDIUM+""";">
        Plataforma de monitoreo de noticias para la industria minera mexicana con resúmenes generados por inteligencia artificial.
    </div>
    """, unsafe_allow_html=True)
    
    # Create a section for keywords
    st.markdown('<div class="subtitle">Filtrar por Palabras Clave</div>', unsafe_allow_html=True)
    
    # Explain how to use keywords
    st.markdown("""
    <div style="margin-bottom: 0.8rem; color: """+MEDIUM+""";">
        Ingrese términos relacionados con la minería separados por comas para encontrar artículos relevantes.
    
    """, unsafe_allow_html=True)
    
    # Show keyword examples as tags
    keyword_tags_html = ""
    for tag in KEYWORD_TAGS:
        keyword_tags_html += f'<span class="keyword-tag">{tag}</span>\n'
    
    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        {keyword_tags_html}
    </div>
    """, unsafe_allow_html=True)
    
    # Keyword input with session state
    if 'keywords' not in st.session_state:
        st.session_state.keywords = DEFAULT_KEYWORDS

    # Create two columns for the text area and reset button
    kw_col1, kw_col2 = st.columns([5, 1])

    # Text area in the first column
    with kw_col1:
        keywords = st.text_area("", value=st.session_state.keywords, height=80,
                            placeholder="Ejemplo: minería, oro, plata, cobre, proyecto")
        
        # Update session state if user changes the input
        if keywords != st.session_state.keywords:
            st.session_state.keywords = keywords

    # Reset button in the second column
    with kw_col2:
        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        reset_button = st.button("⭮ Restaurar", help="Restaurar palabras clave predeterminadas", on_click=reset_keywords)
    
    # Add a divider
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Search button
    search_button = st.button("🔍 Buscar Noticias")
    
    # PROCESO DE BÚSQUEDA
    if search_button:
        if keywords:
            with st.spinner("⏳ Buscando y analizando noticias de la industria minera..."):
                # Progress information
                st.markdown('<div class="info-box">⚙️ Inicializando sistema de búsqueda...</div>', unsafe_allow_html=True)
                
                # Initialize scrapers
                website_one_scraper = WebsiteOneScraper(keywords)
                website_two_scraper = WebsiteTwoScraper(keywords)
                website_three_scraper = WebsiteThreeScraper(keywords)
                website_four_scraper = WebsiteFourScraper(keywords)
                
                # Status container
                status_container = st.empty()
                status_container.markdown('<div class="info-box">⏳ Extrayendo datos de fuentes públicas...</div>', unsafe_allow_html=True)
                
                # Execute scrapers concurrently
                scrapers = [website_one_scraper, website_two_scraper, website_three_scraper, website_four_scraper]
                scraper_names = ["Minería en Línea", "Mundo Minero", "Cluster Minero", "Rumbo Minero"]
                
                # Dictionary to store results
                articles_dict = {}
                
                # Execute scraping concurrently
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit all scraping tasks
                    future_to_scraper = {
                        executor.submit(scraper.scrape): (scraper, name) 
                        for scraper, name in zip(scrapers, scraper_names)
                    }
                    
                    # Process results as they complete
                    for future in concurrent.futures.as_completed(future_to_scraper):
                        scraper, name = future_to_scraper[future]
                        try:
                            articles = future.result()
                            articles_dict[name] = articles
                            status_container.markdown(
                                f'<div class="info-box">✅ {name}: {len(articles)} artículos encontrados</div>', 
                                unsafe_allow_html=True
                            )
                        except Exception as exc:
                            print(f"{name} generó una excepción: {exc}")
                            articles_dict[name] = []
                            status_container.markdown(
                                f'<div class="warning-box">⚠️ Error al procesar {name}: {exc}</div>', 
                                unsafe_allow_html=True
                            )
                
                # Combine all articles
                all_articles = []
                for name, articles in articles_dict.items():
                    all_articles.extend(articles)
                    
                # Remove status container
                status_container.empty()

                # Deduplicate articles
                articles = deduplicate_articles(all_articles)
                
                # Guardar en session_state
                st.session_state.articles = articles
                st.session_state.search_performed = True
                
                # Display articles count
                if len(articles) > 0:
                    st.markdown(f'<div class="success-box">📊 Se encontraron {len(articles)} artículos relacionados con sus términos de búsqueda.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="warning-box">📊 No se encontraron artículos que coincidan con los términos especificados.</div>', unsafe_allow_html=True)
                
                # Si no hay artículos, mostrar recomendaciones
                if not articles:
                    st.markdown("""
                    <div class="info-box">
                        <div class="label">Recomendaciones para mejorar su búsqueda:</div>
                        <ul>
                            <li>Utilice términos más generales del sector minero</li>
                            <li>Reduzca el número de palabras clave (pruebe con 1 o 2)</li>
                            <li>Verifique que las palabras estén escritas correctamente</li>
                            <li>Pruebe con términos como: minería, exploración, proyecto, inversión</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">⚠️ Por favor ingresa al menos una palabra clave para iniciar la búsqueda.</div>', unsafe_allow_html=True)

    # MOSTRAR ARTÍCULOS (ya sea después de buscar o si ya tenemos artículos en session_state)
    if st.session_state.search_performed and st.session_state.articles:
        # Recuperar artículos de session_state
        articles = st.session_state.articles
        summarizer = st.session_state.summarizer
        
        # Add a divider before articles
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Artículos Encontrados</div>', unsafe_allow_html=True)
        
        # Display total articles count
        st.markdown(f"""
        <div style="margin-bottom: 1rem; text-align: right; color: {MEDIUM};">
            Mostrando {len(articles)} artículos | Ordenados por relevancia
        </div>
        """, unsafe_allow_html=True)
        
        # Display summaries
        for i, article in enumerate(articles):
            with st.expander(f"{i+1}. {article['title']}"):
                # Display article metadata
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.8rem; color: {MEDIUM};">
                    <div>Artículo #{i+1}</div>
                    <div>Fuente: {article['link'].split('/')[2]}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display image if available
                if article.get('image') and article['image'].get('url'):
                    try:
                        if article['image']['url'] and article['image']['url'].strip():
                            img_url = article['image']['url']
                            img_alt = article['image'].get('alt', article['title'])
                            
                            st.markdown(f'''
                            <div class="image-container">
                                <img src="{img_url}" alt="{img_alt}" />
                            </div>
                            ''', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown('<div class="image-fallback">No se pudo cargar la imagen del artículo.</div>', unsafe_allow_html=True)
                        print(f"Error cargando imagen: {str(e)}")
                
                # Source link with custom styling
                st.markdown(f"""
                <div style="margin: 0.8rem 0;">
                    <span class="label">Enlace original:</span> 
                    <a href="{article['link']}" target="_blank" class="source-link">{article['link']}</a>
                </div>
                """, unsafe_allow_html=True)
                
                # Add a separator line
                st.markdown('<hr style="margin: 1rem 0; border-color: #eaeaea;">', unsafe_allow_html=True)
                
                # Generate summary with spinner
                with st.spinner("Analizando contenido con IA..."):
                    summary = summarizer.summarize(article['text'])
                
                # Display summary with custom styling
                st.markdown(f"""
                <div style="margin: 0.8rem 0;">
                    <div class="label" style="color: {PRIMARY}; display: flex; align-items: center;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-text" viewBox="0 0 16 16" style="margin-right: 0.5rem;">
                            <path d="M5 4a.5.5 0 0 0 0 1h6a.5.5 0 0 0 0-1zm-.5 2.5A.5.5 0 0 1 5 6h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5M5 8a.5.5 0 0 0 0 1h6a.5.5 0 0 0 0-1zm0 2a.5.5 0 0 0 0 1h3a.5.5 0 0 0 0-1z"/>
                            <path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2zm10-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1"/>
                        </svg>
                        RESUMEN EJECUTIVO
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f'<div class="summary-section">{summary}</div>', unsafe_allow_html=True)

        # SECCIÓN DE ENVÍO DE CORREO
        # Add a divider before email section
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Enviar Informe por Correo</div>', unsafe_allow_html=True)

        # Email distribution section
        st.markdown("""
        <div style="margin-bottom: 1rem; color: """+MEDIUM+""";">
            Envíe un informe con estos artículos a uno o varios destinatarios.
            Ingrese las direcciones de correo electrónico separadas por comas.
        </div>
        """, unsafe_allow_html=True)

        # Feedback container para mensajes
        email_status_container = st.empty()
        
        # Mostrar mensaje anterior si existe
        if st.session_state.email_status:
            success, message = st.session_state.email_status
            if success:
                email_status_container.markdown(f'<div class="success-box">✅ {message}</div>', unsafe_allow_html=True)
            else:
                email_status_container.markdown(f'<div class="warning-box">⚠️ {message}</div>', unsafe_allow_html=True)

        # Email input - usar key para evitar conflictos
        email_recipients = st.text_area("Destinatarios", 
                                key="email_recipients_input",
                                placeholder="ejemplo@empresa.com, gerente@minera.mx", 
                                help="Ingrese una o varias direcciones de correo separadas por comas")

        # Columnas para el botón
        send_col1, send_col2 = st.columns([3, 1])
        with send_col2:
            # Send button con key única
            send_email_button = st.button("📧 Enviar Informe", key="send_email_button")

        if send_email_button:
            if not email_recipients:
                st.session_state.email_status = (False, "Por favor, ingrese al menos una dirección de correo electrónico.")
                email_status_container.markdown('<div class="warning-box">⚠️ Por favor, ingrese al menos una dirección de correo electrónico.</div>', unsafe_allow_html=True)
            else:
                # Parse email addresses
                email_list = [email.strip() for email in email_recipients.split(",")]
                
                # Send email with progress indicator
                with st.spinner("Enviando informe por correo electrónico..."):
                    try:
                        success, message = send_email_report(email_list, articles, st.session_state.keywords)
                        st.session_state.email_status = (success, message)
                        
                        if success:
                            email_status_container.markdown(f'<div class="success-box">✅ {message}</div>', unsafe_allow_html=True)
                        else:
                            email_status_container.markdown(f'<div class="warning-box">⚠️ {message}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        error_msg = f"Error al enviar el correo: {str(e)}"
                        st.session_state.email_status = (False, error_msg)
                        email_status_container.markdown(f'<div class="warning-box">⚠️ {error_msg}</div>', unsafe_allow_html=True)
                        print(f"Error en el envío de correo: {str(e)}")
        
        # Add footer
        st.markdown("""
        <div class="footer">
            <div style="margin-bottom: 0.5rem;">© 2025 Monitor de Noticias Mineras México</div>
            <div style="font-size: 0.7rem;">Desarrollado con tecnología de procesamiento de lenguaje natural | Datos extraídos de fuentes públicas</div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()