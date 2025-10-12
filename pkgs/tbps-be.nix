{pkgs}: let
  pname = "tbps-be";
in
  pkgs.dockerTools.buildImage {
    name = pname;
    tag = "latest";

    copyToRoot = pkgs.buildEnv {
      name = pname;
      pathsToLink = ["/bin"];
      paths = with pkgs; [
        coreutils

        python311
        uv
        nodejs_24
        elan

        (pkgs.runCommand "app-src" {} ''
          mkdir -p $out/app
          cp -r ${pkgs.lib.cleanSource ../.}/* $out/app/
        '')
      ];
    };

    runAsRoot = ''
      cd /app || exit 1

      cd tbps-be || exit 1
      uv venv
      source .venv/bin/activate
      cd ..

      ./scripts/build-lean.sh

      cd tbps-be || exit 1
      uv add -r requirements.txt
    '';

    config = {
      Workdir = "/app/tbps-be";
      Cmd = [
        "uv"
        "run"
        "main_server.py"
      ];
    };
  }
