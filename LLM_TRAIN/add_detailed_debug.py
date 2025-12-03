#!/usr/bin/env python3

with open('llm/langchain_pipeline.py', 'r') as f:
    content = f.read()

# Ajouter du debug avant create_history_aware_retriever
old_code = """        # Retriever conscient de l'historique
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )"""

new_code = """        # Debug: Vérifier que tout est initialisé
        logger.info("=" * 60)
        logger.info("🔍 DEBUG - Vérification avant create_history_aware_retriever:")
        logger.info(f"  - self.llm type: {type(self.llm)}")
        logger.info(f"  - self.llm value: {self.llm}")
        logger.info(f"  - self.retriever type: {type(self.retriever)}")
        logger.info(f"  - self.retriever value: {self.retriever}")
        logger.info(f"  - contextualize_q_prompt type: {type(contextualize_q_prompt)}")
        logger.info("=" * 60)
        
        # Retriever conscient de l'historique
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )"""

content = content.replace(old_code, new_code)

with open('llm/langchain_pipeline.py', 'w') as f:
    f.write(content)

print("✅ Debug ajouté avant create_history_aware_retriever")
