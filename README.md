# Certificate Distribution Platform

FastAPI-based Certificate Distribution System that verifies students and management team members from CSV files and generates downloadable PDF certificates with student names rendered on custom templates.

## Features

✅ **Student Certificate Generation** — Verify students by Name + Student ID, download personalized certificates  
✅ **Management Certificate Generation** — Separate certificate system for management team with professional typography  
✅ **Name + ID Verification** — Secure lookup ensuring only valid entries can generate certificates  
✅ **Bulk Certificate Generation** — Admin endpoint to generate all certificates at once  
✅ **Professional Typography** — Playfair Display Bold font with custom letter spacing  
✅ **CSV-based Data** — No database required; works directly with CSV exports from forms  
✅ **Responsive Web Portal** — Toggle between Student/Management sections

## Project Structure

```
certificate-distribution-platform/
│
├── app/
│   ├── main.py                    # FastAPI app with all endpoints
│   ├── csv_handler.py             # CSV reading and student/management lookup
│   ├── certificate_generator.py   # PDF generation with Pillow
│   └── __init__.py
│
├── templates/
│   ├── index.html                 # Student/Management portal (toggle UI)
│   ├── certificate_template.jpg   # Student certificate background
│   └── CertificateManagement.jpeg # Management certificate background
│
├── data/
│   ├── students.csv               # Student records (from workshop form)
│   └── management.csv             # Management team records
│
├── certificates/                  # Output folder (PDFs saved here)
├── requirements.txt               # Python dependencies
├── runtime.txt                    # Python version for deployment
├── render.yaml                    # Render deployment config
└── README.md                      # This file
```

## Quick Start for Your Team

### Prerequisites

- **Python 3.10+** (check with `python --version`)
- **Git** (check with `git --version`)
- **pip** (comes with Python)

### Step 1: Clone the Repository

```bash
git clone https://github.com/space-cow-boy/certificate-distribution-platform.git
cd certificate-distribution-platform
```

### Step 2: Create Virtual Environment (Recommended)

**On Windows (PowerShell/CMD):**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `pillow` — PDF/image generation
- `python-multipart` — Form data handling

### Step 4: Run the Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

Open your browser to **http://localhost:8000** and you'll see the certificate portal.

### Step 5: Generate a Certificate (Test)

#### **Student Certificate:**
1. Click the **Student** tab (default)
2. Enter any student name and student ID from `data/students.csv`
   - Example: Name: `Aditya singh`, Student ID: `25101280272`
3. Click **Get Certificate**
4. Certificate PDF downloads and is saved to `certificates/` folder

#### **Management Certificate:**
1. Click the **Management** toggle
2. Enter a name and ID from `data/management.csv`
   - Example: Name: `Sandeep Singh`, ID: `240111532`
3. Click **Get Certificate**
4. Management certificate PDF downloads

## CSV File Format

### `data/students.csv`

Expected columns:
```
Timestamp, Name, Email_id, Student_Id, Course, Code
```

Example row:
```
1/20/2024 15:30:00, Aditya singh, email@example.com, 25101280272, Workshop-I, ABC123
```

### `data/management.csv`

Expected columns:
```
Name, Email_id, Student_Id, Year, Course
```

Example row:
```
Sandeep Singh, email@example.com, 240111532, 2024, Workshop-I
```

**Note:** `Student_Id` in management.csv is used as the Management ID for verification.

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serves HTML portal |
| `/health` | GET | Health check (returns `{status: ok}`) |
| `/verify?name=X&student_id=Y` | GET | Verify student exists in CSV |
| `/certificate?name=X&student_id=Y` | GET | Download student certificate |
| `/verify-management?name=X&mgmt_id=Y` | GET | Verify management member exists |
| `/certificate-management?name=X&mgmt_id=Y` | GET | Download management certificate |
| `/generate-all?admin_key=SECRET` | GET | Bulk-generate all student certificates |
| `/generate-all-management?admin_key=SECRET` | GET | Bulk-generate all management certificates |

