# 🔒 Linux SSL Manager (Python & Certbot)

[**راهنمای فارسی در پایین صفحه قرار دارد**](#-مدیریت-ssl-لینوکس-پایتون)

A visually polished, zero-dependency interactive Python CLI tool to issue, list, renew, and delete SSL certificates on Linux servers using Let's Encrypt (Certbot). Designed specifically to be run on remote servers via SSH.

---

## 🌟 Features

- **Interactive TUI Menu:** Navigate through options using arrow keys (or `j`/`k` Vim keys) and select with Enter.
- **Zero External Dependencies:** Built entirely with Python's standard library. Works out-of-the-box on any Linux server.
- **Auto-Installation:** Automatically detects your distribution package manager (`apt`, `dnf`, `yum`, `pacman`) and installs Certbot with Apache/Nginx plugins if they are missing.
- **Polished Visuals:** Colored ANSI outputs for clean status messages, success/error banners, and a dynamic box-drawn certificates table.
- **Automatic Renewal Hooks:** Easily configure post-renewal reload scripts for your web servers (Nginx/Apache/etc.).
- **Bilingual Interface:** Displays clear descriptions in both English and Persian for ease of use.
- **Cross-Platform Test Support:** Falls back to standard numeric menus if run on Windows or non-TTY environments for local testing.

---

## 🚀 Quick Start / installation

To run this tool directly on your remote Linux server:

1. **Download the script:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>/main/ssl_manager.py -o ssl_manager.py
   ```

2. **Make it executable:**
   ```bash
   chmod +x ssl_manager.py
   ```

3. **Run with sudo (required for Certbot actions):**
   ```bash
   sudo ./ssl_manager.py
   ```

---

## 🛠 Menu Breakdown

1. **Issue a new SSL Certificate:** Starts an interactive step-by-step wizard prompting for domains, recovery email, and authentication plugin (Nginx, Apache, Standalone, or Webroot). Allows performing a mock "Dry Run" test before issuing the live certificate.
2. **List all SSL Certificates:** Parses Let's Encrypt certificates database and renders a beautiful terminal table with color-coded days remaining (Green for safe, Yellow for renewal warnings, Red for critical/expired).
3. **Renew SSL Certificates:** Triggers Certbot's renew command with interactive option for a Dry Run.
4. **Delete an SSL Certificate:** Select a certificate from an interactive list and safely delete it.
5. **Configure Web Server Reload Hooks:** Automates writing a reload script to `/etc/letsencrypt/renewal-hooks/post/` that runs every time a certificate is successfully renewed, ensuring Nginx/Apache reloads and applies the new certificate.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](file:///c:/Users/Samael/PycharmProjects/ssl-manager-python/LICENSE) for more information.

---

# 🔒 مدیریت SSL لینوکس (پایتون)

یک ابزار تعاملی خط فرمان (CLI) بسیار زیبا، خوانا و بدون وابستگی خارجی به زبان پایتون جهت صدور، مشاهده لیست، تمدید و حذف گواهی‌های SSL در سرورهای لینوکس با استفاده از Let's Encrypt (Certbot). این ابزار به طور ویژه برای استفاده آسان روی سرورهای لینوکسی از طریق SSH طراحی شده است.

## 🌟 ویژگی‌ها

- **منوی تعاملی پیشرفته:** امکان پیمایش گزینه‌ها با کلیدهای جهت‌نمای بالا و پایین (یا کلیدهای Vim یعنی `j`/`k`) و انتخاب با کلید Enter.
- **بدون نیاز به نصب پکیج:** کاملاً با استفاده از کتابخانه‌های استاندارد پایتون نوشته شده و روی تمام سرورها فوراً اجرا می‌شود.
- **نصب خودکار Certbot:** شناسایی خودکار مدیر بسته توزیع‌های مختلف لینوکس (`apt`, `dnf`, `yum`, `pacman`) و نصب برنامه Certbot همراه با پلاگین‌های وب‌سرور در صورت عدم وجود.
- **ظاهر بصری و خوانا:** استفاده از کدهای رنگی استاندارد ANSI برای پیام‌ها، جدول‌های منظم متنی و کادرهای موفقیت/خطا.
- **تنظیم خودکار هوک‌های وب‌سرور:** امکان پیکربندی اسکریپت بارگذاری مجدد وب‌سرور (Nginx/Apache) بلافاصله پس از تمدید موفق گواهی‌ها.
- **رابط دوزبانه:** نمایش توضیحات به دو زبان انگلیسی و فارسی جهت درک راحت‌تر مراحل کار.
- **قابلیت تست لوکال:** سوئیچ خودکار به منوی عددی ساده در سیستم‌عامل‌های غیر لینوکس (مانند ویندوز) جهت سهولت در توسعه و تست.

---

## 🚀 راه اندازی سریع و اجرا

برای اجرای سریع ابزار روی سرور لینوکس خود دستورات زیر را وارد کنید:

۱. **دانلود اسکریپت:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>/main/ssl_manager.py -o ssl_manager.py
   ```

۲. **ایجاد دسترسی اجرا:**
   ```bash
   chmod +x ssl_manager.py
   ```

۳. **اجرا با دسترسی مدیریت (نیاز به sudo جهت مدیریت گواهی‌ها):**
   ```bash
   sudo ./ssl_manager.py
   ```

---

## 🛠 راهنمای گزینه‌های منو

۱. **صدور گواهی SSL جدید (Issue):** راهنمای گام به گام جهت وارد کردن دامنه‌ها، ایمیل ارتباطی و متد احراز هویت (Nginx, Apache, Standalone, Webroot). همچنین امکان تست آزمایشی (Dry Run) قبل از صدور واقعی وجود دارد.
۲. **لیست گواهی‌ها (List):** استخراج اطلاعات گواهی‌های فعال Let's Encrypt و نمایش آن‌ها در یک جدول متنی بسیار زیبا با رنگ‌بندی بر اساس روزهای باقی‌مانده تا انقضا (سبز: معتبر، زرد: نیاز به تمدید، قرمز: منقضی/بحرانی).
۳. **تمدید گواهی‌ها (Renew):** تمدید دستی گواهی‌ها به همراه گزینه تست آزمایشی.
۴. **حذف گواهی (Delete):** انتخاب و حذف کاملاً امن یکی از گواهی‌های فعال از لیست به صورت تعاملی.
۵. **تنظیم هوک بارگذاری مجدد وب‌سرور (Hooks):** نوشتن خودکار اسکریپت بارگذاری مجدد وب‌سرور در پوشه `/etc/letsencrypt/renewal-hooks/post/` تا وب‌سرور بلافاصله پس از تمدید موفق گواهی‌ها، پیکربندی جدید را اعمال کند و از خطای انقضای کش وب‌سرور جلوگیری شود.
