"""
Generate docs/Secure_Chat_Application_Project_Report.pdf using ReportLab
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf():
    pdf_path = 'docs/Secure_Chat_Application_Project_Report.pdf'
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=24
    )

    badge_style = ParagraphStyle(
        'DocBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0284c7'),
        alignment=1,
        spaceAfter=40
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0284c7'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=15,
        spaceAfter=4
    )

    caption_style = ParagraphStyle(
        'Caption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        spaceAfter=8
    )

    story = []

    # Title Page
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("SECURE CHAT APPLICATION", title_style))
    story.append(Paragraph("A Zero-Knowledge End-to-End Encrypted Web Messaging Platform<br/>Using Hybrid Cryptography and Client-Side Key Storage", subtitle_style))
    story.append(Paragraph("BTech Computer Science and Engineering — Mini Project Report", badge_style))
    story.append(Spacer(1, 1 * inch))

    meta_table_data = [
        [Paragraph("<b>Author / Student:</b>", body_style), Paragraph("Sunny Karthik (sunnykarthik15)", body_style)],
        [Paragraph("<b>Repository:</b>", body_style), Paragraph("https://github.com/sunnykarthik15/SECURECHATAPPLICATION", body_style)],
        [Paragraph("<b>Department:</b>", body_style), Paragraph("Computer Science and Engineering", body_style)],
        [Paragraph("<b>Cryptographic Engine:</b>", body_style), Paragraph("RSA-2048 / OAEP (SHA-256) + AES-256-GCM (96-bit IV)", body_style)]
    ]
    meta_table = Table(meta_table_data, colWidths=[2.2 * inch, 4.3 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # Abstract
    story.append(Paragraph("ABSTRACT", h1_style))
    story.append(Paragraph(
        "Instant messaging has become an essential medium of modern interpersonal and enterprise communication. "
        "However, prevailing web messaging architectures rely almost universally on Transport Layer Security (TLS), "
        "which terminates encryption at the application server. Consequently, the backend infrastructure, database "
        "storage, and server administrators possess uninhibited access to plaintext message data. This mini-project "
        "presents the design, implementation, and empirical verification of the Secure Chat Application—a zero-knowledge, "
        "end-to-end encrypted (E2EE) real-time communication system.", body_style
    ))
    story.append(Paragraph(
        "The system executes client-side hybrid cryptography combining the asymmetric RSA-2048 (RSA-OAEP with SHA-256) "
        "algorithm and the symmetric AES-256-GCM authenticated cipher with unique 96-bit initialization vectors. All "
        "cryptographic keypairs are generated directly inside the client's web browser via the W3C Web Crypto API, and "
        "private keys are persisted exclusively in the browser's sandboxed IndexedDB storage. The Flask application server "
        "acts strictly as an untrusted, zero-knowledge relay and encrypted persistent store. To defend against public-key "
        "substitution attacks without requiring complex Public Key Infrastructure (PKI), the application enforces a "
        "Trust-On-First-Use (TOFU) trust model coupled with deterministic SubjectPublicKeyInfo (SPKI) SHA-256 fingerprinting. "
        "Replay attacks are defeated via client-generated canonical UUIDv4 validation and database uniqueness constraints. "
        "The application is validated across 63 automated tests, confirming zero plaintext leakage and high-throughput real-time delivery.", body_style
    ))

    # Introduction
    story.append(Paragraph("1. INTRODUCTION & PROBLEM STATEMENT", h1_style))
    story.append(Paragraph(
        "Conventional web applications rely on Transport Layer Security (HTTPS) to encrypt packets across the public Internet. "
        "However, once the data reaches the application server, it is decrypted into plaintext in memory before being stored "
        "in relational databases. If the database is compromised, if an employee inspects logs, or if the server infrastructure "
        "is subjected to legal subpoena, private conversations are compromised.", body_style
    ))
    story.append(Paragraph(
        "Our problem was to build an authentic, zero-knowledge end-to-end encrypted messaging system that guarantees:", body_style
    ))
    story.append(Paragraph("• <b>Zero Plaintext Visibility:</b> Plaintext messages never touch the network or the server.", bullet_style))
    story.append(Paragraph("• <b>Client-Side Private Key Custody:</b> Private keys are held strictly in browser-isolated IndexedDB.", bullet_style))
    story.append(Paragraph("• <b>Key Substitution Defense:</b> Deterministic public-key fingerprinting prevents rogue server attacks.", bullet_style))
    story.append(Paragraph("• <b>Replay & Duplicate Protection:</b> Cryptographic UUIDv4 tokens ensure single-use delivery.", bullet_style))

    # Architecture
    story.append(Paragraph("2. SYSTEM ARCHITECTURE", h1_style))
    story.append(Paragraph(
        "The application is architected as a three-tier distributed system comprising the Client Browser Endpoints, "
        "the Application Relay Layer (Flask & Flask-SocketIO), and the Database Tier (SQLite with SQLAlchemy ORM).", body_style
    ))
    if os.path.exists('docs/diagrams/architecture.png'):
        story.append(RLImage('docs/diagrams/architecture.png', width=6.2 * inch, height=4.1 * inch))
        story.append(Paragraph("Figure 2.1: Secure Chat Application System Architecture", caption_style))

    # Encryption Methodology
    story.append(Paragraph("3. HYBRID ENCRYPTION & DATA FLOW", h1_style))
    story.append(Paragraph(
        "Hybrid encryption combines the computational efficiency of symmetric ciphers with the key distribution power "
        "of asymmetric public-key cryptography. For each message, the client browser generates a fresh 256-bit AES key "
        "and a random 96-bit IV. The plaintext is encrypted using AES-256-GCM. The AES key is then dual-wrapped via RSA-OAEP "
        "for both the recipient and the sender.", body_style
    ))
    if os.path.exists('docs/diagrams/encryption-data-flow.png'):
        story.append(RLImage('docs/diagrams/encryption-data-flow.png', width=6.2 * inch, height=4.5 * inch))
        story.append(Paragraph("Figure 3.1: Hybrid Encryption and Key-Wrapping Data Flow", caption_style))

    # Database ER
    story.append(Paragraph("4. DATABASE DESIGN & SCHEMA", h1_style))
    story.append(Paragraph(
        "The relational database schema is normalized into two core entities: `users` and `messages`. All message columns "
        "contain strictly ciphertext, IVs, and wrapped keys. Cascade deletion enforces privacy hygiene when accounts are removed.", body_style
    ))
    if os.path.exists('docs/diagrams/database-er.png'):
        story.append(RLImage('docs/diagrams/database-er.png', width=6.2 * inch, height=4.0 * inch))
        story.append(Paragraph("Figure 4.1: Relational Entity-Relationship Diagram", caption_style))

    # Public Key Fingerprint & TOFU
    story.append(Paragraph("5. PUBLIC-KEY TRUST & TOFU DEFENSE", h1_style))
    story.append(Paragraph(
        "Both backend and frontend derive a deterministic SHA-256 digest of the canonical SPKI DER public key format. "
        "Under the Trust-On-First-Use (TOFU) policy, the fingerprint is stored in IndexedDB. Any subsequent change to "
        "a contact's public key halts message transmission and displays a prominent warning banner.", body_style
    ))
    if os.path.exists('docs/screenshots/06-key-change-warning.png'):
        story.append(RLImage('docs/screenshots/06-key-change-warning.png', width=6.0 * inch, height=3.0 * inch))
        story.append(Paragraph("Figure 5.1: Blocking Key-Change Warning Banner", caption_style))

    # Results & Testing
    story.append(Paragraph("6. TESTING & EMPIRICAL RESULTS", h1_style))
    story.append(Paragraph(
        "The application was subjected to 63 automated tests spanning unit operations, socket message routing, "
        "cryptographic bit-flip tamper detection, and duplicate replay attack prevention. All 63 tests pass consistently.", body_style
    ))
    if os.path.exists('docs/screenshots/07-security-tests.png'):
        story.append(RLImage('docs/screenshots/07-security-tests.png', width=6.0 * inch, height=3.6 * inch))
        story.append(Paragraph("Figure 6.1: Automated Pytest Suite Execution (63 Passing Tests)", caption_style))

    # Limitations & Conclusion
    story.append(Paragraph("7. LIMITATIONS & CONCLUSION", h1_style))
    story.append(Paragraph(
        "Honest technical assessment acknowledges standard academic boundaries: (1) TOFU cannot detect key substitution "
        "on the initial contact without out-of-band verification; (2) long-term RSA key wrapping lacks forward secrecy; "
        "(3) in-memory rate limiting requires Redis for multi-worker clusters; and (4) communication metadata remains visible to the relay.", body_style
    ))
    story.append(Paragraph(
        "In conclusion, the Secure Chat Application successfully proves that standard web technologies (W3C Web Crypto API, "
        "IndexedDB, Flask, and Socket.IO) can deliver genuine zero-knowledge end-to-end encrypted messaging, establishing a "
        "complete, production-ready BTech CSE mini-project.", body_style
    ))

    doc.build(story)
    print(f"Generated {pdf_path} successfully ({os.path.getsize(pdf_path)} bytes)")

if __name__ == '__main__':
    generate_pdf()