**Example Requests:**
```
# Verify a student
http://localhost:8000/verify?name=Aditya%20singh&student_id=25101280272

# Download certificate
http://localhost:8000/certificate?name=Aditya%20singh&student_id=25101280272

# Verify management
http://localhost:8000/verify-management?name=Sandeep%20Singh&mgmt_id=240111532

# Download management certificate
http://localhost:8000/certificate-management?name=Sandeep%20Singh&mgmt_id=240111532
```

## Environment Variables (Optional)

You can customize behavior via environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `CSV_PATH` | `data/students.csv` | Path to student CSV file |
| `CSV_MANAGEMENT_PATH` | `data/management.csv` | Path to management CSV file |
| `CERTIFICATES_DIR` | `certificates` | Output folder for PDFs |
| `ADMIN_KEY` | empty | Required key for bulk generation (leave empty to disable) |
| `CERT_NAME_Y_OFFSET` | `0` | Student certificate name vertical offset (pixels) |
| `CERT_NAME_FONT_SIZE` | `auto` | Student certificate name font size |
| `CERT_MGMT_NAME_Y_OFFSET` | `-134` | Management certificate name vertical offset (pixels) |
| `CERT_MGMT_NAME_X_OFFSET` | `5` | Management certificate name horizontal offset (pixels) |
| `CERT_MGMT_NAME_FONT_SIZE` | `55` | Management certificate name font size |
| `CERT_MGMT_LETTER_SPACING` | `1.5` | Management certificate letter spacing (percentage) |
| `CERT_FONT_PATH` | `C:\\Windows\\Fonts\\PlayfairDisplay-Bold.otf` | Path to Playfair Display Bold font |

**Example (Windows PowerShell):**
```powershell
$env:ADMIN_KEY = "mySecretKey123"
$env:CERT_MGMT_NAME_Y_OFFSET = "-134"
uvicorn app.main:app --reload
```

**Example (macOS/Linux):**
```bash
export ADMIN_KEY="mySecretKey123"
export CERT_MGMT_NAME_Y_OFFSET="-134"
uvicorn app.main:app --reload
```

## Troubleshooting

### "Certificate template image not found"
- Ensure `templates/certificate_template.jpg` and `templates/CertificateManagement.jpeg` exist
- Check that image files are in the correct folder
- Verify file paths in `app/certificate_generator.py` if you moved the files

### "Student not found" / "Management not found"
- Double-check the **exact name spelling** and **student ID** from the CSV
- Open the CSV file to verify the data
- Names are **case-insensitive** but must match otherwise
- Student IDs are **exact match** (whitespace stripped)

### "Font file not found"
- **Windows:** Ensure Playfair Display Bold is installed
  - Download from Google Fonts: https://fonts.google.com/specimen/Playfair+Display
  - Install to `C:\Windows\Fonts\`
- **macOS/Linux:** Update `CERT_FONT_PATH` to your font location or install via package manager

### Certificates folder is empty
- Use the `/generate-all?admin_key=YOUR_KEY` endpoint to bulk-generate
- Or manually generate by accessing `/certificate?name=X&student_id=Y` for each student

### Port 8000 already in use
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
```

## Production Deployment

### Deploy to Render (Recommended)

1. Push this repository to your GitHub account (already done ✓)

