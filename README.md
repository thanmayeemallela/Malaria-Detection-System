# Malaria Detection System

A simple, complete, and demonstrable **Diploma-Level Django Web Application** for automated malaria screening using thin blood smear microscopy images and machine learning.

---

## 1. Project Overview

Malaria remains a major global health concern caused by *Plasmodium* parasites transmitted via *Anopheles* mosquitoes. The gold-standard diagnostic method is microscopic examination of Giemsa-stained thin blood smears.

This project implements an automated, desktop-friendly clinical decision-support application that allows healthcare workers and laboratory technicians to:
1. Register and manage patient demographic records.
2. Record optional clinical symptoms (e.g., fever, chills, sweating, headache).
3. Upload microscopic thin blood smear cell images.
4. Automatically pre-process images (RGB conversion, resizing to $128 \times 128$, normalization).
5. Screen the sample using an AI/ML classification model trained on the official **NIH / National Library of Medicine (NLM) Malaria Dataset**.
6. View real-time screening predictions (**Parasitized** vs. **Uninfected**) with model confidence scores and latency metrics.
7. Track comprehensive patient screening histories.
8. Automatically generate downloadable and printable laboratory reports in PDF and HTML format.

---

## 2. Key Features

- **User Authentication**: Secure login and logout system powered by Django Auth for authorized laboratory staff and administrators.
- **Dashboard Overview**: Summary counters for total patients, total tests performed, detected parasitized cases, healthy uninfected cases, and recent test activity.
- **Patient Management**: Complete CRUD interface (register, view, search, edit, view history) with unique auto-generated IDs (`PAT-1001`, `PAT-1002`).
- **Clinical Symptom Tracking**: Records observed clinical indicators (fever, chills, headache, sweating, fatigue, other notes) as supporting clinical context.
- **Microscopy Image Processing**:
  - Validates file format (JPG, JPEG, PNG) and file size (up to 10 MB).
  - Resizes images to standardized $128 \times 128$ dimensions.
  - Normalizes pixel values for feature extraction.
- **Real ML Model Integration**:
  - Trained on the benchmark **NIH / NLM Malaria Cell Images Dataset** (27,558 Giemsa-stained microscopy cell images).
  - Evaluates color histograms, Giemsa chromatin contrast, intracellular inclusions, and cell edge contours.
  - Achieved **94.0% test accuracy** on real holdout test data.
- **Automated Laboratory Reports**:
  - One-click PDF download generated using ReportLab.
  - Browser-friendly printable HTML report (`Ctrl+P` formatted).
- **Patient Test History**: Complete chronological history of previous tests for each patient.
- **Django Administration**: Built-in Django Admin interface (`/admin/`) with inline viewing of smears, symptoms, predictions, and reports.

---

## 3. Technology Stack

| Component | Technology |
|---|---|
| **Backend Framework** | Python 3.14 & Django 6.1 |
| **Database** | SQLite (default local relational database) |
| **Machine Learning** | scikit-learn (Random Forest Ensemble Classifier), NumPy, SciPy |
| **Image Processing** | Pillow (PIL) |
| **PDF Generation** | ReportLab |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (Image Preview) |
| **Dataset** | Official NIH / NLM Malaria Cell Images Dataset |

---

## 4. Project Structure

```
maleria detection system/
│
├── manage.py                          # Django management script
├── run.bat                            # Windows 1-click startup script
├── requirements.txt                   # Project Python dependencies
├── credentials.txt                    # Auto-generated administrator credentials
├── test_workflow.py                   # Automated end-to-end integration test
├── train_model.py                     # ML model training and evaluation script
├── download_dataset.py                # NIH dataset downloader
│
├── malaria_detection/                 # Project configuration
│   ├── __init__.py
│   ├── settings.py                   # Apps, media, static, database settings
│   ├── urls.py                       # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
│
├── detection/                         # Core Django application
│   ├── models.py                     # Patient, TestRecord, Prediction, Report, etc.
│   ├── views.py                      # Application views and workflow handlers
│   ├── urls.py                       # Application endpoints
│   ├── forms.py                      # Patient and test forms
│   ├── admin.py                      # Django admin customizations
│   ├── ml_model.py                   # ML model loader & inference engine
│   ├── utils.py                      # PDF report generator and validation
│   ├── templates/
│   │   └── detection/
│   │       ├── base.html             # Base layout with navbar and footer
│   │       ├── login.html            # Staff authentication page
│   │       ├── dashboard.html        # Main dashboard with statistics
│   │       ├── patient_list.html     # Searchable patient directory
│   │       ├── patient_form.html     # Patient registration & edit form
│   │       ├── patient_detail.html   # Patient demographic profile
│   │       ├── test_form.html        # Screening test & image upload form
│   │       ├── result.html           # Prediction outcome & analytics view
│   │       ├── history.html          # Individual patient test history
│   │       ├── all_history.html      # Global screening records table
│   │       └── report.html           # Printable laboratory report view
│
├── static/
│   └── css/
│       └── styles.css                # Professional laboratory UI stylesheet
│
├── media/                             # Uploaded and generated files
│   ├── blood_smears/                 # Uploaded microscopy images
│   └── reports/                      # Generated PDF laboratory reports
│
├── models/
│   ├── malaria_classifier.joblib     # Trained ML model weights
│   └── model_metrics.json            # Model evaluation metrics and accuracy
│
├── sample_images/                     # Real NIH sample images for quick testing
│   ├── real_nih_parasitized_1.png
│   └── real_nih_uninfected_1.png
│
└── dataset/
    └── cell_images/                  # Official NIH dataset
        ├── Parasitized/              # 13,779 infected cell images
        └── Uninfected/               # 13,779 healthy cell images
```

