function install_skill() {
    local skill_name=$1
    ln -sf ./$skill_name ~/.agents/skills/$skill_name
}

install_skill academic-paper-writing
install_skill academic-reference-search
install_skill academic-slides
install_skill chinese-polish