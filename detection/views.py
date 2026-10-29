"""
Views for Malaria Detection System.
Handles:
- Authentication (Login / Logout)
- Dashboard statistics
- Patient management (Create, List, Detail, Edit)
- Test creation & ML Model Inference Pipeline
- Prediction results
- Patient history
- Automated reports (HTML and PDF download)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.utils import timezone

from .models import Patient, TestRecord, Symptom, BloodSmearImage, Prediction, MLModelInfo, Report
from .forms import PatientForm, TestCreateForm
from .ml_model import classifier
from .utils import generate_pdf_report


def login_view(request):
    """Simple user login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'detection/login.html')


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Main dashboard displaying summary statistics and recent tests.
    """
    total_patients = Patient.objects.count()
    total_tests = TestRecord.objects.count()
    total_parasitized = Prediction.objects.filter(result='Parasitized').count()
    total_uninfected = Prediction.objects.filter(result='Uninfected').count()

    # Recent test records (up to 8)
    recent_tests = (
        TestRecord.objects.select_related('patient', 'prediction', 'blood_smear')
        .order_by('-test_date')[:8]
    )

    # Calculate infection detection rate
    detection_rate = round((total_parasitized / total_tests * 100), 1) if total_tests > 0 else 0.0

    context = {
        'total_patients': total_patients,
        'total_tests': total_tests,
        'total_parasitized': total_parasitized,
        'total_uninfected': total_uninfected,
        'detection_rate': detection_rate,
        'recent_tests': recent_tests,
    }
    return render(request, 'detection/dashboard.html', context)


@login_required
def patient_list_view(request):
    """
    Lists all registered patients with search functionality.
    """
    query = request.GET.get('q', '').strip()
    patients = Patient.objects.all()

    if query:
        patients = patients.filter(
            Q(patient_id__icontains=query) |
            Q(name__icontains=query) |
            Q(contact__icontains=query)
        )

    context = {
        'patients': patients,
        'query': query,
    }
    return render(request, 'detection/patient_list.html', context)


@login_required
def patient_create_view(request):
    """
    Registers a new patient.
    """
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f"Patient {patient.name} ({patient.patient_id}) registered successfully!")
            # Check if user wants to immediately conduct a test
            if 'save_and_test' in request.POST:
                return redirect(f"/test/new/?patient={patient.id}")
            return redirect('patient_detail', pk=patient.id)
    else:
        # Prepopulate with next suggested ID
        form = PatientForm(initial={'patient_id': Patient.generate_next_patient_id()})

    return render(request, 'detection/patient_form.html', {'form': form, 'title': 'Register New Patient'})


@login_required
def patient_edit_view(request, pk):
    """
    Edits existing patient details.
    """
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f"Patient {patient.name} updated successfully.")
            return redirect('patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)

    return render(request, 'detection/patient_form.html', {
        'form': form,
        'patient': patient,
        'title': f"Edit Patient ({patient.patient_id})",
    })


@login_required
def patient_detail_view(request, pk):
    """
    Displays patient demographics and their complete test history.
    """
    patient = get_object_or_404(Patient, pk=pk)
    tests = patient.tests.select_related('prediction', 'blood_smear').order_by('-test_date')

    context = {
        'patient': patient,
        'tests': tests,
    }
    return render(request, 'detection/patient_detail.html', context)


@login_required
def test_create_view(request):
    """
    Initiates a new malaria screening test:
    1. Selects patient
    2. Uploads blood smear image
    3. Records symptoms
    4. Runs ML inference
    5. Saves prediction & creates automated report
    6. Redirects to result page
    """
    initial_data = {}
    preselect_patient_id = request.GET.get('patient')
    if preselect_patient_id:
        try:
            initial_data['patient'] = Patient.objects.get(pk=preselect_patient_id)
        except Patient.DoesNotExist:
            pass

    if request.method == 'POST':
        form = TestCreateForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.cleaned_data['patient']
            image_file = form.cleaned_data['image']
            fever = form.cleaned_data['fever']
            chills = form.cleaned_data['chills']
            headache = form.cleaned_data['headache']
            sweating = form.cleaned_data['sweating']
            fatigue = form.cleaned_data['fatigue']
            other_symptoms = form.cleaned_data['other_symptoms']
            notes = form.cleaned_data['notes']

            try:
                # 1. Create TestRecord
                test_record = TestRecord.objects.create(
                    test_id=TestRecord.generate_next_test_id(),
                    patient=patient,
                    conducted_by=request.user,
                    notes=notes
                )

                # 2. Save BloodSmearImage
                blood_smear = BloodSmearImage.objects.create(
                    test=test_record,
                    image=image_file,
                    original_filename=image_file.name,
                    file_size_kb=round(image_file.size / 1024, 2)
                )

                # 3. Save Symptoms
                Symptom.objects.create(
                    test=test_record,
                    fever=fever,
                    chills=chills,
                    headache=headache,
                    sweating=sweating,
                    fatigue=fatigue,
                    other_symptoms=other_symptoms
                )

                # 4. Run ML Model Prediction
                image_disk_path = blood_smear.image.path
                inference_output = classifier.predict(image_disk_path)

                # 5. Get or create MLModelInfo record
                ml_model_obj, _ = MLModelInfo.objects.get_or_create(
                    name=inference_output['model_name'],
                    version=inference_output['model_version'],
                    defaults={
                        'model_type': 'Cell Screening Engine',
                        'description': inference_output['details'],
                        'is_active': True,
                    }
                )

                # 6. Save Prediction
                Prediction.objects.create(
                    test=test_record,
                    ml_model=ml_model_obj,
                    result=inference_output['prediction'],
                    confidence_score=inference_output['confidence_score'],
                    raw_score=inference_output['raw_score'],
                    inference_time_ms=inference_output['inference_time_ms']
                )

                # 7. Create Report Record
                report_obj = Report.objects.create(
                    test=test_record,
                    report_id=Report.generate_next_report_id(test_record.test_id),
                    generated_by=request.user
                )

                # Generate and attach PDF report file
                try:
                    pdf_file_content = generate_pdf_report(test_record)
                    report_obj.pdf_file.save(f"report_{test_record.test_id}.pdf", pdf_file_content)
                except Exception as pdf_err:
                    print(f"[PDF_WARNING] Could not save pre-generated PDF: {pdf_err}")

                messages.success(request, f"Screening analysis completed for Test ID: {test_record.test_id}")
                return redirect('test_result', test_id=test_record.test_id)

            except Exception as e:
                messages.error(request, f"Error processing screening test: {str(e)}")
    else:
        form = TestCreateForm(initial=initial_data)

    patients_exist = Patient.objects.exists()
    return render(request, 'detection/test_form.html', {
        'form': form,
        'patients_exist': patients_exist,
    })


@login_required
def test_result_view(request, test_id):
    """
    Displays the prediction result and details for a test.
    """
    test_record = get_object_or_404(
        TestRecord.objects.select_related('patient', 'prediction', 'blood_smear', 'symptoms', 'report'),
        test_id=test_id
    )

    context = {
        'test': test_record,
        'patient': test_record.patient,
        'prediction': getattr(test_record, 'prediction', None),
        'blood_smear': getattr(test_record, 'blood_smear', None),
        'symptoms': getattr(test_record, 'symptoms', None),
        'report': getattr(test_record, 'report', None),
    }
    return render(request, 'detection/result.html', context)


@login_required
def patient_history_view(request, pk):
    """
    Dedicated test history page for an individual patient.
    """
    patient = get_object_or_404(Patient, pk=pk)
    tests = patient.tests.select_related('prediction', 'blood_smear', 'report').order_by('-test_date')

    context = {
        'patient': patient,
        'tests': tests,
    }
    return render(request, 'detection/history.html', context)


@login_required
def all_history_view(request):
    """
    Global test history listing with filter/search options.
    """
    query = request.GET.get('q', '').strip()
    result_filter = request.GET.get('result', '').strip()

    tests = TestRecord.objects.select_related('patient', 'prediction', 'blood_smear').order_by('-test_date')

    if query:
        tests = tests.filter(
            Q(test_id__icontains=query) |
            Q(patient__name__icontains=query) |
            Q(patient__patient_id__icontains=query)
        )

    if result_filter:
        tests = tests.filter(prediction__result=result_filter)

    context = {
        'tests': tests,
        'query': query,
        'result_filter': result_filter,
    }
    return render(request, 'detection/all_history.html', context)


@login_required
def report_html_view(request, test_id):
    """
    Clean, printable HTML laboratory report (renders in browser and can be printed via Ctrl+P).
    """
    test_record = get_object_or_404(
        TestRecord.objects.select_related('patient', 'prediction', 'blood_smear', 'symptoms', 'report'),
        test_id=test_id
    )

    context = {
        'test': test_record,
        'patient': test_record.patient,
        'prediction': getattr(test_record, 'prediction', None),
        'blood_smear': getattr(test_record, 'blood_smear', None),
        'symptoms': getattr(test_record, 'symptoms', None),
        'report': getattr(test_record, 'report', None),
        'today': timezone.now(),
    }
    return render(request, 'detection/report.html', context)


@login_required
def report_pdf_download_view(request, test_id):
    """
    Generates and downloads a clean laboratory screening report as a PDF.
    """
    test_record = get_object_or_404(
        TestRecord.objects.select_related('patient', 'prediction', 'blood_smear', 'symptoms', 'report'),
        test_id=test_id
    )

    # If already generated PDF file exists, serve it; otherwise generate fresh
    if hasattr(test_record, 'report') and test_record.report.pdf_file:
        try:
            pdf_data = test_record.report.pdf_file.read()
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Malaria_Report_{test_record.test_id}.pdf"'
            return response
        except Exception:
            pass

    # Generate fresh via ReportLab
    try:
        content_file = generate_pdf_report(test_record)
        response = HttpResponse(content_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Malaria_Report_{test_record.test_id}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Unable to generate PDF report: {e}")
        return redirect('test_result', test_id=test_id)
