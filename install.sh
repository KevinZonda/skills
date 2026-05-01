function install_skill() {
    local skill_name=$1
    if [ -e ~/.agents/skills/$skill_name ] || [ -L ~/.agents/skills/$skill_name ]; then
        echo "Skill $skill_name already exists, skipping..."
        return
    fi
    ln -sf ./$skill_name ~/.agents/skills/$skill_name
}

install_skill academic-paper-writing
install_skill academic-reference-search
install_skill academic-slides
install_skill chinese-polish