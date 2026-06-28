#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSL Manager for Linux Servers
-----------------------------
A highly interactive, visually polished Python CLI tool to issue, list,
renew, and delete SSL certificates using Let's Encrypt (Certbot).

This script has ZERO external dependencies (standard library only) and is designed
to run smoothly on remote Linux servers via SSH.
"""

import os
import sys
import subprocess
import re
import time
import shutil

# Attempt to import termios and tty for interactive key capture (Unix/Linux only)
try:
    import termios
    import tty
    import select
    TERMIOS_AVAILABLE = True
except ImportError:
    TERMIOS_AVAILABLE = False


class Colors:
    """ANSI color codes for terminal visual styling"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Standard colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright/High-intensity colors
    GREY = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Backgrounds
    BG_CYAN = "\033[46m"
    BG_RED = "\033[41m"


class TerminalUI:
    """Helper class to handle visual output, inputs, and interactive menus"""
    
    @staticmethod
    def clear_screen():
        os.system('clear' if os.name != 'nt' else 'cls')
        
    @staticmethod
    def print_banner():
        banner = f"""
{Colors.BOLD}{Colors.BRIGHT_CYAN}    ┌────────────────────────────────────────────────────────┐
    │                🔒 LINUX SSL MANAGER (Certbot)           │
    └────────────────────────────────────────────────────────┘{Colors.RESET}"""
        print(banner)

    @staticmethod
    def print_header(text):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}=== {text} ==={Colors.RESET}")

    @staticmethod
    def print_success(text):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✔ [SUCCESS] {text}{Colors.RESET}")

    @staticmethod
    def print_error(text):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_RED}✘ [ERROR] {text}{Colors.RESET}")

    @staticmethod
    def print_warning(text):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}⚠ [WARNING] {text}{Colors.RESET}")

    @staticmethod
    def print_info(text):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_BLUE}ℹ [INFO] {text}{Colors.RESET}")

    @staticmethod
    def press_any_key(prompt="Press Enter to continue..."):
        full_prompt = f"\n{Colors.GREY}{prompt}{Colors.RESET}"
        input(full_prompt)

    @staticmethod
    def ask_input(prompt, default=""):
        full_prompt = f"\n{Colors.BOLD}{Colors.CYAN}? {prompt}{Colors.RESET}"
        if default:
            full_prompt += f" [{default}]"
        full_prompt += ": "
        
        try:
            val = input(full_prompt).strip()
            return val if val else default
        except (KeyboardInterrupt, EOFError):
            print("\n")
            return None

    @staticmethod
    def ask_confirm(prompt, default_yes=True):
        suffix = " (Y/n)" if default_yes else " (y/N)"
        full_prompt = f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}? {prompt}{suffix}{Colors.RESET}: "
        
        try:
            val = input(full_prompt).strip().lower()
            if not val:
                return default_yes
            return val in ('y', 'yes', 'ye')
        except (KeyboardInterrupt, EOFError):
            print("\n")
            return False

    @staticmethod
    def get_key():
        """Reads a single keypress from standard input in raw mode (Unix only), bypassing stdin buffering"""
        if not TERMIOS_AVAILABLE:
            return None
            
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            # Read first byte using os.read to bypass Python's sys.stdin buffering
            ch = os.read(fd, 1).decode('utf-8', errors='ignore')
            if ch == '\x1b':
                # Check if there are more bytes waiting (which indicates an escape sequence like arrow keys)
                r, _, _ = select.select([fd], [], [], 0.05)
                if r:
                    extra = os.read(fd, 2).decode('utf-8', errors='ignore')
                    return ch + extra
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    @classmethod
    def select_menu(cls, title, options):
        """Displays an interactive selection menu using arrow keys (Linux) or numerical input (Windows/fallback)"""
        # If termios is not available or stdout is not a TTY, use simple fallback menu
        if not TERMIOS_AVAILABLE or not sys.stdin.isatty():
            cls.clear_screen()
            cls.print_banner()
            print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}=== {title} ==={Colors.RESET}\n")
            
            for idx, opt in enumerate(options, 1):
                print(f"  {Colors.CYAN}{idx}.{Colors.RESET} {opt}")
                
            while True:
                try:
                    choice = input(f"\nSelect option (1-{len(options)}): ").strip()
                    val = int(choice)
                    if 1 <= val <= len(options):
                        return val - 1
                    print(f"{Colors.RED}Invalid option. Please try again.{Colors.RESET}")
                except ValueError:
                    print(f"{Colors.RED}Please enter a valid number.{Colors.RESET}")
                except (KeyboardInterrupt, EOFError):
                    print("\nExiting...")
                    sys.exit(0)

        # Interactive arrow-key menu
        selected = 0
        sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.flush()
        
        try:
            while True:
                cls.clear_screen()
                cls.print_banner()
                print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}=== {title} ==={Colors.RESET}\n")
                
                for idx, opt in enumerate(options):
                    if idx == selected:
                        print(f"  {Colors.BRIGHT_CYAN}{Colors.BOLD}➔  {opt}{Colors.RESET}")
                    else:
                        print(f"     {Colors.GREY}{opt}{Colors.RESET}")
                
                print(f"\n{Colors.GREY}(Use Up/Down Arrow keys or j/k to navigate, Enter to select){Colors.RESET}")
                
                key = cls.get_key()
                
                if key == '\x1b[A' or key == 'k':  # Up Arrow or 'k'
                    selected = (selected - 1) % len(options)
                elif key == '\x1b[B' or key == 'j':  # Down Arrow or 'j'
                    selected = (selected + 1) % len(options)
                elif key in ('\r', '\n'):  # Enter
                    break
                elif key == '\x03' or key == '\x1b':  # Ctrl+C or Esc
                    sys.stdout.write("\033[?25h")  # Restore cursor
                    sys.stdout.flush()
                    cls.clear_screen()
                    print("\nExiting...")
                    sys.exit(0)
        finally:
            sys.stdout.write("\033[?25h")  # Always restore cursor
            sys.stdout.flush()
            
        return selected

    @staticmethod
    def ansi_len(s):
        """Calculates the string length ignoring ANSI escape codes"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return len(ansi_escape.sub('', str(s)))

    @classmethod
    def format_table(cls, headers, rows):
        """Formats a dynamic text table using box drawing characters, supporting ANSI colors"""
        if not rows:
            return "No data available."
            
        col_widths = [cls.ansi_len(h) for h in headers]
        for row in rows:
            for idx, cell in enumerate(row):
                col_widths[idx] = max(col_widths[idx], cls.ansi_len(cell))
                
        def pad(s, w):
            diff = w - cls.ansi_len(s)
            return str(s) + (" " * diff)
            
        top = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        header_line = "│" + "│".join(f" {pad(h, w)} " for h, w in zip(headers, col_widths)) + "│"
        divider = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        bottom = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
        
        lines = [top, header_line, divider]
        for row in rows:
            row_line = "│" + "│".join(f" {pad(cell, w)} " for cell, w in zip(row, col_widths)) + "│"
            lines.append(row_line)
        lines.append(bottom)
        
        return "\n".join(lines)


class SystemManager:
    """Handles OS-specific checks, executions, and Certbot dependency resolution"""
    
    @staticmethod
    def is_root():
        """Checks if running with administrative (root) privileges"""
        if os.name == 'nt':
            return True
        return os.geteuid() == 0

    @staticmethod
    def run_cmd(cmd, get_output=False):
        """Runs a system shell command and returns success code or output"""
        try:
            if get_output:
                res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                return res.returncode == 0, res.stdout, res.stderr
            else:
                res = subprocess.run(cmd, shell=True)
                return res.returncode == 0
        except Exception as e:
            return False, "", str(e) if get_output else False

    @classmethod
    def run_cmd_live(cls, cmd):
        """Runs a system command and streams its output to the terminal in real-time"""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    sys.stdout.write(output)
                    sys.stdout.flush()
                    
            rc = process.poll()
            return rc == 0
        except Exception as e:
            print(f"{Colors.RED}Exception running live command: {e}{Colors.RESET}")
            return False

    @classmethod
    def is_command_installed(cls, cmd):
        """Checks if a command is available in system PATH"""
        check_cmd = "where" if os.name == 'nt' else "which"
        success, _, _ = cls.run_cmd(f"{check_cmd} {cmd}", get_output=True)
        return success

    @classmethod
    def detect_package_manager(cls):
        """Detects the Linux distribution's package manager"""
        if cls.is_command_installed("apt-get"):
            return "apt"
        elif cls.is_command_installed("dnf"):
            return "dnf"
        elif cls.is_command_installed("yum"):
            return "yum"
        elif cls.is_command_installed("pacman"):
            return "pacman"
        return None

    @classmethod
    def install_certbot(cls):
        """Interactively installs Certbot and plugins using the system's package manager"""
        pkg_manager = cls.detect_package_manager()
        
        if not pkg_manager:
            TerminalUI.print_error("Could not detect package manager. Please install Certbot manually.")
            return False
            
        TerminalUI.print_info(f"Detected package manager: {pkg_manager}")
        
        confirm = TerminalUI.ask_confirm(
            "Do you want to install Certbot and Nginx/Apache plugins now?",
            default_yes=True
        )
        
        if not confirm:
            TerminalUI.print_warning("Installation skipped.")
            return False
            
        TerminalUI.print_info("Installing Certbot... Please wait...")
        
        success = False
        if pkg_manager == "apt":
            cls.run_cmd_live("apt-get update")
            success = cls.run_cmd_live("apt-get install -y certbot python3-certbot-nginx python3-certbot-apache")
        elif pkg_manager == "dnf":
            success = cls.run_cmd_live("dnf install -y certbot python3-certbot-nginx python3-certbot-apache")
        elif pkg_manager == "yum":
            success = cls.run_cmd_live("yum install -y epel-release && yum install -y certbot python3-certbot-nginx python3-certbot-apache")
        elif pkg_manager == "pacman":
            success = cls.run_cmd_live("pacman -S --noconfirm certbot certbot-nginx certbot-apache")
            
        if success:
            TerminalUI.print_success("Certbot has been installed successfully!")
            return True
        else:
            TerminalUI.print_error("Failed to install Certbot.")
            return False


