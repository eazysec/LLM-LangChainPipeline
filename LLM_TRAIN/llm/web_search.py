"""
Client de recherche web pour enrichir les réponses du chatbot.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
import aiohttp
import requests
from duckduckgo_search import DDGS
import time
from urllib.parse import quote_plus
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSearchResult:
    """Résultat de recherche web."""
    
    def __init__(self, title: str, url: str, snippet: str, source: str = "web"):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'source': self.source,
            'timestamp': self.timestamp.isoformat()
        }


class WebSearchClient:
    """Client pour effectuer des recherches web."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le client de recherche web.
        
        Args:
            config: Configuration du client
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.max_results = self.config.get('max_results', 3)
        self.timeout = self.config.get('timeout', 10)
        self.user_agent = self.config.get('user_agent', 
                                        'Mozilla/5.0 (compatible; RAG-Bot/1.0)')
        
        # Filtres pour les domaines
        self.blocked_domains = self.config.get('blocked_domains', [
            'facebook.com', 'twitter.com', 'instagram.com', 'tiktok.com'
        ])
        
        self.preferred_domains = self.config.get('preferred_domains', [
            'wikipedia.org', 'stackoverflow.com', 'github.com'
        ])
        
        logger.info(f"Client de recherche web initialisé - Activé: {self.enabled}")
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[WebSearchResult]:
        """
        Effectue une recherche web.
        
        Args:
            query: Requête de recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste des résultats de recherche
        """
        if not self.enabled:
            logger.info("Recherche web désactivée")
            return []
        
        max_results = max_results or self.max_results
        
        try:
            logger.info(f"Recherche web: '{query}'")
            start_time = time.time()
            
            # Utiliser DuckDuckGo pour la recherche
            results = self._search_duckduckgo(query, max_results)
            
            # Filtrer et nettoyer les résultats
            filtered_results = self._filter_results(results)
            
            search_time = time.time() - start_time
            logger.info(f"Recherche terminée en {search_time:.2f}s - {len(filtered_results)} résultats")
            
            return filtered_results[:max_results]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche web: {e}")
            return []
    
    async def search_async(self, query: str, max_results: Optional[int] = None) -> List[WebSearchResult]:
        """
        Effectue une recherche web asynchrone.
        
        Args:
            query: Requête de recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste des résultats de recherche
        """
        if not self.enabled:
            return []
        
        max_results = max_results or self.max_results
        
        try:
            # Exécuter la recherche dans un thread séparé
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self.search, query, max_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche web async: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[WebSearchResult]:
        """Recherche avec DuckDuckGo."""
        results = []
        
        try:
            with DDGS() as ddgs:
                # Recherche de texte
                search_results = ddgs.text(
                    query,
                    max_results=max_results * 2,  # Récupérer plus pour filtrer
                    safesearch='moderate'
                )
                
                for result in search_results:
                    web_result = WebSearchResult(
                        title=result.get('title', ''),
                        url=result.get('href', ''),
                        snippet=result.get('body', ''),
                        source='duckduckgo'
                    )
                    results.append(web_result)
                    
        except Exception as e:
            logger.error(f"Erreur DuckDuckGo: {e}")
        
        return results
    
    def _filter_results(self, results: List[WebSearchResult]) -> List[WebSearchResult]:
        """Filtre et améliore les résultats de recherche."""
        filtered = []
        seen_urls = set()
        
        for result in results:
            # Éviter les doublons
            if result.url in seen_urls:
                continue
            seen_urls.add(result.url)
            
            # Filtrer les domaines bloqués
            if any(domain in result.url for domain in self.blocked_domains):
                continue
            
            # Nettoyer le snippet
            result.snippet = self._clean_snippet(result.snippet)
            
            # Vérifier la qualité du contenu
            if self._is_quality_result(result):
                filtered.append(result)
        
        # Trier par préférence de domaine
        filtered.sort(key=self._result_score, reverse=True)
        
        return filtered
    
    def _clean_snippet(self, snippet: str) -> str:
        """Nettoie un snippet de recherche."""
        if not snippet:
            return ""
        
        # Supprimer les balises HTML restantes
        snippet = re.sub(r'<[^>]+>', '', snippet)
        
        # Supprimer les caractères spéciaux en excès
        snippet = re.sub(r'\s+', ' ', snippet)
        
        # Limiter la longueur
        if len(snippet) > 300:
            snippet = snippet[:297] + "..."
        
        return snippet.strip()
    
    def _is_quality_result(self, result: WebSearchResult) -> bool:
        """Évalue la qualité d'un résultat."""
        # Vérifier la longueur minimale du snippet
        if len(result.snippet) < 50:
            return False
        
        # Vérifier que le titre n'est pas vide
        if not result.title.strip():
            return False
        
        # Vérifier l'URL
        if not result.url.startswith(('http://', 'https://')):
            return False
        
        return True
    
    def _result_score(self, result: WebSearchResult) -> float:
        """Calcule un score de qualité pour un résultat."""
        score = 0.0
        
        # Bonus pour les domaines préférés
        for domain in self.preferred_domains:
            if domain in result.url:
                score += 10.0
                break
        
        # Score basé sur la longueur du snippet
        snippet_length = len(result.snippet)
        score += min(snippet_length / 100, 5.0)
        
        # Bonus pour certains mots-clés dans le titre
        quality_keywords = ['guide', 'tutorial', 'documentation', 'how to', 'comment']
        title_lower = result.title.lower()
        for keyword in quality_keywords:
            if keyword in title_lower:
                score += 2.0
        
        return score
    
    def should_search_web(self, query: str, rag_confidence: float = 0.0) -> bool:
        """
        Détermine si une recherche web est nécessaire.
        
        Args:
            query: Requête utilisateur
            rag_confidence: Confiance du système RAG (0-1)
            
        Returns:
            True si une recherche web est recommandée
        """
        if not self.enabled:
            return False
        
        # Seuil de confiance configuré
        confidence_threshold = self.config.get('fallback_threshold', 0.5)
        
        # Rechercher si la confiance RAG est faible
        if rag_confidence < confidence_threshold:
            return True
        
        # Mots-clés indiquant une recherche d'actualités
        current_keywords = [
            'aujourd\'hui', 'maintenant', 'récent', 'nouveau', 'dernière',
            'actualité', 'news', 'current', 'latest', '2024', '2025'
        ]
        
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in current_keywords):
            return True
        
        # Questions sur des événements récents
        recent_patterns = [
            r'que se passe-t-il',
            r'quoi de neuf',
            r'dernières nouvelles',
            r'mise à jour'
        ]
        
        for pattern in recent_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def format_web_results(self, results: List[WebSearchResult]) -> str:
        """
        Formate les résultats web pour inclusion dans une réponse.
        
        Args:
            results: Résultats de recherche web
            
        Returns:
            Texte formaté des résultats
        """
        if not results:
            return ""
        
        formatted_parts = []
        formatted_parts.append("INFORMATIONS RÉCENTES DU WEB:")
        
        for i, result in enumerate(results, 1):
            formatted_parts.append(f"\n{i}. **{result.title}**")
            formatted_parts.append(f"   {result.snippet}")
            formatted_parts.append(f"   Source: {result.url}")
        
        return "\n".join(formatted_parts)
    
    def extract_key_info(self, results: List[WebSearchResult], query: str) -> str:
        """
        Extrait les informations clés des résultats pour une requête.
        
        Args:
            results: Résultats de recherche
            query: Requête originale
            
        Returns:
            Informations clés extraites
        """
        if not results:
            return ""
        
        # Combiner tous les snippets
        all_text = " ".join([result.snippet for result in results])
        
        # Extraire les phrases les plus pertinentes
        sentences = re.split(r'[.!?]+', all_text)
        query_words = set(query.lower().split())
        
        relevant_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Calculer la pertinence
            sentence_words = set(sentence.lower().split())
            relevance = len(query_words & sentence_words) / len(query_words)
            
            if relevance > 0.2:  # Au moins 20% des mots de la requête
                relevant_sentences.append((sentence, relevance))
        
        # Trier par pertinence et prendre les meilleures
        relevant_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in relevant_sentences[:3]]
        
        return " ".join(top_sentences) if top_sentences else all_text[:500]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du client de recherche."""
        return {
            'enabled': self.enabled,
            'max_results': self.max_results,
            'timeout': self.timeout,
            'blocked_domains_count': len(self.blocked_domains),
            'preferred_domains_count': len(self.preferred_domains)
        }


# Fonctions utilitaires
def create_web_search_client(config: Optional[Dict[str, Any]] = None) -> WebSearchClient:
    """
    Crée un client de recherche web.
    
    Args:
        config: Configuration du client
        
    Returns:
        Instance du client de recherche
    """
    return WebSearchClient(config)


def test_web_search(query: str = "test") -> bool:
    """
    Teste la fonctionnalité de recherche web.
    
    Args:
        query: Requête de test
        
    Returns:
        True si la recherche fonctionne
    """
    try:
        client = WebSearchClient()
        results = client.search(query, max_results=1)
        return len(results) > 0
    except Exception as e:
        logger.error(f"Test de recherche web échoué: {e}")
        return False


def search_and_summarize(query: str, max_results: int = 3) -> str:
    """
    Effectue une recherche et résume les résultats.
    
    Args:
        query: Requête de recherche
        max_results: Nombre de résultats
        
    Returns:
        Résumé des résultats de recherche
    """
    try:
        client = WebSearchClient()
        results = client.search(query, max_results)
        
        if not results:
            return "Aucun résultat trouvé pour cette recherche."
        
        # Créer un résumé
        summary_parts = [f"Voici ce que j'ai trouvé sur '{query}':"]
        
        for i, result in enumerate(results, 1):
            summary_parts.append(f"\n{i}. {result.title}")
            summary_parts.append(f"   {result.snippet[:150]}...")
        
        return "\n".join(summary_parts)
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche et résumé: {e}")
        return f"Erreur lors de la recherche: {str(e)}" 