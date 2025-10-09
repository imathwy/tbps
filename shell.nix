{pkgs}:
pkgs.mkShell {
  packages = with pkgs; [
    xz
    fd
    git-lfs

    python311
    uv
    ruff
    ty

    nodejs_24
    pnpm
    biome

    elan
  ];

  shellHook = ''
    git lfs install

    cd tbps-be || exit 1
    if [ ! -d ".venv" ]; then
      uv venv
    fi
    source .venv/bin/activate
    cd ..
  '';
}
