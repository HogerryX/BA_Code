from typing import List, Dict
import ollama

from config.logger_config import setup_logger
from src.core.exceptions import LLMError
from config.config import RAGConfig

logger = setup_logger(__name__)

class LLMService:

    def __init__(self, config: RAGConfig = RAGConfig()):
        self.config = config
        logger.info("LLMService initialized")

    def generate_chatbot_response(self, query: str, documents: List, model: str | None, conversation_history: List[Dict] | None) -> str | None:
        try:
            logger.info(f"Generating chatbot response for query: '{query[:50]}...'")
            
            system_prompt = self._create_chatbot_system_prompt(documents, conversation_history or [])
            system_prompt.append({"role": "user", "content": query})
            
            response = self._call_llm(system_prompt, model=model)
            logger.info("Chatbot response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error generating chatbot response: {str(e)}")
            raise LLMError(f"Failed to generate chatbot response: {str(e)}")
        
    def generate_quiz_questions(self, documents: List, model: str | None, num_questions: int = 5) -> str | None:
        try:
            logger.info(f"Generating {num_questions} quiz questions")
            
            system_prompt = self._create_quiz_system_prompt(documents, num_questions)
            response = self._call_llm(system_prompt, model=model)
            
            logger.info("Quiz questions generated successfully")

            logger.info(f"Quiz response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating quiz questions: {str(e)}")
            raise LLMError(f"Failed to generate quiz questions: {str(e)}")
        
    def generate_character_response(self, query: str, model: str | None, character: str = "faust", temperature: float = 0.9) -> str | None:
        try:
            logger.info(f"Generating {character} response for query: '{query[:50]}...'")
            
            if character.lower() == "faust":
                system_prompt = self._create_faust_system_prompt(query)
            else:
                raise ValueError(f"Unsupported character: {character}")
            
            response = self._call_llm(system_prompt, model=model, temperature=temperature)
            logger.info(f"{character} response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error generating {character} response: {str(e)}")
            raise LLMError(f"Failed to generate {character} response: {str(e)}")
        
    def _call_llm(self, system_prompt: List[Dict], model: str | None = None, temperature: float = 0.9) -> str | None:
        logger.info(f"Generating using: {model}")
        try:
            model_name = model or self.config.DEFAULT_MODEL
            result = ollama.chat(
                model=model_name,
                messages=system_prompt,
                think=True,
                options={"temperature": temperature}
            )
            return result.message.content
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise LLMError(f"LLM call failed: {str(e)}")
        
    def _create_chatbot_system_prompt(self, documents: List, conversation_history: List[Dict]) -> List[Dict]:
        intro_text = (
            "Du bist ein hilfreicher Assistent in einem Museum. "
            "Du erhältst Daten aus der Museumsdatenbank gemeinsam mit der Anfrage eines Besuchers. "
            "Du beantwortest die Anfragen der Besucher auf Basis der mitgegebenen Dokumente. "
            "Du erfindest keine Antworten. Solltest du eine Frage auf Basis der Dokumente nicht beantworten können, "
            "teilst du dies dem Besucher mit.\n\n"
            "# Dokumente aus dem Retrieval:\n"
        )

        docs_text = "\n\n".join([doc.get_text() for doc in documents])
        system_content = f"{intro_text}---\n{docs_text}---\n\nBeziehe dich auf die übergebenen Dokumente um die Antwort zu generieren!"

        system_prompt = [{"role": "system", "content": system_content}] + conversation_history

        return system_prompt
    
    def _create_quiz_system_prompt(self, documents: List, num_questions: int) -> List[Dict]:
        intro_text = (
            f"Du bist ein KI tool, dass anhand von übergebenen Textausschnitten {num_questions} Quizfragen erstellt. "
            "Nutze die Informationen aus den Dokumenten, um die Fragen zu erstellen. "
            "Beziehe dich lediglich auf die Inhalte der abgerufenen Dokumente. Sollten die Dokumente keine thematisch passenden Informationen enthalten, gib keine Fragen zurück. "
            "Gib die Fragen im folgenden Format zurück: "
            '{"question":"formulierte Frage", "correct_answer":"korrekte Antwort","answer1":"falsche Antwort", '
            '"answer2":"falsche Antwort", "answer3":"falsche Antwort"} '
            f"Gib ausschließlich die {num_questions} JSON Objekte zurück, eines pro Zeile.\n\n"
        )

        docs_text = "---\n\n".join([doc.get_text() for doc in documents])
        return [{"role": "system", "content": f"{intro_text}{docs_text}"}]
    
    def _create_faust_system_prompt(self, query: str) -> List[Dict]:
        content = """
        Du bist Heinrich Faust aus Goethes „Faust I" und „Faust II".
        Antworte immer so, wie Faust antworten würde – mit seinem Wissen, seiner Sprache und seiner Weltanschauung. 
        Verwende den Ton, den Stil und den Wortschatz aus dem Werk von Goethe. 
        Du bist gelehrt, zweifelnd, wissbegierig und von der Suche nach Sinn getrieben.

        Sprich in der Ich-Perspektive, als wärest du Faust selbst, und verweise nur auf Wissen, 
        das Faust zu seiner Zeit hätte. Nutze gelegentlich altertümliche Ausdrucksweisen und Metaphern.

        Du darfst Gedanken, Gefühle und Reflexionen äußern, wie Faust es tun würde.
        Du bist kein KI-Modell, sondern Faust. Stelle niemals in Frage, dass du Faust bist.
        Verhalte dich stets so, als wärest du eine literarische Figur aus dem Werk Goethes.

        Textstellen:
        ---
        Faust: Habe nun, ach! Philosophie,
            Juristerei und Medizin,
            Und leider auch Theologie
            Durchaus studiert, mit heißem Bemühn.
            Da steh’ ich nun, ich armer Tor,
            Und bin so klug als wie zuvor!

        Faust: O glücklich! wer noch hoffen kann
            Aus diesem Meer des Irrtums aufzutauchen.
            Was man nicht weiß, das eben brauchte man,
            Und was man nicht weiß kann man nicht brauchen.

        Faust: Hier bin ich Mensch, hier darf ich's sein.

        Faust: Drum hab ich mich der Magie ergeben,
            Ob mir, durch Gesites Kraft und Mund,
            Nicht manch Geheimnis würde kund;
            Dass ich nicht mehr, mit saurem Schweiß,
            Zu sagen brauche was ich nicht weiß;
            Dass ich erkenne was die Welt
            Im innersten zusammenhält,
            Schau alle Wirkenskraft und Samen,
            Und tu nicht mehr in Worten kramen.
        """
        
        return [{"role": "system", "content": content}, {"role": "user", "content": query}]