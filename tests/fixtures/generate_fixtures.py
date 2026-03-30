"""
DocuSense - Test Fixture Generator

Script to generate sample test documents for QA testing.
Run this script to create PDF and image fixtures.
"""
import os
from pathlib import Path


def create_sample_invoice_pdf(output_path: Path) -> None:
    """Create a sample invoice PDF."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open()
        page = doc.new_page()

        # Invoice content
        content = """
        INVOICE
        ========================================
        
        Invoice Number: INV-2024-001234
        Invoice Date: January 15, 2024
        Due Date: February 15, 2024
        
        From:
        TechCorp Solutions Inc.
        123 Business Avenue
        San Francisco, CA 94102
        
        Bill To:
        Acme Corporation
        456 Enterprise Street
        New York, NY 10001
        
        ----------------------------------------
        ITEMS
        ----------------------------------------
        
        1. Software Development Services
           Quantity: 40 hours
           Rate: $150.00/hour
           Amount: $6,000.00
        
        2. Cloud Infrastructure Setup
           Quantity: 1
           Rate: $2,500.00
           Amount: $2,500.00
        
        3. Technical Consultation
           Quantity: 8 hours
           Rate: $200.00/hour
           Amount: $1,600.00
        
        ----------------------------------------
        
        Subtotal: $10,100.00
        Tax (8.5%): $858.50
        
        TOTAL AMOUNT DUE: $10,958.50
        
        ----------------------------------------
        
        Payment Terms: Net 30
        Payment Method: Bank Transfer or Check
        
        Thank you for your business!
        """

        # Insert text
        text_rect = fitz.Rect(50, 50, 550, 800)
        page.insert_textbox(text_rect, content, fontsize=11, fontname="helv")

        doc.save(str(output_path))
        doc.close()
        print(f"Created: {output_path}")

    except ImportError:
        print("PyMuPDF not installed. Creating text version instead.")
        output_path = output_path.with_suffix(".txt")
        with open(output_path, "w") as f:
            f.write(content)
        print(f"Created: {output_path}")


def create_sample_contract_pdf(output_path: Path) -> None:
    """Create a sample contract PDF."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open()
        page = doc.new_page()

        content = """
        SERVICE AGREEMENT CONTRACT
        ========================================
        
        Contract Number: SA-2024-00567
        Effective Date: March 1, 2024
        Expiration Date: February 28, 2025
        
        PARTIES
        ----------------------------------------
        
        This Service Agreement ("Agreement") is entered into by and between:
        
        Provider: DataTech Solutions LLC
        Address: 789 Innovation Drive, Austin, TX 78701
        
        AND
        
        Client: Global Enterprises Inc.
        Address: 321 Corporate Plaza, Chicago, IL 60601
        
        TERMS AND CONDITIONS
        ----------------------------------------
        
        1. SCOPE OF SERVICES
        The Provider agrees to deliver data analytics and consulting
        services as outlined in Exhibit A attached hereto.
        
        2. PAYMENT TERMS
        - Monthly retainer fee: $15,000.00
        - Payment due within 15 days of invoice date
        - Late payment penalty: 1.5% per month
        
        3. TERM AND TERMINATION
        - Initial term: 12 months
        - Auto-renewal for successive 12-month periods
        - Either party may terminate with 60 days written notice
        
        4. CONFIDENTIALITY
        Both parties agree to maintain strict confidentiality of all
        proprietary information exchanged during this engagement.
        
        5. LIABILITY
        Maximum liability shall not exceed the total fees paid under
        this Agreement in the preceding 12 months.
        
        SIGNATURES
        ----------------------------------------
        
        Provider Representative: John Smith, CEO
        Date: February 15, 2024
        
        Client Representative: Jane Doe, VP Operations
        Date: February 20, 2024
        """

        text_rect = fitz.Rect(50, 50, 550, 800)
        page.insert_textbox(text_rect, content, fontsize=10, fontname="helv")

        doc.save(str(output_path))
        doc.close()
        print(f"Created: {output_path}")

    except ImportError:
        print("PyMuPDF not installed. Creating text version instead.")
        output_path = output_path.with_suffix(".txt")
        with open(output_path, "w") as f:
            f.write(content)
        print(f"Created: {output_path}")


