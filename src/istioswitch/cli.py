import click
from rich.console import Console

from istioswitch import installer, switcher, config, detector
from istioswitch.platform_utils import get_os

console = Console()


def switch_to_version(version: str):
    """Helper function to install and switch to a given version."""
    try:
        if not installer.is_installed(version):
            console.print(
                f"[cyan]Version {version} not found locally. Installing...[/cyan]"
            )
            installer.install_version(version)
            console.print("[green]✓ Checksum verified.[/green]")
            console.print(f"[green]✓ istioctl {version} installed.[/green]")

        in_path, bin_dir = switcher.use_version(version)
        console.print(f"[green]✓ Switched to istioctl {version}[/green]")
        if not in_path:
            console.print(
                f"[yellow]Reminder:[/yellow] Please add {bin_dir} to your PATH."
            )
            if get_os() == "windows":
                console.print(f'[cyan]setx PATH "%PATH%;{bin_dir}"[/cyan]')
            else:
                console.print(f'[cyan]export PATH="{bin_dir}:$PATH"[/cyan]')
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def auto_switch():
    """Detects version from cluster and switches to it."""
    try:
        context_name = detector.get_current_context()
        ctx_str = (
            f" on context {context_name}"
            if context_name and context_name != "unknown-context"
            else ""
        )

        with console.status(f"[cyan]Detecting Istio version{ctx_str}..."):
            version = detector.detect_istio_version()

        console.print(f"Detected Istio version{ctx_str}: {version}")
        switch_to_version(version)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


class IstioSwitchCLI(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # Fallback: Treat unknown command as a version string
        @click.command(name=cmd_name)
        def use_version_cmd():
            switch_to_version(cmd_name)

        return use_version_cmd


@click.group(cls=IstioSwitchCLI, invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """istioswitch - Switch between multiple versions of istioctl"""
    if ctx.invoked_subcommand is None:
        auto_switch()


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
        status = (
            "[active]"
            if v == active
            else ("[cached]" if installer.is_installed(v) else "")
        )
        console.print(f"  {marker} {v:<8} {cached} {status}".strip())


@cli.command()
@click.argument("version")
def install(version: str):
    """Install a specific version of istioctl without switching."""
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
@click.option("--context", "-c", help="Target kubeconfig context")
def detect(context: str):
    """Show the istioctl version from Kubernetes cluster without switching."""
    try:
        ctx_name = context if context else detector.get_current_context()
        with console.status(f"[cyan]Detecting Istio version on context {ctx_name}..."):
            version = detector.detect_istio_version(context)

        console.print(
            f"Detected Istio version on {ctx_name}: [bold green]{version}[/bold green]"
        )
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
