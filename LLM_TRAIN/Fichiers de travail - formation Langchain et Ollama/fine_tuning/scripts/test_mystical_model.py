#!/usr/bin/env python3
'''Test rapide du modèle fine-tuné'''

import ollama

def test_mystical_model():
    try:
        # Test avec le modèle mystique
        response = ollama.chat(
            model='mystical-qwen',
            messages=[{'role': 'user', 'content': 'Parle-moi de l\'alchimie'}]
        )
        
        print("🔮 RÉPONSE DU MODÈLE MYSTIQUE :")
        print("="*50)
        print(response['message']['content'])
        print("="*50)
        
    except Exception as e:
        print(f"❌ Erreur test : {e}")
        print("Vérifiez que le modèle mystical-qwen est bien créé dans Ollama")

if __name__ == "__main__":
    test_mystical_model()
