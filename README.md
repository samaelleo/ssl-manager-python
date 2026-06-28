# 🔒 Linux SSL Manager (Python & Certbot)

[**راهنمای فارسی در پایین صفحه قرار دارد**](#-مدیریت-ssl-لینوکس-پایتون)

A visually polished, zero-dependency interactive Python CLI tool to issue, list, renew, and delete SSL certificates on Linux servers using Let's Encrypt (Certbot). Designed specifically to be run on remote servers via SSH.

---

## 🌟 Features

- **Interactive TUI Menu:** Navigate through options using arrow keys (or `j`/`k` Vim keys) and select with Enter.
- **Multiple Certificate Types:**
  - **Standard Domain:** Automated HTTP/Standalone issuance via Let's Encrypt.
  - **Wildcard Domain:** Automated manual DNS challenge verification (covers both `domain.com` and `*.domain.com`).
  - **Let's Encrypt IP Address:** Generates a publicly trusted short-lived SSL certificate for public IPs using Let's Encrypt's `shortlived` profile (valid for 6 days).
  - **Self-Signed IP Address:** Generates a secure self-signed SSL certificate with IP Subject Alternative Name (SAN) using OpenSSL (valid for 365 days).
- **Zero External Dependencies:** Built entirely with Python's standard library. Works out-of-the-box on any Linux server.
- **Auto-Installation:** Automatically detects your distribution package manager (`apt`, `dnf`, `yum`, `pacman`) and installs Certbot with Apache/Nginx plugins if they are missing.
- **Polished Visuals:** Colored ANSI outputs for clean status messages, success/error banners, and a dynamic box-drawn certificates table.
- **Automatic Renewal Hooks:** Easily configure post-renewal reload scripts for your web servers (Nginx/Apache/etc.).
- **Bilingual Interface:** Displays clear descriptions in both English and Persian for ease of use.
- **Cross-Platform Test Support:** Falls back to standard numeric menus if run on Windows or non-TTY environments for local testing.

---

To run this tool directly on your remote Linux server without saving a permanent copy of the file:

```bash
TMP_FILE=$(mktemp) && curl -sSL https://raw.githubusercontent.com/samaelleo/ssl-manager-python/main/ssl_manager.py -o "$TMP_FILE" && sudo python3 "$TMP_FILE"; rm -f "$TMP_FILE"
```

*Note: The script downloads to a temporary file, executes with root privileges, and is automatically deleted when the CLI exits (even if interrupted).*

---

## 🛠 Menu Breakdown

1. **Issue Standard SSL Certificate:** Interactively issues a standard SSL certificate for domains via Nginx, Apache, Standalone, or Webroot.
2. **Issue Wildcard SSL Certificate:** Issues a wildcard certificate for domains via Let's Encrypt manual DNS challenge.
3. **Issue Let's Encrypt IP SSL:** Issues a publicly trusted short-lived (6-day) certificate for public IPs using Let's Encrypt.
4. **Issue Self-Signed IP SSL:** Generates a 365-day self-signed certificate with IP SAN using OpenSSL.
5. **List all SSL Certificates:** Parses Let's Encrypt certificates database and `/etc/letsencrypt/live` directories to render a beautiful terminal table with color-coded days remaining (Green for safe, Yellow for renewal warnings, Red for critical/expired). Lists both Let's Encrypt and Self-Signed IP certificates.
6. **Renew SSL Certificates:** Triggers Certbot's renew command with interactive option for a Dry Run.
7. **Delete an SSL Certificate:** Select a certificate from an interactive list and safely delete it. For self-signed certificates, it automatically deletes their directory from the disk.
8. **Configure Web Server Reload Hooks:** Automates writing a reload script to `/etc/letsencrypt/renewal-hooks/post/` that runs every time a certificate is successfully renewed, ensuring Nginx/Apache reloads and applies the new certificate.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](file:///c:/Users/Samael/PycharmProjects/ssl-manager-python/LICENSE) for more information.

---

# 🔒 مدیریت SSL لینوکس (پایتون)

یک ابزار تعاملی خط فرمان (CLI) بسیار زیبا، خوانا و بدون وابستگی خارجی به زبان پایتون جهت صدور، مشاهده لیست، تمدید و حذف گواهی‌های SSL در سرورهای لینوکس با استفاده از Let's Encrypt (Certbot). این ابزار به طور ویژه برای استفاده آسان روی سرورهای لینوکسی از طریق SSH طراحی شده است.

## 🌟 ویژگی‌ها

- **منوی تعاملی پیشرفته:** امکان پیمایش گزینه‌ها با کلیدهای جهت‌نمای بالا و پایین (یا کلیدهای Vim یعنی `j`/`k`) و انتخاب با کلید Enter.
- **انواع مختلف گواهی‌نامه:**
  - **دامنه استاندارد (Standard):** صدور خودکار با متدهای HTTP/Standalone توسط Let's Encrypt.
  - **دامنه وایلدکارد (Wildcard):** صدور گواهی وایلدکارد (شامل `domain.com` و `*.domain.com`) از طریق تأیید رکورد DNS TXT به طور تعاملی.
  - **آی‌پی با Let's Encrypt:** تولید گواهی معتبر عمومی برای آی‌پی‌های عمومی با اعتبار ۶ روزه (با قابلیت تمدید خودکار).
  - **آی‌پی خودامضا (Self-Signed):** تولید گواهی خودامضا و ایمن با هدر IP SAN با استفاده از OpenSSL با اعتبار ۳۶۵ روزه.
- **بدون نیاز به نصب پکیج:** کاملاً با استفاده از کتابخانه‌های استاندارد پایتون نوشته شده و روی تمام سرورها فوراً اجرا می‌شود.
- **نصب خودکار Certbot:** شناسایی خودکار مدیر بسته توزیع‌های مختلف لینوکس (`apt`, `dnf`, `yum`, `pacman`) و نصب برنامه Certbot همراه با پلاگین‌های وب‌سرور در صورت عدم وجود.
- **ظاهر بصری و خوانا:** استفاده از کدهای رنگی استاندارد ANSI برای پیام‌ها، جدول‌های منظم متنی و کادرهای موفقیت/خطا.
- **تنظیم خودکار هوک‌های وب‌سرور:** امکان پیکربندی اسکریپت بارگذاری مجدد وب‌سرور (Nginx/Apache) بلافاصله پس از تمدید موفق گواهی‌ها.
- **رابط دوزبانه:** نمایش توضیحات به دو زبان انگلیسی و فارسی جهت درک راحت‌تر مراحل کار.
- **قابلیت تست لوکال:** سوئیچ خودکار به منوی عددی ساده در سیستم‌عامل‌های غیر لینوکس (مانند ویندوز) جهت سهولت در توسعه و تست.

---

برای اجرای مستقیم ابزار روی سرور لینوکس خود بدون ذخیره دائمی فایل اسکریپت:

```bash
TMP_FILE=$(mktemp) && curl -sSL https://raw.githubusercontent.com/samaelleo/ssl-manager-python/main/ssl_manager.py -o "$TMP_FILE" && sudo python3 "$TMP_FILE"; rm -f "$TMP_FILE"
```

*توضیح: این دستور اسکریپت را در یک فایل موقت دانلود و اجرا کرده و بلافاصله پس از بسته شدن برنامه (حتی در صورت بروز خطا یا لغو با Ctrl+C) فایل موقت را به طور کامل حذف می‌کند.*

---

## 🛠 راهنمای گزینه‌های منو

۱. **صدور گواهی دامنه استاندارد:** دریافت اطلاعات دامنه، ایمیل و متد اعتبارسنجی جهت صدور گواهی با قابلیت تست آزمایشی.
۲. **صدور گواهی دامنه Wildcard:** صدور گواهی وایلدکارد برای دامنه و زیردامنه‌ها با ثبت رکورد DNS TXT.
۳. **صدور گواهی آی‌پی با Let's Encrypt:** صدور گواهی معتبر عمومی برای آی‌پی عمومی سرور با اعتبار کوتاه مدت ۶ روزه.
۴. **صدور گواهی آی‌پی خودامضا:** صدور گواهی خودامضا با هدر IP SAN با اعتبار ۳۶۵ روزه با ابزار OpenSSL.
۵. **مشاهده لیست گواهی‌ها:** استخراج اطلاعات گواهی‌های فعال Let's Encrypt و مسیر `/etc/letsencrypt/live` و نمایش آن‌ها در یک جدول متنی بسیار زیبا همراه با هایلایت کردن تاریخ انقضا (شامل گواهی‌های Let's Encrypt و خودامضا).
۶. **تمدید گواهی‌ها:** تمدید دستی گواهی‌های Let's Encrypt به همراه گزینه تست آزمایشی.
۷. **حذف گواهی:** انتخاب و حذف کاملاً امن یکی از گواهی‌های فعال از لیست. در مورد گواهی‌های خودامضا، پوشه مربوطه را مستقیماً از روی دیسک پاک می‌کند.
۸. **تنظیم هوک بارگذاری مجدد وب‌سرور:** نوشتن خودکار اسکریپت بارگذاری مجدد وب‌سرور در پوشه `/etc/letsencrypt/renewal-hooks/post/` تا وب‌سرور بلافاصله پس از تمدید موفق گواهی‌ها، پیکربندی جدید را اعمال کند و از خطای انقضای کش وب‌سرور جلوگیری شود.
