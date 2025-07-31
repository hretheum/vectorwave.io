#!/bin/bash

# Skrypt do konwersji projektu vector-wave na strukturę multirepo z git submodules

echo "🚀 Konwersja vector-wave na strukturę multirepo..."

# Kolory dla lepszej czytelności
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Konfiguracja projektów
declare -A PROJECTS=(
    ["content"]="public"
    ["ideas"]="public"
    ["kolegium"]="public"
    ["n8n"]="private"
    ["presenton"]="private"
)

# Tworzenie głównego repozytorium vector-wave
echo -e "${YELLOW}1. Inicjalizacja głównego repozytorium vector-wave...${NC}"
git init
git add README.md *.md # Dodaj tylko pliki główne
git commit -m "Initial commit: vector-wave AI content generation platform"

# Tworzenie .gitignore
cat > .gitignore << EOF
# Ignoruj foldery projektów (będą jako submodules)
/content/
/ideas/
/kolegium/
/n8n/
/presenton/

# Standardowe ignorowania
.DS_Store
*.log
.env
.env.local
node_modules/
__pycache__/
*.pyc
EOF

echo -e "${GREEN}✅ Utworzono .gitignore${NC}"

# Tworzenie pliku konfiguracyjnego submodules
echo -e "${YELLOW}2. Przygotowanie konfiguracji submodules...${NC}"

cat > setup-submodules.md << EOF
# Konfiguracja Git Submodules dla Vector Wave

## Projekty do wydzielenia:

EOF

for project in "${!PROJECTS[@]}"; do
    visibility="${PROJECTS[$project]}"
    echo "### $project ($visibility)" >> setup-submodules.md
    echo "\`\`\`bash" >> setup-submodules.md
    echo "# Utwórz nowe repo na GitHub jako $visibility" >> setup-submodules.md
    echo "# Następnie w folderze $project:" >> setup-submodules.md
    echo "cd $project" >> setup-submodules.md
    echo "git init" >> setup-submodules.md
    echo "git add ." >> setup-submodules.md
    echo "git commit -m \"Initial commit: $project\"" >> setup-submodules.md
    echo "git remote add origin git@github.com:USERNAME/$project.git" >> setup-submodules.md
    echo "git push -u origin main" >> setup-submodules.md
    echo "" >> setup-submodules.md
    echo "# W głównym repo vector-wave:" >> setup-submodules.md
    echo "git submodule add git@github.com:USERNAME/$project.git $project" >> setup-submodules.md
    echo "\`\`\`" >> setup-submodules.md
    echo "" >> setup-submodules.md
done

echo -e "${GREEN}✅ Utworzono instrukcję setup-submodules.md${NC}"

# Skrypt pomocniczy do inicjalizacji projektów
cat > init-project.sh << 'EOF'
#!/bin/bash
# Użycie: ./init-project.sh <nazwa-projektu> <github-username>

PROJECT=$1
USERNAME=$2

if [ -z "$PROJECT" ] || [ -z "$USERNAME" ]; then
    echo "Użycie: $0 <nazwa-projektu> <github-username>"
    exit 1
fi

cd "$PROJECT" || exit 1
git init
git add .
git commit -m "Initial commit: $PROJECT"
git remote add origin "git@github.com:$USERNAME/$PROJECT.git"
echo "✅ Projekt $PROJECT zainicjalizowany. Teraz wykonaj:"
echo "   git push -u origin main"
echo "   cd .. && git submodule add git@github.com:$USERNAME/$PROJECT.git $PROJECT"
EOF

chmod +x init-project.sh

# Tworzenie README dla głównego repo
cat > README.md << EOF
# Vector Wave - AI Content Generation Platform

Platforma do automatycznej generacji treści z wykorzystaniem AI i zaawansowanych workflow.

## Struktura projektów

| Projekt | Opis | Status | Widoczność |
|---------|------|--------|------------|
| content | Wygenerowane materiały content marketingowe | 🟢 Aktywny | Publiczne |
| ideas | Bank pomysłów i koncepcji | 🟡 W rozwoju | Publiczne |
| kolegium | System zarządzania AI agentami | 🟡 W rozwoju | Publiczne |
| n8n | Workflow automatyzacji | 🟢 Aktywny | Prywatne |
| presenton | Generator prezentacji AI | 🟢 Aktywny | Prywatne |

## Główne funkcjonalności

- 🤖 **AI Agents** - Autonomiczne agenty do zbierania i generowania treści
- 📝 **Content Pipeline** - Automatyczna generacja postów na social media
- 🎨 **Visual Generation** - Integracja z Canva i innymi narzędziami
- 🔄 **Workflow Automation** - N8N workflows dla pełnej automatyzacji
- 📊 **Analytics** - Śledzenie performance content

## Jak pracować z tym repozytorium

### Pierwsze pobranie
\`\`\`bash
git clone --recurse-submodules git@github.com:USERNAME/vector-wave.git
\`\`\`

### Aktualizacja submodułów
\`\`\`bash
git submodule update --init --recursive
\`\`\`

### Praca z konkretnym projektem
\`\`\`bash
cd nazwa-projektu
git checkout main
git pull origin main
# ... wprowadź zmiany ...
git add .
git commit -m "Opis zmian"
git push origin main
\`\`\`

### Aktualizacja referencji w głównym repo
\`\`\`bash
git add nazwa-projektu
git commit -m "Update nazwa-projektu submodule"
git push
\`\`\`

## Dokumentacja

- [5 Tech Blog Influencers Analysis](./5-tech-blog-influencers-analysis.md)
- [Tech Blog Style Guide](./tech-blog-styleguide.md)

## Komendy custom

Projekt obsługuje specjalne komendy jak \`/pisarz\` do generowania materiałów - szczegóły w CLAUDE.md
EOF

echo -e "${GREEN}✅ Utworzono README.md${NC}"

# Podsumowanie
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}✅ Przygotowanie zakończone!${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "Następne kroki:"
echo "1. Przejrzyj plik setup-submodules.md"
echo "2. Utwórz repozytoria na GitHub"
echo "3. Użyj ./init-project.sh <projekt> <username> dla każdego projektu"
echo "4. Dodaj submoduły do głównego repo"
echo ""
echo -e "${YELLOW}WAŻNE:${NC} Przed push'em sprawdź .gitignore i upewnij się,"
echo "że nie committujesz niepotrzebnych plików!"