import typer
import os
from rich.console import Console
from behemoth.core import BattleOrchestrator
from behemoth.utils.scryer import WarlockScryer

app = typer.Typer(help="The Behemoth: An AI-Agent API Security Fuzzer")
console = Console()

@app.command()
def attack(
    url: str = typer.Option(...,"--url", "-u", help="The base URL of the Target API"),
    spec: str = typer.Option(None, "--spec", "-s", help="Path to the Swagger/OpenAPI JSON (optional)"),
    level: str = typer.Option("medium", "--level", "-l", help="Aggression Level: low, medium, high")
):
    """
    Summon the Behemoth to Find and Heal Security Vulnerabilities
    """
    console.print(f"[bold red]Summoning Behemoth...[/bold red] 👹")

    if not spec:
        domain = url.split("//")[-1].split("/")[0]
        console.print(f"[*] No spec provided. Warlock is scrying for [cyan]{domain}[/cyan]...")

        scryer = WarlockScryer(domain)
        spec = scryer.scry_and_absorb()

        if not spec:
            console.print("[bold yellow][!] The Warlock found no battle map in he mists.[/bold yellow]")
            console.print("[*] Please provide a manual path using [green]--spec[/green].")
            raise typer.Exit()
        
        else:
            if not os.path.exists(spec):
                console.print(f"[bold red][!] Error: Local spec file not found at {spec}[/bold red]")
                raise typer.Exit()
            
    console.print(f"[*] Battle Map: [green]{spec}[/green]")
    console.print(f"[*] Targeting: [cyan]{url}[/cyan]")
    console.print(f"[*] Level: [yellow]{level}[/yellow]\n")

    # Initialize the engine
    orchestrator = BattleOrchestrator(spec, url)
    
    # Start the war
    try:
        orchestrator.start_war(level=level)
    except KeyboardInterrupt:
        console.print("\n[bold yellow][!] Retreating... War interrupted by user.[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red][!] The Behemoth has collapsed: {e}[/bold red]")

if __name__ == "__main__":
    app()