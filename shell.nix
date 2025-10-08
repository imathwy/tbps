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
  ];
}
