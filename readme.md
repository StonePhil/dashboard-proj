# SOC Dashboard Simulator

**A retro-styled, fully functional Security Operations Center (SOC) dashboard simulation** built with Flask.

Perfect for demos, training sessions, cybersecurity awareness, or just nostalgic hacker vibes.

![Terminal aesthetic](https://img.shields.io/badge/theme-retro%20green%20on%20black-00FF00?style=for-the-badge)

---

## ✨ Features

- **Authentic retro terminal UI** — green monospace text on black background
- **Login system** with cosmetic 3-attempt timeout
- **Multiple log tables** (`table1`, `table2`, …) — like real SIEM partitions
- **Live continuous event streaming** — new security events appear automatically every 2–5 seconds
- **Realistic weighted event generation**:
  - 40% Port Scan Detected (suspicious)
  - 30% Failed Login Attempt (low)
  - 15% Privilege Escalation Attempt (medium)
  - 10% Suspicious Process (high)
  - 5% Malware Signature Match (critical)
- **Sticky table header** — columns stay visible while scrolling
- **One-click controls**:
  - **[ new ]** — create fresh table + start streaming
  - **[ open ]** — load first existing table (disabled when table is active)
  - **[ remove ]** — delete the last table
  - Tab switching between active tables
- **Real-time total log counter**
- **Auto-limiting** to last 300 visible rows for performance

---

## 🛠 Tech Stack

- **Backend**: Flask + SQLite
- **Frontend**: Pure HTML + Jinja2 + vanilla JavaScript (AJAX polling)
- **Database**: One SQLite file (`soc_logs.db`) with dynamic tables
- **No external dependencies** beyond Flask (see `requirements.txt`)

---

## 🚀 Quick Start

### 1. Clone / Download the project

```bash
git clone https://github.com/StonePhil/dashboard-proj
cd dashboard-proj
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python run.py
```

App will start at **http://127.0.0.1:5000**

---

## 🔑 Default Credentials

- **Username**: `admin`
- **Password**: `admin`

---

## 📖 How to Use

1. Open the app and log in.
2. Click **[ new ]** → a new table (`table1`, `table2`, …) is created and the first event appears.
3. Watch **live events stream in automatically** every 2–5 seconds (random interval).
4. Use the tabs to switch between tables.
5. Click **[ remove ]** to delete the most recent table.
6. Refresh the page safely — events continue without duplication or repeated actions.

---

## Project Structure

```
dashboard-proj/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── fake_data.py
│   └── templates/
│       ├── login.html
│       └── dashboard.html
├── config.py
├── requirements.txt
├── run.py
└── soc_logs.db          # created automatically
```

---

## Customization Tips

- Change polling speed in `dashboard.html` (line with `2000 + Math.random() * 3000`)
- Edit event weights in `fake_data.py`
- Add more statuses or users in `fake_data.py`
- Want faster/slower streaming? Change the random delay range

---

## ⚠️ Important Notes

- **This is a simulation only** — not for production use.
- Data is stored in a local SQLite file and is **not persistent across table deletions**.
- Designed for demonstration and educational purposes.

---
