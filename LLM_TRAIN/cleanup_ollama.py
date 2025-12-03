with open('llm/langchain_pipeline.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_next = False

for i, line in enumerate(lines):
    # Supprimer les imports de callbacks obsolètes
    if 'from langchain_classic.callbacks.manager import CallbackManager' in line:
        continue
    if 'from langchain_classic.callbacks.streaming_stdout import StreamingStdOutCallbackHandler' in line:
        continue
    
    # Supprimer la ligne callback_manager = ...
    if 'callback_manager = CallbackManager' in line:
        skip_next = True  # Skip aussi la ligne vide suivante
        continue
    
    if skip_next:
        skip_next = False
        if line.strip() == '':
            continue
    
    # Modifier la configuration Ollama
    if '        self.llm = Ollama(' in line:
        new_lines.append(line)
        # Ajouter les lignes suivantes simplifiées
        new_lines.append('            model=self.model_name,\n')
        new_lines.append('            temperature=0.1,\n')
        new_lines.append('            num_ctx=4096,\n')
        new_lines.append('        )\n')
        # Skip les anciennes lignes jusqu'à la fermeture
        while i < len(lines) - 1:
            i += 1
            if lines[i].strip() == ')':
                break
        continue
    
    new_lines.append(line)

with open('llm/langchain_pipeline.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Nettoyage complet effectué")
