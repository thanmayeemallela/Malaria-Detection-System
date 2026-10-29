"""
End-to-End Integration Test for Malaria Detection System.
Tests all workflow steps: patient, test, image, prediction, report.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'malaria_detection.settings')
django.setup()

from django.contrib.auth.models import User
from detection.models import Patient, TestRecord, Symptom, BloodSmearImage, Prediction, MLModelInfo, Report
from detection.ml_model import classifier
from detection.utils import generate_pdf_report
from django.core.files.uploadedfile import SimpleUploadedFile


def run_test():
    print("=" * 55)
    print("  MALARIA DETECTION SYSTEM - E2E WORKFLOW TEST")
    print("=" * 55)

    # Step 1: Admin user
    admin = User.objects.get(username='admin')
    print("[OK] Admin user exists:", admin.username)

    # Step 2: Create patient
    p, created = Patient.objects.get_or_create(
        patient_id='PAT-1001',
        defaults={
            'name': 'Ravi Kumar', 'age': 34, 'gender': 'Male',
            'contact': '9876543210', 'address': 'Hyderabad, Telangana'
        }
    )
    print(f"[OK] Patient: {p.patient_id} - {p.name} (new={created})")

    # Step 3: Create test record
    test_id = TestRecord.generate_next_test_id()
    tr = TestRecord.objects.create(
        test_id=test_id, patient=p,
        conducted_by=admin, notes='Routine screening'
    )
    print(f"[OK] Test Record: {tr.test_id}")

    # Step 4: Upload blood smear image
    img_path = 'sample_images/real_nih_parasitized_1.png'
    with open(img_path, 'rb') as f:
        img_data = f.read()
    uploaded = SimpleUploadedFile('parasitized_sample.png', img_data, content_type='image/png')
    bs = BloodSmearImage.objects.create(
        test=tr, image=uploaded,
        original_filename='real_nih_parasitized_1.png',
        file_size_kb=round(len(img_data) / 1024, 2)
    )
    print(f"[OK] Blood Smear Image saved: {bs.image.name}")

    # Step 5: Record symptoms
    sym = Symptom.objects.create(
        test=tr, fever=True, chills=True,
        headache=False, sweating=True,
        fatigue=False, other_symptoms='Body ache'
    )
    print(f"[OK] Symptoms recorded: {sym.symptom_list}")

    # Step 6: Run ML prediction
    result = classifier.predict(bs.image.path)
    pred_label = result['prediction']
    conf = result['confidence_score']
    ms = result['inference_time_ms']
    print(f"[OK] Prediction: {pred_label} | Confidence: {conf}% | Time: {ms}ms")

    # Step 7: Save prediction
    ml_obj, _ = MLModelInfo.objects.get_or_create(
        name=result['model_name'],
        version=result['model_version'],
        defaults={
            'model_type': 'Random Forest',
            'description': result['details'],
            'is_active': True
        }
    )
    pred = Prediction.objects.create(
        test=tr, ml_model=ml_obj,
        result=pred_label,
        confidence_score=conf,
        raw_score=result['raw_score'],
        inference_time_ms=ms
    )
    print(f"[OK] Prediction saved in DB: {pred}")

    # Step 8: Generate PDF report
    report_id = Report.generate_next_report_id(tr.test_id)
    report = Report.objects.create(
        test=tr, report_id=report_id, generated_by=admin
    )
    pdf_content = generate_pdf_report(tr)
    report.pdf_file.save(f"report_{tr.test_id}.pdf", pdf_content)
    print(f"[OK] Report generated: {report.report_id} | PDF: {report.pdf_file.name}")

    # Step 9: Test with uninfected image
    test_id2 = TestRecord.generate_next_test_id()
    tr2 = TestRecord.objects.create(
        test_id=test_id2, patient=p,
        conducted_by=admin, notes='Follow-up screening'
    )
    img_path2 = 'sample_images/real_nih_uninfected_1.png'
    with open(img_path2, 'rb') as f:
        img_data2 = f.read()
    uploaded2 = SimpleUploadedFile('uninfected_sample.png', img_data2, content_type='image/png')
    bs2 = BloodSmearImage.objects.create(
        test=tr2, image=uploaded2,
        original_filename='real_nih_uninfected_1.png',
        file_size_kb=round(len(img_data2) / 1024, 2)
    )
    Symptom.objects.create(test=tr2, fever=False, chills=False)
    result2 = classifier.predict(bs2.image.path)
    Prediction.objects.create(
        test=tr2, ml_model=ml_obj,
        result=result2['prediction'],
        confidence_score=result2['confidence_score'],
        raw_score=result2['raw_score'],
        inference_time_ms=result2['inference_time_ms']
    )
    report2 = Report.objects.create(
        test=tr2,
        report_id=Report.generate_next_report_id(tr2.test_id),
        generated_by=admin
    )
    pdf2 = generate_pdf_report(tr2)
    report2.pdf_file.save(f"report_{tr2.test_id}.pdf", pdf2)
    print(f"[OK] 2nd Test: {tr2.test_id} -> {result2['prediction']} ({result2['confidence_score']}%)")

    # Step 10: Verify patient history
    tests = p.tests.select_related('prediction').all()
    print(f"\n[OK] Patient {p.patient_id} history: {tests.count()} test(s)")
    for t in tests:
        if hasattr(t, 'prediction'):
            print(f"     -> {t.test_id}: {t.prediction.result} ({t.prediction.confidence_score}%)")

    # Summary
    print("\n" + "=" * 55)
    print("  ALL END-TO-END TESTS PASSED SUCCESSFULLY!")
    print("=" * 55)
    print(f"  Patients:    {Patient.objects.count()}")
    print(f"  Tests:       {TestRecord.objects.count()}")
    print(f"  Predictions: {Prediction.objects.count()}")
    print(f"  Reports:     {Report.objects.count()}")
    print(f"  Images:      {BloodSmearImage.objects.count()}")
    print("=" * 55)


if __name__ == '__main__':
    run_test()
