# ChatBot RAG avec Ollama et Qwen

Un chatbot intelligent utilisant la technique RAG (Retrieval-Augmented Generation) avec le modèle Qwen via Ollama, incluant la recherche web et l'historique des conversations.

## 🚀 Fonctionnalités

- **Chat intelligent** : Conversations avec mémoire contextuelle
- **RAG (Retrieval-Augmented Generation)** : Réponses basées sur vos documents
- **Recherche web** : Complément automatique avec DuckDuckGo
- **Support multi-formats** : PDF, TXT, MD, DOCX
- **API FastAPI** : Interface REST complète
- **Interface d'administration** : Monitoring et configuration
- **Embeddings vectoriels** : ChromaDB + Sentence Transformers
- **Streaming** : Réponses en temps réel
- **Historique persistant** : Sessions de conversation

## 📋 Prérequis

- Python 3.8+
- Ollama installé et configuré
- 4GB+ de RAM recommandés

## 🛠️ Installation

### 1. Cloner le projet

```bash
git clone <votre-repo>
cd chatbot_chatgpt
```

### 2. Créer l'environnement virtuel

```bash
python -m venv /home/louto/env/langchain_llm_training
source /home/louto/env/langchain_llm_training/bin/activate  # Linux/Mac
# ou
/home/louto/env/langchain_llm_training/Scripts/activate  # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Installer et configurer Ollama

```bash
# Installer Ollama (voir https://ollama.com)
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger le modèle Qwen
ollama pull qwen2.5:latest

# Démarrer Ollama
ollama serve
```

### 5. Configuration

Copiez et adaptez le fichier de configuration :

```bash
cp configs/settings.yaml.example configs/settings.yaml
# Éditez le fichier selon vos besoins
```

## 🚀 Démarrage rapide

### Démarrer le serveur

```bash
# Méthode 1: Script de démarrage
python scripts/start_server.py

# Méthode 2: Directement avec uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Méthode 3: Mode développement
python scripts/start_server.py --reload --log-level DEBUG
```

Le serveur sera accessible sur :
- **API** : http://localhost:8000
- **Documentation** : http://localhost:8000/docs
- **Admin** : http://localhost:8000/api/v1/admin/status

### Ajouter des documents

```bash
# Via l'API
curl -X POST "http://localhost:8000/api/v1/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@mon_document.pdf" \
     -F "description=Document de test"
```

### Tester le chat

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Bonjour, peux-tu me parler de l'\''intelligence artificielle?",
       "session_id": "test_session"
     }'
```

## 📁 Structure du projet

```
chatbot_chatgpt/
├── api/                    # API FastAPI
│   ├── routes/            # Routes (chat, upload, admin)
│   ├── schemas/           # Modèles Pydantic
│   ├── services/          # Logique métier
│   └── main.py           # Application principale
├── embeddings/            # Gestion des embeddings
│   ├── embedding_model.py # Modèles d'embeddings
│   ├── build_index.py    # Construction d'index
│   └── utils.py          # Utilitaires
├── ingestion/             # Traitement des documents
│   ├── loaders.py        # Chargement de fichiers
│   ├── preprocess.py     # Prétraitement
│   └── chunking.py       # Découpage en chunks
├── llm/                   # Modèles de langage
│   ├── ollama_client.py  # Client Ollama
│   ├── web_search.py     # Recherche web
│   └── chain_builder.py  # Pipeline RAG
├── retriever/             # Récupération de documents
│   ├── retriever.py      # Recherche sémantique
│   ├── query_expansion.py # Extension de requêtes
│   └── filters.py        # Filtres métadonnées
├── configs/               # Configuration
│   └── settings.yaml     # Paramètres principaux
├── tests/                 # Tests unitaires
├── scripts/               # Scripts utilitaires
├── data/                  # Données (documents, index)
└── requirements.txt       # Dépendances Python
```

## 🧪 Tests

### Lancer tous les tests

```bash
# Tests complets
python scripts/run_tests.py

# Tests rapides (sans linting)
python scripts/run_tests.py --quick

# Tests spécifiques
python scripts/run_tests.py --test-file tests/test_api.py

# Avec couverture détaillée
python scripts/run_tests.py --coverage-threshold 90
```

### Tests manuels

```bash
# Tests d'ingestion
pytest tests/test_ingestion.py -v

# Tests d'embeddings
pytest tests/test_embeddings.py -v

# Tests d'API
pytest tests/test_api.py -v
```

## 📖 API Documentation

### Endpoints principaux

