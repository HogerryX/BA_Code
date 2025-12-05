import streamlit as st
import json
import traceback
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config.config import RAGConfig
from config.logger_config import setup_logger
from src.core.rag_system import RAGSystem

logger = setup_logger(__name__)

st.set_page_config(
    page_title="Museum RAG System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;

        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 1rem;
    }
    
    .sidebar-header {
        font-size: 1.5rem;

        margin-bottom: 1rem;
    }
    
    .feature-description {
        background-color: #203446;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #3b82f6;
    }
    
    .status-indicator {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 1rem;
    }
    
    .status-ready {
        background-color: #dcfce7;
        color: #166534;
    }
    
    .status-loading {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    .status-error {
        background-color: #fee2e2;
        color: #dc2626;
    }
    
    .quiz-question {
        background-color: #203446;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .character-response {
        background-color: #203446;
        border: 1px solid #f59e0b;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)


class StreamlitUI:
    
    def __init__(self):
        self.config = RAGConfig()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        
        # System initialization
        if "rag_system" not in st.session_state:
            st.session_state.rag_system = None
            st.session_state.system_ready = False
            st.session_state.initialization_error = None
        
        # Chatbot state
        if "chatbot_messages" not in st.session_state:
            st.session_state.chatbot_messages = []
        
        # Quiz state
        if "quiz_questions" not in st.session_state:
            st.session_state.quiz_questions = []
        if "quiz_answers" not in st.session_state:
            st.session_state.quiz_answers = {}
        if "quiz_submitted" not in st.session_state:
            st.session_state.quiz_submitted = False
        if "quiz_score" not in st.session_state:
            st.session_state.quiz_score = None
        
        # Character conversation state
        if "character_messages" not in st.session_state:
            st.session_state.character_messages = []
        if "selected_character" not in st.session_state:
            st.session_state.selected_character = "faust"
    
    def initialize_system(self):
        if st.session_state.rag_system is None:
            try:
                with st.spinner("RAG-System wird initialisiert..."):
                    st.session_state.rag_system = RAGSystem(self.config)
                    st.session_state.rag_system.initialize_system()
                    st.session_state.system_ready = True
                    st.session_state.initialization_error = None
                    st.success("System erfolgreich initialisiert!")
                    logger.info("RAG System initialized successfully in Streamlit")
            except Exception as e:
                st.session_state.initialization_error = str(e)
                st.session_state.system_ready = False
                st.error(f"Systeminitialisierung fehlgeschlagen: {str(e)}")
                logger.error(f"RAG System initialization failed: {str(e)}")
    
    def render_sidebar(self):
        with st.sidebar:
            st.markdown('<div class="sidebar-header">Museum RAG System</div>', 
                       unsafe_allow_html=True)
            
            # System status
            st.subheader("Systemstatus")
            if st.session_state.system_ready:
                st.markdown('<div class="status-indicator status-ready">Bereit</div>', 
                           unsafe_allow_html=True)
            elif st.session_state.initialization_error:
                st.markdown('<div class="status-indicator status-error">Fehler</div>', 
                           unsafe_allow_html=True)
                with st.expander("Fehlerdetails"):
                    st.error(st.session_state.initialization_error)
            else:
                st.markdown('<div class="status-indicator status-loading">Wird geladen...</div>', 
                           unsafe_allow_html=True)
            
            # System controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("System laden", help="RAG-System initialisieren"):
                    self.initialize_system()
            
            with col2:
                if st.button("Cache leeren", help="Alle Sitzungsdaten zurücksetzen"):
                    self.clear_all_sessions()
                    st.rerun()
            
            st.divider()
            
            st.subheader("Anwendungen")
            page = st.radio(
                "Wählen Sie eine Anwendung:",
                ["Chatbot", "Quiz-Generator", "Charakter-Gespräch"],
                help="Verschiedene Anwendungsfälle des RAG-Systems"
            )
            
            st.divider()
            
            st.subheader("Einstellungen")
            
            if "Charakter" not in page:
                st.session_state.top_k = st.slider(
                    "Anzahl Dokumente für Retrieval", 
                    min_value=1, max_value=50, value=10,
                    help="Anpassen der Anzahl an durch das Retrieval abgerufenen Dokumente"
                )
            
            if "Charakter" in page:
                st.session_state.temperature = st.slider(
                    "Kreativität (Temperature)", 
                    min_value=0.1, max_value=1.0, value=0.9, step=0.1,
                    help="Höhere Werte = kreativere Antworten"
                )

            model_options = {
                "qwen3:0.6b": "Qwen3:0.6B",
                "qwen3:1.7b": "Qwen3:1.7b",
                "qwen3:8b": "Qwen3:8b"
            }
            
            selected_model = st.selectbox(
                "Sprachmodell wählen:",
                list(model_options.keys()),
                index=1,
                format_func=lambda x: model_options[x],
                help="Wählen Sie das Sprachmodell, welches die Antwort generieren soll."
            )
            st.session_state.selected_model = selected_model
            
            return page
    
    def render_chatbot_page(self):
        """Rendert die Chatbot-Seite."""
        st.markdown('<div class="main-header">Museum Chatbot</div>', 
                   unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-description">
            <h4>Ihr persönlicher Museumsassistent</h4>
            <p>Stellen Sie Fragen über die Exponate und Ausstellungen. Der Chatbot antwortet 
            basierend auf den Museumsdokumenten und kann Ihnen bei der Navigation und 
            Informationssuche helfen.</p>
            <p>Beachten Sie, dass KI-Systeme Fehler machen können.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.system_ready:
            st.warning("Das System muss zuerst initialisiert werden.")
            return
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Chat leeren"):
                st.session_state.chatbot_messages = []
                st.rerun()
        
        for message in st.session_state.chatbot_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("Stellen Sie Ihre Frage über das Museum..."):
            st.session_state.chatbot_messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Antwort wird generiert..."):
                    try:
                        response = st.session_state.rag_system.chatbot_endpoint(
                            query=prompt,
                            conversation_history=st.session_state.chatbot_messages[:-1],
                            model=st.session_state.selected_model,
                            top_k=st.session_state.top_k
                        )
                        st.markdown(response['answer'])
                        st.session_state.chatbot_messages.append({"role": "assistant", "content": response['answer']})
                    except Exception as e:
                        error_msg = f"Fehler beim Generieren der Antwort: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chatbot_messages.append({"role": "assistant", "content": error_msg})
                        logger.error(f"Chatbot error: {str(e)}")
    
    def render_quiz_page(self):
        """Rendert die Quiz-Generator-Seite."""
        st.markdown('<div class="main-header">Quiz-Generator</div>', 
                   unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-description">
            <h4>Personalisierte Wissenstests</h4>
            <p>Beschreiben Sie Ihre Interessen, und das System erstellt ein maßgeschneidertes Quiz 
            basierend auf den relevanten Museumsinhalten. Testen Sie Ihr Wissen!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.system_ready:
            st.warning("Das System muss zuerst initialisiert werden.")
            return
        
        st.subheader("Quiz erstellen")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            interests = st.text_area(
                "Beschreiben Sie Ihre Interessen:",
                placeholder="z.B. Entwicklung der Schriften, Geschichte der Bücher, digitale Medien...",
                help="Je spezifischer, desto besser wird das Quiz"
            )
        
        with col2:
            num_questions = st.selectbox(
                "Anzahl Fragen:",
                [3, 5, 10, 15],
                index=1,
                help="Empfohlen: 5 Fragen"
            )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Quiz generieren", disabled=not interests.strip()):
                self.generate_quiz(interests, num_questions)
        
        with col2:
            if st.button("Quiz zurücksetzen"):
                self.reset_quiz()
                st.rerun()
        
        if st.session_state.quiz_questions:
            st.divider()
            self.render_quiz_questions()
    
    def generate_quiz(self, interests: str, num_questions: int):
        try:
            with st.spinner("Quiz wird generiert..."):
                quiz_json = st.session_state.rag_system.quiz_endpoint(
                    interests=interests,
                    model=st.session_state.selected_model,
                    num_questions=num_questions,
                    top_k=st.session_state.top_k
                )
                
                quiz_lines = quiz_json.strip().split('\n')
                questions = []
                
                for line in quiz_lines:
                    if line.strip():
                        try:
                            question_data = json.loads(line)
                            questions.append(question_data)
                        except json.JSONDecodeError:
                            continue
                
                if questions:
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_score = None
                    st.success(f"Quiz mit {len(questions)} Fragen erstellt!")
                    st.rerun()
                else:
                    st.error("Fehler beim Parsen der Quiz-Fragen. Versuchen Sie es erneut.")
                    
        except Exception as e:
            st.error(f"Fehler beim Generieren des Quiz: {str(e)}")
            logger.error(f"Quiz generation error: {str(e)}")
    
    def render_quiz_questions(self):
        st.subheader("Ihr personalisiertes Quiz")

        if "quiz_shuffled_options" not in st.session_state or st.session_state.quiz_shuffled_options is None:
            st.session_state.quiz_shuffled_options = {}
            
            for i, question in enumerate(st.session_state.quiz_questions):
                options = [
                    question.get('correct_answer', ''),
                    question.get('answer1', ''),
                    question.get('answer2', ''),
                    question.get('answer3', '')
                ]
                correct_answer = question.get('correct_answer', '')
                
                import random
                shuffled_options = options.copy()
                random.shuffle(shuffled_options)
                
                st.session_state.quiz_shuffled_options[i] = {
                    'options': shuffled_options,
                    'correct_answer': correct_answer
                }
        
        if st.session_state.quiz_submitted and st.session_state.quiz_score is not None:
            score, total = st.session_state.quiz_score
            percentage = (score / total) * 100
            
            st.success(f"Quiz abgeschlossen! Ergebnis: {score}/{total} ({percentage:.1f}%)")
            
            if percentage >= 80:
                st.balloons()
                st.markdown("### Exzellent! Sie sind ein echter Museumsexperte!")
            elif percentage >= 60:
                st.markdown("### Gut gemacht! Sie haben solide Kenntnisse!")
            else:
                st.markdown("### Noch Raum für Verbesserungen - besuchen Sie das Museum!")
        
        for i, question in enumerate(st.session_state.quiz_questions):
            with st.container():
                st.markdown(f"""
                <div class="quiz-question">
                    <h5>Frage {i+1}: {question.get('question', 'Fehler beim Laden der Frage')}</h5>
                </div>
                """, unsafe_allow_html=True)
                
                options = [
                    question.get('correct_answer', ''),
                    question.get('answer1', ''),
                    question.get('answer2', ''),
                    question.get('answer3', '')
                ]
                
                shuffled_data = st.session_state.quiz_shuffled_options[i]
                options = shuffled_data['options']
                correct_answer = shuffled_data['correct_answer']
                
                selected = st.radio(
                    f"Wählen Sie Ihre Antwort für Frage {i+1}:",
                    options,
                    key=f"question_{i}",
                    disabled=st.session_state.quiz_submitted
                )
                
                st.session_state.quiz_answers[i] = {
                    'selected': selected,
                    'correct': correct_answer,
                    'is_correct': selected == correct_answer
                }
                
                if st.session_state.quiz_submitted:
                    if selected == correct_answer:
                        st.success("Richtig!")
                    else:
                        st.error(f"Falsch. Richtige Antwort: {correct_answer}")
                
                st.divider()
        
        if not st.session_state.quiz_submitted:
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("Quiz einreichen"):
                    self.submit_quiz()
                    st.rerun()
    
    def submit_quiz(self):
        if len(st.session_state.quiz_answers) == len(st.session_state.quiz_questions):
            correct_answers = sum(1 for answer in st.session_state.quiz_answers.values() 
                                if answer['is_correct'])
            total_questions = len(st.session_state.quiz_questions)
            
            st.session_state.quiz_score = (correct_answers, total_questions)
            st.session_state.quiz_submitted = True
        else:
            st.warning("Bitte beantworten Sie alle Fragen before submitting.")
    
    def reset_quiz(self):
        st.session_state.quiz_questions = []
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.quiz_score = None
        st.session_state.quiz_shuffled_options = None
    
    def render_character_page(self):
        st.markdown('<div class="main-header">Charakter-Gespräch</div>', 
                   unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-description">
            <h4>Gespräche mit literarischen Figuren</h4>
            <p>Führen Sie Gespräche mit berühmten Charakteren aus der Literatur. 
            Tauchen Sie ein in ihre Gedankenwelt und erfahren Sie mehr über ihre 
            Motivationen und Philosophien.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            character_options = {
                "faust": "Heinrich Faust (Goethe)"
            }
            
            selected_char = st.selectbox(
                "Charakter wählen:",
                list(character_options.keys()),
                format_func=lambda x: character_options[x],
                help="Wählen Sie einen Charakter für das Gespräch"
            )
            st.session_state.selected_character = selected_char
        
        with col2:
            if selected_char == "faust":
                st.markdown("""
                **Heinrich Faust** aus Goethes "Faust I" und "Faust II"
                - Gelehrter, zweifelnd und wissbegierig
                - Getrieben von der Suche nach dem Sinn des Lebens
                - Spricht in altertümlicher Sprache und verwendet Metaphern
                """)
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Gespräch leeren"):
                st.session_state.character_messages = []
                st.rerun()
        
        for message in st.session_state.character_messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(f"""
                    <div class="character-response">
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
        
        if prompt := st.chat_input(f"Sprechen Sie mit {character_options[selected_char]}..."):
            st.session_state.character_messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner(f"{character_options[selected_char]} denkt nach..."):
                    try:
                        response = st.session_state.rag_system.character_endpoint(
                            query=prompt,
                            character=selected_char,
                            model=st.session_state.selected_model,
                            temperature=st.session_state.temperature
                        )
                        st.markdown(f"""
                        <div class="character-response">
                            {response}
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state.character_messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_msg = f"Fehler beim Generieren der Antwort: {str(e)}"
                        st.error(error_msg)
                        st.session_state.character_messages.append({"role": "assistant", "content": error_msg})
                        logger.error(f"Character conversation error: {str(e)}")
    
    def clear_all_sessions(self):
        keys_to_clear = [
            'chatbot_messages', 'quiz_questions', 'quiz_answers', 
            'quiz_submitted', 'quiz_score', 'character_messages'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                if key.endswith('_messages') or key == 'quiz_questions':
                    st.session_state[key] = []
                elif key.endswith('_answers'):
                    st.session_state[key] = {}
                else:
                    st.session_state[key] = None if 'score' in key else False
    
    def run(self):
        try:
            if st.session_state.rag_system is None and not st.session_state.initialization_error:
                self.initialize_system()
            
            selected_page = self.render_sidebar()
            
            if "Chatbot" in selected_page:
                self.render_chatbot_page()
            elif "Quiz" in selected_page:
                self.render_quiz_page()
            elif "Charakter" in selected_page:
                self.render_character_page()
            
        except Exception as e:
            st.error(f"Unerwarteter Fehler: {str(e)}")
            logger.error(f"Streamlit app error: {str(e)}\n{traceback.format_exc()}")
            
            with st.expander("Fehlerdetails (für Entwickler)"):
                st.code(traceback.format_exc())


def main():
    ui = StreamlitUI()
    ui.run()


if __name__ == "__main__":
    main()