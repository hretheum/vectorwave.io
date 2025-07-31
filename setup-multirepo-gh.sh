#!/bin/bash

# Skrypt do konwersji projektu vector-wave na strukturę multirepo z automatycznym tworzeniem repo przez gh CLI

echo "🚀 Konwersja vector-wave na strukturę multirepo z GitHub CLI..."

# Kolory dla lepszej czytelności
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Sprawdzenie czy gh jest zainstalowane
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) nie jest zainstalowane!${NC}"
    echo "Zainstaluj przez: brew install gh"
    echo "Lub pobierz z: https://cli.github.com/"
    exit 1
fi

# Sprawdzenie czy użytkownik jest zalogowany
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Musisz się zalogować do GitHub CLI${NC}"
    echo "Wykonaj: gh auth login"
    exit 1
fi

# Pobranie nazwy użytkownika GitHub
GITHUB_USER=$(gh api user --jq .login)
echo -e "${GREEN}✅ Zalogowany jako: $GITHUB_USER${NC}"

# Konfiguracja projektów
declare -A PROJECTS=(
    ["content"]="public"
    ["ideas"]="public"
    ["kolegium"]="public"
    ["n8n"]="private"
    ["presenton"]="private"
)

# Pytanie o prefix dla nazw repo
echo -e "${BLUE}Podaj prefix dla nazw repozytoriów (np. 'vector-wave-' da 'vector-wave-content')${NC}"
read -p "Prefix (zostaw puste dla brak): " REPO_PREFIX

# Funkcja do tworzenia i inicjalizacji repo
create_and_init_repo() {
    local project=$1
    local visibility=$2
    local repo_name="${REPO_PREFIX}${project}"
    
    echo -e "${YELLOW}📦 Przetwarzanie: $project ($visibility)${NC}"
    
    # Sprawdź czy repo już istnieje
    if gh repo view "$GITHUB_USER/$repo_name" &> /dev/null; then
        echo -e "${YELLOW}   ⚠️  Repo $repo_name już istnieje, pomijam tworzenie${NC}"
    else
        # Tworzenie repo na GitHub
        echo -e "${BLUE}   🌐 Tworzenie repo na GitHub...${NC}"
        if [ "$visibility" == "private" ]; then
            gh repo create "$repo_name" --private --description "Part of Vector Wave platform - $project module"
        else
            gh repo create "$repo_name" --public --description "Part of Vector Wave platform - $project module"
        fi
        echo -e "${GREEN}   ✅ Utworzono repo: $repo_name${NC}"
    fi
    
    # Inicjalizacja lokalnego repo
    if [ -d "$project" ]; then
        cd "$project"
        
        # Sprawdź czy to już jest repo git
        if [ -d ".git" ]; then
            echo -e "${YELLOW}   ⚠️  Folder $project już jest repozytorium git${NC}"
            # Dodaj remote jeśli nie istnieje
            if ! git remote get-url origin &> /dev/null; then
                git remote add origin "git@github.com:$GITHUB_USER/$repo_name.git"
                echo -e "${GREEN}   ✅ Dodano remote origin${NC}"
            fi
        else
            # Nowe repo
            git init
            git add .
            git commit -m "Initial commit: $project module for Vector Wave platform"
            git branch -M main
            git remote add origin "git@github.com:$GITHUB_USER/$repo_name.git"
            echo -e "${GREEN}   ✅ Zainicjalizowano lokalne repo${NC}"
        fi
        
        # Push do GitHub
        echo -e "${BLUE}   📤 Push do GitHub...${NC}"
        if git push -u origin main; then
            echo -e "${GREEN}   ✅ Push zakończony sukcesem${NC}"
        else
            echo -e "${YELLOW}   ⚠️  Push nieudany - sprawdź ręcznie${NC}"
        fi
        
        cd ..
    else
        echo -e "${RED}   ❌ Folder $project nie istnieje!${NC}"
    fi
    
    echo ""
}

# Tworzenie głównego repozytorium vector-wave
echo -e "${YELLOW}📦 Inicjalizacja głównego repozytorium vector-wave...${NC}"

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

# Inicjalizacja głównego repo
if [ ! -d ".git" ]; then
    git init
    git add README.md *.md .gitignore
    git commit -m "Initial commit: Vector Wave AI content generation platform"
fi

# Tworzenie głównego repo na GitHub
MAIN_REPO_NAME="${REPO_PREFIX}main"
if [ -z "$REPO_PREFIX" ]; then
    MAIN_REPO_NAME="vector-wave"
fi

