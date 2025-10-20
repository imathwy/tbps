{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        formatter = pkgs.alejandra;
        devShells.default = import ./pkgs/shell.nix {inherit pkgs;};
        packages = {
          tbps-be = import ./pkgs/tbps-be.nix {inherit pkgs;};
        };
      }
    );
}
