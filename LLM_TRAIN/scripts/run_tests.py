#!/usr/bin/env python3
"""
Script pour lancer les tests unitaires du ChatBot RAG.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_command(command, description, continue_on_error=False):
    """Exécute une commande et affiche le résultat."""
    print(f"\n🔧 {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings/Info: {result.stderr}")
        print(f"✅ {description} - OK")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ÉCHEC")
        print(f"Code de sortie: {e.returncode}")
        print(f"Sortie d'erreur: {e.stderr}")
        if e.stdout:
            print(f"Sortie standard: {e.stdout}")
        
        if not continue_on_error:
            return False
        return True


def check_test_dependencies():
    """Vérifie que les dépendances de test sont installées."""
    required_packages = ['pytest', 'pytest-asyncio']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} est installé")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} n'est pas installé")
    
    if missing:
        print(f"\nInstallation des dépendances manquantes: {' '.join(missing)}")
        cmd = f"pip install {' '.join(missing)}"
        return run_command(cmd, "Installation des dépendances de test")
    
    return True


def run_linting(args):
    """Lance les outils de linting."""
    if args.skip_lint:
        print("🔍 Linting ignoré")
        return True
    
    success = True
    
    # Black - formatage du code
    if not run_command("black --check --diff .", "Vérification du formatage avec Black", continue_on_error=True):
        print("💡 Pour corriger: black .")
        success = False
    
    # isort - tri des imports
    if not run_command("isort --check-only --diff .", "Vérification des imports avec isort", continue_on_error=True):
        print("💡 Pour corriger: isort .")
        success = False
    
    # flake8 - linting
    if not run_command("flake8 --max-line-length=120 --extend-ignore=E203,W503 .", "Linting avec flake8", continue_on_error=True):
        success = False
    
    return success


def run_type_checking(args):
    """Lance la vérification de types."""
    if args.skip_typing:
        print("🔍 Vérification de types ignorée")
        return True
    
    return run_command("mypy --ignore-missing-imports .", "Vérification de types avec mypy", continue_on_error=True)


def run_tests(args):
    """Lance les tests unitaires."""
    pytest_args = []
    
    # Configuration de base
    pytest_args.extend(["-v", "--tb=short"])
    
    # Coverage
    if not args.no_coverage:
        pytest_args.extend([
            "--cov=.",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            f"--cov-fail-under={args.coverage_threshold}"
        ])
    
    # Tests spécifiques
    if args.test_pattern:
        pytest_args.extend(["-k", args.test_pattern])
    
    if args.test_file:
        pytest_args.append(args.test_file)
    else:
        pytest_args.append("tests/")
    
    # Mode parallèle
    if args.parallel and not args.test_file:
        pytest_args.extend(["-n", "auto"])
    
    # Mode verbose
    if args.verbose:
        pytest_args.append("-vv")
    
    # Arrêter au premier échec
    if args.fail_fast:
        pytest_args.append("-x")
    
    command = f"pytest {' '.join(pytest_args)}"
    return run_command(command, "Exécution des tests unitaires")


def generate_coverage_report():
    """Génère un rapport de couverture détaillé."""
    print("\n📊 Génération du rapport de couverture...")
    
    # Générer le rapport HTML
    if run_command("coverage html", "Rapport HTML de couverture", continue_on_error=True):
        print("📁 Rapport HTML généré dans: htmlcov/index.html")
    
    # Générer le rapport XML (pour CI/CD)
    run_command("coverage xml", "Rapport XML de couverture", continue_on_error=True)
    
    # Afficher le résumé
    run_command("coverage report", "Résumé de la couverture", continue_on_error=True)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Lance les tests du ChatBot RAG")
    
    # Options générales
    parser.add_argument("--skip-lint", action="store_true", help="Ignorer le linting")
    parser.add_argument("--skip-typing", action="store_true", help="Ignorer la vérification de types")
    parser.add_argument("--no-coverage", action="store_true", help="Désactiver la mesure de couverture")
    parser.add_argument("--coverage-threshold", type=int, default=80, help="Seuil de couverture requis (%)")
    
    # Options de test
    parser.add_argument("--test-file", help="Fichier de test spécifique à exécuter")
    parser.add_argument("--test-pattern", help="Pattern pour filtrer les tests (ex: test_api)")
    parser.add_argument("--parallel", action="store_true", help="Exécuter les tests en parallèle")
    parser.add_argument("--verbose", action="store_true", help="Mode verbose")
    parser.add_argument("--fail-fast", action="store_true", help="Arrêter au premier échec")
    
    # Modes spéciaux
    parser.add_argument("--quick", action="store_true", help="Tests rapides (pas de linting/typing)")
    parser.add_argument("--full", action="store_true", help="Suite complète (linting + typing + tests)")
    
    args = parser.parse_args()
    
    # Mode quick
    if args.quick:
        args.skip_lint = True
        args.skip_typing = True
    
    print("🧪 Suite de tests ChatBot RAG")
    print("=" * 50)
    
    # Changer vers le répertoire du projet
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"📁 Répertoire de travail: {project_root}")
    
    # Vérifier les dépendances de test
    print("\n📦 Vérification des dépendances de test...")
    if not check_test_dependencies():
        print("❌ Impossible d'installer les dépendances de test")
        sys.exit(1)
    
    success = True
    
    # Linting
    if not run_linting(args):
        success = False
        print("⚠️  Problèmes de style détectés")
    
    # Vérification de types
    if not run_type_checking(args):
        success = False
        print("⚠️  Problèmes de types détectés")
    
    # Tests unitaires
    if not run_tests(args):
        success = False
        print("❌ Échecs dans les tests")
    else:
        print("✅ Tous les tests sont passés")
    
    # Rapport de couverture
    if not args.no_coverage:
        generate_coverage_report()
    
    # Résumé final
    print("\n" + "=" * 50)
    if success:
        print("🎉 Tous les contrôles sont passés avec succès!")
        print("\n📈 Prochaines étapes recommandées:")
        print("   - Vérifiez le rapport de couverture: htmlcov/index.html")
        print("   - Commitez vos changements si tout est OK")
        sys.exit(0)
    else:
        print("❌ Certains contrôles ont échoué")
        print("\n🔧 Actions recommandées:")
        print("   - Corrigez les problèmes de style: black . && isort .")
        print("   - Corrigez les erreurs de types avec mypy")
        print("   - Vérifiez les tests qui échouent")
        sys.exit(1)


if __name__ == "__main__":
    main() 