class CertbotWrapper:
    """Wraps Certbot commands, provides parsing, issuing, and lifecycle operations"""

    @classmethod
    def get_certificates(cls):
        """Runs 'certbot certificates' and parses the output into structured data"""
        if not SystemManager.is_command_installed("certbot"):
            return []
            
        success, stdout, stderr = SystemManager.run_cmd("certbot certificates", get_output=True)
        if not success:
            if "No certificates found" in stdout or "No certificates found" in stderr:
                return []
            return []
            
        return cls.parse_certificates_output(stdout)

    @staticmethod
    def parse_certificates_output(output_text):
        """Parses the text output of 'certbot certificates' using regex"""
        certs = []
        blocks = output_text.split("Certificate Name:")
        for block in blocks[1:]:
            lines = block.split('\n')
            name = lines[0].strip()
            
            domains = ""
            expiry = ""
            days_left = 0
            status = "UNKNOWN"
            cert_path = ""
            key_path = ""
            
            for line in lines:
                line_str = line.strip()
                if line_str.startswith("Domains:"):
                    domains = line_str.replace("Domains:", "").strip()
                elif line_str.startswith("Expiry Date:"):
                    expiry_part = line_str.replace("Expiry Date:", "").strip()
                    expiry = expiry_part
                    match = re.search(r'\((VALID|INVALID):\s*(.*?)\)', expiry_part)
                    if match:
                        state = match.group(1)
                        info = match.group(2)
                        if state == "VALID":
                            status = "VALID"
                            days_match = re.search(r'(\d+)\s+days', info)
                            if days_match:
                                days_left = int(days_match.group(1))
                        else:
                            status = "EXPIRED"
                            days_left = 0
                elif line_str.startswith("Certificate Path:"):
                    cert_path = line_str.replace("Certificate Path:", "").strip()
                elif line_str.startswith("Private Key Path:"):
                    key_path = line_str.replace("Private Key Path:", "").strip()
            
            certs.append({
                "name": name,
                "domains": domains,
                "expiry": expiry,
                "days_left": days_left,
                "status": status,
                "cert_path": cert_path,
                "key_path": key_path,
                "is_self_signed": False
            })
            
        return certs

    @classmethod
    def get_all_certificates(cls):
        """Retrieves Certbot certificates and scans for manual/self-signed IP certificates"""
        certs = cls.get_certificates()
        cert_names = {c["name"] for c in certs}
        
        live_dir = "/etc/letsencrypt/live"
        if os.name == 'nt':
            live_dir = "./mock_certs"
            
        if os.path.exists(live_dir):
            for name in os.listdir(live_dir):
                if name == "README" or name in cert_names:
                    continue
                cert_path = os.path.join(live_dir, name, "fullchain.pem")
                key_path = os.path.join(live_dir, name, "privkey.pem")
                if os.path.exists(cert_path) and os.path.exists(key_path):
                    # Parse utilizing openssl x509
                    success, stdout, _ = SystemManager.run_cmd(f"openssl x509 -in {cert_path} -noout -enddate -subject", get_output=True)
                    if success:
                        cn_match = re.search(r'CN\s*=\s*([^,\n]+)', stdout)
                        cn = cn_match.group(1).strip() if cn_match else name
                        
                        expiry_match = re.search(r'notAfter=(.+)', stdout)
                        expiry_str = expiry_match.group(1).strip() if expiry_match else "UNKNOWN"
                        
                        days_left = 0
                        status = "EXPIRED"
                        if expiry_str != "UNKNOWN":
                            try:
                                t_expiry = None
                                clean_expiry = re.sub(r'\s+', ' ', expiry_str)
                                for fmt in ('%b %d %H:%M:%S %Y %Z', '%b %d %H:%M:%S %Y'):
                                    try:
                                        t_expiry = time.strptime(clean_expiry, fmt)
                                        break
                                    except ValueError:
                                        continue
                                if t_expiry:
                                    expiry_epoch = time.mktime(t_expiry)
                                    days_left = int((expiry_epoch - time.time()) / 86400)
                                    if days_left > 0:
                                        status = "VALID"
                            except Exception:
                                pass
                                
                        certs.append({
                            "name": name,
                            "domains": cn,
                            "expiry": expiry_str + " (Manual/Self-Signed)",
                            "days_left": days_left,
                            "status": status,
                            "cert_path": cert_path,
                            "key_path": key_path,
                            "is_self_signed": True
                        })
        return certs

    @classmethod
    def display_certificates(cls):
        """Displays all certificates in a beautiful table format"""
        certs = cls.get_all_certificates()
        
        if not certs:
            TerminalUI.print_warning("No SSL Certificates found in this server.")
            return False
            
        headers = [
            f"{Colors.BOLD}Cert Name{Colors.RESET}",
            f"{Colors.BOLD}Domains{Colors.RESET}",
            f"{Colors.BOLD}Expiry Date{Colors.RESET}",
            f"{Colors.BOLD}Days Left{Colors.RESET}"
        ]
        
        rows = []
        for c in certs:
            if c["status"] == "EXPIRED":
                days_str = f"{Colors.BRIGHT_RED}EXPIRED{Colors.RESET}"
            elif c["days_left"] < 15:
                days_str = f"{Colors.BRIGHT_RED}{c['days_left']} days (CRITICAL){Colors.RESET}"
            elif c["days_left"] < 30:
                days_str = f"{Colors.BRIGHT_YELLOW}{c['days_left']} days (RENEWAL NEEDED){Colors.RESET}"
            else:
                days_str = f"{Colors.BRIGHT_GREEN}{c['days_left']} days (VALID){Colors.RESET}"
                
            domain_list = c["domains"].replace(" ", ", ")
            if len(domain_list) > 40:
                domain_list = domain_list[:37] + "..."
                
            expiry_short = c["expiry"].split(" (")[0]
            if "Manual/Self-Signed" in c["expiry"]:
                expiry_short += " (Self-Signed)"
            
            rows.append([c["name"], domain_list, expiry_short, days_str])
            
        table_str = TerminalUI.format_table(headers, rows)
        print("\n" + table_str)
        return True

    @classmethod
    def select_ca(cls):
        """Allows the user to select the Certificate Authority (CA)"""
        ca_options = [
            "Let's Encrypt (Default - 90 days validity, no account needed)",
            "ZeroSSL (90 days validity, requires free ZeroSSL account & EAB credentials)"
        ]
        choice = TerminalUI.select_menu("Select Certificate Authority (CA)", ca_options)
        if choice == 0:
            return "letsencrypt", None, None, None
        else:
            TerminalUI.print_info(
                "ZeroSSL requires External Account Binding (EAB) credentials.\n"
                "You can generate them for free in your ZeroSSL dashboard under Developer Settings -> EAB Credentials."
            )
            eab_kid = TerminalUI.ask_input("Enter ZeroSSL EAB KID")
            eab_hmac = TerminalUI.ask_input("Enter ZeroSSL EAB HMAC Key")
            if not eab_kid or not eab_hmac:
                TerminalUI.print_error("EAB credentials are required for ZeroSSL. Falling back to Let's Encrypt.")
                return "letsencrypt", None, None, None
            return "zerossl", "https://acme.zerossl.com/v2/DV90", eab_kid, eab_hmac

    @classmethod
    def issue_standard_certificate(cls):
        """Steps through issuing a standard SSL certificate interactively"""
        TerminalUI.print_header("Issue Standard Domain SSL")
        
        ca_name, ca_server, eab_kid, eab_hmac = cls.select_ca()
        
        domains_input = TerminalUI.ask_input("Enter domains (comma-separated, e.g., example.com, www.example.com)")
        if not domains_input:
            TerminalUI.print_warning("Operation cancelled.")
            return
            
        domains = [d.strip() for d in domains_input.split(",") if d.strip()]
        if not domains:
            TerminalUI.print_error("Invalid domains list.")
            return
            
        email = TerminalUI.ask_input(f"Enter email (for {ca_name.capitalize()} recovery & renewal warnings)")
        if not email:
            TerminalUI.print_warning("Operation cancelled.")
            return
            
        methods = [
            "Nginx Plugin (Auto-configure Nginx)",
            "Apache Plugin (Auto-configure Apache)",
            "Standalone Mode (Temporary web server - stops existing servers)",
            "Webroot Mode (Provide path to existing webroot)"
        ]
        
        method_idx = TerminalUI.select_menu("Select Validation Method", methods)
        
        # In Standalone mode, warn about port 80
        if method_idx == 2:
            TerminalUI.print_warning("Standalone mode will temporarily bind to port 80. Ensure it is free.")
            
        webroot_path = ""
        if method_idx == 3:
            webroot_path = TerminalUI.ask_input("Enter webroot path (e.g. /var/www/html)")
            if not webroot_path or not os.path.exists(webroot_path):
                TerminalUI.print_error("Invalid webroot directory path.")
                return
                
        dry_run = TerminalUI.ask_confirm("Perform a test dry-run first?", default_yes=True)
        
        # Helper to construct certbot command
        def build_cmd(is_dry):
            command = ["certbot", "certonly", "--non-interactive", "--agree-tos", "--email", email]
            
            # ZeroSSL does not support dry-run on their production endpoint.
            # Fall back to Let's Encrypt staging for dry-runs to verify webserver validation routing.
            if is_dry:
                if ca_name == "zerossl":
                    # Omit ZeroSSL custom server and EAB to let Certbot default to Let's Encrypt staging
                    pass
                else:
                    # Let's Encrypt default staging or custom CAs (if staging is supported)
                    if ca_server:
                        command.extend(["--server", ca_server])
            else:
                if ca_server:
                    command.extend(["--server", ca_server])
                if eab_kid and eab_hmac:
                    command.extend(["--eab-kid", eab_kid, "--eab-hmac-key", eab_hmac])
                
            for d in domains:
                command.extend(["-d", d])
                
            if method_idx == 0:
                command.append("--nginx")
            elif method_idx == 1:
                command.append("--apache")
            elif method_idx == 2:
                command.append("--standalone")
            elif method_idx == 3:
                command.extend(["--webroot", "-w", webroot_path])
                
            if is_dry:
                command.append("--dry-run")
            return command
            
        cmd = build_cmd(dry_run)
        full_command = " ".join(cmd)
        TerminalUI.print_info(f"Executing Command: {full_command}")
        
        print("\n" + "="*50 + " CERTBOT OUTPUT " + "="*50 + "\n")
        success = SystemManager.run_cmd_live(full_command)
        print("\n" + "="*116 + "\n")
        
        if success:
            if dry_run:
                TerminalUI.print_success("Dry-run succeeded! The parameters are valid.")
                
                run_real = TerminalUI.ask_confirm("Would you like to issue the actual certificate now?", default_yes=True)
                if run_real:
                    real_cmd = build_cmd(is_dry=False)
                    real_command = " ".join(real_cmd)
                    TerminalUI.print_info("Issuing real certificate...")
                    print("\n" + "="*50 + " CERTBOT OUTPUT " + "="*50 + "\n")
                    real_success = SystemManager.run_cmd_live(real_command)
                    print("\n" + "="*116 + "\n")
                    if real_success:
                        TerminalUI.print_success("SSL certificate issued successfully!")
                    else:
                        TerminalUI.print_error("Failed to issue SSL certificate.")
            else:
                TerminalUI.print_success("SSL certificate issued successfully!")
        else:
            TerminalUI.print_error("Certbot command failed. Check outputs above for details.")
 
    @classmethod
    def issue_wildcard_certificate(cls):
        """Issues a wildcard certificate via manual DNS challenge"""
        TerminalUI.print_header("Issue Wildcard SSL Certificate")
        
        ca_name, ca_server, eab_kid, eab_hmac = cls.select_ca()
        
        domain = TerminalUI.ask_input("Enter base domain name (e.g., example.com)")
        if not domain:
            TerminalUI.print_warning("Operation cancelled.")
            return
            
        # Standardize domain name (remove wildcard prefix if entered by user)
        domain = domain.replace("*.", "").strip()
        
        email = TerminalUI.ask_input(f"Enter email (for {ca_name.capitalize()} recovery & renewal warnings)")
        if not email:
            TerminalUI.print_warning("Operation cancelled.")
            return
            
        dry_run = TerminalUI.ask_confirm("Perform a test dry-run first?", default_yes=True)
        
        # Helper to construct wildcard command
        def build_wildcard_cmd(is_dry):
            command = [
                "certbot", "certonly",
                "--manual",
                "--preferred-challenges", "dns",
                "--email", email,
                "--agree-tos",
                "-d", domain,
                "-d", f"*.{domain}"
            ]
            
            # ZeroSSL fallback to Let's Encrypt staging for dry-runs
            if is_dry:
                if ca_name == "zerossl":
                    pass
                else:
                    if ca_server:
                        command.extend(["--server", ca_server])
            else:
                if ca_server:
                    command.extend(["--server", ca_server])
                if eab_kid and eab_hmac:
                    command.extend(["--eab-kid", eab_kid, "--eab-hmac-key", eab_hmac])
                
            if is_dry:
                command.append("--dry-run")
            return command
            
        cmd = build_wildcard_cmd(dry_run)
        full_command = " ".join(cmd)
        
        TerminalUI.print_info("Wildcard SSL requires creating a DNS TXT record in your DNS provider.")
        TerminalUI.print_warning("This command is interactive. Follow Certbot prompts to add DNS records.")
        TerminalUI.print_info(f"Running Command: {full_command}")
        
        TerminalUI.press_any_key("Press Enter to launch Certbot manual DNS execution...")
        
        print("\n" + "="*50 + " CERTBOT MANUAL DNS " + "="*50 + "\n")
        success = SystemManager.run_cmd_live(full_command)
        print("\n" + "="*116 + "\n")
        
        if success:
            if dry_run:
                TerminalUI.print_success("Dry-run wildcard validation succeeded!")
                run_real = TerminalUI.ask_confirm("Issue the actual wildcard certificate now?", default_yes=True)
                if run_real:
                    real_cmd = build_wildcard_cmd(is_dry=False)
                    real_command = " ".join(real_cmd)
                    print("\n" + "="*50 + " CERTBOT MANUAL DNS " + "="*50 + "\n")
                    real_success = SystemManager.run_cmd_live(real_command)
                    print("\n" + "="*116 + "\n")
                    if real_success:
                        TerminalUI.print_success(f"Wildcard certificate for *.{domain} and {domain} issued successfully!")
                    else:
                        TerminalUI.print_error("Failed to issue wildcard certificate.")
            else:
                TerminalUI.print_success(f"Wildcard certificate for *.{domain} and {domain} issued successfully!")
        else:
            TerminalUI.print_error("Certbot manual wildcard execution failed.")

    @classmethod
    def issue_letsencrypt_ip_certificate(cls):
        """Issues a publicly trusted short-lived IP certificate using Let's Encrypt (Certbot v5.3+)"""
        TerminalUI.print_header("Issue Let's Encrypt IP SSL")
        TerminalUI.print_warning("Let's Encrypt IP SSL requires Certbot v5.3+ and is valid for only 6 DAYS.")
        TerminalUI.print_info("Only public IPv4/IPv6 addresses are supported (no private IPs like 192.168.x.x).")
        
        ip = TerminalUI.ask_input("Enter your public IP address (e.g., 1.2.3.4)")
        if not ip:
            TerminalUI.print_warning("Operation cancelled.")
            return
            
        # Basic validation (looks like IPv4 or IPv6)
        if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip) and not ':' in ip:
            TerminalUI.print_error("Invalid IP address format.")
            return
            
        email = TerminalUI.ask_input("Enter email (for Let's Encrypt recovery & renewal warnings)")
        if not email:
            TerminalUI.print_warning("Operation cancelled.")
            return
            
        methods = [
            "Nginx Plugin (Auto-configure Nginx)",
            "Apache Plugin (Auto-configure Apache)",
            "Standalone Mode (Temporary web server - stops existing servers)",
            "Webroot Mode (Provide path to existing webroot)"
        ]
        
        method_idx = TerminalUI.select_menu("Select Validation Method", methods)
        
        cmd = [
            "certbot", "certonly",
            "--preferred-profile", "shortlived",
            "--non-interactive",
            "--agree-tos",
            "--email", email,
            "--ip-address", ip
        ]
        
        if method_idx == 0:
            cmd.append("--nginx")
        elif method_idx == 1:
            cmd.append("--apache")
        elif method_idx == 2:
            cmd.append("--standalone")
            TerminalUI.print_warning("Standalone mode will temporarily bind to port 80. Ensure it is free.")
        elif method_idx == 3:
            webroot_path = TerminalUI.ask_input("Enter webroot path (e.g. /var/www/html)")
            if not webroot_path or not os.path.exists(webroot_path):
                TerminalUI.print_error("Invalid webroot directory path.")
                return
            cmd.extend(["--webroot", "-w", webroot_path])
            
        dry_run = TerminalUI.ask_confirm("Perform a test dry-run first?", default_yes=True)
        if dry_run:
            cmd.append("--dry-run")
            
        full_command = " ".join(cmd)
        TerminalUI.print_info(f"Executing Command: {full_command}")
        
        print("\n" + "="*50 + " CERTBOT OUTPUT " + "="*50 + "\n")
        success = SystemManager.run_cmd_live(full_command)
        print("\n" + "="*116 + "\n")
        
        if success:
            if dry_run:
                TerminalUI.print_success("Dry-run succeeded! The parameters are valid.")
                run_real = TerminalUI.ask_confirm("Would you like to issue the actual certificate now?", default_yes=True)
                if run_real:
                    cmd.remove("--dry-run")
                    real_command = " ".join(cmd)
                    TerminalUI.print_info("Issuing real short-lived IP certificate...")
                    print("\n" + "="*50 + " CERTBOT OUTPUT " + "="*50 + "\n")
                    real_success = SystemManager.run_cmd_live(real_command)
                    print("\n" + "="*116 + "\n")
                    if real_success:
                        TerminalUI.print_success(f"Let's Encrypt SSL certificate for IP: {ip} issued successfully!")
                    else:
                        TerminalUI.print_error("Failed to issue Let's Encrypt IP SSL certificate.")
            else:
                TerminalUI.print_success(f"Let's Encrypt SSL certificate for IP: {ip} issued successfully!")
        else:
            TerminalUI.print_error("Certbot IP SSL command failed. Ensure Certbot is v5.3+ and IP is publicly accessible.")

    @classmethod
    def issue_self_signed_ip_certificate(cls):
        """Generates a self-signed SSL certificate with IP Subject Alternative Name (SAN) using OpenSSL"""
        TerminalUI.print_header("Issue IP Address SSL Certificate (Self-Signed)")
        
        ip = TerminalUI.ask_input("Enter IP address (e.g., 1.2.3.4)")
        if not ip:
            TerminalUI.print_warning("Operation cancelled.")
            return
            
        # Basic validation (looks like IPv4 or IPv6)
        if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip) and not ':' in ip:
            TerminalUI.print_error("Invalid IP address format.")
            return
            
        cert_dir = f"/etc/letsencrypt/live/{ip}"
        if os.name == 'nt':
            cert_dir = f"./mock_certs/{ip}"
            
        TerminalUI.print_info(f"Generating self-signed certificate for IP: {ip}")
        
        # OpenSSL config template
        ssl_config = f"""[req]
default_bits = 2048
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = {ip}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
IP.1 = {ip}
"""
        # Create temp config file
        config_path = "/tmp/openssl_ip.conf" if os.name != 'nt' else "./openssl_ip.conf"
        try:
            os.makedirs(cert_dir, exist_ok=True)
            with open(config_path, 'w') as f:
                f.write(ssl_config)
                
            cert_path = os.path.join(cert_dir, "fullchain.pem")
            key_path = os.path.join(cert_dir, "privkey.pem")
            
            cmd = f"openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout {key_path} -out {cert_path} -config {config_path}"
            
            success = SystemManager.run_cmd_live(cmd)
            
            # Cleanup config file
            if os.path.exists(config_path):
                os.remove(config_path)
                
            if success:
                TerminalUI.print_success(f"Self-signed SSL certificate generated successfully for IP: {ip}!")
                TerminalUI.print_info(f"Certificate Path: {cert_path}")
                TerminalUI.print_info(f"Private Key Path: {key_path}")
            else:
                TerminalUI.print_error("OpenSSL generation failed.")
        except Exception as e:
            TerminalUI.print_error(f"Error generating certificate: {e}")

    @classmethod
    def renew_certificates(cls):
        """Runs the Certbot renewal command manually"""
        TerminalUI.print_header("Renew SSL Certificates")
        
        dry_run = TerminalUI.ask_confirm("Perform a test dry-run renewal first?", default_yes=True)
        
        cmd = "certbot renew"
        if dry_run:
            cmd += " --dry-run"
            
        TerminalUI.print_info(f"Running: {cmd}")
        print("\n" + "="*50 + " CERTBOT OUTPUT " + "="*50 + "\n")
        success = SystemManager.run_cmd_live(cmd)
        print("\n" + "="*116 + "\n")
        
        if success:
            TerminalUI.print_success("Certbot renewal process completed successfully!")
        else:
            TerminalUI.print_error("Certbot renewal failed. Check logs above.")

    @classmethod
    def delete_certificate(cls):
        """Displays list of active certificates, lets user select one, and deletes it"""
        TerminalUI.print_header("Delete SSL Certificate")
        
        certs = cls.get_all_certificates()
        if not certs:
            TerminalUI.print_warning("No certificates found to delete.")
            return
            
        options = []
        for c in certs:
            cert_type = "Self-Signed/Manual" if c["is_self_signed"] else "Let's Encrypt"
            options.append(f"{c['name']} ({cert_type} - Domains: {c['domains'].replace(' ', ', ')})")
            
        options.append("Back to Main Menu")
        
        selected_idx = TerminalUI.select_menu("Select Certificate to Delete", options)
        
        if selected_idx == len(certs):
            return
            
        cert_data = certs[selected_idx]
        cert_name = cert_data["name"]
        
        confirm = TerminalUI.ask_confirm(
            f"Are you SURE you want to delete certificate '{cert_name}'? This cannot be undone!",
            default_yes=False
        )
        
        if not confirm:
            TerminalUI.print_warning("Delete operation aborted.")
            return
            
        if cert_data["is_self_signed"]:
            # Delete directory directly since Certbot doesn't manage it
            try:
                dir_to_remove = os.path.dirname(cert_data["cert_path"])
                shutil.rmtree(dir_to_remove)
                TerminalUI.print_success(f"Self-signed certificate '{cert_name}' and directory removed successfully.")
            except Exception as e:
                TerminalUI.print_error(f"Failed to delete self-signed certificate directory: {e}")
        else:
            # Let certbot delete it
            cmd = f"certbot delete --cert-name {cert_name}"
            TerminalUI.print_info(f"Running: {cmd}")
            success = SystemManager.run_cmd_live(cmd)
            if success:
                TerminalUI.print_success(f"Certificate '{cert_name}' has been deleted successfully.")
            else:
                TerminalUI.print_error(f"Failed to delete certificate '{cert_name}'.")

    @classmethod
    def configure_renewal_hooks(cls):
        """Configures automated renewal post-hooks in renewal-hooks/post/"""
        TerminalUI.print_header("Configure Reload Hooks")
        
        timer_active = False
        if SystemManager.is_command_installed("systemctl"):
            success, stdout, _ = SystemManager.run_cmd("systemctl is-active certbot.timer", get_output=True)
            if success and "active" in stdout:
                timer_active = True
                
        if timer_active:
            TerminalUI.print_success("Active systemd Certbot timer detected! Expiry checks run automatically twice a day.")
        else:
            TerminalUI.print_warning("No active systemd Certbot timer detected. Ensure cron or systemd timer runs 'certbot renew'.")
            
        hook_dir = "/etc/letsencrypt/renewal-hooks/post"
        hook_file = f"{hook_dir}/reload-webserver.sh"
        
        TerminalUI.print_info(
            f"We can create a reload hook script in '{hook_file}'.\nThis runs automatically after any successful SSL certificate renewal."
        )
        
        confirm = TerminalUI.ask_confirm("Do you want to configure a web server reload hook?", default_yes=True)
        
        if not confirm:
            TerminalUI.print_warning("Operation skipped.")
            return
            
        reload_command = TerminalUI.ask_input(
            "Enter web server reload command (e.g., systemctl reload nginx)",
            default="systemctl reload nginx || systemctl reload apache2 || systemctl reload httpd"
        )
        
        if not reload_command:
            TerminalUI.print_warning("Reload command skipped.")
            return
            
        if os.name == 'nt':
            TerminalUI.print_success(f"[Mocked] Created hook file '{hook_file}' with command: '{reload_command}'")
            return
            
        try:
            os.makedirs(hook_dir, exist_ok=True)
            
            script_content = f"""#!/bin/bash
# Auto-generated by SSL Manager Python
echo "[$(date)] Executing SSL renewal hook: {reload_command}" >> /var/log/certbot-renew-hook.log
{reload_command} >> /var/log/certbot-renew-hook.log 2>&1
"""
            with open(hook_file, 'w') as f:
                f.write(script_content)
                
            os.chmod(hook_file, 0o755)
            
            TerminalUI.print_success(f"Webserver reload hook configured successfully in '{hook_file}'!")
        except Exception as e:
            TerminalUI.print_error(f"Failed to create renewal hook: {e}")


