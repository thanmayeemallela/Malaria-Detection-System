from django.contrib import admin
from .models import Patient, TestRecord, Symptom, BloodSmearImage, Prediction, MLModelInfo, Report


class SymptomInline(admin.StackedInline):
    model = Symptom
    extra = 0


class BloodSmearImageInline(admin.StackedInline):
    model = BloodSmearImage
    extra = 0


class PredictionInline(admin.StackedInline):
    model = Prediction
    extra = 0
    readonly_fields = ('created_at',)


class ReportInline(admin.StackedInline):
    model = Report
    extra = 0
    readonly_fields = ('generated_at',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'name', 'age', 'gender', 'contact', 'created_at')
    search_fields = ('patient_id', 'name', 'contact')
    list_filter = ('gender', 'created_at')


@admin.register(TestRecord)
class TestRecordAdmin(admin.ModelAdmin):
    list_display = ('test_id', 'patient', 'get_result', 'get_confidence', 'conducted_by', 'test_date')
    search_fields = ('test_id', 'patient__name', 'patient__patient_id')
    list_filter = ('test_date', 'prediction__result')
    inlines = [BloodSmearImageInline, SymptomInline, PredictionInline, ReportInline]

    def get_result(self, obj):
        return obj.prediction.result if hasattr(obj, 'prediction') else '-'
    get_result.short_description = 'Result'

    def get_confidence(self, obj):
        return f"{obj.prediction.confidence_score:.1f}%" if hasattr(obj, 'prediction') else '-'
    get_confidence.short_description = 'Confidence'


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('test', 'result', 'confidence_score', 'raw_score', 'inference_time_ms', 'created_at')
    list_filter = ('result', 'created_at')
    search_fields = ('test__test_id', 'test__patient__name')


@admin.register(BloodSmearImage)
class BloodSmearImageAdmin(admin.ModelAdmin):
    list_display = ('test', 'original_filename', 'file_size_kb', 'uploaded_at')
    search_fields = ('test__test_id', 'original_filename')


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('test', 'fever', 'chills', 'headache', 'sweating', 'fatigue', 'other_symptoms')
    list_filter = ('fever', 'chills', 'headache')


@admin.register(MLModelInfo)
class MLModelInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'model_type', 'is_active', 'created_at')
    list_filter = ('is_active',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'test', 'generated_at', 'generated_by')
    search_fields = ('report_id', 'test__test_id')
