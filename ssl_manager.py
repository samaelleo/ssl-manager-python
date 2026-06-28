#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSL Manager for Linux Servers
-----------------------------
A highly interactive, visually polished Python CLI tool to issue, list,
renew, and delete SSL certificates using Let's Encrypt (Certbot).

This script has ZERO external dependencies (standard library only) and is designed
to run smoothly on remote Linux servers via SSH.

مدیر SSL برای سرورهای لینوکس
---------------------------
یک ابزار خط فرمان تعاملی و زیبا به زبان پایتون برای صدور، مشاهده، تمدید و حذف
گواهی‌های SSL با استفاده از Let's Encrypt (Certbot).
این اسکریپت فاقد هرگونه وابستگی خارجی است و به سادگی روی سرورهای لینوکسی اجرا می‌شود.
"""

import os
import sys
import subprocess
import re
import time

# Attempt to import termios and tty for interactive key capture (Unix/Linux only)
# تلاش برای ایمپورت کتابخانه‌های مورد نیاز برای ناوبری با کلیدهای جهت‌نما در لینوکس
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
    │        مدیریت گواهی‌های SSL در سرورهای لینوکس          │
    └────────────────────────────────────────────────────────┘{Colors.RESET}"""
        print(banner)

    @staticmethod
    def print_header(text, farsi_text=""):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}=== {text} ==={Colors.RESET}")
        if farsi_text:
            print(f"{Colors.GREY}# {farsi_text}{Colors.RESET}")

    @staticmethod
    def print_success(text, farsi_text=""):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✔ [SUCCESS] {text}{Colors.RESET}")
        if farsi_text:
            print(f"{Colors.GREEN}  {farsi_text}{Colors.RESET}")

    @staticmethod
    def print_error(text, farsi_text=""):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_RED}✘ [ERROR] {text}{Colors.RESET}")
        if farsi_text:
            print(f"{Colors.RED}  {farsi_text}{Colors.RESET}")

    @staticmethod
    def print_warning(text, farsi_text=""):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}⚠ [WARNING] {text}{Colors.RESET}")
        if farsi_text:
            print(f"{Colors.YELLOW}  {farsi_text}{Colors.RESET}")

    @staticmethod
    def print_info(text, farsi_text=""):
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_BLUE}ℹ [INFO] {text}{Colors.RESET}")
        if farsi_text:
            print(f"{Colors.BLUE}  {farsi_text}{Colors.RESET}")

    @staticmethod
    def press_any_key(prompt="Press Enter to continue...", farsi_prompt="برای ادامه کلید Enter را فشار دهید..."):
        full_prompt = f"\n{Colors.GREY}{prompt} ({farsi_prompt}){Colors.RESET}"
        input(full_prompt)

    @staticmethod
    def ask_input(prompt, farsi_prompt="", default=""):
        full_prompt = f"\n{Colors.BOLD}{Colors.CYAN}? {prompt}{Colors.RESET}"
        if farsi_prompt:
            full_prompt += f"\n  {Colors.GREY}({farsi_prompt}){Colors.RESET}"
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
    def ask_confirm(prompt, farsi_prompt="", default_yes=True):
        suffix = " (Y/n)" if default_yes else " (y/N)"
        full_prompt = f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}? {prompt}{suffix}{Colors.RESET}"
        if farsi_prompt:
            full_prompt += f"\n  {Colors.GREY}({farsi_prompt}){Colors.RESET}"
        full_prompt += ": "
        
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
        """Reads a single keypress from standard input in raw mode (Unix only)"""
        if not TERMIOS_AVAILABLE:
            return None
            
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            # Read 1 byte
            ch = sys.stdin.read(1)
            # Check if escape sequence (e.g. arrow keys)
            if ch == '\x1b':
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if rlist:
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                        if rlist:
                            ch3 = sys.stdin.read(1)
                            return ch + ch2 + ch3
                    return ch + ch2
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    @classmethod
    def select_menu(cls, title, options, farsi_title=""):
        """Displays an interactive selection menu using arrow keys (Linux) or numerical input (Windows/fallback)"""
        # If termios is not available or stdout is not a TTY, use simple fallback menu
        if not TERMIOS_AVAILABLE or not sys.stdin.isatty():
            cls.clear_screen()
            cls.print_banner()
            print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}=== {title} ==={Colors.RESET}")
            if farsi_title:
                print(f"{Colors.GREY}# {farsi_title}{Colors.RESET}")
            
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
        # Hide cursor
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        
        try:
            while True:
                cls.clear_screen()
                cls.print_banner()
                print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}=== {title} ==={Colors.RESET}")
                if farsi_title:
                    print(f"{Colors.GREY}# {farsi_title}{Colors.RESET}\n")
                else:
                    print("\n")
                
                for idx, opt in enumerate(options):
                    if idx == selected:
                        print(f"  {Colors.BRIGHT_CYAN}{Colors.BOLD}➔  {opt}{Colors.RESET}")
                    else:
                        print(f"     {Colors.GREY}{opt}{Colors.RESET}")
                
                print(f"\n{Colors.GREY}(Use Up/Down Arrow keys or j/k to navigate, Enter to select){Colors.RESET}")
                print(f"{Colors.GREY}(برای پیمایش از کلیدهای جهت‌نما بالا/پایین و برای انتخاب از Enter استفاده کنید){Colors.RESET}")
                
                key = cls.get_key()
                
                if key == '\x1b[A' or key == 'k':  # Up Arrow or 'k'
                    selected = (selected - 1) % len(options)
                elif key == '\x1b[B' or key == 'j':  # Down Arrow or 'j'
                    selected = (selected + 1) % len(options)
                elif key in ('\r', '\n'):  # Enter
                    break
                elif key == '\x03' or key == '\x1b':  # Ctrl+C or Esc
                    # Restore cursor and exit
                    sys.stdout.write("\033[?25h")
                    sys.stdout.flush()
                    cls.clear_screen()
                    print("\nExiting... (خروج از برنامه)")
                    sys.exit(0)
        finally:
            # Always ensure the cursor is restored
            sys.stdout.write("\033[?25h")
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
            # Simplified for local Windows development testing
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
            TerminalUI.print_error(
                "Could not detect package manager. Please install Certbot manually.",
                "سیستم مدیریت بسته شناسایی نشد. لطفا Certbot را به صورت دستی نصب کنید."
            )
            return False
            
        TerminalUI.print_info(
            f"Detected package manager: {pkg_manager}",
            f"سیستم مدیریت بسته شناسایی شده: {pkg_manager}"
        )
        
        confirm = TerminalUI.ask_confirm(
            "Do you want to install Certbot and Nginx/Apache plugins now?",
            "آیا می‌خواهید برنامه Certbot و افزونه‌های Nginx/Apache را همین الان نصب کنید؟",
            default_yes=True
        )
        
        if not confirm:
            TerminalUI.print_warning("Installation skipped.", "فرآیند نصب لغو شد.")
            return False
            
        TerminalUI.print_info("Installing Certbot... Please wait...", "در حال نصب Certbot... لطفا شکیبا باشید...")
        
        success = False
        if pkg_manager == "apt":
            # Update and install
            cls.run_cmd_live("apt-get update")
            success = cls.run_cmd_live("apt-get install -y certbot python3-certbot-nginx python3-certbot-apache")
        elif pkg_manager == "dnf":
            success = cls.run_cmd_live("dnf install -y certbot python3-certbot-nginx python3-certbot-apache")
        elif pkg_manager == "yum":
            success = cls.run_cmd_live("yum install -y epel-release && yum install -y certbot python3-certbot-nginx python3-certbot-apache")
        elif pkg_manager == "pacman":
            success = cls.run_cmd_live("pacman -S --noconfirm certbot certbot-nginx certbot-apache")
            
        if success:
            TerminalUI.print_success("Certbot has been installed successfully!", "Certbot با موفقیت نصب شد!")
            return True
        else:
            TerminalUI.print_error("Failed to install Certbot.", "خطا در نصب Certbot.")
            return False


