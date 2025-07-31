#!/bin/bash

# Skrypt do instalacji git hooks zapobiegających przypadkowemu commitowaniu .env

echo "🔒 Instalacja git hooks dla ochrony plików .env..."

# Kolory
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Pre-commit hook content
create_pre_commit_hook() {
    cat > .git/hooks/pre-commit << 'HOOK_EOF'
#!/bin/bash

# Pre-commit hook to prevent committing .env files
# This hook checks for any .env files in the staged changes

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Check for .env files in staged changes
ENV_FILES=$(git diff --cached --name-only | grep -E '(^|/)\.env(\.|$)|\.env$')

if [ ! -z "$ENV_FILES" ]; then
    echo -e "${RED}❌ BŁĄD: Próbujesz commitować pliki .env!${NC}"
    echo -e "${RED}Znalezione pliki:${NC}"
    echo "$ENV_FILES" | while read -r file; do
        echo -e "${YELLOW}  - $file${NC}"
    done
    echo ""
    echo -e "${YELLOW}💡 Wskazówka: Usuń te pliki ze stage area używając:${NC}"
    echo "$ENV_FILES" | while read -r file; do
        echo "   git reset HEAD $file"
    done
    echo ""
    echo -e "${RED}Commit został anulowany ze względów bezpieczeństwa.${NC}"
    exit 1
fi

# Check for CLAUDE.md files in staged changes
CLAUDE_FILES=$(git diff --cached --name-only | grep -iE '(^|/)claude\.md$')

if [ ! -z "$CLAUDE_FILES" ]; then
    echo -e "${RED}❌ BŁĄD: Próbujesz commitować pliki CLAUDE.md!${NC}"
    echo -e "${RED}Te pliki zawierają prywatne instrukcje projektu i nie powinny być publiczne.${NC}"
    echo -e "${RED}Znalezione pliki:${NC}"
    echo "$CLAUDE_FILES" | while read -r file; do
        echo -e "${YELLOW}  - $file${NC}"
    done
    echo ""
    echo -e "${YELLOW}💡 Wskazówka: Usuń te pliki ze stage area używając:${NC}"
    echo "$CLAUDE_FILES" | while read -r file; do
        echo "   git reset HEAD $file"
    done
    echo ""
    echo -e "${RED}Commit został anulowany ze względów bezpieczeństwa.${NC}"
    exit 1
fi

# Additional check for common secret patterns
SECRETS=$(git diff --cached --name-only -z | xargs -0 grep -l -E '(api[_-]?key|secret|password|token|private[_-]?key)[\s]*=[\s]*["\']?[A-Za-z0-9+/=]{20,}' 2>/dev/null)

if [ ! -z "$SECRETS" ]; then
    echo -e "${YELLOW}⚠️  OSTRZEŻENIE: Znaleziono potencjalne sekrety w plikach:${NC}"
    echo "$SECRETS" | while read -r file; do
        echo -e "${YELLOW}  - $file${NC}"
    done
    echo ""
    echo -e "${YELLOW}Sprawdź te pliki przed commitowaniem!${NC}"
    echo -e "${YELLOW}Jeśli to false positive, możesz wymusić commit używając: git commit --no-verify${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Sprawdzenie bezpieczeństwa zakończone pomyślnie${NC}"
exit 0
HOOK_EOF
    
    chmod +x .git/hooks/pre-commit
}

# Install hook in current directory
install_hook_current() {
    if [ ! -d ".git" ]; then
        echo -e "${RED}❌ To nie jest repozytorium git!${NC}"
        return 1
    fi
    
    create_pre_commit_hook
    echo -e "${GREEN}✅ Zainstalowano hook w bieżącym repozytorium${NC}"
}

# Install hooks in all subdirectories
install_hooks_recursive() {
    local count=0
    
    # Install in main repo
    if [ -d ".git" ]; then
        create_pre_commit_hook
        echo -e "${GREEN}✅ Zainstalowano hook w głównym repozytorium${NC}"
        ((count++))
    fi
    
    # Find all git repositories in subdirectories
    for dir in */; do
        if [ -d "$dir/.git" ]; then
            cd "$dir"
            create_pre_commit_hook
            echo -e "${GREEN}✅ Zainstalowano hook w: $dir${NC}"
            cd ..
            ((count++))
        fi
    done
    
    echo ""
    echo -e "${BLUE}📊 Podsumowanie: Zainstalowano hooks w $count repozytoriach${NC}"
}

