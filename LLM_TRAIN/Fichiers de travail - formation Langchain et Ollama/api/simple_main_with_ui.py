"""
Version simplifiée de l'API avec interface intégrée, persistance des conversations et Ollama.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au path pour l'import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_conversation_db, conversation_db
from ollama_simple import init_ollama_client, check_ollama_setup, ollama_client
from rag_integration import init_rag, rag_service

# Nouveau: Import du pipeline LangChain
try:
    from llm.langchain_pipeline import create_langchain_rag_pipeline, LangChainRAGPipeline
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"LangChain pipeline non disponible: {e}")
    LANGCHAIN_AVAILABLE = False

# Nouveau: Import du système mystique
try:
    from llm.mystical_persona import create_mystical_processor, MysticalPersona
    MYSTICAL_AVAILABLE = True
except ImportError as e:
    print(f"Module mystique non disponible: {e}")
    MYSTICAL_AVAILABLE = False

app = FastAPI(title="RAG ChatBot", version="1.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales
ollama_status = {"available": False, "model": None, "error": None}
rag_status = {"available": False, "chunks": 0, "error": None}
langchain_pipeline = None  # Nouveau: Pipeline LangChain
mystical_mode = False  # Nouveau: Mode mystique
mystical_processor = None  # Processeur mystique

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage."""
    global ollama_status, rag_status, langchain_pipeline, mystical_mode, mystical_processor
    
    # Initialiser la base de données des conversations
    init_conversation_db()
    
    # Initialiser Ollama
    try:
        init_ollama_client()
        result = check_ollama_setup()
        if result.get("available"):  # Changé de "success" à "available"
            ollama_status = {
                "available": True,
                "model": result.get("current_model"),  # Changé de "model" à "current_model"
                "error": None
            }
            print(f"✅ Ollama configuré avec le modèle: {result.get('current_model')}")
        else:
            ollama_status = {
                "available": False,
                "model": None,
                "error": result.get("error", "Erreur inconnue")
            }
            print(f"❌ Erreur Ollama: {result.get('error', 'Erreur inconnue')}")
    except Exception as e:
        ollama_status = {
            "available": False,
            "model": None,
            "error": str(e)
        }
        print(f"❌ Erreur initialisation Ollama: {e}")
    
    # Initialiser le service RAG
    try:
        rag_service = init_rag()
        rag_service_status = rag_service.get_status()
        
        if rag_service_status["available"]:
            rag_status = {
                "available": True,
                "chunks": rag_service_status["total_chunks"],
                "index_type": rag_service_status["index_type"],
                "error": None
            }
            print(f"✅ RAG configuré: {rag_service_status['total_chunks']} chunks disponibles")
        else:
            rag_status = {
                "available": False,
                "chunks": 0,
                "error": rag_service_status.get("error", "Erreur inconnue")
            }
            print(f"❌ Erreur RAG: {rag_service_status.get('error', 'Erreur inconnue')}")
    except Exception as e:
        rag_status = {
            "available": False,
            "chunks": 0,
            "error": str(e)
        }
        print(f"❌ Erreur initialisation RAG: {e}")

    # Nouveau: Initialisation pipeline LangChain
    if LANGCHAIN_AVAILABLE:
        try:
            langchain_pipeline = await create_langchain_rag_pipeline()
            print(f"🔗 Pipeline LangChain initialisé: {langchain_pipeline.get_stats()}")
        except Exception as e:
            print(f"❌ Erreur pipeline LangChain: {e}")
            langchain_pipeline = None

    # Initialisation système mystique
    if MYSTICAL_AVAILABLE:
        mystical_processor = create_mystical_processor(intensity=0.8)
        print(f"🔮 Système mystique prêt (mode désactivé par défaut)")

# Modèles Pydantic
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    timestamp: str
    indicators: List[str] = []
    metadata: Dict[str, Any] = {}
    confidence: float = 0.8
    sources: List[Dict] = []
    conversation_id: Optional[str] = None
    learned_from_history: bool = False
    used_ollama: bool = False
    used_rag: bool = False

