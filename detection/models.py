from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Patient(models.Model):
    """
    Stores basic demographic and contact information of the patient.
    """
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    patient_id = models.CharField(max_length=20, unique=True, help_text="Unique Patient ID (e.g., PAT-1001)")
    name = models.CharField(max_length=120)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    contact = models.CharField(max_length=25, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient_id} - {self.name}"

    @classmethod
    def generate_next_patient_id(cls):
        """Generates the next sequential patient ID like PAT-1001, PAT-1002."""
        last_patient = cls.objects.all().order_by('-id').first()
        if not last_patient:
            return "PAT-1001"
        next_id_num = 1000 + last_patient.id + 1
        return f"PAT-{next_id_num}"


class MLModelInfo(models.Model):
    """
    Metadata about the Machine Learning / Deep Learning model used for inference.
    """
    name = models.CharField(max_length=120, default="Malaria Cell Classifier (CNN / Heuristic Engine)")
    version = models.CharField(max_length=20, default="1.0.0")
    model_type = models.CharField(max_length=100, default="Deep Learning / Image Screening")
    description = models.TextField(blank=True, default="Microscopy thin blood smear cell image classifier.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ML Model Information"
        verbose_name_plural = "ML Model Information"

    def __str__(self):
        return f"{self.name} (v{self.version})"


class TestRecord(models.Model):
    """
    Represents an individual malaria screening test conducted for a patient.
    """
    test_id = models.CharField(max_length=30, unique=True, help_text="Unique Test ID (e.g., TST-20261008-001)")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='tests')
    conducted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_tests')
    test_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, help_text="Clinical observations or remarks")

    class Meta:
        ordering = ['-test_date']

    def __str__(self):
        return f"{self.test_id} - {self.patient.name}"

    @classmethod
    def generate_next_test_id(cls):
        """Generates a date-based test ID: TST-YYYYMMDD-XXXX."""
        date_str = timezone.now().strftime("%Y%m%d")
        count_today = cls.objects.filter(test_id__startswith=f"TST-{date_str}").count() + 1
        return f"TST-{date_str}-{count_today:03d}"


class Symptom(models.Model):
    """
    Optional supporting clinical symptoms recorded during the screening test.
    Note: These do not alter the ML model prediction; they are clinical observations.
    """
    test = models.OneToOneField(TestRecord, on_delete=models.CASCADE, related_name='symptoms')
    fever = models.BooleanField(default=False)
    chills = models.BooleanField(default=False)
    headache = models.BooleanField(default=False)
    sweating = models.BooleanField(default=False)
    fatigue = models.BooleanField(default=False)
    other_symptoms = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Symptoms for Test {self.test.test_id}"

    @property
    def symptom_list(self):
        """Returns list of active symptoms for display."""
        active = []
        if self.fever: active.append("Fever")
        if self.chills: active.append("Chills")
        if self.headache: active.append("Headache")
        if self.sweating: active.append("Sweating")
        if self.fatigue: active.append("Fatigue")
        if self.other_symptoms: active.append(self.other_symptoms)
        return active


class BloodSmearImage(models.Model):
    """
    Stores the uploaded thin blood smear microscopy image for a test.
    """
    test = models.OneToOneField(TestRecord, on_delete=models.CASCADE, related_name='blood_smear')
    image = models.ImageField(upload_to='blood_smears/%Y/%m/')
    original_filename = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size_kb = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Blood Smear for {self.test.test_id}"


class Prediction(models.Model):
    """
    Stores the screening outcome and model confidence score.
    """
    RESULT_CHOICES = [
        ('Parasitized', 'Parasitized (Infected)'),
        ('Uninfected', 'Uninfected (Healthy)'),
    ]

    test = models.OneToOneField(TestRecord, on_delete=models.CASCADE, related_name='prediction')
    ml_model = models.ForeignKey(MLModelInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name='predictions')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    confidence_score = models.FloatField(help_text="Model confidence score as a percentage (e.g., 94.6%)")
    raw_score = models.FloatField(default=0.0, help_text="Raw model output probability value [0.0 - 1.0]")
    inference_time_ms = models.FloatField(default=0.0, help_text="Inference execution time in milliseconds")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.test.test_id}: {self.result} ({self.confidence_score:.1f}%)"


class Report(models.Model):
    """
    Automated laboratory report generated for a completed malaria test.
    """
    test = models.OneToOneField(TestRecord, on_delete=models.CASCADE, related_name='report')
    report_id = models.CharField(max_length=40, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    pdf_file = models.FileField(upload_to='reports/%Y/%m/', null=True, blank=True)
    disclaimer = models.TextField(
        default="This application is intended for educational and screening purposes. "
                "AI-generated results should not be considered a definitive medical diagnosis "
                "and should be confirmed by an appropriately qualified healthcare professional."
    )

    def __str__(self):
        return f"Report {self.report_id} ({self.test.test_id})"

    @classmethod
    def generate_next_report_id(cls, test_id):
        return f"REP-{test_id.replace('TST-', '')}"
