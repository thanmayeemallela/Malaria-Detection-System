"""
Django Forms for Malaria Detection System.
Includes:
- Patient registration and edit form
- Test creation form with blood smear image upload and symptoms
"""

from django import forms
from .models import Patient, TestRecord, Symptom, BloodSmearImage
from .utils import validate_image_file


class PatientForm(forms.ModelForm):
    """
    Form to register or update patient details.
    """
    class Meta:
        model = Patient
        fields = ['patient_id', 'name', 'age', 'gender', 'contact', 'address']
        widgets = {
            'patient_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank to auto-generate (e.g. PAT-1001)',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full patient name',
                'required': True,
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter age in years',
                'min': '0',
                'max': '130',
                'required': True,
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number or email',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Residential address / Location',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient_id'].required = False

    def clean_patient_id(self):
        pid = self.cleaned_data.get('patient_id')
        if not pid:
            # Auto-generate if not provided
            if not self.instance.pk:
                pid = Patient.generate_next_patient_id()
            else:
                pid = self.instance.patient_id
        return pid.strip().upper()


class TestCreateForm(forms.Form):
    """
    Form to upload a blood smear image, select a patient, and record symptoms.
    """
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select select-patient', 'required': True}),
        empty_label="-- Select Patient --",
        help_text="Choose the registered patient for this screening test."
    )

    image = forms.ImageField(
        validators=[validate_image_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png',
            'id': 'bloodSmearInput',
            'required': True,
        }),
        help_text="Upload thin blood smear microscopy cell image (.jpg, .jpeg, .png)"
    )

    # Optional clinical symptoms
    fever = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    chills = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    headache = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    sweating = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    fatigue = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    other_symptoms = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Nausea, body ache (optional)'
        })
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Additional clinical notes or microscopy preparation details (optional)'
        })
    )
