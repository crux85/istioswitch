import click
from rich.console import Console

from istioswitch import installer, switcher, config, detector
from istioswitch.platform_utils import get_os

console = Console()

@click.group()
def cli():
    """istioswitch - Switch between multiple versions of istioctl"""
    pass

@cli.command()
def list():
    """List available istioctl versions."""
    try:
        with console.status("[cyan]Fetching available versions..."):
            versions = installer.get_available_versions(20)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return

    active = config.get_active_version()
    console.print("Available istioctl versions (last 20):")
    for v in versions:
        marker = "->" if v == active else "  "
        cached = "*" if installer.is_installed(v) else " "
        status = "[active]" if v == active else ("[cached]" if installer.is_installed(v) else "")
        console.print(f"  {marker} {v:<8} {cached} {status}".strip())

@cli.command()
@click.argument("version")
def install(version: str):
    """Install a specific version of istioctl."""
    if installer.is_installed(version):
        console.print(f"[yellow]Version {version} is already installed.[/yellow]")
        return
        
    try:
        installer.install_version(version)
        console.print("[green]✓ Checksum verified.[/green]")
        console.print(f"[green]✓ istioctl {version} installed.[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@cli.command()
@click.argument("version")
def use(version: str):
    """Use a specific version of istioctl."""
    try:
        if not installer.is_installed(version):
            console.print(f"[cyan]Version {version} not found locally. Installing...[/cyan]")
            installer.install_version(version)
            console.print("[green]✓ Checksum verified.[/green]")
            console.print(f"[green]✓ istioctl {version} installed.[/green]")
            
        in_path, bin_dir = switcher.use_version(version)
        console.print(f"[green]✓ Switched to istioctl {version}[/green]")
        if not in_path:
            console.print(f"[yellow]Reminder:[/yellow] Please add {bin_dir} to your PATH.")
            if get_os() == "windows":
                console.print(f'[cyan]setx PATH "%PATH%;{bin_dir}"[/cyan]')
            else:
                console.print(f'[cyan]export PATH="{bin_dir}:$PATH"[/cyan]')
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@cli.command()
def current():
    """Show the currently active istioctl version."""
    active = config.get_active_version()
    if active:
        console.print(f"Active version: {active}")
    else:
        console.print("No active version set.")

@cli.command()
@click.option("--context", "-c", help="Target kubeconfig context")
def detect(context: str):
    """Detect istioctl version from Kubernetes cluster."""
    try:
        with console.status("[cyan]Detecting Istio version..."):
            version = detector.detect_istio_version(context)
        
        ctx_str = f" on context {context}" if context else ""
        console.print(f"Detected Istio version{ctx_str}: {version}")
        
        if installer.is_installed(version):
            console.print(f"[green]✓ Version {version} already cached.[/green]")
        else:
            installer.install_version(version)
            console.print(f"[green]✓ istioctl {version} installed.[/green]")
            
        switcher.use_version(version)
        console.print(f"[green]✓ Switched to istioctl {version}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@cli.command()
@click.argument("version")
def uninstall(version: str):
    """Uninstall a specific cached version."""
    try:
        installer.uninstall_version(version)
        console.print(f"[green]✓ Version {version} removed from cache.[/green]")
        if config.get_active_version() == version:
            config.set_active_version(None)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

if __name__ == "__main__":
    cli()
