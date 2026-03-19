import subprocess
import re
from typing import Optional


def get_current_context() -> str:
    cmd = ["kubectl", "config", "current-context"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown-context"
    except FileNotFoundError:
        return "unknown-context"


def detect_istio_version(context: Optional[str] = None) -> str:
    # Use label selector to find any istiod deployment (works for vanilla and ASM)
    cmd = [
        "kubectl",
        "get",
        "deployment",
        "-n",
        "istio-system",
        "-l",
        "app=istiod",
        "-o",
        "jsonpath={.items[0].spec.template.spec.containers[0].image}",
    ]
    if context:
        cmd.extend(["--context", context])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Failed to detect istiod deployment in istio-system namespace. Make sure kubectl is configured and you have access."
        )
    except FileNotFoundError:
        raise RuntimeError("kubectl command not found.")

    image = result.stdout.strip()
    if not image:
        raise RuntimeError(
            "No image found for istiod deployment. Ensure the istio-system namespace has a deployment with label app=istiod."
        )

    match = re.search(r":([\w\.\-]+)", image)
    if not match:
        raise RuntimeError(f"Could not parse version from image: {image}")

    version = match.group(1)
    # Strip potential suffixes like -distroless or -asm.1
    version = version.split("-")[0]
    return version
