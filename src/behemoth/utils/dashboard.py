from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from datetime import datetime

class WarRoom:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.logs = []
        self.stats = {"strikes": 0, "vulns": 0, "criticals": 0}

        self.layout.split_column(
            Layout(name="upper", size=10),
            Layout(name="lower")
        )

        self.layout["upper"].split_row(
            Layout(name="status", ratio=2),
            Layout(name="stats", ratio=1)
        )

    def update_status(self, key, value):
        stats_text = (
            f"[bold cyan]Total Strikes:[/bold cyan] {self.stats['strikes']}\n"
            f"[bold yellow]Potential Vulns:[/bold yellow] {self.stats['vulns']}\n"
            f"[bold red]Criticals Leaks:[/bold red] {self.stats['criticals']}\n"
            f"[bold green]Target:[/bold green] {key}\n"
            f"[bold magenta]Method:[/bold magenta] {value}\n"
        )
        self.layout["status"].update(
            Panel(stats_text, title="Battle Analytics")
        )

    def update_loot_display(self, session_cookies):
        loot_count = len([k for k in session_cookies.keys() if k.startswith('loot_')])
        self.stats["loot_harvested"] = loot_count
    
    def generate_table(self):
        table = Table(title="Live Battle Logs", expand=True)
        table.add_column("Time", style="cyan")
        table.add_column("Agent", style="magenta")
        table.add_column("Message", style="white")

        for log in self.logs[-20:]:
            table.add_row(*log)
        
        return Panel(table, title="Spirit-Eye Log Stream", border_style="blue")
    
    def add_log(self, agent, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        agent_colors = {
            "Warlock": "[purple]Warlock[/purple]",
            "Berserker": "[red]Berserker[/red]",
            "Alchemist": "[green]Alchemist[/green]",
            "Paladin": "[blue]Paladin[/blue]"
        }
        display_agent = agent_colors.get(agent, agent)
        self.logs.append([timestamp, display_agent, message])
        
        self.layout["lower"].update(self.generate_table())