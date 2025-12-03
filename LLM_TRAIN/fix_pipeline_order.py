#!/usr/bin/env python3
"""Corrige l'ordre d'initialisation dans langchain_pipeline.py"""

with open('llm/langchain_pipeline.py', 'r') as f:
    content = f.read()

# Correction 1: Ordre dans initialize()
old_order = """        # 1. Modèle d'embeddings
        await self._setup_embeddings()
        
        # 2. Chargement ou création du vector store
        await self._setup_vector_store()
        
        # 3. Configuration du retriever
        await self._setup_retriever()
        
        # 4. Configuration du LLM
        await self._setup_llm()"""

new_order = """        # 1. Modèle d'embeddings
        await self._setup_embeddings()
        
        # 2. Chargement ou création du vector store
        await self._setup_vector_store()
        
        # 3. Configuration du LLM (AVANT le retriever)
        await self._setup_llm()
        
        # 4. Configuration du retriever (APRÈS le LLM)
        await self._setup_retriever()"""

content = content.replace(old_order, new_order)

# Correction 2: MultiQueryRetriever avec llm
old_retriever = """        # Multi-query retriever pour améliorer les résultats
        self.retriever = MultiQueryRetriever.from_llm(
            retriever=vector_retriever,
            llm=None,  # Sera configuré plus tard
        )"""

new_retriever = """        # Multi-query retriever pour améliorer les résultats
        self.retriever = MultiQueryRetriever.from_llm(
            retriever=vector_retriever,
            llm=self.llm,  # ✅ Utilise le LLM déjà initialisé
        )"""

content = content.replace(old_retriever, new_retriever)

# Correction 3: Supprimer la mise à jour du retriever dans _setup_llm
old_llm_update = """        
        # Mise à jour du retriever avec le LLM
        if hasattr(self.retriever, 'llm'):
            self.retriever.llm = self.llm"""

content = content.replace(old_llm_update, "")

# Sauvegarder
with open('llm/langchain_pipeline.py', 'w') as f:
    f.write(content)

print("✅ Corrections appliquées:")
print("  1. ✅ LLM initialisé AVANT retriever")
print("  2. ✅ MultiQueryRetriever utilise self.llm")
print("  3. ✅ Code obsolète supprimé")
print("")
print("📋 Nouvel ordre d'initialisation:")
print("  1. Embeddings")
print("  2. Vector Store")
print("  3. LLM ⬅️ Déplacé ici")
print("  4. Retriever (peut maintenant utiliser le LLM)")
print("  5. Memory")
print("  6. Chain")
