# SmartPOS - Point of Sale Management System

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django 3.2+](https://img.shields.io/badge/Django-3.2+-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)](https://www.postgresql.org/)
[![Status: Production](https://img.shields.io/badge/Status-Production-brightgreen.svg)](#)

A modern, user-friendly Point of Sale (POS) system built with Django. SmartPOS streamlines retail operations with real-time sales tracking, inventory management, and comprehensive reporting.

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Contributing](#-contributing) • [License](#-license)

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [User Roles](#-user-roles--permissions)
- [API Documentation](#-api-endpoints)
- [Troubleshooting](#-troubleshooting)
- [Backup & Recovery](#-backing-up-data)
- [Security](#-security-best-practices)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support--contact)

---

## ✨ Features

### 🛒 Core POS Functions

- **Quick Sales Processing** - Fast checkout with product search and barcode support
- **Multiple Payment Methods** - Cash, M-Pesa, Card, and other payment options
- **Real-time Inventory** - Automatic stock updates with low stock alerts
- **Transaction History** - Complete record of all sales and transactions
- **Receipt Management** - Print or email receipts to customers

### 📊 Dashboard & Reporting

- **Real-time Dashboard** - KPIs including daily sales, profit margins, and transaction counts
- **Top Selling Products** - View best-performing products at a glance
- **Payment Distribution Analytics** - Track payment method usage patterns
- **Stock Management** - Monitor low stock and out-of-stock items
- **Detailed Reports** - Generate sales reports by date range, product, or category

### 📦 Inventory Management

- **Product Catalog** - Add, edit, and manage products with pricing tiers
- **Stock Tracking** - Monitor quantities across locations
- **Low Stock Alerts** - Automatic notifications for items needing reorder
- **Barcode Support** - Quick product lookup via barcodes
- **Stock Adjustments** - Manual inventory corrections and audits

### 👥 User Management

- **Role-Based Access Control** - Admin, manager, and cashier roles
- **Activity Logs** - Track user actions and system events
- **Multi-user Support** - Secure login and session management
- **Permission Management** - Granular control over user capabilities

---

## 🖥️ System Requirements

| Requirement  | Version             | Notes                           |
| ------------ | ------------------- | ------------------------------- |
| **Python**   | 3.8+                | Required for Django framework   |
| **Database** | PostgreSQL 10+      | SQLite for development only     |
| **Django**   | 3.2+                | Web framework                   |
| **OS**       | Windows/macOS/Linux | Cross-platform support          |
| **RAM**      | 2GB minimum         | 4GB+ recommended for production |
| **Storage**  | 500MB               | Initial installation + data     |

---

## 📦 Installation

### Prerequisites

- Git installed on your system
- Python 3.8 or higher
- PostgreSQL (for production) or SQLite (development)
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/smartpos.git
cd smartpos
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Environment Setup

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/smartpos

# POS Settings
CURRENCY=KES
TIME_ZONE=Africa/Nairobi

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

> **Note:** Generate a secret key using `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`

### Step 5: Database Migration

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser
```

### Step 6: Load Sample Data (Optional)

```bash
python manage.py loaddata sample_products.json
python manage.py loaddata sample_categories.json
```

### Step 7: Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

---

## 🚀 Quick Start

1. **Login**: Navigate to `http://localhost:8000/login/`
2. **Explore Dashboard**: View real-time sales metrics
3. **Add Products**: Go to Products → Add New Product
4. **Process Sale**: Click "New Sale" to start checkout
5. **View Reports**: Generate sales analytics

---

## ⚙️ Configuration

### Database Setup

**PostgreSQL (Production)**

```bash
# Create database
createdb smartpos

# Create user
createuser smartpos_user

# Update .env
DATABASE_URL=postgresql://smartpos_user:password@localhost:5432/smartpos
```

**SQLite (Development)**

```env
DATABASE_URL=sqlite:///db.sqlite3
```

### Email Configuration

For automated receipt and report emails:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Localization

Update settings for your region:

```python
# settings.py
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True
CURRENCY = 'KES'
DECIMAL_PLACES = 2
```

---

## 📖 Usage Guide

### Processing a Sale

1. Click **"New Sale"** from dashboard
2. Search for product or scan barcode
3. Enter quantity and add to cart
4. Review cart total
5. Select payment method (Cash, M-Pesa, Card)
6. Process payment
7. Print or email receipt

### Managing Inventory

1. Navigate to **Products**
2. View all products with current stock levels
3. Click product to edit details, pricing, or stock
4. Set reorder levels for automatic alerts
5. Track stock history

### Generating Reports

1. Go to **Reports** section
2. Select report type:
   - Sales Report
   - Inventory Report
   - Profit Analysis
   - Payment Methods
3. Choose date range
4. Click **Generate**
5. Export as PDF or Excel

### Admin Functions

1. Navigate to **Settings**
2. Manage users and roles
3. Configure payment methods
4. View system logs
5. Backup database

---

## 👥 User Roles & Permissions

| Role        | Sales | Inventory | Reports | Settings | Users |
| ----------- | :---: | :-------: | :-----: | :------: | :---: |
| **Cashier** |  ✅   |    ❌     | Limited |    ❌    |  ❌   |
| **Manager** |  ✅   |    ✅     |   ✅    |    ❌    |  ❌   |
| **Admin**   |  ✅   |    ✅     |   ✅    |    ✅    |  ✅   |

### Role Descriptions

**Cashier**

- Process sales transactions
- View personal transaction history
- Print receipts
- No access to settings or reports

**Manager**

- All Cashier permissions
- Manage products and inventory
- View and generate reports
- Manage low stock alerts
- No access to user management

**Admin**

- Full system access
- Create and manage users
- Configure system settings
- Access activity logs
- Database management

---

## 🔌 API Endpoints

### Products

```
GET    /api/products/              List all products
POST   /api/products/              Create new product
GET    /api/products/{id}/         Get product details
PUT    /api/products/{id}/         Update product
DELETE /api/products/{id}/         Delete product
```

### Sales

```
POST   /api/sales/                 Create new sale
GET    /api/sales/                 Get sales history
GET    /api/sales/{id}/            Get sale details
GET    /api/sales/today/           Get today's sales
```

### Reports

```
GET    /api/reports/sales/         Generate sales report
GET    /api/reports/inventory/     Generate inventory report
GET    /api/reports/profit/        Generate profit analysis
GET    /api/reports/payments/      Payment methods breakdown
```

### Categories

```
GET    /api/categories/            List all categories
POST   /api/categories/            Create category
PUT    /api/categories/{id}/       Update category
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Use a different port
python manage.py runserver 8001
```

### Database Connection Error

```bash
# Verify PostgreSQL is running
psql -U username -d smartpos -h localhost

# Check .env DATABASE_URL format
DATABASE_URL=postgresql://user:password@localhost:5432/smartpos
```

### Static Files Not Loading

```bash
python manage.py collectstatic --noinput
```

### Missing Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Migration Issues

```bash
# Reset migrations (development only)
python manage.py migrate yourapp zero
python manage.py migrate
```

---

## 💾 Backing Up Data

### PostgreSQL Backup

```bash
# Full backup
pg_dump -U smartpos_user -d smartpos > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql -U smartpos_user -d smartpos < backup.sql
```

### Django Data Export

```bash
# Export all data
python manage.py dumpdata > data_backup.json

# Restore data
python manage.py loaddata data_backup.json
```

### Scheduled Backups (Linux/macOS)

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * pg_dump -U smartpos_user -d smartpos > /backup/smartpos_$(date +\%Y\%m\%d).sql
```

---

## 🔒 Security Best Practices

- [ ] Change default admin credentials immediately
- [ ] Set `DEBUG=False` in production
- [ ] Use strong, unique database passwords
- [ ] Enable HTTPS/SSL in production
- [ ] Regularly update Django and dependencies
  ```bash
  pip list --outdated
  pip install --upgrade -r requirements.txt
  ```
- [ ] Implement regular automated backups
- [ ] Enable activity logging and review logs regularly
- [ ] Use environment variables for sensitive data (never commit `.env`)
- [ ] Implement rate limiting for API endpoints
- [ ] Run security checks
  ```bash
  python manage.py check --deploy
  ```
- [ ] Keep system dependencies updated
- [ ] Use strong passwords and 2FA for admin accounts

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

### Fork & Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/yourusername/smartpos.git
cd smartpos
```

### Create Feature Branch

```bash
git checkout -b feature/amazing-feature
```

### Make Your Changes

- Write clean, readable code
- Add/update comments for complex logic
- Follow Django best practices
- Include tests for new features

### Commit & Push

```bash
git add .
git commit -m "feat: add amazing feature"
git push origin feature/amazing-feature
```

### Submit Pull Request

1. Go to GitHub and open a Pull Request
2. Provide clear description of changes
3. Reference any related issues
4. Wait for review and feedback

### Coding Standards

- Use PEP 8 style guide
- Write descriptive commit messages
- Add docstrings to functions
- Keep functions small and focused
- Write unit tests for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

---

## 💬 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/smartpos/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/smartpos/discussions)
- **Email**: support@smartpos.local
- **Documentation**: [Wiki](https://github.com/yourusername/smartpos/wiki)

---

## 🗺️ Roadmap

### Version 1.1 (Q2 2026)

- [ ] Mobile app (iOS/Android)
- [ ] Cloud synchronization
- [ ] Advanced analytics dashboard

### Version 1.2 (Q3 2026)

- [ ] Multi-location support
- [ ] Customer loyalty program
- [ ] Integration with accounting software

### Future

- [ ] Predictive analytics
- [ ] AI-powered inventory management
- [ ] Voice-assisted checkout

---

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/smartpos?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/smartpos?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/smartpos)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/smartpos)

---

## 🙏 Acknowledgments

- Built with [Django](https://www.djangoproject.com/)
- Database: [PostgreSQL](https://www.postgresql.org/)
- Frontend: [Bootstrap](https://getbootstrap.com/)
- Icons: [FontAwesome](https://fontawesome.com/)

---

<div align="center">

**[⬆ back to top](#smartpos---point-of-sale-management-system)**

Made with ❤️ for retail businesses

</div>