def main():
    TerminalUI.clear_screen()
    TerminalUI.print_banner()
    
    if not SystemManager.is_root():
        TerminalUI.print_error("This script requires root privileges to read and write Let's Encrypt certificates.")
        TerminalUI.print_info("Please run: sudo python3 ssl_manager.py")
        sys.exit(1)
        
    if not SystemManager.is_command_installed("certbot"):
        TerminalUI.print_warning("Certbot is not installed on this system.")
        installed = SystemManager.install_certbot()
        if not installed:
            TerminalUI.print_error("Certbot is required to run this manager. Exiting.")
            sys.exit(1)
            
    while True:
        options = [
            "Issue Standard SSL Certificate (Domain)",
            "Issue Wildcard SSL Certificate (DNS)",
            "Issue IP Address SSL Certificate (Let's Encrypt - Short-lived 6 days)",
            "Issue IP Address SSL Certificate (Self-Signed - 365 days)",
            "List all SSL Certificates",
            "Renew SSL Certificates",
            "Delete an SSL Certificate",
            "Configure Web Server Reload Hooks",
            "Exit"
        ]
        
        choice = TerminalUI.select_menu("SSL Manager Main Menu", options)
        
        TerminalUI.clear_screen()
        TerminalUI.print_banner()
        
        if choice == 0:
            CertbotWrapper.issue_standard_certificate()
        elif choice == 1:
            CertbotWrapper.issue_wildcard_certificate()
        elif choice == 2:
            CertbotWrapper.issue_letsencrypt_ip_certificate()
        elif choice == 3:
            CertbotWrapper.issue_self_signed_ip_certificate()
        elif choice == 4:
            TerminalUI.print_header("Active SSL Certificates")
            CertbotWrapper.display_certificates()
        elif choice == 5:
            CertbotWrapper.renew_certificates()
        elif choice == 6:
            CertbotWrapper.delete_certificate()
        elif choice == 7:
            CertbotWrapper.configure_renewal_hooks()
        elif choice == 8:
            TerminalUI.clear_screen()
            print(f"\n{Colors.BOLD}{Colors.GREEN}Thank you for using SSL Manager! Goodbye.{Colors.RESET}\n")
            break
            
        TerminalUI.press_any_key()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        print("\n\nOperation aborted by user.")
        sys.exit(0)
