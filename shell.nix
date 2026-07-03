{
  pkgs ? import <nixpkgs> { },
}:

let
  pythonPackages = ps: [
    ps.ansible-core
    ps.docker
    ps.molecule
    ps.molecule-plugins
    ps.pytest
    ps.pytest-testinfra
  ];
  python = pkgs.python3.withPackages pythonPackages;

in

pkgs.mkShell {
  packages = with pkgs; [
    python
    python311Packages.requests
    docker
    rsync
    zsh
  ];

  shellHook = ''
    export PYTHONDONTWRITEBYTECODE=1
    export ANSIBLE_ALLOW_BROKEN_CONDITIONALS=True
    # TODO: remove ANSIBLE_INJECT_INVOCATION workaround when
    # https://github.com/ansible-community/molecule-plugins/issues/363 is resolved
    export ANSIBLE_INJECT_INVOCATION=true

    echo "============================================"
    echo "*** Ansible Molecule Development Environment"
    echo "============================================"
    echo "Installed Versions:"
    python --version
    ansible --version | head -n 1
    molecule --version | head -n 1
    echo "============================================"
    echo "Run: molecule test -s default"
  '';
}