class CertbotWrapper:
    """Wraps Certbot commands, provides parsing, issuing, and lifecycle operations"""

    @classmethod
    def get_certificates(cls):
        """Runs 'certbot certificates' and parses the output into structured data"""
        if not SystemManager.is_command_installed("certbot"):
            return []
            
        # Run certbot certificates
        success, stdout, stderr = SystemManager.run_cmd("certbot certificates", get_output=True)
        if not success:
            # Certbot certificates might exit with non-zero if no certs exist or permissions are blocked
            if "No certificates found" in stdout or "No certificates found" in stderr:
                return []
            # Otherwise return empty list, but display warning
            return []
            
        return cls.parse_certificates_output(stdout)

    @staticmethod
    def parse_certificates_output(output_text):
        """Parses the text output of 'certbot certificates' using regex"""
        certs = []
        
        # Split output by "Certificate Name:" block
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
                    # Extract validity info e.g. (VALID: 89 days) or (INVALID: EXPIRED)
                    match = re.search(r'\((VALID|INVALID):\s*(.*?)\)', expiry_part)
                    if match:
                        state = match.group(1)
                        info = match.group(2)
                        if state == "VALID":
                            status = "VALID"
                            # Try to extract the number of days
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
                "key_path": key_path
            })
            
        return certs

    @classmethod
    def display_certificates(cls):
        """Displays all certificates in a beautiful table format"""
        certs = cls.get_certificates()
        
        if not certs:
            TerminalUI.print_warning(
                "No SSL Certificates found in this server.",
                "هیچ گواهی SSL در این سرور یافت نشد."
            )
            return False
            
        headers = [
            f"{Colors.BOLD}Cert Name (نام گواهی){Colors.RESET}",
            f"{Colors.BOLD}Domains (دامنه‌ها){Colors.RESET}",
            f"{Colors.BOLD}Expiry (تاریخ انقضا){Colors.RESET}",
            f"{Colors.BOLD}Days Left (روزهای باقی‌مانده){Colors.RESET}"
        ]
        
        rows = []
        for c in certs:
            # Color coding days left
            if c["status"] == "EXPIRED":
                days_str = f"{Colors.BRIGHT_RED}EXPIRED (منقضی شده){Colors.RESET}"
            elif c["days_left"] < 15:
                days_str = f"{Colors.BRIGHT_RED}{c['days_left']} days (بحرانی){Colors.RESET}"
            elif c["days_left"] < 30:
                days_str = f"{Colors.BRIGHT_YELLOW}{c['days_left']} days (نیاز به تمدید){Colors.RESET}"
            else:
                days_str = f"{Colors.BRIGHT_GREEN}{c['days_left']} days (معتبر){Colors.RESET}"
                
            # Clean up domains length for UI layout
            domain_list = c["domains"].replace(" ", ", ")
            if len(domain_list) > 40:
                domain_list = domain_list[:37] + "..."
                
            # Clean up expiry string
            expiry_short = c["expiry"].split(" (")[0]
            
            rows.append([c["name"], domain_list, expiry_short, days_str])
            
        table_str = TerminalUI.format_table(headers, rows)
        print("\n" + table_str)
        return True

    @classmethod
    def issue_new_certificate(cls):
        """Steps through issuing a new SSL certificate interactively"""
        TerminalUI.print_header("Issue New SSL Certificate", "صدور گواهی SSL جدید")
        
        # Get domains
        domains_input = TerminalUI.ask_input(
            "Enter domains (comma-separated, e.g., example.com, www.example.com)",
            "دامنه‌ها را وارد کنید (با کاما جدا کنید، مانند example.com, www.example.com)"
        )
        if not domains_input:
            TerminalUI.print_warning("Operation cancelled.", "عملیات لغو شد.")
            return
            
        # Parse domains
        domains = [d.strip() for d in domains_input.split(",") if d.strip()]
        if not domains:
            TerminalUI.print_error("Invalid domains list.", "لیست دامنه‌ها نامعتبر است.")
            return
            
        # Get email
        email = TerminalUI.ask_input(
            "Enter email (for Let's Encrypt recovery & warning emails)",
            "ایمیل خود را وارد کنید (جهت اطلاع‌رسانی انقضای گواهی)"
        )
        if not email:
            TerminalUI.print_warning("Operation cancelled.", "عملیات لغو شد.")
            return
            
        # Choose authentication method
        methods = [
            "Nginx Plugin (Auto-configure Nginx) - پیشنهادی برای Nginx",
            "Apache Plugin (Auto-configure Apache) - پیشنهادی برای Apache",
            "Standalone Mode (Temporary web server - stops existing servers) - وب‌سرور موقت",
            "Webroot Mode (Provide path to existing webroot) - مشخص کردن مسیر پوشه هاست"
        ]
        
        method_idx = TerminalUI.select_menu(
            "Select Validation Method (روش احراز هویت)",
            methods,
            "متد احراز هویت دامنه توسط Let's Encrypt را انتخاب کنید"
        )
        
        # Build Certbot command
        # Force non-interactive and auto-agree to terms
        cmd = ["certbot", "certonly", "--non-interactive", "--agree-tos", "--email", email]
        
        # Add domains
        for d in domains:
            cmd.extend(["-d", d])
            
        if method_idx == 0:  # Nginx
            cmd.append("--nginx")
        elif method_idx == 1:  # Apache
            cmd.append("--apache")
        elif method_idx == 2:  # Standalone
            cmd.append("--standalone")
            TerminalUI.print_warning(
                "Standalone mode will temporarily bind to port 80. Ensure it is free.",
                "متد Standalone نیاز به پورت ۸۰ دارد. مطمئن شوید هیچ وب‌سروری روی این پورت در حال اجرا نیست."
            )
        elif method_idx == 3:  # Webroot
            webroot_path = TerminalUI.ask_input(
                "Enter webroot path (e.g. /var/www/html)",
                "مسیر پوشه اصلی وب‌سایت را وارد کنید (مانند /var/www/html)"
            )
            if not webroot_path or not os.path.exists(webroot_path):
                TerminalUI.print_error("Invalid webroot directory path.", "مسیر پوشه وب معتبر نیست یا وجود ندارد.")
                return
            cmd.extend(["--webroot", "-w", webroot_path])
            
        # Ask for Dry-run (testing)
        dry_run = TerminalUI.ask_confirm(
            "Perform a test dry-run first?",
            "آیا می‌خواهید ابتدا یک تست آزمایشی (Dry Run) انجام دهید؟",
            default_yes=True
        )
        
        if dry_run:
            cmd.append("--dry-run")
            
        full_command = " ".join(cmd)
        TerminalUI.print_info(
            f"Executing Command: {full_command}",
            f"در حال اجرای دستور: {full_command}"
        )
        
        print("\n" + "="*50 + " CERTBOT OUTPUT " + "="*50 + "\n")
        success = SystemManager.run_cmd_live(full_command)
        print("\n" + "="*116 + "\n")
        
        if success:
            if dry_run:
                TerminalUI.print_success(
                    "Dry-run succeeded! The parameters are valid.",
                    "تست آزمایشی با موفقیت انجام شد! پارامترها صحیح هستند."
                )
                
                # Ask if they want to run the real issuance now
                run_real = TerminalUI.ask_confirm(
                    "Would you like to issue the actual certificate now?",
                    "آیا می‌خواهید گواهی واقعی را اکنون صادر کنید؟",
                    default_yes=True
                )
                if run_real:
                    # Remove --dry-run
                    cmd.remove("--dry-run")
                    real_command = " ".join(cmd)
                    TerminalUI.print_info("Issuing real certificate...", "در حال صدور گواهی واقعی...")
                    print("\n" + "="*50 + " CERTBOT OUTPUT " + "="*50 + "\n")
                    real_success = SystemManager.run_cmd_live(real_command)
                    print("\n" + "="*116 + "\n")
                    if real_success:
                        TerminalUI.print_success(
                            "SSL certificate issued successfully!",
                            "گواهی SSL واقعی با موفقیت صادر گردید!"
                        )
                    else:
                        TerminalUI.print_error(
                            "Failed to issue SSL certificate.",
                            "صدور گواهی SSL واقعی با خطا مواجه شد."
                        )
            else:
                TerminalUI.print_success(
                    "SSL certificate issued successfully!",
                    "گواهی SSL با موفقیت صادر گردید!"
                )
        else:
            TerminalUI.print_error(
                "Certbot command failed. Check outputs above for details.",
                "عملیات Certbot ناموفق بود. خطاهای بالا را بررسی کنید."
            )

    @classmethod
    def renew_certificates(cls):
        """Runs the Certbot renewal command manually"""
        TerminalUI.print_header("Renew SSL Certificates", "تمدید گواهی‌های SSL")
        
        dry_run = TerminalUI.ask_confirm(
            "Perform a test dry-run renewal first?",
            "آیا می‌خواهید ابتدا یک تمدید آزمایشی (Dry Run) انجام دهید؟",
            default_yes=True
        )
        
        cmd = "certbot renew"
        if dry_run:
            cmd += " --dry-run"
            
        TerminalUI.print_info(f"Running: {cmd}", f"در حال اجرا: {cmd}")
        print("\n" + "="*50 + " CERTBOT OUTPUT " + "="*50 + "\n")
        success = SystemManager.run_cmd_live(cmd)
        print("\n" + "="*116 + "\n")
        
        if success:
            TerminalUI.print_success(
                "Certbot renewal process completed successfully!",
                "فرآیند تمدید گواهی‌ها با موفقیت پایان یافت!"
            )
        else:
            TerminalUI.print_error(
                "Certbot renewal failed. Check logs above.",
                "تمدید گواهی‌ها با خطا مواجه شد. لاگ بالا را بررسی کنید."
            )

    @classmethod
    def delete_certificate(cls):
        """Displays list of active certificates, lets user select one, and deletes it"""
        TerminalUI.print_header("Delete SSL Certificate", "حذف گواهی SSL")
        
        certs = cls.get_certificates()
        if not certs:
            TerminalUI.print_warning(
                "No certificates found to delete.",
                "هیچ گواهی برای حذف کردن یافت نشد."
            )
            return
            
        # Prepare list for interactive menu
        options = []
        for c in certs:
            options.append(f"{c['name']} (Domains: {c['domains'].replace(' ', ', ')})")
            
        options.append("Back to Main Menu (بازگشت به منوی اصلی)")
        
        selected_idx = TerminalUI.select_menu(
            "Select Certificate to Delete (انتخاب گواهی جهت حذف)",
            options,
            "گواهی مورد نظر خود را جهت حذف انتخاب کنید (غیر قابل بازگشت)"
        )
        
        if selected_idx == len(certs):
            return  # User chose "Back"
            
        cert_to_delete = certs[selected_idx]["name"]
        
        confirm = TerminalUI.ask_confirm(
            f"Are you SURE you want to delete certificate '{cert_to_delete}'? This cannot be undone!",
            f"آیا کاملاً مطمئنید که می‌خواهید گواهی '{cert_to_delete}' را حذف کنید؟ این عمل غیرقابل بازگشت است!",
            default_yes=False
        )
        
        if not confirm:
            TerminalUI.print_warning("Delete operation aborted.", "عملیات حذف لغو شد.")
            return
            
        cmd = f"certbot delete --cert-name {cert_to_delete}"
        TerminalUI.print_info(f"Running: {cmd}", f"در حال اجرا: {cmd}")
        
        success = SystemManager.run_cmd_live(cmd)
        if success:
            TerminalUI.print_success(
                f"Certificate '{cert_to_delete}' has been deleted successfully.",
                f"گواهی '{cert_to_delete}' با موفقیت حذف گردید."
            )
        else:
            TerminalUI.print_error(
                f"Failed to delete certificate '{cert_to_delete}'.",
                f"حذف گواهی '{cert_to_delete}' با خطا مواجه شد."
            )

    @classmethod
    def configure_renewal_hooks(cls):
        """Configures automated renewal post-hooks (e.g. reload Nginx/Apache) in renewal-hooks/post/"""
        TerminalUI.print_header("Configure Reload Hooks", "تنظیم هوک بارگذاری مجدد وب‌سرور")
        
        # Check systemd certbot timer
        timer_active = False
        if SystemManager.is_command_installed("systemctl"):
            success, stdout, _ = SystemManager.run_cmd("systemctl is-active certbot.timer", get_output=True)
            if success and "active" in stdout:
                timer_active = True
                
        if timer_active:
            TerminalUI.print_success(
                "Active systemd Certbot timer detected! Expiry checks run automatically twice a day.",
                "تایمر فعال systemd مربوط به Certbot شناسایی شد! بررسی انقضا به صورت خودکار ۲ بار در روز انجام می‌شود."
            )
        else:
            TerminalUI.print_warning(
                "No active systemd Certbot timer detected. Please ensure cron or systemd timer runs 'certbot renew'.",
                "تایمر فعال Certbot در سیستم یافت نشد. مطمئن شوید کرون‌جاب یا تایمر جهت اجرای 'certbot renew' تنظیم شده باشد."
            )
            
        # Certbot post-hooks reload webserver
        hook_dir = "/etc/letsencrypt/renewal-hooks/post"
        hook_file = f"{hook_dir}/reload-webserver.sh"
        
        TerminalUI.print_info(
            f"We can create a reload hook script in '{hook_file}'.\nThis runs automatically after any successful SSL certificate renewal.",
            f"می‌توانیم یک اسکریپت هوک در مسیر '{hook_file}' بسازیم.\nاین اسکریپت پس از تمدید موفق گواهی‌ها، به صورت خودکار وب‌سرور شما را مجددا بارگذاری می‌کند."
        )
        
        confirm = TerminalUI.ask_confirm(
            "Do you want to configure a web server reload hook?",
            "آیا می‌خواهید هوک بارگذاری مجدد وب‌سرور را تنظیم کنید؟",
            default_yes=True
        )
        
        if not confirm:
            TerminalUI.print_warning("Operation skipped.", "عملیات لغو شد.")
            return
            
        reload_command = TerminalUI.ask_input(
            "Enter web server reload command (e.g., systemctl reload nginx)",
            "دستور بارگذاری مجدد وب‌سرور خود را وارد کنید (مانند systemctl reload nginx)",
            default="systemctl reload nginx || systemctl reload apache2 || systemctl reload httpd"
        )
        
        if not reload_command:
            TerminalUI.print_warning("Reload command skipped.", "دستوری وارد نشد.")
            return
            
        if os.name == 'nt':
            # Stub for Windows local test
            TerminalUI.print_success(
                f"[Mocked] Created hook file '{hook_file}' with command: '{reload_command}'",
                f"[شبیه‌سازی] فایل هوک ایجاد گردید."
            )
            return
            
        try:
            # Ensure the directory exists
            os.makedirs(hook_dir, exist_ok=True)
            
            # Write bash script
            script_content = f"""#!/bin/bash
# Auto-generated by SSL Manager Python
echo "[$(date)] Executing SSL renewal hook: {reload_command}" >> /var/log/certbot-renew-hook.log
{reload_command} >> /var/log/certbot-renew-hook.log 2>&1
"""
            with open(hook_file, 'w') as f:
                f.write(script_content)
                
            # Make executable
            os.chmod(hook_file, 0o755)
            
            TerminalUI.print_success(
                f"Webserver reload hook configured successfully in '{hook_file}'!",
                f"هوک بارگذاری مجدد وب‌سرور با موفقیت در '{hook_file}' ایجاد گردید!"
            )
        except Exception as e:
            TerminalUI.print_error(
                f"Failed to create renewal hook: {e}",
                f"خطا در ایجاد فایل هوک: {e}"
            )


