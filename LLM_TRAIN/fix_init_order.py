#!/usr/bin/env python3

with open('llm/langchain_pipeline.py', 'r') as f:
    content = f.read()

# Corriger l'ordre dans initialize()
old_order = """            # 1. Modèle d'embeddings
            await self._setup_embeddings()
            
            # 2. Chargement ou création du vector store
            await self._setup_vector_store()
            
            # 3. Configuration du retriever
            await self._setup_retriever()
            
            # 4. Configuration du LLM
            await self._setup_llm()
            
            # 5. Configuration de la mémoire
            await self._setup_memory()
            
            # 6. Création de la chaîne RAG
            await self._setup_chain()"""

new_order = """            # 1. Modèle d'embeddings
            await self._setup_embeddings()
            
            # 2. Chargement ou création du vector store
            await self._setup_vector_store()
            
            # 3. Configuration du LLM (AVANT retriever)
            await self._setup_llm()
            
            # 4. Configuration du retriever (APRÈS LLM)
            await self._setup_retriever()
            
            # 5. Configuration de la mémoire
            await self._setup_memory()
            
            # 6. Création de la chaîne RAG
            await self._setup_chain()"""

content = content.replace(old_order, new_order)

with open('llm/langchain_pipeline.py', 'w') as f:
    f.write(content)

print("✅ Ordre d'initialisation corrigé:")
print("  1. Embeddings")
print("  2. Vector Store")
print("  3. LLM ⬅️ Déplacé ici")
print("  4. Retriever (peut maintenant utiliser le LLM)")
print("  5. Memory")
print("  6. Chain")