---

## 5. Database Architecture

```
User (Django Auth)
  │
  ▼
Patient (patient_id, name, age, gender, contact, address, created_at)
  │
  ├── 1 : Many ──► TestRecord (test_id, conducted_by, test_date, notes)
                     │
                     ├── 1 : 1 ──► BloodSmearImage (image, file_size_kb, uploaded_at)
                     │
                     ├── 1 : 1 ──► Symptom (fever, chills, headache, sweating, fatigue)
                     │
                     ├── 1 : 1 ──► Prediction (result, confidence_score, raw_score)
                     │               │
                     │               └── Many : 1 ──► MLModelInfo (name, version)
                     │
                     └── 1 : 1 ──► Report (report_id, generated_at, pdf_file)
```

---

## 6. How to Run Locally

### Option A: Using Windows Batch Script (Recommended)
Double-click `run.bat` or run from PowerShell / Command Prompt:
```powershell
.\run.bat
```
This automatically activates the local virtual environment, verifies migrations, checks model weights, and starts the Django development server at `http://127.0.0.1:8000`.

### Option B: Manual Command Line
1. Open PowerShell in the project directory:
   ```powershell
   cd "c:\Users\Swapna\OneDrive\Desktop\maleria detection system"
   ```
2. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\activate
   ```
3. Run migrations:
   ```powershell
   python manage.py migrate
   ```
4. Start the server:
   ```powershell
   python manage.py runserver 127.0.0.1:8000
   ```
5. Open your browser to:
   - Application: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - Admin Panel: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### Default Login Credentials
Staff credentials are automatically configured in `credentials.txt`:
- **Username**: `admin`
- **Password**: *(See `credentials.txt`)*

---

## 7. Model Training & Evaluation Details

The screening engine was trained using `train_model.py` on real thin blood smear microscopy images from the **NIH / National Library of Medicine (NLM)** dataset:

- **Classes**:
  - `Parasitized`: Red blood cells exhibiting intracellular *Plasmodium falciparum* chromatin rings or trophozoites.
  - `Uninfected`: Healthy biconcave erythrocytes without intracellular parasite inclusions.
- **Evaluation on Holdout Test Set (20% split)**:
  - **Accuracy**: $94.0\%$
  - **Precision**: $94.44\%$
  - **Recall**: $93.50\%$
  - **F1-Score**: $93.97\%$
  - **Inference Latency**: Under $300\text{ ms}$ per cell image on standard laptop CPU.

To retrain the model at any time:
```powershell
python train_model.py
```

---

## 8. Application Screening Workflow

```
1. Login to Staff Portal
   │
2. Dashboard Overview
   │
3. Register Patient (or choose existing patient)
   │
4. Upload Microscopy Blood Smear Image (.png / .jpg)
   │
5. (Optional) Check Observed Symptoms (Fever, Chills, Sweating, etc.)
   │
6. Image Pre-processing (128x128 RGB normalization)
   │
7. ML Model Feature Extraction & Classification
   │
8. View Prediction Result & Model Confidence Score
   │
9. Download Automated PDF Laboratory Report / Print
   │
10. View Updated Patient Chronological Test History
```

---

## 9. Limitations

1. **Cell Segmentation**: The model evaluates single-cell microscopy patches (thin smear microscopy standard). Field-of-view whole-slide images must be cropped to individual cells prior to inference.
2. **Microscopy Quality**: Results depend on proper Giemsa staining and microscope focus. Artifacts, debris, or staining defects may affect accuracy.
3. **Screening Purpose**: This system is designed as an educational decision-support screening tool, not an automated diagnostic authority.

---

## 10. Medical Disclaimer

> **IMPORTANT MEDICAL DISCLAIMER:**  
> This application is intended strictly for educational, academic demonstration, and screening decision-support purposes. AI-generated predictions and model confidence scores must not be considered a definitive medical diagnosis. All screening results must be confirmed by an appropriately qualified healthcare professional using standard laboratory protocols.