# Create global git hook template
create_global_hook_template() {
    TEMPLATE_DIR="$HOME/.git-templates/hooks"
    mkdir -p "$TEMPLATE_DIR"
    
    cat > "$TEMPLATE_DIR/pre-commit" << 'HOOK_EOF'
#!/bin/bash

# Global pre-commit hook to prevent committing .env files
# This will be automatically installed in all new git repositories

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Check for .env files in staged changes
ENV_FILES=$(git diff --cached --name-only | grep -E '(^|/)\.env(\.|$)|\.env$')

if [ ! -z "$ENV_FILES" ]; then
    echo -e "${RED}❌ BŁĄD: Próbujesz commitować pliki .env!${NC}"
    echo -e "${RED}Znalezione pliki:${NC}"
    echo "$ENV_FILES" | while read -r file; do
        echo -e "${YELLOW}  - $file${NC}"
    done
    echo ""
    echo -e "${YELLOW}💡 Wskazówka: Usuń te pliki ze stage area używając:${NC}"
    echo "$ENV_FILES" | while read -r file; do
        echo "   git reset HEAD $file"
    done
    echo ""
    echo -e "${RED}Commit został anulowany ze względów bezpieczeństwa.${NC}"
    exit 1
fi

# Check for CLAUDE.md files in staged changes
CLAUDE_FILES=$(git diff --cached --name-only | grep -iE '(^|/)claude\.md$')

if [ ! -z "$CLAUDE_FILES" ]; then
    echo -e "${RED}❌ BŁĄD: Próbujesz commitować pliki CLAUDE.md!${NC}"
    echo -e "${RED}Te pliki zawierają prywatne instrukcje projektu i nie powinny być publiczne.${NC}"
    echo -e "${RED}Znalezione pliki:${NC}"
    echo "$CLAUDE_FILES" | while read -r file; do
        echo -e "${YELLOW}  - $file${NC}"
    done
    echo ""
    echo -e "${YELLOW}💡 Wskazówka: Usuń te pliki ze stage area używając:${NC}"
    echo "$CLAUDE_FILES" | while read -r file; do
        echo "   git reset HEAD $file"
    done
    echo ""
    echo -e "${RED}Commit został anulowany ze względów bezpieczeństwa.${NC}"
    exit 1
fi

exit 0
HOOK_EOF
    
    chmod +x "$TEMPLATE_DIR/pre-commit"
    
    # Configure git to use this template
    git config --global init.templatedir "$HOME/.git-templates"
    
    echo -e "${GREEN}✅ Utworzono globalny template hook${NC}"
    echo -e "${BLUE}   Będzie automatycznie instalowany we wszystkich nowych repozytoriach${NC}"
}

# Main menu
echo -e "${BLUE}Wybierz opcję instalacji:${NC}"
echo "1) Zainstaluj hook tylko w bieżącym repozytorium"
echo "2) Zainstaluj hooks we wszystkich submodułach (rekursywnie)"
echo "3) Utwórz globalny template (dla wszystkich przyszłych repo)"
echo "4) Wszystkie powyższe"
echo ""
read -p "Wybór (1-4): " choice

case $choice in
    1)
        install_hook_current
        ;;
    2)
        install_hooks_recursive
        ;;
    3)
        create_global_hook_template
        ;;
    4)
        install_hooks_recursive
        create_global_hook_template
        ;;
    *)
        echo -e "${RED}❌ Nieprawidłowy wybór${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}💡 Dodatkowe wskazówki bezpieczeństwa:${NC}"
echo "• Zawsze używaj .gitignore z wzorcami dla .env"
echo "• Przechowuj przykładowe konfiguracje w .env.example"
echo "• Używaj narzędzi jak git-secrets lub truffleHog"
echo "• Regularnie przeglądaj historię commitów"
echo ""
echo -e "${GREEN}✅ Instalacja zakończona!${NC}"