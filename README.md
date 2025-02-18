# Locus - IP Range Scanner by Location

Locus is a powerful command-line tool for IP intelligence gathering that allows you to search for and analyze IP ranges by geographic location. With interactive console capabilities and modular design, Locus helps security researchers, network administrators, and penetration testers identify and scan IP ranges across different regions.

## Features

- Search IP ranges by city, region, country name, or country code
- Automatic IP2Location database management
- Rich, colorful console interface with command history
- Modular architecture for extensibility
- Export IP ranges or individual IPs to files
- Create and manage selections of IP ranges
- Integrated scanning capabilities using RustScan and ZMap modules

## Prerequisites

- Python 3.6+
- Required Python packages (install via `pip3 install -r requirements.txt`):

- External dependencies:
  - RustScan (https://github.com/RustScan/RustScan)
  - ZMap (https://github.com/zmap/zmap)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/setpasslock/Reticulum-Locus.git
   cd Reticulum-Locus
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install RustScan and ZMap:
   - For Debian/Ubuntu:
     ```
     apt-get update
     apt-get install -y zmap
     cargo install rustscan
     ```
   - For other systems, refer to the respective project documentation

4. Configure your IP2Location API token:
   - Register for a free account at [IP2Location](https://lite.ip2location.com/database-download)
   - Get your download token from the account dashboard
   - Edit the `config.py` file and replace the placeholder with your token:
     ```python
     IP2LOCATION_TOKEN = "your_token_here"
     ```

5. Initialize the database:
   ```
   python3 locus.py --update
   ```

## Usage

### Basic Usage

Start the interactive console:
```
python locus.py
```

Or run a query and enter the interactive console:
```
python locus.py --city "San Juan"
```

### Interactive Console Commands

The tool features an interactive console with the following commands:

#### Basic Commands
- `help` - Show help message
- `exit` - Exit the console
- `clear` - Clear the screen
- `history` - Show command history
- `!<command>` - Execute shell command (e.g., `!ls`, `!ifconfig`)

#### Target Setting
- `set city NAME` - Set target city
- `set country NAME` - Set target country
- `set region NAME` - Set target region/state  
- `set country-code CC` - Set target country code
- `show current` - Show current target settings

#### IP Range Management
- `show ranges` - Show stored IP ranges
- `show selections` - Show stored selections
- `select ranges QUERY_ID RANGE_SPEC` - Select specific ranges
- `export ranges QUERY_ID [FILENAME] [--full]` - Export IP ranges or IPs
- `get ips QUERY_ID` - Show all individual IPs for a query

#### Module Commands
- `show modules` - List available modules
- `use module MODULE_ID` - Switch to a specific module
- `show options` - Show current module options
- `set OPTION VALUE` - Set module option
- `run` - Run current module
- `back` - Exit from current module

### Selection Syntax Examples

```
select ranges city_1 1-5        # Select ranges 1 through 5
select ranges city_1 1,3,5      # Select specific ranges
select ranges city_1 1-3,7,9-11 # Select multiple ranges
```

### Scanning Example

```
use module rustscan_module
set query_id city_1
set ports 80,443,8080
run
```

## Modules

### Built-in Modules

1. **RustScan Module**
   - Fast port scanning using RustScan
   - Customize scan parameters including ports, timeouts, and batch size

2. **ZMap Module**
   - Efficient network scanning for single ports across large IP ranges
   - Supports bandwidth limiting and custom probe modules

## Database Updates

Update the IP2Location database:
```
python locus.py --update
```
Or from the interactive console:
```
update
```

## Exporting Data

Export IP ranges to a file:
```
export ranges city_1 ranges.txt
```

Export individual IPs:
```
export ranges city_1 ips.txt --full
```

## Important Notes

1. The IP2Location database requires a valid token for initialization and updates
2. Scanning modules depend on RustScan and ZMap being properly installed
3. Large IP ranges may require significant system resources when using `--full` export

