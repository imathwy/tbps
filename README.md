# Tree-Based Premise Selection for Lean4

This repository contains the implementation of the paper [Tree-Based Premise Selection for Lean4](https://neurips.cc/virtual/2025/poster/116011), presented at NeurIPS 2025.

## Quick Start

### Install Docker

- **macOS**: See [OrbStack documentation](https://orbstack.dev/)
- **Windows/Linux**: See [Docker Desktop documentation](https://www.docker.com/products/docker-desktop/)

### Install Nix

```sh
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

For additional details, refer to the [Zero to Nix documentation](https://zero-to-nix.com/start/install/).

### Clone this Repository

```sh
git clone https://github.com/imathwy/tbps.git
```

### Enter Shell with Required Dependencies

```sh
nix develop
```

> [!CAUTION]
> All subsequent operations must be executed within the `nix develop` shell. Required dependencies will not be available outside this environment.

### Enable Git LFS

This repository uses Git LFS. The tool is included in the `nix develop` shell, or can be installed separately via the [Git LFS documentation](https://git-lfs.com/).

Execute the following command to initialize Git LFS and retrieve data:

```sh
git lfs pull
```

### Initialize Database Service and Import Data

```sh
./scripts/import-data.sh
```

## Usage

The premise selection tool provides two interfaces: a command-line interface and a web GUI.

### Command Line Tool

```sh
./scripts/run-cli.sh
```

### Web GUI

```sh
./scripts/run-web.sh
```

After starting the service, access the web GUI at <http://localhost:3000/>.
