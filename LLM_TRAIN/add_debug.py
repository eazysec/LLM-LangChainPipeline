with open('llm/langchain_pipeline.py', 'r') as f:
    content = f.read()

# Ajouter du logging avant create_history_aware_retriever
old_code = """        # Retriever conscient de l'historique
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )"""

new_code = """        # Debug: Vérifier que tout est initialisé
        logger.info(f"🔍 Debug - LLM: {self.llm}")
        logger.info(f"🔍 Debug - Retriever: {self.retriever}")
        logger.info(f"🔍 Debug - Prompt: {contextualize_q_prompt}")
        
        # Retriever conscient de l'historique
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )"""

content = content.replace(old_code, new_code)

with open('llm/langchain_pipeline.py', 'w') as f:
    f.write(content)

print("✅ Debug ajouté")
