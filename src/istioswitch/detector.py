import subprocess
import re
from typing import Optional


def detect_istio_version(context: Optional[str] = None) -> str:
    cmd = [
        "kubectl",
        "get",
        "deployment",
        "istiod",
        "-n",
        "istio-system",
        "-o",
        "jsonpath={.spec.template.spec.containers[0].image}",
    ]
    if context:
        cmd.extend(["--context", context])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Failed to detect istiod deployment in istio-system namespace. Make sure kubectl is configured."
        )
    except FileNotFoundError:
        raise RuntimeError("kubectl command not found.")

    image = result.stdout.strip()
    match = re.search(r":([\w\.\-]+)", image)
    if not match:
        raise RuntimeError(f"Could not parse version from image: {image}")

    version = match.group(1)
    # Strip potential suffixes like -distroless
    version = version.split("-")[0]
    return version
