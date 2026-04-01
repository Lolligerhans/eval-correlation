#!/usr/bin/env bash
# ╭──────────────────────╮
# │ 🅅 version            │
# ╰──────────────────────╯
# version 0.0.0
# ╭──────────────────────╮
# │ 🛈 Info              │
# ╰──────────────────────╯
# TODO: This is a template runscript.
# ╭──────────────────────╮
# │ ⚙ Boilerplate        │
# ╰──────────────────────╯
# shellcheck disable=SC2034 # Defined-but-not-used caused by set_args
# shellcheck disable=SC2154 # Not-defined caused by set_args
declare -gr dotfiles="${DOTFILES:-"$HOME/dotfiles"}" # TOKEN_DOTFILES_GLOBAL
# ☯ Every file prevents multi-loads itself using this global dict
declare -gA _sourced_files=(["runscript"]="")
# 🖈 If the runscript requires a specific location, set it here
#declare -gr this_location=""
# shellcheck source-path=/home/username/dotfiles/scripts/boilerplate.sh
source "$dotfiles/scripts/boilerplate.sh" "${BASH_SOURCE[0]}" "$@"
# ╭──────────────────────╮
# │ 🛠Configuration      │
# ╰──────────────────────╯
_run_config["versioning"]=0   # {0, 1}
_run_config["log_loads"]=0    # {0, 1}
_run_config["error_frames"]=4 # {1, 2, ...}
# ╭──────────────────────╮
# │ 🗀 Dependencies      │
# ╰──────────────────────╯
# ✔ Ensure versions with satisfy_version
satisfy_version "$dotfiles/scripts/boilerplate.sh" "0.0.0"
# ✔ Source versioned dependencies with load_version
load_version "$dotfiles/scripts/version.sh" "0.0.0"
#load_version "$dotfiles/scripts/assert.sh"
#load_version "$dotfiles/scripts/bash_meta.sh"
#load_version "$dotfiles/scripts/cache.sh"
#load_version "$dotfiles/scripts/error_handling.sh"
#load_version "$dotfiles/scripts/fileinteracts.sh"
#load_version "$dotfiles/scripts/git_utils.sh"
#load_version "$dotfiles/scripts/progress_bar.sh"
#load_version "$dotfiles/scripts/nyx/nyx.sh"
#load_version "$dotfiles/scripts/setargs.sh"
#load_version "$dotfiles/scripts/termcap.sh"
#load_version "$dotfiles/scripts/userinteracts.sh"
#load_version "$dotfiles/scripts/utils.sh"
# ╭──────────────────────╮
# │ 🗺 Globals           │
# ╰──────────────────────╯
declare -r python_binary="venv/bin/python3"
declare -r test_games="test/games.pgn"
# ╭──────────────────────╮
# │ ⌨  Commands          │
# ╰──────────────────────╯

# Default command (when no arguments are given)
command_default() {
    # Use smaller testing file
    "$python_binary" main.py "test/games.pgn"
}

command_divp() {
    # Use real data as input
    analyze_files data/TCEC_Season_29_-_Division_P.pgn
}

command_swiss() {
    analyze_files data/*Swiss*.pgn
}

# ╭──────────────────────╮
# │ 🖩 Utils             │
# ╰──────────────────────╯
# Run analysis scrip on all files in $@
analyze_files() {
    "$python_binary" main.py "$@"
}

# ╭──────────────────────╮
# │ 𝑓 Functional         │
# ╰──────────────────────╯
# ╭──────────────────────╮
# │ 🖹 Help strings      │
# ╰──────────────────────╯
#declare -r default_help_string=''
# ╭──────────────────────╮
# │ ⚙ Boilerplate        │
# ╰──────────────────────╯
# ⌂ Transition to provided command
subcommand "${@}"
# ╭──────────────────────╮
# │ 🕮  Documentation    │
# ╰──────────────────────╯
