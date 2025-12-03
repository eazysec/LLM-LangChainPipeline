#!/usr/bin/env python3
'''Script de lancement du fine-tuning mystique'''

import sys
import asyncio
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from fine_tuning.mystical_fine_tuner import main

if __name__ == "__main__":
    print("🔥 LANCEMENT DU FINE-TUNING MYSTIQUE")
    asyncio.run(main())
