"""
Client Ollama pour la génération de texte avec le modèle Qwen.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Generator
import ollama
from ollama import AsyncClient, Client
import json
import time

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client pour interagir avec Ollama et le modèle Qwen."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le client Ollama.
        
        Args:
            config: Configuration du client
        """
        self.config = config
        self.base_url = config.get('base_url', 'http://100.64.0.34:11434')
        self.model_name = config.get('model_name', 'llama3:latest')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2048)
        self.timeout = config.get('timeout', 60)
        
        # Clients Ollama
        self.client = Client(host=self.base_url)
        self.async_client = AsyncClient(host=self.base_url)
        
        # Vérifier la disponibilité du modèle
        self._check_model_availability()
        
        logger.info(f"Client Ollama initialisé - Modèle: {self.model_name}")
    
    def _check_model_availability(self):
        """Vérifie si le modèle est disponible."""
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            
            if self.model_name not in available_models:
                logger.warning(f"Modèle {self.model_name} non trouvé. Modèles disponibles: {available_models}")
                
                # Essayer de télécharger le modèle
                logger.info(f"Tentative de téléchargement du modèle {self.model_name}...")
                try:
                    self.client.pull(self.model_name)
                    logger.info(f"Modèle {self.model_name} téléchargé avec succès")
                except Exception as e:
                    logger.error(f"Erreur lors du téléchargement du modèle: {e}")
                    raise
            else:
                logger.info(f"Modèle {self.model_name} disponible")
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du modèle: {e}")
            # Continuer sans vérification en mode dégradé
    
    def generate(self, prompt: str, 
                system_prompt: Optional[str] = None,
                context: Optional[List[Dict[str, str]]] = None,
                **kwargs) -> str:
        """
        Génère une réponse à partir d'un prompt.
        
        Args:
            prompt: Prompt utilisateur
            system_prompt: Prompt système optionnel
            context: Contexte de conversation optionnel
            **kwargs: Arguments supplémentaires
            
        Returns:
            Réponse générée
        """
        try:
            # Construire les messages
            messages = []
            
            # Ajouter le prompt système
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })
            
            # Ajouter le contexte de conversation
            if context:
                messages.extend(context)
            
            # Ajouter le prompt utilisateur
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            # Paramètres de génération
            options = {
                'temperature': kwargs.get('temperature', self.temperature),
                'top_p': kwargs.get('top_p', 0.9),
                'top_k': kwargs.get('top_k', 40),
                'num_predict': kwargs.get('max_tokens', self.max_tokens),
            }
            
            # Générer la réponse
            start_time = time.time()
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options=options
            )
            
            generation_time = time.time() - start_time
            
            # Extraire le contenu de la réponse
            if response and 'message' in response:
                content = response['message']['content']
                
                logger.info(f"Génération terminée en {generation_time:.2f}s - {len(content)} caractères")
                return content
            else:
                logger.error("Réponse vide ou malformée")
                return "Désolé, je n'ai pas pu générer une réponse."
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            return f"Erreur lors de la génération: {str(e)}"
    
    async def generate_async(self, prompt: str,
                           system_prompt: Optional[str] = None,
                           context: Optional[List[Dict[str, str]]] = None,
                           **kwargs) -> str:
        """
        Génère une réponse de manière asynchrone.
        
        Args:
            prompt: Prompt utilisateur
            system_prompt: Prompt système optionnel
            context: Contexte de conversation optionnel
            **kwargs: Arguments supplémentaires
            
        Returns:
            Réponse générée
        """
        try:
            # Construire les messages
            messages = []
            
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })
            
            if context:
                messages.extend(context)
            
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            # Paramètres de génération
            options = {
                'temperature': kwargs.get('temperature', self.temperature),
                'top_p': kwargs.get('top_p', 0.9),
                'top_k': kwargs.get('top_k', 40),
                'num_predict': kwargs.get('max_tokens', self.max_tokens),
            }
            
            # Générer la réponse
            start_time = time.time()
            response = await self.async_client.chat(
                model=self.model_name,
                messages=messages,
                options=options
            )
            
            generation_time = time.time() - start_time
            
            if response and 'message' in response:
                content = response['message']['content']
                logger.info(f"Génération async terminée en {generation_time:.2f}s")
                return content
            else:
                return "Désolé, je n'ai pas pu générer une réponse."
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération async: {e}")
            return f"Erreur lors de la génération: {str(e)}"
    
    def generate_stream(self, prompt: str,
                       system_prompt: Optional[str] = None,
                       context: Optional[List[Dict[str, str]]] = None,
                       **kwargs) -> Generator[str, None, None]:
        """
        Génère une réponse en streaming.
        
        Args:
            prompt: Prompt utilisateur
            system_prompt: Prompt système optionnel
            context: Contexte de conversation optionnel
            **kwargs: Arguments supplémentaires
            
        Yields:
            Chunks de la réponse
        """
        try:
            # Construire les messages
            messages = []
            
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })
            
            if context:
                messages.extend(context)
            
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            # Paramètres de génération
            options = {
                'temperature': kwargs.get('temperature', self.temperature),
                'top_p': kwargs.get('top_p', 0.9),
                'top_k': kwargs.get('top_k', 40),
                'num_predict': kwargs.get('max_tokens', self.max_tokens),
            }
            
            # Générer en streaming
            stream = self.client.chat(
                model=self.model_name,
                messages=messages,
                options=options,
                stream=True
            )
            
            for chunk in stream:
                if chunk and 'message' in chunk:
                    content = chunk['message']['content']
                    if content:
                        yield content
                        
        except Exception as e:
            logger.error(f"Erreur lors du streaming: {e}")
            yield f"Erreur lors de la génération: {str(e)}"
    
    async def generate_stream_async(self, prompt: str,
                                  system_prompt: Optional[str] = None,
                                  context: Optional[List[Dict[str, str]]] = None,
                                  **kwargs) -> AsyncGenerator[str, None]:
        """
        Génère une réponse en streaming asynchrone.
        
        Args:
            prompt: Prompt utilisateur
            system_prompt: Prompt système optionnel
            context: Contexte de conversation optionnel
            **kwargs: Arguments supplémentaires
            
        Yields:
            Chunks de la réponse
        """
        try:
            # Construire les messages
            messages = []
            
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })
            
            if context:
                messages.extend(context)
            
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            # Paramètres de génération
            options = {
                'temperature': kwargs.get('temperature', self.temperature),
                'top_p': kwargs.get('top_p', 0.9),
                'top_k': kwargs.get('top_k', 40),
                'num_predict': kwargs.get('max_tokens', self.max_tokens),
            }
            
            # Générer en streaming async
            stream = await self.async_client.chat(
                model=self.model_name,
                messages=messages,
                options=options,
                stream=True
            )
            
            async for chunk in stream:
                if chunk and 'message' in chunk:
                    content = chunk['message']['content']
                    if content:
                        yield content
                        
        except Exception as e:
            logger.error(f"Erreur lors du streaming async: {e}")
            yield f"Erreur lors de la génération: {str(e)}"
    
    def build_rag_prompt(self, question: str, 
                        context_chunks: List[str],
                        conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Construit un prompt RAG avec contexte et historique.
        
        Args:
            question: Question de l'utilisateur
            context_chunks: Chunks de contexte pertinents
            conversation_history: Historique de conversation
            
        Returns:
            Prompt RAG formaté
        """
        try:
            # Construire le contexte
            context_text = ""
            if context_chunks:
                context_text = "\n\n".join([f"Document {i+1}:\n{chunk}" 
                                          for i, chunk in enumerate(context_chunks)])
            
            # Construire l'historique
            history_text = ""
            if conversation_history:
                recent_history = conversation_history[-3:]  # 3 derniers échanges
                history_parts = []
                for msg in recent_history:
                    role = "Utilisateur" if msg.get('role') == 'user' else "Assistant"
                    content = msg.get('content', '')
                    history_parts.append(f"{role}: {content}")
                history_text = "\n".join(history_parts)
            
            # Template de prompt RAG
            prompt_template = """Tu es un assistant IA intelligent spécialisé dans l'analyse de documents. 
Utilise les informations fournies ci-dessous pour répondre à la question de l'utilisateur.

{history_section}

CONTEXTE PERTINENT:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Base ta réponse principalement sur les informations fournies dans le contexte
2. Si l'information n'est pas dans le contexte, indique-le clairement
3. Sois précis, informatif et utile
4. Si tu mentionnes des informations spécifiques, cite le document source quand c'est pertinent
5. Réponds en français de manière naturelle et conversationnelle

RÉPONSE:"""

            # Ajouter la section historique si disponible
            history_section = ""
            if history_text:
                history_section = f"HISTORIQUE DE CONVERSATION:\n{history_text}\n"
            
            # Construire le prompt final
            prompt = prompt_template.format(
                history_section=history_section,
                context=context_text if context_text else "Aucun contexte spécifique trouvé.",
                question=question
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Erreur lors de la construction du prompt RAG: {e}")
            return f"Question: {question}\n\nRéponse: Erreur lors de la préparation de la réponse."
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retourne les informations du modèle."""
        try:
            models = self.client.list()
            model_info = None
            
            for model in models['models']:
                if model['name'] == self.model_name:
                    model_info = model
                    break
            
            return {
                'model_name': self.model_name,
                'base_url': self.base_url,
                'temperature': self.temperature,
                'max_tokens': self.max_tokens,
                'model_info': model_info,
                'available': model_info is not None
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos modèle: {e}")
            return {
                'model_name': self.model_name,
                'base_url': self.base_url,
                'available': False,
                'error': str(e)
            }
    
    def health_check(self) -> bool:
        """Vérifie la santé du client Ollama."""
        try:
            # Test simple de génération
            response = self.client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': 'Test'}],
                options={'num_predict': 10}
            )
            
            return response is not None and 'message' in response
            
        except Exception as e:
            logger.error(f"Health check échoué: {e}")
            return False


# Fonctions utilitaires
def create_ollama_client(config: Dict[str, Any]) -> OllamaClient:
    """
    Crée un client Ollama depuis une configuration.
    
    Args:
        config: Configuration du client
        
    Returns:
        Instance du client Ollama
    """
    return OllamaClient(config)


def test_ollama_connection(base_url: str = 'http://100.64.0.34:11434') -> bool:
    """
    Teste la connexion à Ollama.
    
    Args:
        base_url: URL de base d'Ollama
        
    Returns:
        True si la connexion fonctionne
    """
    try:
        client = Client(host=base_url)
        models = client.list()
        return True
    except Exception as e:
        logger.error(f"Test de connexion Ollama échoué: {e}")
        return False


def download_model(model_name: str, base_url: str = 'http://100.64.0.34:11434') -> bool:
    """
    Télécharge un modèle Ollama.
    
    Args:
        model_name: Nom du modèle à télécharger
        base_url: URL de base d'Ollama
        
    Returns:
        True si le téléchargement réussit
    """
    try:
        client = Client(host=base_url)
        logger.info(f"Téléchargement du modèle {model_name}...")
        
        # Télécharger avec callback de progression
        def progress_callback(progress):
            if progress.get('status') == 'downloading':
                completed = progress.get('completed', 0)
                total = progress.get('total', 1)
                percent = (completed / total) * 100
                logger.info(f"Téléchargement: {percent:.1f}%")
        
        client.pull(model_name, stream=True)
        logger.info(f"Modèle {model_name} téléchargé avec succès")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du modèle: {e}")
        return False 