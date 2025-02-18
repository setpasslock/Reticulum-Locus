import os
import importlib
import shlex
import subprocess
from rich.console import Console
from rich.panel import Panel
from prompt_toolkit.styles import Style 
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from storage import IPRangeStorage

class InteractiveConsole:
    def __init__(self):
        self.console = Console()
        self.running = True
        self.current_city = None
        self.current_country = None
        self.current_country_code = None
        self.current_region = None
        
        self.ip_storage = IPRangeStorage()
        
        self.modules = {}
        self.current_module = None
        self.load_modules()
        
        history_file = os.path.expanduser('~/.locus_history')

        style = Style.from_dict({
            'red': '#ff0000',
            'cyan': '#00ffff'
        })

        self.session = PromptSession(
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            complete_while_typing=True,
            style=style
        )

        
        
        self._init_commands()
        self._init_completer()
    
    def _init_commands(self):
        self.commands = {
            'help': self.show_help,
            'exit': self.exit,
            'back': self.back,
            'clear': self.clear_screen,
            'history': self.show_history,
            'show_current': self.show_current,
            'show_ranges': self.show_ranges,
            'show_modules': self.show_modules,
            'show_options': self.show_options,
            'show_selections': self.show_selections,
            'use_module': self.use_module,
            'export_ranges': self.export_ranges,
            'get_ips': self.get_ips,
            'select_ranges': self.select_ranges,
        }
    
    def _init_completer(self):
        self.completer = WordCompleter([
            'set city', 'set country', 'set country-code', 'set region',
            'update', 'help', 'exit', 'back', 'clear', 'history', 
            'show current', 'show ranges', 'show modules', 'show options',
            'show selections', 'use module', 'export ranges', 'get ips',
            'select ranges', 'run'
        ])
    
    def _get_prompt(self):
        if self.current_module:
            return [
                ('class:default', '['),
                ('class:red', 'locus'),
                ('class:default', ']\n['),
                ('class:cyan', self.current_module),
                ('class:default', '] > ')
            ]
        return [
            ('class:default', '['),
            ('class:red', 'locus'),
            ('class:default', '] > ')
        ]
    
    def back(self, *args):
        if self.current_module:
            self.current_module = None
            self.console.print("[yellow]Exited from module[/yellow]")
            self._init_completer()
        else:
            self.console.print("[yellow]Not in a module[/yellow]")
    
    def execute_shell_command(self, command):
        try:
            command = command[1:].strip()
            
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True
            )
            
            if result.stdout:
                self.console.print(result.stdout.strip())
            
            if result.stderr:
                self.console.print(f"[red]{result.stderr.strip()}[/red]")
                
            return result.returncode == 0
        except Exception as e:
            self.console.print(f"[red]Error executing command: {str(e)}[/red]")
            return False
    def load_modules(self):
        current_dir = os.path.dirname(__file__)
        for file in os.listdir(current_dir):
            if file.endswith('_module.py'):
                module_name = file[:-3]
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, 'MODULE_INFO'):
                        self.modules[module_name] = {
                            'info': module.MODULE_INFO,
                            'module': module
                        }
                except Exception as e:
                    self.console.print(f"[red]Error loading module {module_name}: {str(e)}[/red]")
    
    def show_help(self, *args):
        help_text = """
            [bold cyan]Available Commands:[/bold cyan]

            [yellow]Shell Commands:[/yellow]
            !<command>       Execute shell command (e.g., !ls, !whoami, !ifconfig)

            [yellow]Basic Commands:[/yellow]
            help              Show this help message
            exit              Exit module or console
            back              Exit from current module
            clear             Clear the screen
            history           Show command history

            [yellow]Module Commands:[/yellow]
            show modules      List available modules
            show options     Show current module options and values
            use module       Switch to a specific module
            set <option>     Set module option value
            run              Run current module

            [yellow]Target Commands:[/yellow]
            set city NAME        Set target city
            set country NAME     Set target country
            set region NAME      Set target region/state
            set country-code CC  Set target country code
            show current         Show current target settings

            [yellow]IP Range Commands:[/yellow]
            show ranges       Show stored IP ranges
            show selections   Show stored selections
            select ranges    Select specific ranges from a query
            export ranges     Export IPs to file (Use --full for individual IPs)
            get ips          Show all individual IPs for a specific query

            [yellow]Selection Examples:[/yellow]
            select ranges city_1 1-5        Select ranges 1 through 5
            select ranges city_1 1,3,5      Select specific ranges
            select ranges city_1 1-3,7,9-11 Select multiple ranges
            
            [yellow]Shell Command Examples:[/yellow]
            !ls -la           List files with details
            !whoami           Show current user
            !ifconfig         Show network interfaces
            !ping -c 4 host   Ping a host
            """
        self.console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def show_current(self, *args):
        settings = f"""
            [cyan]Current Target Settings:[/cyan]
            City: {self.current_city or 'Not set'}
            Region: {self.current_region or 'Not set'}
            Country: {self.current_country or 'Not set'}
            Country Code: {self.current_country_code or 'Not set'}
        """
        self.console.print(Panel(settings, border_style="blue"))
    
    def clear_screen(self, *args):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def exit(self, *args):
        if self.current_module:
            self.back()
        else:
            self.running = False
            self.console.print("[yellow]Goodbye![/yellow]")
    
    def _reset_targets(self):
        self.current_city = None
        self.current_country = None
        self.current_country_code = None
        self.current_region = None

    def show_modules(self, *args):
        if not self.modules:
            self.console.print("[yellow]No modules available[/yellow]")
            return
            
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="blue")
        table.add_column("Version", style="yellow")
        
        for module_id, module_data in self.modules.items():
            info = module_data['info']
            table.add_row(
                module_id,
                info.get('name', 'Unknown'),
                info.get('description', 'No description'),
                info.get('version', '1.0.0')
            )
        
        self.console.print(table)
    
    def show_options(self, *args):
        if not self.current_module:
            self.console.print("[red]Error: No module selected. Use 'use module <module_id>' first[/red]")
            return
            
        module_options = self.modules[self.current_module]['info'].get('options', {})
        if not module_options:
            self.console.print("[yellow]No options available for this module[/yellow]")
            return
            
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan")
        table.add_column("Current Value", style="green")
        table.add_column("Description", style="blue")
        table.add_column("Required", style="yellow")
        
        for option, details in module_options.items():
            table.add_row(
                option,
                str(details.get('value', 'Not set')),
                details.get('description', ''),
                '✓' if details.get('required', False) else ''
            )
        
        self.console.print("\n[cyan]Module Options:[/cyan]")
        self.console.print(table)
    
    def use_module(self, *args):
        if len(args) < 1:
            self.console.print("[red]Usage: use module <module_id>[/red]")
            return
            
        module_id = args[0]
        if module_id not in self.modules:
            self.console.print(f"[red]Module '{module_id}' not found[/red]")
            return
            
        self.current_module = module_id
        module_info = self.modules[module_id]['info']
        
        module_options = module_info.get('options', {})
        completer_words = [
            'set city', 'set country', 'set country-code', 'set region',
            'update', 'help', 'exit', 'back', 'clear', 'history', 
            'show current', 'show ranges', 'show modules', 'show options', 'show selections',
            'use module', 'export ranges', 'get ips', 'select ranges', 'run'
        ]
        
        for option in module_options.keys():
            completer_words.append(f'set {option}')
            
        self.completer = WordCompleter(completer_words)
        
        self.console.print(f"[green]Switched to module: {module_info['name']}[/green]")
        
        if module_options:
            self.show_options()
    
    def show_history(self, *args):
        try:
            with open(self.session.history.filename, 'r') as f:
                history = f.readlines()
            
            history_text = "\n".join(f"[dim]{i+1}[/dim] {line.strip()}" 
                                   for i, line in enumerate(history[-20:]))
            self.console.print(Panel(history_text, 
                                   title="Last 20 Commands", 
                                   border_style="blue"))
        except Exception as e:
            self.console.print(f"[red]Error reading history: {str(e)}[/red]")
    
    def store_query_results(self, query_type, query_value, results):
        query_id = self.ip_storage.add_range(query_type, query_value, results)
        self.console.print(f"[green]Query results stored with ID: {query_id}[/green]")
        return query_id
    
    def show_ranges(self, *args):
        ranges = self.ip_storage.get_ranges()
        selections = self.ip_storage.selections
        
        if not ranges and not selections:
            self.console.print("[yellow]No stored IP ranges or selections found[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Value/Selection", style="blue")
        table.add_column("Range Count", style="yellow")
        
        for query_id, data in ranges.items():
            table.add_row(
                query_id,
                data['query_type'],
                data['query_value'],
                str(len(data['ip_ranges']))
            )
        
        for sel_id, data in selections.items():
            table.add_row(
                sel_id,
                "selection",
                f"From {data['query_id']}: {data['selection_str']}",
                str(len(data['indices']))
            )
        
        self.console.print(table)
    
    def show_selections(self, *args):
        selections = self.ip_storage.selections
        if not selections:
            self.console.print("[yellow]No selections found[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Selection ID", style="cyan")
        table.add_column("Query ID", style="green")
        table.add_column("Selection", style="blue")
        table.add_column("Range Count", style="yellow")
        
        for sel_id, data in selections.items():
            table.add_row(
                sel_id,
                data['query_id'],
                data['selection_str'],
                str(len(data['indices']))
            )
        
        self.console.print(table)
    
    def select_ranges(self, *args):
        if len(args) < 2:
            self.console.print("[red]Usage: select ranges <query_id> <selection>[/red]")
            self.console.print("[yellow]Examples:[/yellow]")
            self.console.print("  select ranges city_1 1-5")
            self.console.print("  select ranges city_1 1,3,5")
            self.console.print("  select ranges city_1 1-3,7,9-11")
            return
        
        query_id = args[0]
        selection_str = args[1]
        
        selection_id = self.ip_storage.create_selection(query_id, selection_str)
        if selection_id:
            self.console.print(f"[green]Selection created with ID: {selection_id}[/green]")
            
            selection = self.ip_storage.get_selection(selection_id)
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Index", style="cyan")
            table.add_column("IP Range", style="green")
            table.add_column("Location", style="blue")
            
            query_ranges = self.ip_storage.get_ranges(query_id)['ip_ranges']
            for idx in selection['indices']:
                ip_range = query_ranges[idx]
                location = ip_range['location']
                table.add_row(
                    str(idx + 1),
                    f"{ip_range['start']} - {ip_range['end']}",
                    f"{location['city']}, {location['region']}, {location['country']}"
                )
            
            self.console.print(table)
        else:
            self.console.print("[red]Error: Invalid selection format or query ID[/red]")
    
    def export_ranges(self, *args):
        if len(args) < 1:
            self.console.print("[red]Usage: export ranges <query_id/selection_id> [filename] [--full][/red]")
            self.console.print("[yellow]Use --full flag to export all individual IPs instead of ranges[/yellow]")
            return
        
        query_id = args[0]
        filename = args[1] if len(args) > 1 else f"ips_{query_id}.txt"
        export_full = '--full' in args
        
        if '_sel_' in query_id:
            if export_full:
                ip_list = self.ip_storage.get_selection_ip_list(query_id)
            else:
                ranges = self.ip_storage.get_selection_range_list(query_id)
        else:
            if export_full:
                ip_list = self.ip_storage.get_ip_list(query_id)
            else:
                ranges = self.ip_storage.get_range_list(query_id)
        
        try:
            if export_full:
                if not ip_list:
                    self.console.print(f"[red]No IPs found for ID: {query_id}[/red]")
                    return
                
                with open(filename, 'w') as f:
                    for ip in ip_list:
                        f.write(f"{ip}\n")
                
                self.console.print(f"[green]{len(ip_list)} IPs exported to {filename}[/green]")
            else:
                if not ranges:
                    self.console.print(f"[red]No ranges found for ID: {query_id}[/red]")
                    return
                
                with open(filename, 'w') as f:
                    for start, end in ranges:
                        f.write(f"{start} - {end}\n")
                
                self.console.print(f"[green]{len(ranges)} IP ranges exported to {filename}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error exporting: {str(e)}[/red]")
    
    def get_ips(self, *args):
        if len(args) < 1:
            self.console.print("[red]Usage: get ips <query_id/selection_id>[/red]")
            return
        
        query_id = args[0]
        
        if '_sel_' in query_id:
            ip_list = self.ip_storage.get_selection_ip_list(query_id)
        else:
            ip_list = self.ip_storage.get_ip_list(query_id)
            
        if not ip_list:
            self.console.print(f"[red]No IPs found for ID: {query_id}[/red]")
            return
        
        self.console.print(f"[cyan]IPs for {query_id} (Total: {len(ip_list)}):[/cyan]")
        
        for i in range(0, len(ip_list), 5):
            group = ip_list[i:i+5]
            self.console.print("  " + "  ".join(group))
    
    def process_command(self, command_line):
        if not command_line.strip():
            return
            
        if command_line.startswith('!'):
            self.execute_shell_command(command_line)
            return
            
        try:
            args = shlex.split(command_line)
            if not args:
                return
                
            command = args[0].lower()
            
            if len(args) > 1:
                possible_command = f"{command}_{args[1].lower()}"
                if possible_command in self.commands:
                    self.commands[possible_command](*args[2:])
                    return
            
            if command == 'set':
                if len(args) < 3:
                    self.console.print("[red]Error: Invalid set command[/red]")
                    return
                
                target_type = args[1].lower()
                target_value = " ".join(args[2:])
                
                if self.current_module:
                    module_options = self.modules[self.current_module]['info'].get('options', {})
                    if target_type in module_options:
                        module_options[target_type]['value'] = target_value
                        self.console.print(f"[green]Set {target_type} = {target_value}[/green]")
                        return
                
                self._reset_targets()
                
                if target_type == 'city':
                    self.current_city = target_value
                    self.console.print(f"[green]City target set to: {target_value}[/green]")
                    return "--city " + shlex.quote(target_value)
                elif target_type == 'country':
                    self.current_country = target_value
                    self.console.print(f"[green]Country target set to: {target_value}[/green]")
                    return "--country " + shlex.quote(target_value)
                elif target_type == 'country-code':
                    self.current_country_code = target_value
                    self.console.print(f"[green]Country code target set to: {target_value}[/green]")
                    return "--country-code " + shlex.quote(target_value)
                elif target_type == 'region':
                    self.current_region = target_value
                    self.console.print(f"[green]Region target set to: {target_value}[/green]")
                    return "--region " + shlex.quote(target_value)
                else:
                    self.console.print("[red]Error: Invalid target type[/red]")
                    return
            
            if command == 'run':
                if not self.current_module:
                    self.console.print("[red]Error: No module selected. Use 'use module <module_id>' first[/red]")
                    return
                
                module_options = self.modules[self.current_module]['info']['options']
                input_file = module_options.get('input_file', {}).get('value')
                query_id = module_options.get('query_id', {}).get('value')
                
                if input_file and os.path.exists(input_file):
                    self.console.print(f"[yellow]Using input file: {input_file}[/yellow]")
                    module_instance = self.modules[self.current_module]['module'].create_instance()
                    success, result = module_instance.run([])
                elif query_id:
                    if '_sel_' in query_id:
                        ip_list = self.ip_storage.get_selection_ip_list(query_id)
                    else:
                        if query_id.lower() == 'all':
                            ip_list = []
                            for qid in self.ip_storage.get_ranges().keys():
                                ip_list.extend(self.ip_storage.get_ip_list(qid))
                        else:
                            ip_list = self.ip_storage.get_ip_list(query_id)
                    
                    if not ip_list:
                        self.console.print(f"[red]Error: No IPs found for ID: {query_id}[/red]")
                        return
                    
                    self.console.print(f"[yellow]Starting scan of {len(ip_list)} IP addresses...[/yellow]")
                    
                    module_instance = self.modules[self.current_module]['module'].create_instance()
                    success, result = module_instance.run(ip_list)
                else:
                    self.console.print("[red]Error: Either input_file or query_id must be set[/red]")
                    return
                
                if success:
                    if not result:
                        self.console.print("[yellow]No results found[/yellow]")
                        return
                        
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("IP", style="cyan")
                    table.add_column("Open Ports", style="green")
                    
                    for ip_result in result:
                        table.add_row(
                            ip_result['ip'],
                            ", ".join(map(str, ip_result['open_ports']))
                        )
                    
                    self.console.print(table)
                else:
                    self.console.print(f"[red]Error running module: {result}[/red]")
                return
            
            if command in self.commands:
                self.commands[command](*args[1:])
            elif command == 'update':
                return '--update'
            else:
                self.console.print(f"[red]Unknown command: {command}[/red]")
                
        except Exception as e:
            self.console.print(f"[red]Error processing command: {str(e)}[/red]")
    
    def run(self):
        while self.running:
            try:
                command_line = self.session.prompt(
                    self._get_prompt(),
                    completer=self.completer,
                    complete_while_typing=True
                )
                
                result = self.process_command(command_line)
                
                if result:
                    return result
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except EOFError:
                self.exit()
                break