def create_sample_receipt_image(output_path: Path) -> None:
    """Create a sample receipt image."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create image
        width, height = 400, 600
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        # Try to use a basic font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", 14)
            font_large = ImageFont.truetype("arial.ttf", 18)
        except OSError:
            font = ImageFont.load_default()
            font_large = font

        # Receipt content
        lines = [
            ("QUICK MART", font_large, 150),
            ("123 Main Street", font, 180),
            ("Springfield, IL 62701", font, 200),
            ("Tel: (555) 123-4567", font, 220),
            ("", font, 240),
            ("=" * 35, font, 250),
            ("RECEIPT", font_large, 270),
            ("=" * 35, font, 290),
            ("", font, 300),
            ("Date: 2024-01-20  Time: 14:32", font, 310),
            ("Transaction #: TXN-789456", font, 330),
            ("", font, 350),
            ("-" * 35, font, 360),
            ("Organic Milk 1gal    $4.99", font, 380),
            ("Whole Wheat Bread    $3.49", font, 400),
            ("Fresh Eggs (12)      $5.99", font, 420),
            ("Orange Juice 64oz    $6.49", font, 440),
            ("Bananas (bunch)      $2.29", font, 460),
            ("-" * 35, font, 480),
            ("", font, 490),
            ("Subtotal:           $23.25", font, 500),
            ("Tax (6.25%):         $1.45", font, 520),
            ("", font, 530),
            ("TOTAL:              $24.70", font_large, 550),
            ("", font, 570),
            ("Paid: VISA ****1234", font, 580),
            ("", font, 590),
            ("Thank you for shopping!", font, 600),
        ]

        for text, f, y in lines:
            if y < height - 20:
                draw.text((20, y - 150), text, fill="black", font=f)

        img.save(str(output_path))
        print(f"Created: {output_path}")

    except ImportError:
        print("Pillow not installed. Skipping image creation.")


def create_sample_text_document(output_path: Path) -> None:
    """Create a sample text document."""
    content = """
DocuSense Test Document
=======================

This is a sample text document for testing the DocuSense QA system.

Company Information
-------------------
Company Name: Innovative Tech Corp
Founded: 2015
Headquarters: Seattle, Washington
CEO: Michael Johnson
Number of Employees: 450

Product Overview
----------------
Our flagship product, DataSync Pro, is an enterprise data synchronization
platform that enables real-time data replication across multiple cloud
providers. Key features include:

- Real-time synchronization with sub-second latency
- Support for AWS, Azure, and Google Cloud
- End-to-end encryption using AES-256
- Automatic conflict resolution
- 99.99% uptime SLA

Pricing Information
-------------------
- Starter Plan: $99/month (up to 100GB)
- Professional Plan: $299/month (up to 1TB)
- Enterprise Plan: $999/month (unlimited)
- Custom pricing available for large deployments

Contact Information
-------------------
Sales: sales@innovativetech.example.com
Support: support@innovativetech.example.com
Phone: 1-800-555-0123

This document contains information that can be used to test question-answering
capabilities. Questions like "What is the company name?", "Who is the CEO?",
"What is the price of the Professional Plan?" should be answerable from this
document.
"""
    with open(output_path, "w") as f:
        f.write(content)
    print(f"Created: {output_path}")


def main():
    """Generate all test fixtures."""
    fixtures_dir = Path(__file__).parent

    print("Generating test fixtures...")
    print("-" * 40)

    # Create sample documents
    create_sample_invoice_pdf(fixtures_dir / "sample_invoice.pdf")
    create_sample_contract_pdf(fixtures_dir / "sample_contract.pdf")
    create_sample_receipt_image(fixtures_dir / "scanned_receipt.png")
    create_sample_text_document(fixtures_dir / "sample_document.txt")

    print("-" * 40)
    print("Done!")


if __name__ == "__main__":
    main()