def main():
    # 1. Clear screen and display banner
    TerminalUI.clear_screen()
    TerminalUI.print_banner()
    
    # 2. Check for administrative (root) access
    if not SystemManager.is_root():
        TerminalUI.print_error(
            "This script requires root privileges to read and write Let's Encrypt certificates.",
            "این اسکریپت برای خواندن و نوشتن گواهی‌های SSL نیاز به دسترسی root (Sudo) دارد."
        )
        TerminalUI.print_info(
            "Please run: sudo python3 ssl_manager.py",
            "لطفاً به این صورت اجرا کنید: sudo python3 ssl_manager.py"
        )
        sys.exit(1)
        
    # 3. Check if Certbot is installed
    if not SystemManager.is_command_installed("certbot"):
        TerminalUI.print_warning(
            "Certbot is not installed on this system.",
            "نرم‌افزار Certbot بر روی این سیستم نصب نیست."
        )
        installed = SystemManager.install_certbot()
        if not installed:
            TerminalUI.print_error(
                "Certbot is required to run this manager. Exiting.",
                "برای استفاده از این برنامه، نصب بودن Certbot الزامی است. در حال خروج."
            )
            sys.exit(1)
            
    # Main CLI Loop
    while True:
        options = [
            "Issue a new SSL Certificate (صدور گواهی SSL جدید)",
            "List all SSL Certificates (مشاهده لیست گواهی‌های SSL)",
            "Renew SSL Certificates (تمدید گواهی‌های SSL)",
            "Delete an SSL Certificate (حذف گواهی SSL)",
            "Configure Web Server Reload Hooks (تنظیم هوک‌های وب‌سرور پس از تمدید)",
            "Exit (خروج از برنامه)"
        ]
        
        choice = TerminalUI.select_menu(
            "SSL Manager Main Menu",
            options,
            "منوی اصلی مدیریت SSL - گزینه مورد نظر را انتخاب کنید"
        )
        
        TerminalUI.clear_screen()
        TerminalUI.print_banner()
        
        if choice == 0:
            CertbotWrapper.issue_new_certificate()
        elif choice == 1:
            TerminalUI.print_header("Active SSL Certificates", "لیست گواهی‌های SSL فعال")
            CertbotWrapper.display_certificates()
        elif choice == 2:
            CertbotWrapper.renew_certificates()
        elif choice == 3:
            CertbotWrapper.delete_certificate()
        elif choice == 4:
            CertbotWrapper.configure_renewal_hooks()
        elif choice == 5:
            TerminalUI.clear_screen()
            print(f"\n{Colors.BOLD}{Colors.GREEN}Thank you for using SSL Manager! Goodbye.{Colors.RESET}")
            print(f"{Colors.GREEN}با تشکر از استفاده شما از برنامه مدیریت SSL. به امید دیدار.{Colors.RESET}\n")
            break
            
        TerminalUI.press_any_key()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h") # Ensure cursor is visible
        sys.stdout.flush()
        print("\n\nOperation aborted by user. (عملیات توسط کاربر متوقف شد)")
        sys.exit(0)
