python3 << 'EOF'
print("🧪 Test COMPLET de tous les imports\n")

imports_to_test = [
    ("langchain_community.retrievers", "BM25Retriever"),
    ("langchain_classic.retrievers", "EnsembleRetriever"),
    ("langchain_classic.retrievers.multi_query", "MultiQueryRetriever"),
    ("langchain_classic.chains", "RetrievalQA"),
    ("langchain_classic.memory", "ConversationBufferWindowMemory"),
    ("langchain_classic.prompts", "ChatPromptTemplate"),
    ("langchain_classic.callbacks.manager", "CallbackManager"),
    ("langchain_core.documents", "Document"),
    ("langchain_text_splitters", "RecursiveCharacterTextSplitter"),
    ("langchain_community.vectorstores", "Chroma"),
    ("langchain_community.embeddings", "HuggingFaceEmbeddings"),
    ("langchain_community.llms", "Ollama"),
]

success = 0
failed = 0

for module, obj in imports_to_test:
    try:
        exec(f"from {module} import {obj}")
        print(f"✅ {module}.{obj}")
        success += 1
    except ImportError as e:
        print(f"❌ {module}.{obj}: {e}")
        failed += 1

print(f"\n{'='*60}")
print(f"📊 Résultats: {success}/{len(imports_to_test)} réussis")

if failed == 0:
    print("✅ TOUS LES IMPORTS FONCTIONNENT !")
    print("\n🚀 Prêt à lancer l'application !")
else:
    print(f"⚠️  {failed} import(s) échoué(s) - vérifiez les erreurs ci-dessus")
EOF
