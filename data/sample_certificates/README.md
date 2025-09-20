# Sample Certificate Images

This directory contains sample certificate images for testing the verification system.

## Structure

- `valid/` - Valid certificates for positive testing
- `invalid/` - Invalid or tampered certificates for negative testing
- `edge_cases/` - Edge cases like poor quality, rotated, or partially obscured certificates

## Usage

These images are used for:
- Training and fine-tuning the Donut model
- Testing the extraction pipeline
- Validation of the fusion engine
- Performance benchmarking

## Guidelines

- Images should be high quality (minimum 300 DPI)
- Various formats supported: JPEG, PNG, PDF
- Include diverse certificate layouts and institutions
- Anonymize personal data or use synthetic certificates
- Maximum file size: 10MB per image

## Labeling Format

For training data, use JSON format:
```json
{
  "image_path": "valid/university_cert_001.jpg",
  "extracted_fields": {
    "name": "John Doe",
    "institution": "University of Technology",
    "course_name": "Computer Science",
    "issue_date": "2023-06-15",
    "certificate_id": "CS2023-001234",
    "grade": "First Class Honours"
  }
}
```
