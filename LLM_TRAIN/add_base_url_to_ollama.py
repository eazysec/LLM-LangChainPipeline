#!/usr/bin/env python3

with open('llm/langchain_pipeline.py', 'r') as f:
    content = f.read()

# Ajouter base_url à la configuration Ollama
old_config = """        self.llm = Ollama(
            model=self.model_name,
            temperature=0.1,
            num_ctx=4096,
        )"""

new_config = """        self.llm = Ollama(
            model=self.model_name,
            base_url="http://100.64.0.34:11434",
            temperature=0.1,
            num_ctx=4096,
        )"""

if old_config in content:
    content = content.replace(old_config, new_config)
    print("✅ base_url ajouté à Ollama()")
else:
    print("⚠️  Configuration Ollama non trouvée avec ce format exact")
    print("Vérification manuelle nécessaire")

with open('llm/langchain_pipeline.py', 'w') as f:
    f.write(content)