class ConversationHistoryResponse(BaseModel):
    session_id: str
    history: List[Dict]
    total_messages: int

class SessionsResponse(BaseModel):
    sessions: List[Dict]
    total_sessions: int

class OllamaStatusResponse(BaseModel):
    available: bool
    models: List[str] = []
    current_model: Optional[str] = None
    error: Optional[str] = None

# Interface HTML mise à jour avec bouton nouvelle conversation et intégration Ollama
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatBot RAG - Interface</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f7f7f8; height: 100vh; display: flex; flex-direction: column;
        }
        .header {
            background: #fff; border-bottom: 1px solid #e5e5e7; padding: 1rem 2rem;
            display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .header h1 { color: #333; font-size: 1.5rem; font-weight: 600; }
        .header-controls { display: flex; gap: 1rem; align-items: center; }
        .status {
            padding: 0.5rem 1rem; border-radius: 20px; background: #10a37f;
            color: white; font-size: 0.9rem; font-weight: 500;
        }
        .status.offline { background: #ef4444; }
        .status.ollama-off { background: #f59e0b; }
        .btn {
            padding: 0.5rem 1rem; border-radius: 20px; border: none; 
            cursor: pointer; font-size: 0.9rem; font-weight: 500;
            transition: background 0.2s;
        }
        .btn-primary { background: #6366f1; color: white; }
        .btn-primary:hover { background: #4f46e5; }
        .btn-success { background: #10b981; color: white; }
        .btn-success:hover { background: #059669; }
        .chat-container {
            flex: 1; display: flex; flex-direction: column; max-width: 800px;
            margin: 0 auto; width: 100%; padding: 0 1rem;
        }
        .messages {
            flex: 1; overflow-y: auto; padding: 2rem 0;
            display: flex; flex-direction: column; gap: 1.5rem;
        }
        .message { display: flex; gap: 1rem; max-width: 100%; }
        .message.user { justify-content: flex-end; }
        .message.assistant { justify-content: flex-start; }
        .message-content {
            max-width: 70%; padding: 1rem 1.5rem; border-radius: 1rem;
            font-size: 0.95rem; line-height: 1.5; word-wrap: break-word;
        }
        .message.user .message-content {
            background: #10a37f; color: white; border-bottom-right-radius: 0.3rem;
        }
        .message.assistant .message-content {
            background: #f1f1f2; color: #333; border-bottom-left-radius: 0.3rem;
            border: 1px solid #e5e5e7;
        }
        .message-avatar {
            width: 32px; height: 32px; border-radius: 50%; display: flex;
            align-items: center; justify-content: center; font-weight: 600;
            font-size: 0.8rem; flex-shrink: 0;
        }
        .message.user .message-avatar { background: #10a37f; color: white; }
        .message.assistant .message-avatar { background: #9333ea; color: white; }
        .ai-indicator {
            font-size: 0.8rem; color: #10b981; margin-top: 0.5rem;
            font-style: italic;
        }
        .learned-indicator {
            font-size: 0.8rem; color: #6366f1; margin-top: 0.5rem;
            font-style: italic;
        }
        .input-area { padding: 1rem 0 2rem; background: #f7f7f8; }
        .input-container {
            position: relative; background: white; border: 1px solid #e5e5e7;
            border-radius: 1rem; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .input-field {
            width: 100%; border: none; outline: none; padding: 1rem 4rem 1rem 1.5rem;
            font-size: 1rem; resize: none; min-height: 24px; max-height: 120px;
            font-family: inherit; background: transparent;
        }
        .send-button {
            position: absolute; right: 0.5rem; top: 50%; transform: translateY(-50%);
            background: #10a37f; color: white; border: none; border-radius: 0.5rem;
            width: 2.5rem; height: 2.5rem; cursor: pointer; display: flex;
            align-items: center; justify-content: center; transition: background 0.2s;
        }
        .send-button:hover:not(:disabled) { background: #0d8f6b; }
        .send-button:disabled { background: #d1d5db; cursor: not-allowed; }
        .welcome { text-align: center; padding: 3rem 1rem; color: #666; }
        .welcome h2 { font-size: 1.8rem; margin-bottom: 0.5rem; color: #333; }
        .welcome p { font-size: 1rem; line-height: 1.6; }
        .typing-indicator { display: none; padding: 1rem; color: #666; font-style: italic; }
        .typing-dots { display: inline-block; animation: typing 1.4s infinite; }
        @keyframes typing { 0%, 60%, 100% { opacity: 0; } 30% { opacity: 1; } }
        .modal {
            display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5); z-index: 1000;
        }
        .modal-content {
            background: white; max-width: 600px; margin: 5% auto; padding: 2rem;
            border-radius: 1rem; max-height: 80vh; overflow-y: auto;
        }
        .session-item {
            padding: 1rem; border: 1px solid #e5e5e7; border-radius: 0.5rem;
            margin-bottom: 0.5rem; cursor: pointer; transition: background 0.2s;
        }
        .session-item:hover { background: #f8f9fa; }
        .session-title { font-weight: 600; margin-bottom: 0.25rem; }
        .session-meta { font-size: 0.8rem; color: #666; }
        .close-btn {
            float: right; background: none; border: none; font-size: 1.5rem;
            cursor: pointer; color: #666;
        }
        .ollama-status {
            background: #f3f4f6; padding: 0.5rem 1rem; border-radius: 0.5rem;
            font-size: 0.8rem; margin-bottom: 1rem;
        }
        .ollama-status.ready { background: #d1fae5; color: #065f46; }
        .ollama-status.error { background: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 ChatBot RAG</h1>
        <div class="header-controls">
            <button class="btn btn-success" onclick="newConversation()">✨ Nouvelle Conversation</button>
            <button class="btn btn-primary" onclick="showSessions()">📚 Historique</button>
            <div class="status" id="status">En ligne</div>
        </div>
    </div>

    <div class="chat-container">
        <div class="ollama-status" id="ollamaStatus">
            🔄 Vérification d'Ollama...
        </div>
        
        <div class="messages" id="messages">
            <div class="welcome">
                <h2>Bienvenue dans ChatBot RAG ! 👋</h2>
                <p>Je suis votre assistant intelligent avec mémoire persistante et IA Ollama.<br>
                Vos conversations sont sauvegardées et m'aident à mieux vous répondre !</p>
            </div>
        </div>

        <div class="typing-indicator" id="typingIndicator">
            <div class="message assistant">
                <div class="message-avatar">AI</div>
                <div class="message-content">
                    En train d'écrire<span class="typing-dots">...</span>
                </div>
            </div>
        </div>

        <div class="input-area">
            <div class="input-container">
                <textarea 
                    id="messageInput" 
                    class="input-field" 
                    placeholder="Tapez votre message..." 
                    rows="1"></textarea>
                <button id="sendButton" class="send-button">📤</button>
            </div>
        </div>
    </div>

    <!-- Modal des sessions -->
    <div class="modal" id="sessionsModal">
        <div class="modal-content">
            <button class="close-btn" onclick="closeSessions()">&times;</button>
            <h3>Historique des conversations</h3>
            <div id="sessionsList"></div>
        </div>
    </div>

    <!-- CONTROLS MYSTIQUES -->
    <div class="mystical-controls" style="margin: 10px 0; padding: 10px; background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 8px; border: 1px solid #ffd700;">
        <h4 style="color: #ffd700; margin: 0 0 10px 0;">🔮 Contrôles Mystiques</h4>
        <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
            <label style="color: #e0e0e0;">
                <input type="checkbox" id="mysticalToggle" onchange="toggleMysticalMode()"> Mode Gourou Mystique
            </label>
            <div style="display: flex; align-items: center; gap: 5px;">
                <label style="color: #e0e0e0;">Intensité:</label>
                <input type="range" id="mysticalIntensity" min="0.1" max="1.0" step="0.1" value="0.8" 
                       style="width: 100px;" onchange="updateIntensity()">
                <span id="intensityValue" style="color: #ffd700;">0.8</span>
            </div>
            <button onclick="checkMysticalStatus()" style="background: #4a5568; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">📊 Statut</button>
        </div>
        <div id="mysticalStatus" style="margin-top: 10px; color: #e0e0e0; font-size: 0.9em;"></div>
    </div>

    <script>
        class ChatBot {
            constructor() {
                this.messages = document.getElementById('messages');
                this.messageInput = document.getElementById('messageInput');
                this.sendButton = document.getElementById('sendButton');
                this.status = document.getElementById('status');
                this.typingIndicator = document.getElementById('typingIndicator');
                this.ollamaStatus = document.getElementById('ollamaStatus');
                
                this.sessionId = this.getOrCreateSessionId();
                this.conversationHistory = [];
                this.ollamaAvailable = false;
                
                this.initializeEventListeners();
                this.checkServerStatus();
                this.checkOllamaStatus();
                this.loadHistory();
            }

            getOrCreateSessionId() {
                let sessionId = localStorage.getItem('chatbot_session_id');
                if (!sessionId) {
                    sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
                    localStorage.setItem('chatbot_session_id', sessionId);
                }
                return sessionId;
            }

            initializeEventListeners() {
                this.sendButton.addEventListener('click', () => this.sendMessage());
                
                this.messageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.sendMessage();
                    }
                });

                this.messageInput.addEventListener('input', () => {
                    this.updateSendButton();
                    this.messageInput.style.height = 'auto';
                    this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
                });
            }

            async checkOllamaStatus() {
                try {
                    const response = await fetch('/api/v1/ollama/status');
                    if (response.ok) {
                        const data = await response.json();
                        this.ollamaAvailable = data.available;
                        
                        if (data.available) {
                            this.ollamaStatus.textContent = `✅ Ollama actif - Modèle: ${data.current_model || 'qwen'}`;
                            this.ollamaStatus.className = 'ollama-status ready';
                        } else {
                            this.ollamaStatus.textContent = `⚠️ Ollama non disponible: ${data.error}`;
                            this.ollamaStatus.className = 'ollama-status error';
                        }
                    }
                } catch (error) {
                    this.ollamaStatus.textContent = '❌ Erreur de connexion à Ollama';
                    this.ollamaStatus.className = 'ollama-status error';
                }
            }

            async loadHistory() {
                try {
                    const response = await fetch(`/api/v1/conversations/${this.sessionId}`);
                    if (response.ok) {
                        const data = await response.json();
                        this.conversationHistory = data.history;
                        this.displayHistory();
                    }
                } catch (error) {
                    console.log('Pas d\\'historique trouvé pour cette session');
                }
            }

            displayHistory() {
                if (this.conversationHistory.length > 0) {
                    const welcome = this.messages.querySelector('.welcome');
                    if (welcome) welcome.remove();

                    this.conversationHistory.forEach(msg => {
                        this.addMessage(msg.role, msg.content, msg.sources, false, false, msg.used_ollama);
                    });
                }
            }

            updateSendButton() {
                this.sendButton.disabled = this.messageInput.value.trim().length === 0;
            }

            async checkServerStatus() {
                try {
                    const response = await fetch('/health');
                    if (response.ok) {
                        this.status.textContent = 'En ligne';
                        this.status.className = 'status';
                    } else {
                        throw new Error('Server error');
                    }
                } catch (error) {
                    this.status.textContent = 'Hors ligne';
                    this.status.className = 'status offline';
                }
            }

            async sendMessage() {
                const message = this.messageInput.value.trim();
                if (!message) return;

                this.messageInput.value = '';
                this.messageInput.style.height = 'auto';
                this.updateSendButton();

                this.addMessage('user', message);
                this.showTypingIndicator();

                try {
                    const response = await fetch('/api/v1/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            message: message,
                            session_id: this.sessionId,
                            conversation_history: this.conversationHistory.slice(-10)
                        })
                    });

                    if (!response.ok) throw new Error('Erreur de réseau');

                    const data = await response.json();
                    
                    this.hideTypingIndicator();
                    this.addMessage('assistant', data.answer, data.sources, true, data.learned_from_history, data.used_ollama);
                    
                    // Mettre à jour l'historique local
                    this.conversationHistory.push(
                        { role: 'user', content: message },
                        { role: 'assistant', content: data.answer, sources: data.sources, used_ollama: data.used_ollama }
                    );

                    if (this.conversationHistory.length > 20) {
                        this.conversationHistory = this.conversationHistory.slice(-20);
                    }

                } catch (error) {
                    this.hideTypingIndicator();
                    this.addMessage('assistant', '❌ Désolé, une erreur s\\'est produite. Veuillez réessayer.');
                    console.error('Error:', error);
                }
            }

            addMessage(role, content, sources = [], scrollToBottom = true, learnedFromHistory = false, usedOllama = false) {
                const welcome = this.messages.querySelector('.welcome');
                if (welcome) welcome.remove();

                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}`;

                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                avatar.textContent = role === 'user' ? 'U' : 'AI';

                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                messageContent.textContent = content;

                if (role === 'assistant') {
                    if (usedOllama) {
                        const aiDiv = document.createElement('div');
                        aiDiv.className = 'ai-indicator';
                        aiDiv.textContent = '🧠 Généré par Ollama';
                        messageContent.appendChild(aiDiv);
                    }
                    
                    if (learnedFromHistory) {
                        const learnedDiv = document.createElement('div');
                        learnedDiv.className = 'learned-indicator';
                        learnedDiv.textContent = '💡 Enrichi par les conversations passées';
                        messageContent.appendChild(learnedDiv);
                    }
                }

                if (role === 'user') {
                    messageDiv.appendChild(messageContent);
                    messageDiv.appendChild(avatar);
                } else {
                    messageDiv.appendChild(avatar);
                    messageDiv.appendChild(messageContent);
                }

                this.messages.appendChild(messageDiv);
                if (scrollToBottom) this.scrollToBottom();
            }

            showTypingIndicator() {
                this.typingIndicator.style.display = 'block';
                this.scrollToBottom();
            }

            hideTypingIndicator() {
                this.typingIndicator.style.display = 'none';
            }

            scrollToBottom() {
                setTimeout(() => {
                    this.messages.scrollTop = this.messages.scrollHeight;
                }, 100);
            }

            newConversation() {
                this.sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('chatbot_session_id', this.sessionId);
                this.conversationHistory = [];
                this.messages.innerHTML = `
                    <div class="welcome">
                        <h2>Nouvelle conversation ! 🆕</h2>
                        <p>Prêt pour une nouvelle discussion !</p>
                    </div>
                `;
                this.messageInput.focus();
            }

            switchToSession(sessionId) {
                this.sessionId = sessionId;
                localStorage.setItem('chatbot_session_id', sessionId);
                this.conversationHistory = [];
                this.messages.innerHTML = '';
                this.loadHistory();
                closeSessions();
            }
        }

        // Fonctions globales
        function newConversation() {
            chatBot.newConversation();
        }

        async function showSessions() {
            try {
                const response = await fetch('/api/v1/sessions');
                const data = await response.json();
                
                const sessionsList = document.getElementById('sessionsList');
                sessionsList.innerHTML = '';
                
                data.sessions.forEach(session => {
                    const sessionDiv = document.createElement('div');
                    sessionDiv.className = 'session-item';
                    sessionDiv.onclick = () => chatBot.switchToSession(session.session_id);
                    
                    sessionDiv.innerHTML = `
                        <div class="session-title">${session.title || session.session_id}</div>
                        <div class="session-meta">
                            ${session.total_messages} messages • ${new Date(session.last_activity).toLocaleDateString()}
                        </div>
                    `;
                    
                    sessionsList.appendChild(sessionDiv);
                });
                
                document.getElementById('sessionsModal').style.display = 'block';
            } catch (error) {
                console.error('Erreur lors du chargement des sessions:', error);
            }
        }

        function closeSessions() {
            document.getElementById('sessionsModal').style.display = 'none';
        }

        // Initialiser le chatbot
        let chatBot;
        document.addEventListener('DOMContentLoaded', () => {
            chatBot = new ChatBot();
        });
    </script>
</body>
</html>
"""

def enhance_response_with_history(user_message: str, base_response: str) -> tuple[str, bool]:
    """Enrichit la réponse avec les conversations passées."""
    try:
        # Rechercher dans les conversations passées
        past_conversations = conversation_db.search_conversations(user_message, limit=3)
        
        if past_conversations:
            # Construire une réponse enrichie
            enhanced_response = base_response + "\n\n💡 **Informations complémentaires basées sur nos conversations passées :**\n"
            
            for i, conv in enumerate(past_conversations, 1):
                enhanced_response += f"\n{i}. **Q**: {conv['user_question'][:100]}...\n"
                enhanced_response += f"   **R**: {conv['assistant_answer'][:150]}...\n"
            
            return enhanced_response, True
        
    except Exception as e:
        print(f"Erreur lors de l'enrichissement: {e}")
    
    return base_response, False

async def generate_smart_response(
    message: str, 
    session_id: str, 
    conversation_history: List[Dict[str, Any]] = None,
    use_langchain: bool = True  # Nouveau paramètre
) -> tuple[str, bool, bool, bool]:
    """
    Génère une réponse intelligente avec choix du pipeline.
    
    Args:
        message: Message utilisateur
        session_id: ID de session
        conversation_history: Historique (optionnel)
        use_langchain: Utiliser le pipeline LangChain si disponible
        
    Returns:
        (response, used_ollama, learned_from_history, used_rag, used_langchain)
    """
    global ollama_client, rag_service, langchain_pipeline, mystical_mode, mystical_processor
    
    # Récupération historique si non fourni
    if conversation_history is None:
        history = conversation_db.get_session_history(session_id, limit=10)
        print(f"📚 Historique récupéré: {len(history)} messages pour session {session_id}")
    else:
        history = conversation_history
        print(f"✅ Utilisation de l'historique fourni ({len(history)} messages)")
    
    # Nouveau: Choix du pipeline
    if use_langchain and langchain_pipeline:
        try:
            print(f"🔗 Utilisation pipeline LangChain")
            
            # Utilisation du pipeline LangChain
            result = await langchain_pipeline.query(
                question=message,
                session_id=session_id
            )
            
            return (
                result["answer"], 
                True,  # used_ollama
                len(history) > 0,  # learned_from_history  
                len(result.get("sources", [])) > 0,  # used_rag
                True   # used_langchain
            )
            
        except Exception as e:
            print(f"❌ Erreur pipeline LangChain: {e}")
            print(f"⚠️ Fallback vers pipeline classique")
    
    # Pipeline classique (existant)
    context_rag = ""
    used_rag = False
    rag_sources = []
    
    if rag_service:
        print(f"🔍 Recherche RAG pour: '{message}'")
        context_rag = rag_service.get_rag_response_context(message)
        
        if context_rag and len(context_rag.strip()) > 10:
            sources = rag_service.get_last_search_sources()
            source_files = list(set([s.get('source', 'inconnu') for s in sources]))
            print(f"📚 RAG trouvé: {len(sources)} chunks de {source_files}")
            used_rag = True
            rag_sources = sources
        else:
            print(f"📭 RAG: Aucun contexte pertinent trouvé")
    
    # Enrichissement avec historique
    enhanced_history = ""
    try:
        enhanced_history = conversation_db.search_relevant_conversations(message, limit=3)
        if enhanced_history:
            print(f"💡 Trouvé {len(enhanced_history.split('---'))} conversations pertinentes")
    except Exception as e:
        print(f"Erreur FTS5: {e}")
        enhanced_history = ""
    
    # Génération avec Ollama
    used_ollama = False
    if ollama_client and check_ollama_setup():
        try:
            print(f"🧠 Ollama utilisé avec {len(history)} messages d'historique")
            
            documents = [{"content": context_rag}] if context_rag else []
            response = ollama_client.generate_with_rag(
                user_question=message,
                context_documents=documents,
                conversation_history=history
            )
            used_ollama = True
            
            return response, used_ollama, len(history) > 0, used_rag, False
            
        except Exception as e:
            print(f"Erreur Ollama: {e}")
    
    # Fallback response
    if used_rag and rag_sources:
        source_list = ", ".join(set([s.get('source', 'inconnu') for s in rag_sources[:2]]))
        response = f"Je suis un assistant IA en cours de configuration. J'ai trouvé des informations pertinentes dans {len(rag_sources)} source(s) : {source_list}.\n\nContexte trouvé:\n{context_rag[:500]}..."
        indicators = ["📚 Informations des documents indexés"]
    else:
        response = "Je suis un assistant IA en cours de configuration. Je n'ai pas trouvé d'informations spécifiques dans ma base documentaire pour cette question."
        indicators = []
    
    return response, used_ollama, len(history) > 0, used_rag, False

# Routes
@app.get("/")
async def root():
    return {
        "message": "ChatBot RAG API (avec Interface, Historique et Ollama)",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "chat_ui": "/chat",
        "features": ["persistent_conversations", "conversation_learning", "session_management", "ollama_integration"],
        "ollama_status": ollama_status
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "with_ollama"}

@app.get("/chat")
async def serve_chat_ui():
    """Interface de chat web."""
    return HTMLResponse(content=HTML_INTERFACE)

@app.get("/ui")
async def serve_ui_alt():
    """Interface alternative."""
    return HTMLResponse(content=HTML_INTERFACE)

@app.get("/api/v1/ollama/status", response_model=OllamaStatusResponse)
async def get_ollama_status():
    """Vérifie le statut d'Ollama."""
    return OllamaStatusResponse(**ollama_status)

@app.get("/api/v1/rag/status")
async def get_rag_status():
    """Retourne le statut du service RAG."""
    global rag_status
    return {
        "available": rag_status.get("available", False),
        "chunks": rag_status.get("chunks", 0),
        "index_type": rag_status.get("index_type", "faiss"),
        "error": rag_status.get("error")
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint de chat avec Ollama et apprentissage des conversations."""
    # Générer la réponse intelligente
    response, used_ollama, learned_from_history, used_rag = await generate_smart_response(
        request.message, 
        request.session_id or "demo_session",
        request.conversation_history or []
    )
    
    # Sauvegarder dans la base de données avec métadonnées
    try:
        conversation_db.save_conversation(
            session_id=request.session_id or "demo_session",
            user_message=request.message,
            assistant_response=response,
            confidence=0.9 if used_ollama else 0.5,
            metadata={
                "used_ollama": used_ollama,
                "learned_from_history": learned_from_history,
                "used_rag": used_rag,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")
    
    # Préparer les indicateurs pour l'UI
    indicators = []
    if used_ollama:
        indicators.append("🧠 Généré par Ollama")
    if learned_from_history:
        indicators.append("💡 Enrichi par les conversations passées")
    if used_rag:
        indicators.append("📚 Informations des documents indexés")
    
    return {
        "answer": response,  # Changé de "response" à "answer"
        "session_id": request.session_id or "demo_session",
        "timestamp": datetime.now().isoformat(),
        "indicators": indicators,
        "metadata": {
            "used_ollama": used_ollama,
            "learned_from_history": learned_from_history,
            "used_rag": used_rag
        }
    }

@app.get("/api/v1/conversations/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(session_id: str):
    """Récupère l'historique d'une session."""
    history = conversation_db.get_session_history(session_id)
    return ConversationHistoryResponse(
        session_id=session_id,
        history=history,
        total_messages=len(history)
    )

@app.get("/api/v1/sessions", response_model=SessionsResponse)
async def get_sessions():
    """Récupère la liste des sessions."""
    sessions = conversation_db.get_sessions()
    return SessionsResponse(
        sessions=sessions,
        total_sessions=len(sessions)
    )

@app.get("/api/v1/admin/status")
async def get_admin_status():
    """Retourne le statut général du système."""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "ollama": ollama_status,
        "rag": rag_status,
        "database": {
            "available": True,
            "type": "SQLite"
        }
    }

@app.get("/api/v1/admin/conversations/stats")
async def get_conversation_stats():
    """Récupère les statistiques des conversations."""
    return conversation_db.get_conversation_stats()

# Nouveau: Endpoint pour choisir le pipeline
@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint de chat avec choix de pipeline.
    """
    try:
        # Choix automatique du pipeline basé sur la disponibilité
        use_langchain = bool(langchain_pipeline and LANGCHAIN_AVAILABLE)
        
        response, used_ollama, learned_from_history, used_rag, used_langchain = await generate_smart_response(
            message=request.message,
            session_id=request.session_id,
            conversation_history=request.conversation_history,
            use_langchain=use_langchain
        )
        
        # Sauvegarde conversation
        conversation_db.save_conversation(
            session_id=request.session_id,
            user_message=request.message,
            ai_response=response,
            metadata={
                "used_ollama": used_ollama,
                "learned_from_history": learned_from_history, 
                "used_rag": used_rag,
                "used_langchain": used_langchain,
                "pipeline": "langchain" if used_langchain else "classic"
            }
        )
        
        # Indicateurs visuels
        indicators = []
        if used_rag:
            indicators.append("📚 Informations des documents indexés")
        if learned_from_history:
            indicators.append("🧠 Contexte de conversations précédentes")
        if used_ollama:
            indicators.append("🤖 Réponse générée par Ollama")
        if used_langchain:
            indicators.append("🔗 Pipeline LangChain utilisé")
        
        return ChatResponse(
            answer=response,
            session_id=request.session_id,
            timestamp=datetime.now().isoformat(),
            indicators=indicators,
            metadata={
                "used_ollama": used_ollama,
                "learned_from_history": learned_from_history,
                "used_rag": used_rag,
                "used_langchain": used_langchain
            }
        )
        
    except Exception as e:
        print(f"Erreur chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Nouveau: Endpoint status LangChain
@app.get("/api/v1/langchain/status")
async def langchain_status():
    """Status du pipeline LangChain."""
    if not LANGCHAIN_AVAILABLE:
        return {"status": "unavailable", "reason": "LangChain non installé"}
    
    if not langchain_pipeline:
        return {"status": "not_initialized", "reason": "Pipeline non initialisé"}
    
    stats = langchain_pipeline.get_stats()
    return {
        "status": "active",
        "stats": stats,
        "available": True
    }

# Nouveau endpoint: Toggle mystique
@app.post("/api/v1/mystical/toggle")
async def toggle_mystical_mode(request: dict):
    """Active/désactive le mode mystique."""
    global mystical_mode, mystical_processor
    
    if not MYSTICAL_AVAILABLE:
        return {"error": "Module mystique non disponible"}
    
    enable = request.get("enable", True)
    intensity = request.get("intensity", 0.8)
    
    mystical_mode = enable
    
    if enable:
        mystical_processor = create_mystical_processor(intensity=intensity)
        message = f"🔮 Mode mystique ACTIVÉ (Intensité: {intensity})"
    else:
        mystical_processor = None
        message = "📝 Mode mystique DÉSACTIVÉ"
    
    print(message)
    
    return {
        "success": True,
        "mystical_mode": mystical_mode,
        "intensity": intensity if enable else None,
        "message": message
    }

@app.get("/api/v1/mystical/status")
async def get_mystical_status():
    """Statut du système mystique."""
    return {
        "available": MYSTICAL_AVAILABLE,
        "enabled": mystical_mode,
        "intensity": mystical_processor.style.mystical_intensity if mystical_processor else None,
        "persona": "Thoth-Hermès" if mystical_mode else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 