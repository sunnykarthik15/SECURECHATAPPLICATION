"""
Script to generate high-resolution, professional PNG diagrams for the Secure Chat Application:
1. docs/diagrams/architecture.png
2. docs/diagrams/encryption-data-flow.png
3. docs/diagrams/database-er.png
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

os.makedirs('docs/diagrams', exist_ok=True)

# -------------------------------------------------------------
# 1. ARCHITECTURE DIAGRAM
# -------------------------------------------------------------
def render_architecture():
    fig, ax = plt.subplots(figsize=(15, 10), dpi=200)
    fig.patch.set_facecolor('#090d16')
    ax.set_facecolor('#090d16')
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(7.5, 9.5, "Secure Chat Application — System Architecture", 
            ha='center', va='center', fontsize=18, fontweight='bold', color='#f8fafc', fontfamily='sans-serif')
    ax.text(7.5, 9.1, "BTech CSE Mini-Project • Zero-Knowledge End-to-End Encrypted Relay Architecture", 
            ha='center', va='center', fontsize=11, color='#94a3b8', fontfamily='sans-serif')

    def draw_box(x, y, w, h, title, subtitle, bg_color='#111827', border_color='#38bdf8', title_color='#38bdf8'):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.2",
                             facecolor=bg_color, edgecolor=border_color, linewidth=1.5, alpha=0.95)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.35, title, ha='center', va='top', 
                fontsize=11, fontweight='bold', color=title_color, fontfamily='sans-serif')
        ax.text(x + w/2, y + h/2 - 0.2, subtitle, ha='center', va='center', 
                fontsize=9, color='#cbd5e1', fontfamily='sans-serif', linespacing=1.4)

    # Client A (Sender)
    box_a = FancyBboxPatch((0.5, 3.8), 3.8, 4.6, boxstyle="round,pad=0.2,rounding_size=0.25",
                           facecolor='#0f172a', edgecolor='#38bdf8', linewidth=2)
    ax.add_patch(box_a)
    ax.text(2.4, 8.1, "CLIENT A (ALICE - SENDER)", ha='center', va='center', 
            fontsize=12, fontweight='bold', color='#38bdf8')
    
    draw_box(0.8, 6.7, 3.2, 1.0, "Frontend UI / DOM", "HTML5 / CSS / Vanilla JS\nEvent Listeners & Modals", '#1e293b', '#38bdf8')
    draw_box(0.8, 5.3, 3.2, 1.1, "Web Crypto API", "RSA-2048 / OAEP (SHA-256)\nAES-256-GCM / 96-bit IV", '#1e293b', '#38bdf8')
    draw_box(0.8, 4.1, 3.2, 0.9, "IndexedDB Sandbox", "• Alice RSA Private Key\n• Scoped TOFU Fingerprints", '#1e1b4b', '#818cf8', '#a5b4fc')

    # Server (Relay)
    box_s = FancyBboxPatch((5.6, 2.5), 3.8, 5.9, boxstyle="round,pad=0.2,rounding_size=0.25",
                           facecolor='#0f172a', edgecolor='#6366f1', linewidth=2)
    ax.add_patch(box_s)
    ax.text(7.5, 8.1, "FLASK RELAY SERVER (ZERO-KNOWLEDGE)", ha='center', va='center', 
            fontsize=12, fontweight='bold', color='#818cf8')
    
    draw_box(5.9, 6.7, 3.2, 1.0, "Security Controls", "CSRF • IP/Account Rate Limiter\nSecurity Headers • Error Sanitizer", '#1e293b', '#6366f1')
    draw_box(5.9, 5.3, 3.2, 1.1, "Authentication & Authz", "Session Cookies • Scrypt Hash\nUser Identity Verification", '#1e293b', '#6366f1')
    draw_box(5.9, 3.9, 3.2, 1.1, "Transport & Validation", "Flask-SocketIO Rooms • REST\nUUIDv4 & Replay Protection", '#1e293b', '#6366f1')
    draw_box(5.9, 2.7, 3.2, 0.9, "SQLAlchemy ORM", "Ciphertext / Key Persistence\nReferential Integrity", '#1e293b', '#6366f1')

    # Client B (Recipient)
    box_b = FancyBboxPatch((10.7, 3.8), 3.8, 4.6, boxstyle="round,pad=0.2,rounding_size=0.25",
                           facecolor='#0f172a', edgecolor='#38bdf8', linewidth=2)
    ax.add_patch(box_b)
    ax.text(12.6, 8.1, "CLIENT B (BOB - RECIPIENT)", ha='center', va='center', 
            fontsize=12, fontweight='bold', color='#38bdf8')
    
    draw_box(11.0, 6.7, 3.2, 1.0, "Frontend UI / DOM", "HTML5 / CSS / Vanilla JS\nDynamic Stream Decryption", '#1e293b', '#38bdf8')
    draw_box(11.0, 5.3, 3.2, 1.1, "Web Crypto API", "RSA-OAEP Key Unwrapping\nAES-256-GCM Decryption", '#1e293b', '#38bdf8')
    draw_box(11.0, 4.1, 3.2, 0.9, "IndexedDB Sandbox", "• Bob RSA Private Key\n• Scoped TOFU Fingerprints", '#1e1b4b', '#818cf8', '#a5b4fc')

    # Database
    box_d = FancyBboxPatch((5.6, 0.4), 3.8, 1.6, boxstyle="round,pad=0.15,rounding_size=0.2",
                           facecolor='#1e1b4b', edgecolor='#a855f7', linewidth=2)
    ax.add_patch(box_d)
    ax.text(7.5, 1.65, "SQLite Database (Encrypted Storage)", ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#c084fc')
    ax.text(7.5, 1.05, "users table (public_key only)\nmessages table (ciphertext, iv, wrapped keys)\nNO PLAINTEXT • NO PRIVATE KEYS", 
            ha='center', va='center', fontsize=9, color='#e2e8f0', linespacing=1.3)

    # Connecting Arrows
    def draw_arrow(start, end, label="", curve=0.0, color='#38bdf8'):
        arrow = FancyArrowPatch(start, end, connectionstyle=f"arc3,rad={curve}",
                                arrowstyle="-|>,head_length=6,head_width=4",
                                color=color, linewidth=1.8, linestyle='-')
        ax.add_patch(arrow)
        if label:
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2 + (0.25 if curve >= 0 else -0.25)
            ax.text(mid_x, mid_y, label, ha='center', va='center', fontsize=8.5,
                    fontweight='bold', color=color, bbox=dict(boxstyle="round,pad=0.2", fc="#090d16", ec=color, lw=0.8))

    draw_arrow((4.3, 7.2), (5.6, 7.2), "HTTPS REST / Auth", 0.05, '#38bdf8')
    draw_arrow((4.3, 5.8), (5.6, 4.6), "Socket.IO: Encrypted Envelope", 0.05, '#38bdf8')
    draw_arrow((9.4, 4.6), (10.7, 5.8), "Socket.IO: Envelope Push", 0.05, '#38bdf8')
    draw_arrow((10.7, 7.2), (9.4, 7.2), "HTTPS REST / Auth", -0.05, '#38bdf8')
    draw_arrow((7.5, 2.5), (7.5, 2.0), "SQLAlchemy", 0.0, '#a855f7')

    # Security Footnote
    ax.text(7.5, 0.15, "Security Guarantee: Private keys never leave IndexedDB. The server never observes plaintext messages.",
            ha='center', va='center', fontsize=10, fontweight='bold', color='#34d399',
            bbox=dict(boxstyle="round,pad=0.3", fc="#064e3b", ec="#10b981", lw=1.2))

    plt.tight_layout()
    plt.savefig('docs/diagrams/architecture.png', dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Generated docs/diagrams/architecture.png")


# -------------------------------------------------------------
# 2. ENCRYPTION DATA-FLOW DIAGRAM
# -------------------------------------------------------------
def render_encryption_flow():
    fig, ax = plt.subplots(figsize=(15, 11), dpi=200)
    fig.patch.set_facecolor('#090d16')
    ax.set_facecolor('#090d16')
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 11)
    ax.axis('off')

    # Title
    ax.text(7.5, 10.5, "Secure Chat Application — Hybrid Encryption Data Flow", 
            ha='center', va='center', fontsize=18, fontweight='bold', color='#f8fafc', fontfamily='sans-serif')
    ax.text(7.5, 10.1, "Step-by-Step Cryptographic Operation Pipeline (AES-256-GCM + Dual RSA-OAEP Key Wrapping)", 
            ha='center', va='center', fontsize=11, color='#94a3b8', fontfamily='sans-serif')

    def draw_step(x, y, w, h, step_num, title, details, color_theme='#38bdf8'):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.2",
                             facecolor='#111827', edgecolor=color_theme, linewidth=1.5)
        ax.add_patch(box)
        
        # Step badge
        badge = FancyBboxPatch((x - 0.2, y + h - 0.3), 0.5, 0.5, boxstyle="round,pad=0.05,rounding_size=0.1",
                               facecolor=color_theme, edgecolor='none')
        ax.add_patch(badge)
        ax.text(x + 0.05, y + h - 0.05, str(step_num), ha='center', va='center',
                fontsize=10, fontweight='bold', color='#090d16')
        
        ax.text(x + 0.45, y + h - 0.2, title, ha='left', va='center',
                fontsize=10.5, fontweight='bold', color=color_theme)
        ax.text(x + w/2, y + h/2 - 0.2, details, ha='center', va='center',
                fontsize=8.5, color='#cbd5e1', linespacing=1.3)

    # Column 1: SENDER CLIENT
    col1_bg = FancyBboxPatch((0.5, 1.2), 4.2, 8.5, boxstyle="round,pad=0.2,rounding_size=0.25",
                             facecolor='#0f172a', edgecolor='#38bdf8', linewidth=1.8)
    ax.add_patch(col1_bg)
    ax.text(2.6, 9.3, "SENDER CLIENT (ALICE BROWSER)", ha='center', va='center',
            fontsize=12, fontweight='bold', color='#38bdf8')

    draw_step(0.8, 7.7, 3.6, 1.2, 1, "Plaintext Input", "Sender writes message\ne.g., 'Hello Bob! Safe E2EE Chat.'\n(Never sent over network)", '#38bdf8')
    draw_step(0.8, 6.2, 3.6, 1.2, 2, "Ephemeral AES Key & IV", "Web Crypto generates fresh AES-256 key\nand random 96-bit IV (12 bytes)", '#38bdf8')
    draw_step(0.8, 4.7, 3.6, 1.2, 3, "AES-256-GCM Encryption", "Plaintext + AES key + 96-bit IV\nProduces: Ciphertext + 128-bit Auth Tag", '#38bdf8')
    draw_step(0.8, 3.2, 3.6, 1.2, 4, "Dual RSA-OAEP Wrapping", "Wrap AES key with Bob's Public Key\nWrap AES key with Alice's Public Key", '#38bdf8')
    draw_step(0.8, 1.7, 3.6, 1.2, 5, "Package Assembly", "Envelope: UUIDv4, v1, IV, Ciphertext,\nsender_encrypted_key, recipient_key", '#38bdf8')

    # Column 2: SERVER RELAY
    col2_bg = FancyBboxPatch((5.4, 1.2), 4.2, 8.5, boxstyle="round,pad=0.2,rounding_size=0.25",
                             facecolor='#0f172a', edgecolor='#6366f1', linewidth=1.8)
    ax.add_patch(col2_bg)
    ax.text(7.5, 9.3, "SERVER RELAY (ZERO-KNOWLEDGE)", ha='center', va='center',
            fontsize=12, fontweight='bold', color='#818cf8')

    draw_step(5.7, 6.8, 3.6, 1.5, 6, "Ingress & Validation", "• Authenticate Sender Session\n• Validate Canonical UUIDv4\n• Check for Replay / Duplicate ID\n• Verify Protocol Version 1", '#818cf8')
    draw_step(5.7, 4.5, 3.6, 1.5, 7, "Zero-Knowledge Storage", "Persists encrypted envelope to SQLite:\nCiphertext, IV, Wrapped AES Keys\nServer cannot decrypt payload", '#818cf8')
    draw_step(5.7, 2.2, 3.6, 1.5, 8, "Socket.IO Dispatch", "Pushes encrypted payload to Bob's room\nEnsures sender isolation\nEmits ack back to Alice", '#818cf8')

    # Column 3: RECIPIENT CLIENT
    col3_bg = FancyBboxPatch((10.3, 1.2), 4.2, 8.5, boxstyle="round,pad=0.2,rounding_size=0.25",
                             facecolor='#0f172a', edgecolor='#10b981', linewidth=1.8)
    ax.add_patch(col3_bg)
    ax.text(12.4, 9.3, "RECIPIENT CLIENT (BOB BROWSER)", ha='center', va='center',
            fontsize=12, fontweight='bold', color='#34d399')

    draw_step(10.6, 6.8, 3.6, 1.5, 9, "Envelope Receipt", "Receives encrypted package via Socket.IO\nExtracts IV, Ciphertext, and\nrecipient_encrypted_key", '#34d399')
    draw_step(10.6, 4.5, 3.6, 1.5, 10, "RSA-OAEP Unwrapping", "Bob's RSA Private Key (IndexedDB)\nunwraps recipient_encrypted_key\nRecovers ephemeral AES-256 Key", '#34d399')
    draw_step(10.6, 2.2, 3.6, 1.5, 11, "AES-GCM Decryption", "Decrypts Ciphertext with AES key + IV\nValidates 128-bit authentication tag\nRenders Plaintext in DOM", '#34d399')

    # Connecting Flow Arrows
    def draw_flow_arrow(start, end, label, color='#f59e0b'):
        arrow = FancyArrowPatch(start, end, arrowstyle="-|>,head_length=7,head_width=5",
                                color=color, linewidth=2)
        ax.add_patch(arrow)
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        ax.text(mid_x, mid_y + 0.2, label, ha='center', va='bottom', fontsize=8.5,
                fontweight='bold', color=color, bbox=dict(boxstyle="round,pad=0.2", fc="#090d16", ec=color, lw=0.8))

    draw_flow_arrow((4.4, 2.3), (5.7, 7.5), "Encrypted Envelope Transmit", '#38bdf8')
    draw_flow_arrow((9.3, 2.9), (10.6, 7.5), "Relay Envelope via Socket.IO", '#34d399')

    # Security Callout
    ax.text(7.5, 0.45, "Cryptographic Guarantee: Authenticated AES-256-GCM ensures confidentiality & integrity; RSA-OAEP ensures zero-knowledge key transport.",
            ha='center', va='center', fontsize=9.5, fontweight='bold', color='#38bdf8',
            bbox=dict(boxstyle="round,pad=0.3", fc="#0b1e33", ec="#0284c7", lw=1.2))

    plt.tight_layout()
    plt.savefig('docs/diagrams/encryption-data-flow.png', dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Generated docs/diagrams/encryption-data-flow.png")


# -------------------------------------------------------------
# 3. DATABASE ER DIAGRAM
# -------------------------------------------------------------
def render_database_er():
    fig, ax = plt.subplots(figsize=(14, 9), dpi=200)
    fig.patch.set_facecolor('#090d16')
    ax.set_facecolor('#090d16')
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Title
    ax.text(7.0, 8.5, "Secure Chat Application — Database Entity-Relationship Diagram", 
            ha='center', va='center', fontsize=17, fontweight='bold', color='#f8fafc', fontfamily='sans-serif')
    ax.text(7.0, 8.1, "Relational Schema, Constraints, Referential Cascades & Indexing Architecture", 
            ha='center', va='center', fontsize=11, color='#94a3b8', fontfamily='sans-serif')

    def draw_table_header(x, y, w, h, title, subtitle):
        hdr = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15",
                             facecolor='#1e293b', edgecolor='#38bdf8', linewidth=1.5)
        ax.add_patch(hdr)
        ax.text(x + w/2, y + h/2 + 0.1, title, ha='center', va='center',
                fontsize=13, fontweight='bold', color='#38bdf8')
        ax.text(x + w/2, y + h/2 - 0.25, subtitle, ha='center', va='center',
                fontsize=8.5, color='#94a3b8')

    def draw_table_body(x, y, w, h, fields):
        body = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15",
                              facecolor='#0f172a', edgecolor='#334155', linewidth=1.2)
        ax.add_patch(body)
        
        row_height = h / len(fields)
        for i, f in enumerate(fields):
            curr_y = y + h - (i + 0.5) * row_height
            
            # Badge
            badge_color = '#38bdf8' if 'PK' in f[0] else ('#f59e0b' if 'FK' in f[0] else '#64748b')
            ax.text(x + 0.3, curr_y, f[0], ha='left', va='center', fontsize=8, fontweight='bold', color=badge_color)
            ax.text(x + 1.2, curr_y, f[1], ha='left', va='center', fontsize=9.5, fontweight='bold', color='#f8fafc')
            ax.text(x + 3.2, curr_y, f[2], ha='left', va='center', fontsize=9, color='#38bdf8')
            ax.text(x + w - 0.3, curr_y, f[3], ha='right', va='center', fontsize=8, color='#94a3b8')

    # USERS Table
    draw_table_header(0.8, 6.7, 5.4, 0.9, "USERS", "User Accounts & Public Cryptographic Keys")
    user_fields = [
        ("PK", "id", "INTEGER", "autoincrement, primary_key"),
        ("UK", "username", "VARCHAR(64)", "unique, index=True, nullable=False"),
        (" ", "password_hash", "VARCHAR(256)", "scrypt / pbkdf2, nullable=False"),
        (" ", "public_key", "TEXT", "RSA-2048 SPKI DER Base64, nullable=False"),
        (" ", "created_at", "DATETIME", "UTC timestamp, nullable=False")
    ]
    draw_table_body(0.8, 3.4, 5.4, 3.2, user_fields)

    # MESSAGES Table
    draw_table_header(7.8, 6.7, 5.4, 0.9, "MESSAGES", "Encrypted Payloads & Wrapped AES Keys")
    msg_fields = [
        ("PK", "id", "INTEGER", "autoincrement, primary_key"),
        ("UK", "message_id", "VARCHAR(64)", "UUIDv4, unique=True, index=True"),
        (" ", "version", "INTEGER", "Protocol version, default=1"),
        ("FK", "sender_id", "INTEGER", "users.id (CASCADE), index=True"),
        ("FK", "recipient_id", "INTEGER", "users.id (CASCADE), index=True"),
        (" ", "ciphertext", "TEXT", "AES-256-GCM + 128-bit Tag Base64"),
        (" ", "iv", "VARCHAR(64)", "96-bit random IV Base64"),
        (" ", "sender_encrypted_key", "TEXT", "Wrapped AES Key (Sender RSA)"),
        (" ", "recipient_encrypted_key", "TEXT", "Wrapped AES Key (Recipient RSA)"),
        ("IDX", "created_at", "DATETIME", "UTC timestamp, index=True")
    ]
    draw_table_body(7.8, 1.2, 5.4, 5.4, msg_fields)

    # Relationship Lines
    arrow1 = FancyArrowPatch((6.2, 5.8), (7.8, 5.1), connectionstyle="arc3,rad=-0.15",
                             arrowstyle="-|>,head_length=6,head_width=4",
                             color='#38bdf8', linewidth=2)
    ax.add_patch(arrow1)
    ax.text(7.0, 5.8, "1 : N (sends via sender_id)", ha='center', va='center',
            fontsize=8.5, fontweight='bold', color='#38bdf8',
            bbox=dict(boxstyle="round,pad=0.2", fc="#090d16", ec="#38bdf8", lw=0.8))

    arrow2 = FancyArrowPatch((6.2, 4.4), (7.8, 4.5), connectionstyle="arc3,rad=0.15",
                             arrowstyle="-|>,head_length=6,head_width=4",
                             color='#10b981', linewidth=2)
    ax.add_patch(arrow2)
    ax.text(7.0, 4.1, "1 : N (receives via recipient_id)", ha='center', va='center',
            fontsize=8.5, fontweight='bold', color='#10b981',
            bbox=dict(boxstyle="round,pad=0.2", fc="#090d16", ec="#10b981", lw=0.8))

    # Composite Index Note
    note_box = FancyBboxPatch((0.8, 1.2), 5.4, 1.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                              facecolor='#1e1b4b', edgecolor='#6366f1', linewidth=1.2)
    ax.add_patch(note_box)
    ax.text(3.5, 2.7, "Composite Dialogue Indexes & Referential Integrity", ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='#a5b4fc')
    ax.text(3.5, 1.9, "• ix_messages_dialogue_sender (sender_id, recipient_id, created_at)\n• ix_messages_dialogue_recipient (recipient_id, sender_id, created_at)\n• ON DELETE CASCADE enforces relational hygiene on user deletion\n• Zero plaintext and zero private keys stored in SQLite",
            ha='center', va='center', fontsize=8, color='#cbd5e1', linespacing=1.3)

    plt.tight_layout()
    plt.savefig('docs/diagrams/database-er.png', dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Generated docs/diagrams/database-er.png")

if __name__ == '__main__':
    render_architecture()
    render_encryption_flow()
    render_database_er()
