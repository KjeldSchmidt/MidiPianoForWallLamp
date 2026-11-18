#!/usr/bin/env bash
set -eu

## pi-restart: restarts the midi service
function task_pi_restart {
  if [[ "$USER" == "pi" ]]; then
    printf "Running locally on Raspberry Pi\n\n"
    _pi_restart_local
  else
    printf "Running via SSH to Raspberry Pi\n\n"
    ssh "${ssh_connect_string}" "$(declare -f _pi_restart_local); _pi_restart_local"
  fi

}

function _pi_restart_local {
  sudo systemctl restart midi-piano-lights.service
}

ssh_connect_string=pi@rpi-piano
## setup: Installs the python runtime and dependencies for local development
function task_setup {
  sudo add-apt-repository ppa:deadsnakes/ppa -y
  sudo apt update
  sudo apt-get install mosquitto python3.10 pipx -y
  pipx install poetry
  pipx ensurepath
  source ~/.bashrc
  poetry install
  git config --local core.hooksPath .githooks/
}

##pi-status: check the status of all three systemctl services
function task_pi_status {
  printf "Checking status of systemctl services...\n\n"
  
  if [[ "$USER" == "pi" ]]; then
    # Running directly on Raspberry Pi
    printf "Running locally on Raspberry Pi\n\n"
    _pi_status_local
  else
    # Running from remote machine, SSH to Pi
    printf "Running via SSH to Raspberry Pi\n\n"
    ssh "${ssh_connect_string}" "$(declare -f _pi_status_local); _pi_status_local"
  fi
}

function _pi_status_local {
  echo "=== MIDI-PIANO-SERVER SERVICE ==="
  sudo systemctl status midi-piano-lights.service --no-pager -l || true
  echo ""
  
  echo "=== SUMMARY ==="
  echo "Active services:"
  sudo systemctl is-active midi-piano-lights.service || true
  echo ""
  echo "Enabled services:"
  sudo systemctl is-enabled midi-piano-lights.service || true
}

##pi-setup: prepare a fresh raspberry pi OS installation to run the required software
function task_pi_setup {
  sudo apt install libfluidsynth-dev fluid-soundfont-gm
  _pi_install_python_deps
  printf "Python dependencies are probably maybe installed ✅\n"
  printf "Starting midi-piano-lights service...\n\n"
  sudo systemctl enable midi-piano-lights.service
}

function _pi_install_python_deps {
  poetry install
  sudo mv midi-piano-lights.service /etc/systemd/system/midi-piano-lights.service
}

#-------- All task definitions go above this line --------#
# Bash Strict Mode - For details, see
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -u     # Raise error when using undefined variables
set -e     # Raise error if any command has a non-zero exit status
# set -x   # Enable this optionally to print every command executed by bash
set -o pipefail  # Prevent pipelines from masking errors

function task_usage {
    echo "Usage: $0"
    sed -n 's/^##//p' <"$0" | column -t -s ':' |  sed -E $'s/^/\t/'
}

cmd=${1:-}
shift || true
resolved_command=$(echo "task_${cmd}" | sed 's/-/_/g')
if [[ "$(LC_ALL=C type -t "${resolved_command}")" == "function" ]]; then
    pushd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null || exit
    ${resolved_command} "$@"
else
    task_usage
fi
