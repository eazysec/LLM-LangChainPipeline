# 📚 Guide d'Indexation des Documents - RAG ChatBot

Ce guide explique comment indexer votre base documentaire avec FAISS et ChromaDB pour alimenter votre système RAG (Retrieval-Augmented Generation).

## 🎯 Vue d'ensemble

Le système d'indexation transforme vos documents (PDFs, TXT, DOCX, MD) en base de connaissances vectorielle que votre ChatBot peut interroger intelligemment.

### 🔄 Pipeline d'indexation

```
📄 Documents → 🔪 Chunking → 🧠 Embeddings → 📊 Index Vectoriel → 🔍 Recherche
```

## 🏗️ Architecture

### 📁 Structure des fichiers

```
data/
├── raw/                          # 📚 Documents sources
│   ├── john-dees-five-books.pdf
│   └── pdf_tablette_thoth.pdf
├── processed/                    # 📊 Données traitées
│   ├── indexes/                  # 🗂️ Index vectoriels
│   │   ├── faiss_index.bin      # FAISS binary index
│   │   ├── faiss_metadata.json  # Métadonnées FAISS
│   │   └── chroma_db/           # Base ChromaDB
│   └── indexation_stats.json    # 📈 Statistiques
└── conversations.db              # 💬 Historique conversations
```

### 🛠️ Composants clés

1. **DocumentLoader** (`ingestion/loaders.py`)
   - Charge PDFs, DOCX, TXT, MD
   - Extrait le texte brut
   - Ajoute les métadonnées

2. **DocumentChunker** (`ingestion/chunking.py`)
   - Découpe en chunks de 500 caractères
   - Overlap de 50 caractères
   - Préserve le contexte sémantique

3. **EmbeddingModel** (`embeddings/embedding_model.py`)
   - Modèle: `sentence-transformers/all-MiniLM-L6-v2`
   - Vecteurs de 384 dimensions
   - Support CPU/GPU

4. **VectorIndexBuilder** (`embeddings/build_index.py`)
   - FAISS: Index L2 (distance euclidienne)
   - ChromaDB: Base vectorielle avec persistance
   - Métadonnées enrichies

## 🚀 Utilisation

### 1️⃣ Indexation automatique

```bash
# Activer l'environnement virtuel
source /home/louto/env/langchain_llm_training/bin/activate

# Indexer tous les documents dans data/raw
python scripts/index_documents.py

# Options avancées
python scripts/index_documents.py --verbose --directory custom_dir
```

### 2️⃣ Configuration personnalisée

Créer un fichier `config.json` :

```json
{
  "chunking": {
    "chunk_size": 800,        # Taille des chunks
    "chunk_overlap": 100,     # Chevauchement
    "min_chunk_size": 100     # Taille minimale
  },
  "embedding": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "device": "cpu"           # ou "cuda"
  },
  "indexes": {
    "faiss": {
      "index_path": "custom/path/faiss_index.bin"
    },
    "chroma": {
      "persist_directory": "custom/path/chroma_db"
    }
  }
}
```

```bash
python scripts/index_documents.py --config config.json
```

## 🔍 Test et Recherche

### 3️⃣ Tester l'index créé

```bash
# Test complet (FAISS + ChromaDB)
python scripts/test_search.py "mystères alchimiques"

# Test FAISS uniquement
python scripts/test_search.py "tablette de Thoth" --engine faiss

# Test ChromaDB uniquement  
python scripts/test_search.py "john dee" --engine chroma --results 10
```

### 4️⃣ Exemple de sortie

```
🔍 Test FAISS - Recherche: 'mystères alchimiques'
📊 FAISS - 5 résultats trouvés:
  1. Score: 0.7234
     Source: john-dees-five-books.pdf
     Chunk: Les mystères de l'alchimie révèlent des secrets anciens...
     --------------------------------------------------
  2. Score: 0.6891
     Source: pdf_tablette_thoth.pdf  
     Chunk: La tablette contient des formules alchimiques...
```

## 🔧 Mécanismes techniques

### 📊 FAISS (Facebook AI Similarity Search)

**Avantages :**
- ⚡ Très rapide (optimisé C++)
- 🎯 Précision élevée
- 💾 Faible consommation mémoire
- 🔧 Contrôle fin des paramètres

**Fonctionnement :**
1. Crée un index L2 (distance euclidienne)
2. Stockage binaire optimisé
3. Métadonnées séparées en JSON

### 🔮 ChromaDB

**Avantages :**
- 🔄 Base de données complète
- 📝 Métadonnées riches
- 🔍 Filtrage avancé
- 🔒 Persistance automatique

