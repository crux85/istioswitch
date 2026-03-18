# istioswitch

A cross-platform CLI tool for Windows, Linux, and macOS to switch between multiple versions of `istioctl` binaries easily. Inspired by [tfswitch](https://github.com/warrensbox/terraform-switcher).

## Features

- **Cross-Platform:** Native support for Windows (x64), Linux (amd64, arm64), and macOS (Intel, Apple Silicon).
- **Automated Downloads:** Fetches binaries directly from official Istio GitHub releases.
- **Auto-Detection:** Detects the required Istio version from your current Kubernetes cluster (`istiod` image).
- **Shim Management:** Automatically manages wrapper scripts injected into your PATH.
- **Caching:** Caches downloaded versions locally to avoid repeated downloads.

## Installation

Install via pip:

```bash
pip install istioswitch
```

*(Note: Since it is not yet on PyPI, clone this repo and run `pip install .`)*

### Post-installation Setup

To allow `istioswitch` to switch versions on the fly, you must add its bin directory to your PATH:

- **Windows (PowerShell):**
  ```powershell
  $env:PATH += ";$env:USERPROFILE\.istioswitch\bin"
  [System.Environment]::SetEnvironmentVariable("PATH", $env:PATH, [System.EnvironmentVariableTarget]::User)
  ```
- **Linux/macOS:**
  ```bash
  export PATH="$HOME/.istioswitch/bin:$PATH"
  ```

## Usage

List available and cached versions:
```bash
istioswitch list
```

Install a specific version:
```bash
istioswitch install 1.25.3
```

Use a specific version (will install if missing):
```bash
istioswitch use 1.25.3
```

Show current active version:
```bash
istioswitch current
```

Detect Istio version from current Kubernetes context and use it:
```bash
istioswitch detect
```

Uninstall a cached version:
```bash
istioswitch uninstall 1.24.6
```

## Contributing

We follow **GitHub Flow**:
- `main` is always stable.
- Open a PR for any features/fixes from a `feature/*` or `hotfix/*` branch.
- Squash merges are preferred to maintain a clean history.
- Ensure all tests pass (`pytest --cov`). We maintain an 80% coverage minimum.

### GitHub Branch Protection Rules (For Admins)
- Require a Pull Request before merging to `main`.
- Require status checks to pass (CI workflows).
- Require at least 1 approving review.
- No force pushes allowed on `main`.

## License

MIT License