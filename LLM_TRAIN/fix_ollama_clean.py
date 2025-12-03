#!/usr/bin/env python3
import re

with open('llm/langchain_pipeline.py', 'r') as f:
    content = f.read()

# Pattern pour trouver toute la méthode _setup_llm
pattern = r'(    async def _setup_llm\(self\) -> None:.*?"""Configure le modèle LLM \(Ollama\)\."""\s+logger\.info\(f"🤖 Configuration LLM: {self\.model_name}"\)\s+)(.*?)(logger\.info\("✅ LLM configuré"\))'

replacement = r'''\1
        self.llm = Ollama(
            model=self.model_name,
            temperature=0.1,
            num_ctx=4096,
        )
        
        \3'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('llm/langchain_pipeline.py', 'w') as f:
    f.write(content)

print("✅ Méthode _setup_llm() corrigée")
