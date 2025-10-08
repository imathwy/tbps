{pkgs}:
pkgs.mkShell {
  packages = with pkgs; [
    xz

    python311
    uv
    ruff
    ty

    nodejs_24
    pnpm
    biome
  ];
}