if ! gh repo view "$GITHUB_USER/$MAIN_REPO_NAME" &> /dev/null; then
    echo -e "${BLUE}🌐 Tworzenie głównego repo na GitHub...${NC}"
    gh repo create "$MAIN_REPO_NAME" --public --description "Vector Wave - AI Content Generation Platform"
    git remote add origin "git@github.com:$GITHUB_USER/$MAIN_REPO_NAME.git"
    git push -u origin main
    echo -e "${GREEN}✅ Utworzono główne repo: $MAIN_REPO_NAME${NC}"
else
    echo -e "${YELLOW}⚠️  Główne repo już istnieje${NC}"
fi

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${BLUE}🔧 Tworzenie i inicjalizacja submodułów${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Przetwarzanie każdego projektu
for project in "${!PROJECTS[@]}"; do
    create_and_init_repo "$project" "${PROJECTS[$project]}"
done

# Dodawanie submodułów do głównego repo
echo -e "${YELLOW}🔗 Dodawanie submodułów do głównego repo...${NC}"
for project in "${!PROJECTS[@]}"; do
    repo_name="${REPO_PREFIX}${project}"
    if [ ! -d "$project/.git" ]; then
        echo -e "${RED}❌ Pominięto $project - nie jest repozytorium git${NC}"
        continue
    fi
    
    # Usuń folder z głównego repo jeśli istnieje
    if [ -d "$project" ] && [ ! -f ".gitmodules" ]; then
        git rm -r --cached "$project" 2>/dev/null || true
        git commit -m "Remove $project folder before adding as submodule" 2>/dev/null || true
    fi
    
    # Dodaj jako submodule
    if ! grep -q "path = $project" .gitmodules 2>/dev/null; then
        git submodule add "git@github.com:$GITHUB_USER/$repo_name.git" "$project"
        echo -e "${GREEN}✅ Dodano submodule: $project${NC}"
    else
        echo -e "${YELLOW}⚠️  Submodule $project już istnieje${NC}"
    fi
done

# Commit submodułów
git add .gitmodules
git commit -m "Add all submodules" 2>/dev/null || true
git push

# Tworzenie README jeśli nie istnieje
if [ ! -f "README.md" ]; then
    cat > README.md << EOF
# Vector Wave - AI Content Generation Platform

Platforma do automatycznej generacji treści z wykorzystaniem AI i zaawansowanych workflow.

## Struktura projektów

| Projekt | Opis | Status | Widoczność | Repo |
|---------|------|--------|------------|------|
| content | Wygenerowane materiały content marketingowe | 🟢 Aktywny | Publiczne | [${REPO_PREFIX}content](https://github.com/$GITHUB_USER/${REPO_PREFIX}content) |
| ideas | Bank pomysłów i koncepcji | 🟡 W rozwoju | Publiczne | [${REPO_PREFIX}ideas](https://github.com/$GITHUB_USER/${REPO_PREFIX}ideas) |
| kolegium | System zarządzania AI agentami | 🟡 W rozwoju | Publiczne | [${REPO_PREFIX}kolegium](https://github.com/$GITHUB_USER/${REPO_PREFIX}kolegium) |
| n8n | Workflow automatyzacji | 🟢 Aktywny | Prywatne | [${REPO_PREFIX}n8n](https://github.com/$GITHUB_USER/${REPO_PREFIX}n8n) |
| presenton | Generator prezentacji AI | 🟢 Aktywny | Prywatne | [${REPO_PREFIX}presenton](https://github.com/$GITHUB_USER/${REPO_PREFIX}presenton) |

## Jak pracować z tym repozytorium

### Pierwsze pobranie
\`\`\`bash
git clone --recurse-submodules git@github.com:$GITHUB_USER/$MAIN_REPO_NAME.git
\`\`\`

### Aktualizacja submodułów
\`\`\`bash
git submodule update --init --recursive
\`\`\`
EOF
    git add README.md
    git commit -m "Add README with repo links"
    git push
fi

# Podsumowanie
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}✅ Konwersja zakończona!${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${BLUE}📋 Utworzone repozytoria:${NC}"
echo -e "   🏠 Główne: https://github.com/$GITHUB_USER/$MAIN_REPO_NAME"
for project in "${!PROJECTS[@]}"; do
    echo -e "   📦 $project: https://github.com/$GITHUB_USER/${REPO_PREFIX}${project}"
done
echo ""
echo -e "${YELLOW}💡 Następne kroki:${NC}"
echo "1. Sprawdź repozytoria na GitHub"
echo "2. Sklonuj główne repo ze wszystkimi submodułami:"
echo "   git clone --recurse-submodules git@github.com:$GITHUB_USER/$MAIN_REPO_NAME.git"
echo ""