with open('llm/langchain_pipeline.py', 'r') as f:
    lines = f.readlines()

# Trouver et remplacer la méthode _setup_retriever
in_method = False
new_lines = []
skip_until_logger = False

for i, line in enumerate(lines):
    if 'async def _setup_retriever(self)' in line:
        in_method = True
        new_lines.append(line)
        continue
    
    if in_method:
        if 'logger.info("🔍 Configuration du retriever...")' in line:
            new_lines.append(line)
            new_lines.append('        \n')
            new_lines.append('        # Retriever vectoriel simple (compatible avec history_aware_retriever)\n')
            new_lines.append('        self.retriever = self.vector_store.as_retriever(\n')
            new_lines.append('            search_type="similarity_score_threshold",\n')
            new_lines.append('            search_kwargs={\n')
            new_lines.append('                "k": self.top_k,\n')
            new_lines.append('                "score_threshold": 0.3\n')
            new_lines.append('            }\n')
            new_lines.append('        )\n')
            new_lines.append('        \n')
            new_lines.append('        logger.info("✅ Retriever configuré")\n')
            skip_until_logger = True
            continue
        
        if skip_until_logger:
            if 'async def _setup_llm' in line:
                in_method = False
                skip_until_logger = False
                new_lines.append(line)
            continue
        
        new_lines.append(line)
    else:
        new_lines.append(line)

with open('llm/langchain_pipeline.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Méthode _setup_retriever() réécrite")
print("  - MultiQueryRetriever supprimé")
print("  - Retriever vectoriel simple utilisé")
