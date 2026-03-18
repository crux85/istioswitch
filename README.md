# istioswitch

A cross-platform CLI tool for Windows, Linux, and macOS to switch between multiple versions of `istioctl` binaries easily. Inspired by [tfswitch](https://github.com/warrensbox/terraform-switcher).

## Features

- **Cross-Platform:** Native support for Windows (x64), Linux (amd64, arm64), and macOS (Intel, Apple Silicon).
- **Standalone Binaries:** No Python required! Download the executable and run it directly.
- **Automated Downloads:** Fetches binaries directly from official Istio GitHub releases.
- **Auto-Detection:** Detects the required Istio version from your current Kubernetes cluster (`istiod` image).
- **Shim Management:** Automatically manages wrapper scripts injected into your PATH.
- **Caching:** Caches downloaded versions locally to avoid repeated downloads.

## Installation

### Option 1: Download Standalone Binary (Recommended)
You can download the pre-compiled binary for your OS directly from the [GitHub Releases](https://github.com/crux85/istioswitch/releases) page.

1. Download the executable:
   - **Windows:** `istioswitch-windows-amd64.exe` (rename it to `istioswitch.exe`)
   - **Linux:** `istioswitch-linux-amd64` (rename to `istioswitch` and `chmod +x istioswitch`)
   - **macOS:** `istioswitch-darwin-amd64` (rename to `istioswitch` and `chmod +x istioswitch`)
2. Place the executable in a directory that is in your system's `PATH`.

### Option 2: Install via pip
If you prefer using Python, you can install the tool via pip:

```bash
pip install istioswitch
```
*(Note: If not published on PyPI yet, clone the repo and run `pip install .`)*

## Post-installation Setup (Shim configuration)

To allow `istioswitch` to switch `istioctl` versions on the fly, it creates a "shim" (a small wrapper script) that needs to be accessible globally. 
**You must add its bin directory to your PATH:**

- **Windows (PowerShell):**
  ```powershell
  $env:PATH += ";$env:USERPROFILE\.istioswitch\bin"
  [System.Environment]::SetEnvironmentVariable("PATH", $env:PATH, [System.EnvironmentVariableTarget]::User)
  ```
- **Linux/macOS:**
  ```bash
  export PATH="$HOME/.istioswitch/bin:$PATH"
  ```
*(Add the Linux/macOS line to your `~/.bashrc` or `~/.zshrc` to make it persistent).*

## Usage

List available and cached versions:
```bash
istioswitch list
```

Install a specific version without switching to it:
```bash
istioswitch install 1.25.3
```

Use a specific version (will download and install it if missing):
```bash
istioswitch use 1.25.3
```

Show the currently active version:
```bash
istioswitch current
```

Detect Istio version from the current Kubernetes context and use it:
```bash
istioswitch detect
```
*(Tip: You can pass a specific context using `istioswitch detect --context my-cluster-ctx`)*

Uninstall a cached version to free up disk space:
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