#### Chat
- `POST /api/v1/chat` - Chat simple
- `POST /api/v1/chat/stream` - Chat en streaming
- `GET /api/v1/conversations/{session_id}` - Historique
- `DELETE /api/v1/conversations/{session_id}` - Effacer l'historique

#### Upload
- `POST /api/v1/upload` - Upload un document
- `POST /api/v1/upload/bulk` - Upload multiple
- `GET /api/v1/documents` - Lister les documents

#### Administration
- `GET /api/v1/admin/status` - Statut du système
- `GET /api/v1/admin/metrics` - Métriques détaillées
- `POST /api/v1/admin/index/rebuild` - Reconstruire l'index

### Exemples d'utilisation

#### Chat avec historique

```python
import requests

# Premier message
response = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "Qu'est-ce que l'IA?",
    "session_id": "ma_session"
})

# Message de suivi
response = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "Comment ça fonctionne?",
    "session_id": "ma_session",
    "conversation_history": [
        {"role": "user", "content": "Qu'est-ce que l'IA?"},
        {"role": "assistant", "content": "L'IA est..."}
    ]
})
```

## ⚙️ Configuration

### Fichier `configs/settings.yaml`

```yaml
app:
  name: "ChatBot RAG"
  debug: false

models:
  ollama:
    base_url: "http://localhost:11434"
    model_name: "qwen2.5:latest"
    temperature: 0.7
    max_tokens: 2048

  embeddings:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    device: "cpu"

database:
  chroma:
    persist_directory: "./data/chroma"
    collection_name: "documents"

rag:
  chunk_size: 500
  chunk_overlap: 50
  top_k: 5
  similarity_threshold: 0.7

web_search:
  enabled: true
  engine: "duckduckgo"
  max_results: 5
```

### Variables d'environnement

```bash
# Configuration optionnelle
export CONFIG_PATH="configs/settings.yaml"
export LOG_LEVEL="INFO"
export OLLAMA_BASE_URL="http://localhost:11434"
```

## 🔧 Développement

### Architecture

Le système utilise une architecture modulaire :

1. **Ingestion** : Charge et traite les documents
2. **Embeddings** : Convertit le texte en vecteurs
3. **Retriever** : Recherche les documents pertinents
4. **LLM** : Génère les réponses avec Ollama
5. **API** : Interface REST avec FastAPI

### Ajouter un nouveau type de document

```python
# Dans ingestion/loaders.py
def load_new_format(self, file_path: str) -> Dict[str, Any]:
    # Votre logique de chargement
    pass
```

### Personnaliser les embeddings

```python
# Dans embeddings/embedding_model.py
class CustomEmbeddingModel(EmbeddingModel):
    def encode(self, texts):
        # Votre logique d'encodage
        pass
```

## 🚨 Dépannage

### Problèmes courants

#### Ollama ne démarre pas
```bash
# Vérifier le statut
ollama list

# Redémarrer
ollama serve
```

#### Erreurs d'importation
```bash
# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall
```

#### Index vectoriel corrompu
```bash
# Via l'API admin
curl -X DELETE "http://localhost:8000/api/v1/admin/index/clear"
curl -X POST "http://localhost:8000/api/v1/admin/index/rebuild"
```

#### Mémoire insuffisante
- Réduire `chunk_size` dans la configuration
- Utiliser `device: "cpu"` pour les embeddings
- Limiter `max_tokens` pour Ollama

### Logs et debugging

```bash
# Logs détaillés
python scripts/start_server.py --log-level DEBUG

# Logs dans un fichier
tail -f logs/chatbot_rag.log
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commiter les changements (`git commit -am 'Ajouter nouvelle fonctionnalité'`)
4. Pousser la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

### Standards de code

```bash
# Formatage automatique
black .
isort .

# Vérification
flake8 .
mypy .

# Tests avant commit
python scripts/run_tests.py
```

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- [Ollama](https://ollama.com) pour l'interface LLM
- [FastAPI](https://fastapi.tiangolo.com) pour l'API web
- [ChromaDB](https://www.trychroma.com) pour le stockage vectoriel
- [Sentence Transformers](https://www.sbert.net) pour les embeddings
- La communauté open source pour les nombreuses librairies utilisées

## 📞 Support

- 📧 Email : [votre-email]
- 💬 Discord : [votre-discord]
- 🐛 Issues : [GitHub Issues](https://github.com/votre-repo/issues)
- 📖 Wiki : [GitHub Wiki](https://github.com/votre-repo/wiki) 