**Fonctionnement :**
1. Embedding automatique intégré
2. Stockage SQLite + index vectoriel
3. API simple et intuitive

### 🧠 Embeddings (Sentence Transformers)

**Modèle utilisé :** `all-MiniLM-L6-v2`
- 📐 384 dimensions
- 🏃‍♂️ Rapide et efficace
- 🌍 Multilingue (français supporté)
- 🎯 Optimisé pour la similarité sémantique

**Processus :**
```python
text = "Les mystères alchimiques..."
embedding = model.encode(text)  # → [0.1, -0.3, 0.7, ...]
```

### ✂️ Chunking intelligent

**Stratégie de découpage :**
1. Priorité aux paragraphes (`\n\n`)
2. Puis phrases (`. `)
3. Puis mots (` `)
4. Respect de la taille max (500 chars)
5. Overlap pour préserver le contexte

**Exemple :**
```
Chunk 1: "Les mystères de l'alchimie révèlent..." (450 chars)
Chunk 2: "...révèlent des secrets anciens. La transmutation..." (500 chars)
         └── Overlap de 50 chars ──┘
```

## 📈 Métriques et Performance

### 📊 Statistiques générées

Le script génère automatiquement `data/processed/indexation_stats.json` :

```json
{
  "documents_processed": 2,
  "chunks_created": 156,
  "processing_time": 12.34,
  "files_processed": [
    "data/raw/john-dees-five-books.pdf",
    "data/raw/pdf_tablette_thoth.pdf"
  ]
}
```

### ⚡ Performance estimée

| Métrique | FAISS | ChromaDB |
|----------|-------|----------|
| **Recherche** | ~1ms | ~10ms |
| **Indexation** | ~100ms/doc | ~500ms/doc |
| **Mémoire** | Faible | Moyenne |
| **Précision** | Élevée | Très élevée |

## 🔗 Intégration avec le ChatBot

### 🤖 Utilisation dans le RAG

```python
# Dans ollama_simple.py
def generate_with_rag(user_question, context_documents, ...):
    # 1. Recherche dans l'index
    relevant_chunks = search_index(user_question, k=5)
    
    # 2. Construction du contexte
    context = "\n".join([chunk['content'] for chunk in relevant_chunks])
    
    # 3. Prompt augmenté
    prompt = f"""
    Contexte documentaire :
    {context}
    
    Question : {user_question}
    Réponse :
    """
```

### 🔄 Mise à jour automatique

Pour ajouter de nouveaux documents :

```bash
# 1. Placer les nouveaux PDFs dans data/raw/
cp nouveau_livre.pdf data/raw/

# 2. Re-indexer (conserve l'existant)
python scripts/index_documents.py

# 3. Tester
python scripts/test_search.py "nouveau concept"
```

## 🐛 Résolution de problèmes

### ❌ Erreurs courantes

**"No module named 'faiss'"**
```bash
pip install faiss-cpu  # ou faiss-gpu si CUDA
```

**"ChromaDB collection not found"**
```bash
# Supprimer et recréer l'index
rm -rf data/processed/indexes/chroma_db
python scripts/index_documents.py
```

**"PDF parsing error"**
- Vérifier que le PDF n'est pas corrompu
- Essayer avec un autre extracteur PDF

### 🔧 Debug

```bash
# Mode verbeux
python scripts/index_documents.py --verbose

# Logs détaillés
tail -f indexation.log
```

## 📚 Vos Documents Actuels

### 📖 Livres indexés

1. **john-dees-five-books-of-myster-joseph-h-peterson.pdf** (6.3MB)
   - Mystères alchimiques de John Dee
   - Magie énochienne et rituels

2. **pdf_tablette_thoth.pdf** (684KB)
   - Tablette de Thoth
   - Sagesse hermétique ancienne

### 🎯 Requêtes suggérées

```bash
# Alchimie et transmutation
python scripts/test_search.py "transmutation des métaux"

# Magie énochienne
python scripts/test_search.py "anges énochiens"

# Sagesse hermétique
python scripts/test_search.py "hermès trismégiste"

# Rituels et invocations
python scripts/test_search.py "rituel d'invocation"
```

## 🚀 Prochaines étapes

1. **Indexer vos livres** maintenant
2. **Tester** les recherches
3. **Intégrer** au ChatBot RAG
4. **Ajouter** d'autres documents selon vos besoins

---

🎉 **Votre base documentaire vectorielle est prête !** 

Votre ChatBot pourra maintenant puiser dans la sagesse de John Dee et des tablettes de Thoth pour répondre à vos questions ésotériques ! ✨ 