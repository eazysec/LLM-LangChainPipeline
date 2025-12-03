"""
Pipeline LangChain simplifié et fonctionnel pour RAG
Sans dépendances relatives complexes
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

# LangChain imports
try:
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.llms import Ollama
    from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"❌ LangChain non disponible: {e}")
    LANGCHAIN_AVAILABLE = False

# Import du module mystique
try:
    from mystical_persona import (
        MysticalPersona, 
        MysticalResponseProcessor, 
        create_mystical_processor,
        enhance_langchain_with_mystical_persona
    )
    MYSTICAL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module mystique non disponible: {e}")
    MYSTICAL_AVAILABLE = False

logger = logging.getLogger(__name__)


class SimpleLangChainRAG:
    """
    Pipeline RAG simplifié avec LangChain natif
    + BONUS: Persona mystique de maître spirituel hermétique
    
    Architecture simplifiée:
    📚 PDF → 📄 Chunks → 🧠 Embeddings → 📊 FAISS → 🔍 Retriever → 🔗 Chain → 🔮 Mystical Transform
    """
    
    def __init__(self, 
                 data_path: str = "data/raw",
                 index_path: str = "data/processed/langchain_simple",
                 model_name: str = "qwen2.5:1.5b",
                 mystical_mode: bool = True,
                 mystical_intensity: float = 0.8):
        """
        Initialise le pipeline RAG simplifié avec persona mystique.
        
        Args:
            mystical_mode: Active la transformation mystique des réponses
            mystical_intensity: Niveau d'ésotérisme (0.0-1.0)
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain n'est pas disponible")
            
        self.data_path = Path(data_path)
        self.index_path = Path(index_path)
        self.model_name = model_name
        self.mystical_mode = mystical_mode
        self.mystical_intensity = mystical_intensity
        
        # Composants
        self.embeddings = None
        self.vector_store = None
        self.retriever = None
        self.llm = None
        self.chain = None
        
        # Composant mystique
        self.mystical_processor = None
        if mystical_mode and MYSTICAL_AVAILABLE:
            self.mystical_processor = create_mystical_processor(mystical_intensity)
        
        # Configuration
        self.chunk_size = 500
        self.chunk_overlap = 50
        self.top_k = 3
        
        print(f"🔗 Pipeline LangChain {'🔮 MYSTIQUE' if mystical_mode else 'Standard'} initialisé")
    
    async def initialize(self) -> bool:
        """Initialise tous les composants."""
        try:
            print("🚀 Initialisation LangChain simplifié...")
            
            # 1. Embeddings
            self._setup_embeddings()
            
            # 2. Vector Store
            await self._setup_vector_store()
            
            # 3. LLM
            self._setup_llm()
            
            # 4. Chain
            self._setup_chain()
            
            print("✅ Pipeline LangChain prêt")
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False
    
    def _setup_embeddings(self):
        """Configure les embeddings."""
        print("🧠 Configuration embeddings...")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        print("✅ Embeddings configurés")
    
    async def _setup_vector_store(self):
        """Configure le vector store."""
        try:
            # Essayer de charger existant
            if self.index_path.exists():
                print("📂 Chargement index existant...")
                self.vector_store = FAISS.load_local(
                    str(self.index_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"✅ Index chargé: {self.vector_store.index.ntotal} vecteurs")
            else:
                print("🔨 Création nouvel index...")
                await self._create_vector_store()
                
        except Exception as e:
            print(f"⚠️ Erreur chargement index: {e}")
            await self._create_vector_store()
    
    async def _create_vector_store(self):
        """Crée un nouvel index vectoriel."""
        print("📚 Chargement documents...")
        
        # Chargement PDFs
        documents = []
        if self.data_path.exists():
            for pdf_file in self.data_path.glob("*.pdf"):
                try:
                    loader = PyPDFLoader(str(pdf_file))
                    docs = loader.load()
                    documents.extend(docs)
                    print(f"📄 {pdf_file.name}: {len(docs)} pages")
                except Exception as e:
                    print(f"❌ Erreur {pdf_file.name}: {e}")
        
        if not documents:
            raise ValueError("Aucun document trouvé")
        
        # Chunking
        print("✂️ Découpage en chunks...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", " "]
        )
        
        chunks = splitter.split_documents(documents)
        print(f"📄 {len(chunks)} chunks créés")
        
        # Création index
        print("🔧 Création index FAISS...")
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        # Sauvegarde
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(self.index_path))
        
        print(f"✅ Index créé: {len(chunks)} chunks")
    
    def _setup_llm(self):
        """Configure le LLM Ollama avec prompt mystique."""
        print(f"🤖 Configuration LLM: {self.model_name}")
        
        self.llm = Ollama(
            model=self.model_name,
            temperature=0.1,
            num_ctx=4096
        )
        
        print("✅ LLM configuré")
    
    def _setup_chain(self):
        """Configure la chaîne RAG avec template mystique."""
        print("🔗 Configuration chaîne RAG...")
        
        # Retriever
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": self.top_k,
                "score_threshold": 0.3
            }
        )
        
        # Template mystique ou standard
        if self.mystical_mode and self.mystical_processor:
            template = self.mystical_processor.persona.get_mystical_prompt_template()
        else:
            # Template standard
            template = """
Tu es un assistant expert en ésotérisme, alchimie et traditions hermétiques.

Tu as accès aux textes anciens de John Dee et aux Tablettes de Thoth.

CONTEXTE:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Utilise UNIQUEMENT les informations du contexte fourni
2. Réponds en français de manière claire et érudite
3. Cite naturellement les sources quand tu mentionnes des informations
4. Si le contexte ne contient pas l'information, dis-le clairement

RÉPONSE:"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Chaîne RAG
        self.chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        style_msg = "🔮 MYSTIQUE" if self.mystical_mode else "Standard"
        print(f"✅ Chaîne RAG {style_msg} configurée")
    
    async def query(self, question: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Interroge le système RAG avec transformation mystique optionnelle.
        
        Args:
            question: Question utilisateur
            session_id: ID de session
            
        Returns:
            Réponse avec métadonnées (et transformation mystique si activée)
        """
        if not self.chain:
            raise ValueError("Pipeline non initialisé")
        
        try:
            print(f"❓ Question: {question}")
            
            # Exécution de la chaîne
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.chain({"query": question})
            )
            
            # Réponse de base
            base_response = {
                "answer": result["result"],
                "sources": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    }
                    for doc in result["source_documents"]
                ],
                "session_id": session_id,
                "metadata": {
                    "model": self.model_name,
                    "num_sources": len(result["source_documents"]),
                    "pipeline": "langchain_simple",
                    "mystical_mode": self.mystical_mode
                }
            }
            
            # Transformation mystique si activée
            if self.mystical_mode and self.mystical_processor:
                print("🔮 Application transformation mystique...")
                
                mystical_result = self.mystical_processor.process_langchain_response(
                    query=question,
                    response=result["result"],
                    sources=base_response["sources"]
                )
                
                # Fusion des résultats
                enhanced_response = {
                    **base_response,
                    "answer": mystical_result["mystical_answer"],
                    "sources": mystical_result["sacred_sources"],
                    "mystical_metadata": mystical_result["spiritual_metadata"],
                    "hermetic_topic": mystical_result["hermetic_topic"]
                }
                
                print(f"✨ Réponse mystique générée (Sujet: {mystical_result['hermetic_topic']})")
                return enhanced_response
            
            else:
                print(f"✅ Réponse standard générée avec {len(base_response['sources'])} sources")
                return base_response
            
        except Exception as e:
            print(f"❌ Erreur query: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du pipeline avec info mystique."""
        base_stats = {
            "vector_store_size": self.vector_store.index.ntotal if self.vector_store else 0,
            "model_name": self.model_name,
            "chunk_size": self.chunk_size,
            "top_k": self.top_k,
            "status": "ready" if self.chain else "not_ready"
        }
        
        if self.mystical_mode:
            base_stats.update({
                "mystical_mode": True,
                "mystical_intensity": self.mystical_intensity,
                "spiritual_enhancement": "Thoth-Hermès Persona Active",
                "consciousness_level": "Elevated Wisdom State"
            })
        
        return base_stats

    def toggle_mystical_mode(self, enable: bool = True, intensity: float = None):
        """
        Active/désactive le mode mystique à la volée.
        
        Args:
            enable: Activer le mode mystique
            intensity: Nouveau niveau d'intensité (optionnel)
        """
        if not MYSTICAL_AVAILABLE:
            print("⚠️ Module mystique non disponible")
            return
        
        self.mystical_mode = enable
        
        if enable:
            if intensity is not None:
                self.mystical_intensity = intensity
            
            self.mystical_processor = create_mystical_processor(self.mystical_intensity)
            print(f"🔮 Mode mystique ACTIVÉ (Intensité: {self.mystical_intensity})")
            
            # Reconfigurer la chaîne avec le template mystique
            self._setup_chain()
        else:
            self.mystical_processor = None
            print("📝 Mode mystique DÉSACTIVÉ - Retour mode standard")
            
            # Reconfigurer la chaîne avec le template standard
            self._setup_chain()


# Fonction helper mise à jour
async def create_simple_langchain_rag(mystical_mode: bool = True, 
                                     mystical_intensity: float = 0.8,
                                     **kwargs) -> SimpleLangChainRAG:
    """
    Crée et initialise un pipeline RAG simplifié avec persona mystique.
    
    Args:
        mystical_mode: Activer la transformation mystique
        mystical_intensity: Niveau d'ésotérisme (0.0-1.0)
    
    Usage:
        # Mode mystique intense
        pipeline = await create_simple_langchain_rag(mystical_mode=True, mystical_intensity=0.9)
        
        # Mode standard
        pipeline = await create_simple_langchain_rag(mystical_mode=False)
        
        result = await pipeline.query("Question sur John Dee")
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain non disponible")
    
    pipeline = SimpleLangChainRAG(
        mystical_mode=mystical_mode,
        mystical_intensity=mystical_intensity,
        **kwargs
    )
    success = await pipeline.initialize()
    
    if not success:
        raise RuntimeError("Échec initialisation pipeline")
    
    return pipeline


# Test du pipeline mystique
async def test_mystical_pipeline():
    """Test complet du pipeline mystique."""
    try:
        print("🧪 Test pipeline LangChain MYSTIQUE...")
        
        # Test mode mystique intense
        mystical_pipeline = await create_simple_langchain_rag(
            mystical_mode=True, 
            mystical_intensity=0.9
        )
        
        # Test question ésotérique
        result = await mystical_pipeline.query(
            "Révèle-moi les secrets alchimiques de John Dee"
        )
        
        print("🔮 RÉPONSE MYSTIQUE :")
        print(result['answer'][:500] + "...")
        print(f"\n📚 Sources sacrées: {len(result['sources'])}")
        print(f"🌟 Sujet hermétique: {result.get('hermetic_topic', 'Mystères')}")
        print(f"📊 Stats: {mystical_pipeline.get_stats()}")
        
        # Test basculement vers mode standard
        print("\n" + "="*50)
        print("🔄 Test basculement vers mode standard...")
        
        mystical_pipeline.toggle_mystical_mode(enable=False)
        
        result_standard = await mystical_pipeline.query(
            "Parle-moi de John Dee"
        )
        
        print("📝 RÉPONSE STANDARD :")
        print(result_standard['answer'][:300] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_mystical_pipeline()) 