# Docling Document Parser

![Component ID](https://img.shields.io/badge/Component%20ID-comp__ecc50-blue)
![Version](https://img.shields.io/badge/Version-v1.0.0-green)

A robust document parsing component powered by [Docling](https://github.com/DS4SD/docling). This component converts documents (like PDFs) into structured Markdown, with support for OCR, table extraction, and image handling.

## 🚀 Features

- **Document Conversion**: Converts PDFs and other formats to clean Markdown.
- **OCR Support**: Optical Character Recognition for scanned documents.
- **Table Structure**: Preserves table layouts in the output.
- **Image Extraction**: Extracts and handles images within documents.

## 🛠️ Installation

1. Ensure you have Python installed.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 📖 Usage

### Basic Conversion

```python
from docling.document_converter import DocumentConverter

source = "your_document.pdf"  # local path or URL
converter = DocumentConverter()
result = converter.convert(source)
markdown_output = result.document.export_to_markdown()

print(markdown_output)
```

### Advanced Configuration (OCR & Tables)

For more control over the conversion process (e.g., enabling OCR or adjusting image scale):

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Configure PDF pipeline options
pipeline_options = PdfPipelineOptions(
    do_ocr=True,                      # Enable OCR
    do_table_structure=True,          # Enable table detection
    generate_picture_images=True,     # Extract images
    images_scale=2.0                  # Set image resolution
)

# Create converter with options
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Convert
result = converter.convert("your_document.pdf")
```

## 📋 Metadata

- **Author**: Vijay Ram Enaganti
- **Tags**: `ocr`, `document-parsing`, `data-ingestion`, `markdown`
- **Component ID**: `comp_ecc50`