2. Go to [https://render.com](https://render.com) and sign up/login

3. Create a new **Web Service**:
   - Click **New** → **Web Service**
   - Connect your GitHub repository
   - Select `certificate-distribution-platform`

4. Configure settings:
   - **Name:** `certificate-distribution-platform` (or your choice)
   - **Root Directory:** (leave empty)
   - **Runtime:** Python
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
     ```
   - **Python Version:** 3.10.13 (set via `runtime.txt`)

5. Add Environment Variables (in Render dashboard):
   - `ADMIN_KEY` = your secret key
   - `CERT_MGMT_NAME_Y_OFFSET` = `-134`
   - `CERT_MGMT_NAME_X_OFFSET` = `5`

6. Click **Create Web Service** and wait for deployment (usually 2-3 minutes)

7. Your live URL will be something like: `https://certificate-distribution-platform.onrender.com`

### Deploy to Other Platforms

**Heroku, Railway, or Replit:**
- Same build/start commands as Render
- Ensure Python 3.10+ is available
- Set environment variables via platform's UI

**Docker (for any platform):**
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Development Notes

### Code Structure

- **`app/main.py`** — FastAPI application with 8 endpoints
  - Routes requests to CSV handler and certificate generator
  - Handles both student and management verification
  - CORS middleware enabled for frontend requests

- **`app/csv_handler.py`** — CSV file operations
  - `CSVHandler` class handles reading and searching
  - `find_student_by_name_and_id()` — Case-insensitive name, exact ID match
  - `find_management_by_name_and_id()` — Same for management team
  - Generates certificate IDs in format: `CERT-{student_id}` and `CERT-MGMT-{mgmt_id}`

- **`app/certificate_generator.py`** — PDF generation
  - `CertificateGenerator` class uses Pillow for image rendering
  - `generate_certificate()` — Renders student name on template
  - `generate_management_certificate()` — Renders management member name
  - Font: Playfair Display Bold (Windows), fallback to DejaVuSans-Bold
  - Letter spacing support for professional appearance

- **`templates/index.html`** — Single-page application
  - Toggle between Student and Management tabs
  - JavaScript handles form submission and API calls
  - Displays certificate preview images

### Adding More Students/Management

1. **Students:** Add rows to `data/students.csv` with columns: `Name, Email_id, Student_Id, Course, Code`
2. **Management:** Add rows to `data/management.csv` with columns: `Name, Email_id, Student_Id, Year, Course`
3. Restart the server — new entries are immediately available
4. No need to regenerate certificates (they're created on-demand)

### Updating Certificate Templates

1. Replace `templates/certificate_template.jpg` (for students) or `templates/CertificateManagement.jpeg` (for management)
2. Delete old PDFs in `certificates/` folder to force regeneration
3. Restart the server

### Customizing Certificate Appearance

Edit environment variables to adjust positioning and font size:
- For **management certificates**, tune: `CERT_MGMT_NAME_Y_OFFSET`, `CERT_MGMT_NAME_X_OFFSET`
- Test locally with different values, then update in production

## Production Server (Gunicorn + Uvicorn Workers)

Render start command (required):

```
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

## Environment Variables

You can configure the service using environment variables (Render  Service  Environment):

- `CSV_PATH` (default: `data/students.csv`) — path to the CSV file.
- `CERTIFICATES_DIR` (default: `certificates`) — folder where PDFs are stored.
- `CERTIFICATE_TEMPLATE_IMAGE` (default: `templates/certificate_template.jpg`) — optional background image. If missing, the PDF is generated with a simple background.
- `CERTIFICATE_ID_PREFIX` (default: `CERT`) — prefix used for generated certificate IDs.
- `ADMIN_KEY` (default: empty) — if set, `/generate-all` requires `admin_key` to match.
- `CORS_ALLOW_ORIGINS` (default: `*`) — comma-separated list of allowed origins.

## API Endpoints

- `GET /` — serves the HTML portal from `templates/index.html`
- `GET /health` — returns JSON status
- `GET /verify?name=...&student_id=...` — validates the student from CSV
- `GET /certificate?name=...&student_id=...` — generates (if needed) and downloads the PDF
- `GET /generate-all?admin_key=...` — bulk-generate PDFs (optional admin key)

## Local Development

1) Install dependencies

```
pip install -r requirements.txt
```

2) Run locally

```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Deploy to Render (Web Service)

1) Push this repository to GitHub.

2) In Render:
- Dashboard  **New**  **Web Service**
- Connect your GitHub repo

3) Settings:
- **Runtime**: Python
- **Build Command**:
  ```
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```
  gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
  ```

4) Deploy.

## If Render shows Python 3.13 in logs

This repo pins Python via `runtime.txt` (python-3.10.13). If your Render build log shows something like `.venv/lib/python3.13/...`, Render is not using the repo root.

- In your Render service settings, ensure **Root Directory** is empty (repo root), and that `runtime.txt` exists at the repo root.
- Redeploy after changing Root Directory.

### Using render.yaml (recommended)

This repo includes `render.yaml`. You can use Render Blueprint deploy, or just keep it for documentation; Render will read it during blueprint deployments.
