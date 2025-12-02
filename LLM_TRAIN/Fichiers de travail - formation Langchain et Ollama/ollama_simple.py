"""
Client Ollama simple pour le chatbot RAG.
"""

import json
import requests
from typing import List, Dict, Optional, Iterator
import asyncio
import aiohttp


class OllamaClient:
    """Client simple pour interagir avec Ollama."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
        self.base_url = base_url
        self.model = model
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtient une session HTTP async."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Ferme la session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def is_available(self) -> bool:
        """Vérifie si Ollama est disponible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_models(self) -> List[str]:
        """Récupère la liste des modèles disponibles."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except:
            pass
        return []
    
    def pull_model(self, model_name: str) -> bool:
        """Télécharge un modèle si nécessaire."""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=300
            )
            return response.status_code == 200
        except:
            return False
    
    def generate_sync(self, prompt: str, context: List[Dict] = None, 
                     system: str = None) -> Optional[str]:
        """Génère une réponse de façon synchrone."""
        try:
            messages = []
            
            if system:
                messages.append({"role": "system", "content": system})
            
            if context:
                messages.extend(context)
            
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            
        except Exception as e:
            print(f"Erreur Ollama sync: {e}")
        
        return None
    
    async def generate_async(self, prompt: str, context: List[Dict] = None,
                           system: str = None) -> Optional[str]:
        """Génère une réponse de façon asynchrone."""
        try:
            session = await self._get_session()
            
            messages = []
            
            if system:
                messages.append({"role": "system", "content": system})
            
            if context:
                messages.extend(context)
            
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("message", {}).get("content", "")
            
        except Exception as e:
            print(f"Erreur Ollama async: {e}")
        
        return None
    
    def generate_with_rag(self, user_question: str, context_documents: List[Dict],
                         conversation_history: List[Dict] = None,
                         past_conversations: List[Dict] = None) -> Optional[str]:
        """Génère une réponse avec contexte RAG."""
        
        # Construire le prompt système
        system_prompt = """Tu es un assistant intelligent avec accès à une base de connaissances.
Réponds en français de manière claire et précise.

INSTRUCTIONS IMPORTANTES :
1. UTILISE L'HISTORIQUE DE CONVERSATION pour te rappeler du contexte et des informations partagées précédemment
2. Si l'utilisateur fait référence à quelque chose dit plus tôt, cherche dans l'historique de conversation
3. Utilise les documents fournis pour enrichir tes réponses si pertinent
4. RÉPONDS TOUJOURS, même si les documents ne contiennent pas l'information - utilise ton intelligence et l'historique
5. Sois naturel et conversationnel, comme un assistant qui se souvient de tout

IMPORTANT POUR LES RÔLES :
- JE/MOI = TOI (l'assistant IA)
- VOUS/UTILISATEUR = L'UTILISATEUR qui pose la question
- Quand l'utilisateur dit "je suis Louis", retiens que L'UTILISATEUR s'appelle Louis
- Quand l'utilisateur demande "comment je m'appelle", réponds "Vous vous appelez Louis"

Tu as accès à l'historique complet de la conversation, utilise-le intelligemment."""
        
        # Construire le contexte
        context_text = ""
        if context_documents:
            context_text += "=== DOCUMENTS DISPONIBLES ===\n"
            for i, doc in enumerate(context_documents[:5], 1):
                context_text += f"\nDocument {i}:\n"
                context_text += f"Source: {doc.get('filename', 'Inconnu')}\n"
                content = doc.get('content', '')[:500]  # Limiter la taille
                context_text += f"Contenu: {content}...\n"
        
        # Ajouter les conversations passées pertinentes
        if past_conversations:
            context_text += "\n=== CONVERSATIONS PASSÉES PERTINENTES ===\n"
            for i, conv in enumerate(past_conversations[:3], 1):
                context_text += f"\nConversation {i}:\n"
                context_text += f"Q: {conv.get('user_question', '')[:100]}...\n"
                context_text += f"R: {conv.get('assistant_answer', '')[:200]}...\n"
        
        # Construire l'historique de conversation
        messages = []
        if conversation_history:
            for msg in conversation_history[-6:]:  # Garder les 6 derniers messages
                if msg.get('role') in ['user', 'assistant']:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
        
        # Construire le prompt final
        final_prompt = f"{context_text}\n\n=== QUESTION UTILISATEUR ===\n{user_question}"
        
        return self.generate_sync(
            prompt=final_prompt,
            context=messages,
            system=system_prompt
        )


# Instance globale
ollama_client = OllamaClient()


def init_ollama_client(base_url: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
    """Initialise le client Ollama."""
    global ollama_client
    ollama_client = OllamaClient(base_url, model)
    return ollama_client


def check_ollama_setup():
    """Vérifie et configure Ollama."""
    client = ollama_client
    
    if not client.is_available():
        return {
            "available": False,
            "error": "Ollama n'est pas accessible. Assurez-vous qu'il fonctionne sur localhost:11434"
        }
    
    models = client.get_models()
    
    if client.model not in models:
        print(f"Téléchargement du modèle {client.model}...")
        if client.pull_model(client.model):
            print(f"Modèle {client.model} téléchargé avec succès")
        else:
            return {
                "available": True,
                "models": models,
                "error": f"Impossible de télécharger le modèle {client.model}"
            }
    
    return {
        "available": True,
        "models": models,
        "current_model": client.model,
        "status": "ready"
    } 