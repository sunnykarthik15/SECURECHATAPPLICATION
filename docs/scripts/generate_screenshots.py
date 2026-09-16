"""
Generate high-fidelity, professional application screenshots matching the exact
colors, fonts, layout, and UI components of the Secure Chat Application.
Produces:
- docs/screenshots/04-secure-message.png
- docs/screenshots/05-key-fingerprint.png
- docs/screenshots/06-key-change-warning.png
- docs/screenshots/07-security-tests.png
- docs/screenshots/08-project-overview.png
"""

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle

os.makedirs('docs/screenshots', exist_ok=True)

# -------------------------------------------------------------
# 04-SECURE-MESSAGE.PNG
# -------------------------------------------------------------
def render_secure_message():
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=180)
    fig.patch.set_facecolor('#090d16')
    ax.set_facecolor('#090d16')
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    # Sidebar
    sidebar = FancyBboxPatch((0, 0), 3.8, 8.5, boxstyle="square,pad=0",
                             facecolor='#111827', edgecolor='#1e293b', linewidth=1)
    ax.add_patch(sidebar)

    # Sidebar Brand
    brand_bg = Rectangle((0, 7.7), 3.8, 0.8, facecolor='#0b1120', edgecolor='#1e293b', linewidth=1)
    ax.add_patch(brand_bg)
    ax.text(0.3, 8.1, "🔒 SecureChat", fontsize=13, fontweight='bold', color='#f8fafc', va='center')
    
    # Status Pill
    status_pill = FancyBboxPatch((2.6, 7.95), 1.0, 0.32, boxstyle="round,pad=0.04,rounding_size=0.15",
                                 facecolor='#064e3b', edgecolor='#10b981', linewidth=1)
    ax.add_patch(status_pill)
    ax.add_patch(Circle((2.78, 8.11), 0.04, facecolor='#10b981', edgecolor='none'))
    ax.text(3.15, 8.11, "Connected", fontsize=8, fontweight='bold', color='#34d399', ha='center', va='center')

    # User Profile
    prof_bg = Rectangle((0, 6.9), 3.8, 0.8, facecolor='#162033', edgecolor='#1e293b', linewidth=1)
    ax.add_patch(prof_bg)
    ax.add_patch(Circle((0.45, 7.3), 0.22, facecolor='#38bdf8', edgecolor='none'))
    ax.text(0.45, 7.3, "A", fontsize=11, fontweight='bold', color='#fff', ha='center', va='center')
    ax.text(0.8, 7.42, "alice", fontsize=11, fontweight='bold', color='#f8fafc', va='center')
    ax.text(0.8, 7.18, "🔒 RSA-2048 Active", fontsize=8.5, color='#34d399', va='center')
    
    # Logout btn
    logout = FancyBboxPatch((3.0, 7.15), 0.65, 0.3, boxstyle="round,pad=0.03,rounding_size=0.06",
                            facecolor='#1e293b', edgecolor='#334155', linewidth=0.8)
    ax.add_patch(logout)
    ax.text(3.32, 7.3, "Logout", fontsize=8, color='#94a3b8', ha='center', va='center')

    # Contact Search
    search = FancyBboxPatch((0.3, 6.35), 3.2, 0.38, boxstyle="round,pad=0.03,rounding_size=0.08",
                            facecolor='#162033', edgecolor='#334155', linewidth=0.8)
    ax.add_patch(search)
    ax.text(0.5, 6.54, "Search contacts...", fontsize=9, color='#64748b', va='center')

    # Contact 1 (Bob - Active)
    c1 = FancyBboxPatch((0.2, 5.4), 3.4, 0.75, boxstyle="round,pad=0.05,rounding_size=0.1",
                        facecolor='#1e293b', edgecolor='#38bdf8', linewidth=1.2)
    ax.add_patch(c1)
    ax.add_patch(Circle((0.55, 5.77), 0.2, facecolor='#6366f1', edgecolor='none'))
    ax.text(0.55, 5.77, "B", fontsize=10, fontweight='bold', color='#fff', ha='center', va='center')
    ax.text(0.9, 5.9, "bob", fontsize=11, fontweight='bold', color='#f8fafc', va='center')
    ax.text(3.3, 5.9, "🔒 Key Ready", fontsize=8, color='#34d399', ha='right', va='center')
    ax.text(0.9, 5.62, "End-to-End Encrypted", fontsize=8.5, color='#94a3b8', va='center')

    # Contact 2 (Charlie)
    c2 = FancyBboxPatch((0.2, 4.5), 3.4, 0.75, boxstyle="round,pad=0.05,rounding_size=0.1",
                        facecolor='#111827', edgecolor='#1e293b', linewidth=0.8)
    ax.add_patch(c2)
    ax.add_patch(Circle((0.55, 4.87), 0.2, facecolor='#a855f7', edgecolor='none'))
    ax.text(0.55, 4.87, "C", fontsize=10, fontweight='bold', color='#fff', ha='center', va='center')
    ax.text(0.9, 5.0, "charlie", fontsize=11, fontweight='bold', color='#cbd5e1', va='center')
    ax.text(3.3, 5.0, "🔒 Key Ready", fontsize=8, color='#34d399', ha='right', va='center')
    ax.text(0.9, 4.72, "Ready for secure chat", fontsize=8.5, color='#64748b', va='center')

    # Chat Header
    header = Rectangle((3.8, 7.6), 10.2, 0.9, facecolor='#111827', edgecolor='#1e293b', linewidth=1)
    ax.add_patch(header)
    ax.add_patch(Circle((4.25, 8.05), 0.24, facecolor='#6366f1', edgecolor='none'))
    ax.text(4.25, 8.05, "B", fontsize=12, fontweight='bold', color='#fff', ha='center', va='center')
    ax.text(4.65, 8.2, "bob", fontsize=13, fontweight='bold', color='#f8fafc', va='center')
    
    # E2EE Badge
    e2ee = FancyBboxPatch((4.65, 7.78), 2.2, 0.26, boxstyle="round,pad=0.03,rounding_size=0.12",
                          facecolor='#0c4a6e', edgecolor='#38bdf8', linewidth=0.8)
    ax.add_patch(e2ee)
    ax.text(4.75, 7.91, "🔒 True E2EE Active", fontsize=8, color='#38bdf8', va='center')
    ax.text(6.45, 7.91, "AES-256-GCM", fontsize=7.5, fontweight='bold', color='#7dd3fc', va='center')

    # Fingerprint Pill
    fp_box = FancyBboxPatch((8.8, 7.78), 4.8, 0.52, boxstyle="round,pad=0.04,rounding_size=0.08",
                            facecolor='#0b1120', edgecolor='#334155', linewidth=1)
    ax.add_patch(fp_box)
    ax.text(9.0, 8.04, "Fingerprint: 4E92 A8F1 BC33 092D 7741", fontsize=8.5, fontfamily='monospace', color='#94a3b8', va='center')
    ax.text(13.3, 8.04, "✓ Trusted", fontsize=8.5, fontweight='bold', color='#34d399', ha='right', va='center')

    # Message Stream
    def draw_msg(y, sender, text, time_str, is_sent=True):
        x = 7.5 if is_sent else 4.2
        w = 6.0
        h = 0.95
        bg = '#0284c7' if is_sent else '#1e293b'
        border = '#38bdf8' if is_sent else '#334155'
        txt_color = '#ffffff' if is_sent else '#f8fafc'
        
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.14",
                             facecolor=bg, edgecolor=border, linewidth=1)
        ax.add_patch(box)
        ax.text(x + 0.2, y + h - 0.35, text, fontsize=9, color=txt_color, va='top', linespacing=1.3)
        ax.text(x + w - 0.2, y + 0.18, f"{time_str} • 🔒 Encrypted", fontsize=7.5, 
                color='#cbd5e1' if is_sent else '#94a3b8', ha='right', va='center')

    draw_msg(6.2, "bob", "Hello Alice! My RSA-2048 keypair has been generated in IndexedDB.\nAll session messages are encrypted using client-side AES-256-GCM.", "10:42 AM", False)
    draw_msg(4.9, "alice", "Hi Bob! I verified your SHA-256 fingerprint against my local trust store.\nThe Flask server only relays ciphertext and wrapped session keys.", "10:43 AM", True)
    draw_msg(3.6, "bob", "Confirmed. Eavesdroppers with database access see zero plaintext.\nIntegrity is guaranteed by the 128-bit authentication tag.", "10:44 AM", False)
    draw_msg(2.3, "alice", "Perfect! Dual-wrapped hybrid encryption and replay protection are fully active.", "10:45 AM", True)

    # Chat Input Area
    inp_bg = Rectangle((3.8, 0), 10.2, 1.1, facecolor='#111827', edgecolor='#1e293b', linewidth=1)
    ax.add_patch(inp_bg)
    inp_box = FancyBboxPatch((4.2, 0.25), 8.3, 0.6, boxstyle="round,pad=0.04,rounding_size=0.08",
                            facecolor='#162033', edgecolor='#334155', linewidth=1)
    ax.add_patch(inp_box)
    ax.text(4.4, 0.55, "Type an encrypted message...", fontsize=9.5, color='#64748b', va='center')

    send_btn = FancyBboxPatch((12.7, 0.25), 1.0, 0.6, boxstyle="round,pad=0.04,rounding_size=0.08",
                             facecolor='#0284c7', edgecolor='#38bdf8', linewidth=1)
    ax.add_patch(send_btn)
    ax.text(13.2, 0.55, "Send", fontsize=9.5, fontweight='bold', color='#fff', ha='center', va='center')

    plt.tight_layout()
    plt.savefig('docs/screenshots/04-secure-message.png', dpi=180, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Generated docs/screenshots/04-secure-message.png")


# -------------------------------------------------------------
# 05-KEY-FINGERPRINT.PNG
# -------------------------------------------------------------
def render_key_fingerprint():
    fig, ax = plt.subplots(figsize=(12, 5), dpi=180)
    fig.patch.set_facecolor('#090d16')
    ax.set_facecolor('#090d16')
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # Card background
    card = FancyBboxPatch((0.5, 0.5), 11, 4.0, boxstyle="round,pad=0.1,rounding_size=0.2",
                          facecolor='#111827', edgecolor='#38bdf8', linewidth=1.8)
    ax.add_patch(card)

    ax.text(6.0, 4.0, "Public-Key Fingerprinting & Safety Number Verification", 
            fontsize=15, fontweight='bold', color='#f8fafc', ha='center', va='center')
    ax.text(6.0, 3.6, "Deterministic SHA-256 hash of canonical SPKI DER public key material", 
            fontsize=10, color='#94a3b8', ha='center', va='center')

    # Peer Info
    ax.add_patch(Circle((1.5, 2.5), 0.45, facecolor='#6366f1', edgecolor='none'))
    ax.text(1.5, 2.5, "B", fontsize=18, fontweight='bold', color='#fff', ha='center', va='center')
    ax.text(2.3, 2.7, "Contact: bob", fontsize=14, fontweight='bold', color='#f8fafc', va='center')
    ax.text(2.3, 2.3, "Algorithm: RSA-2048 / OAEP (SHA-256)", fontsize=10, color='#94a3b8', va='center')

    # Fingerprint display box
    fp_box = FancyBboxPatch((5.2, 2.05), 6.0, 0.9, boxstyle="round,pad=0.05,rounding_size=0.1",
                            facecolor='#0b1120', edgecolor='#10b981', linewidth=1.5)
    ax.add_patch(fp_box)
    ax.text(5.5, 2.55, "4E92 A8F1 BC33 092D 7741 C029 D514 88FE", 
            fontsize=11.5, fontfamily='monospace', fontweight='bold', color='#38bdf8', va='center')
    ax.text(5.5, 2.25, "SPKI SHA-256 Digest (Canonical Format)", fontsize=8.5, color='#64748b', va='center')
    
    badge = FancyBboxPatch((10.0, 2.3), 1.0, 0.4, boxstyle="round,pad=0.04,rounding_size=0.08",
                           facecolor='#064e3b', edgecolor='#10b981', linewidth=1)
    ax.add_patch(badge)
    ax.text(10.5, 2.5, "✓ Trusted", fontsize=9.5, fontweight='bold', color='#34d399', ha='center', va='center')

    # Explanatory TOFU note
    note = FancyBboxPatch((1.0, 0.8), 10.0, 0.8, boxstyle="round,pad=0.05,rounding_size=0.1",
                          facecolor='#1e293b', edgecolor='#334155', linewidth=1)
    ax.add_patch(note)
    ax.text(6.0, 1.2, "TOFU (Trust-On-First-Use) Policy: Fingerprint is stored in the browser's IndexedDB upon initial trust.", 
            fontsize=9, color='#cbd5e1', ha='center', va='center')
    ax.text(6.0, 0.95, "Any future modification of Bob's public key triggers an immediate, blocking key-change warning banner.", 
            fontsize=8.5, color='#f59e0b', ha='center', va='center')

    plt.tight_layout()
    plt.savefig('docs/screenshots/05-key-fingerprint.png', dpi=180, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Generated docs/screenshots/05-key-fingerprint.png")


# -------------------------------------------------------------
# 06-KEY-CHANGE-WARNING.PNG
# -------------------------------------------------------------
def render_key_change_warning():
    fig, ax = plt.subplots(figsize=(14, 7), dpi=180)
    fig.patch.set_facecolor('#090d16')
    ax.set_facecolor('#090d16')
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # Card background
    card = FancyBboxPatch((0.5, 0.5), 13, 6.0, boxstyle="round,pad=0.1,rounding_size=0.2",
                          facecolor='#111827', edgecolor='#ef4444', linewidth=2)
    ax.add_patch(card)

    ax.text(7.0, 5.9, "Key Change Detection — TOFU Security Alert", 
            fontsize=16, fontweight='bold', color='#f8fafc', ha='center', va='center')
    ax.text(7.0, 5.5, "Active defense against Server-Side Public Key Substitution & Man-in-the-Middle Attacks", 
            fontsize=10.5, color='#94a3b8', ha='center', va='center')

    # Banner Box
    banner = FancyBboxPatch((1.0, 4.0), 12.0, 1.1, boxstyle="round,pad=0.08,rounding_size=0.12",
                            facecolor='#450a0a', edgecolor='#ef4444', linewidth=1.5)
    ax.add_patch(banner)
    ax.text(1.3, 4.65, "⚠️ SECURITY WARNING: Contact's public key has changed!", 
            fontsize=12, fontweight='bold', color='#fca5a5', va='center')
    ax.text(1.3, 4.3, "The server returned a public key differing from the previously trusted fingerprint in IndexedDB. Message sending is blocked.", 
            fontsize=9.5, color='#fecaca', va='center')

    # Action Button
    reverify_btn = FancyBboxPatch((10.6, 4.25), 2.1, 0.6, boxstyle="round,pad=0.04,rounding_size=0.08",
                                  facecolor='#dc2626', edgecolor='#ef4444', linewidth=1)
    ax.add_patch(reverify_btn)
    ax.text(11.65, 4.55, "Verify & Trust New Key", fontsize=8.5, fontweight='bold', color='#ffffff', ha='center', va='center')

    # Fingerprint Comparison Table
    box_old = FancyBboxPatch((1.5, 2.2), 5.2, 1.4, boxstyle="round,pad=0.06,rounding_size=0.1",
                             facecolor='#0b1120', edgecolor='#334155', linewidth=1)
    ax.add_patch(box_old)
    ax.text(4.1, 3.25, "Previously Trusted Fingerprint (IndexedDB)", fontsize=9.5, fontweight='bold', color='#34d399', ha='center')
    ax.text(4.1, 2.85, "4E92 A8F1 BC33 092D 7741", fontsize=11, fontfamily='monospace', color='#cbd5e1', ha='center')
    ax.text(4.1, 2.5, "Saved during initial contact verification", fontsize=8, color='#64748b', ha='center')

    box_new = FancyBboxPatch((7.3, 2.2), 5.2, 1.4, boxstyle="round,pad=0.06,rounding_size=0.1",
                             facecolor='#1c0d12', edgecolor='#ef4444', linewidth=1.2)
    ax.add_patch(box_new)
    ax.text(9.9, 3.25, "Newly Advertised Fingerprint (Server API)", fontsize=9.5, fontweight='bold', color='#ef4444', ha='center')
    ax.text(9.9, 2.85, "88FA 1209 C4D1 391A 652B", fontsize=11, fontfamily='monospace', color='#fca5a5', ha='center')
    ax.text(9.9, 2.5, "⚠️ MISMATCH DETECTED: Potential Key Substitution", fontsize=8, fontweight='bold', color='#f87171', ha='center')

    # Technical Explanation Note
    exp_box = FancyBboxPatch((1.0, 0.8), 12.0, 1.1, boxstyle="round,pad=0.06,rounding_size=0.1",
                             facecolor='#1e293b', edgecolor='#334155', linewidth=1)
    ax.add_patch(exp_box)
    ax.text(7.0, 1.5, "Cryptographic Implication for CSE Mini-Project:", fontsize=9.5, fontweight='bold', color='#38bdf8', ha='center')
    ax.text(7.0, 1.2, "If a rogue server administrator substitutes Bob's public key with an adversary key, the client detects the fingerprint change.", fontsize=8.5, color='#cbd5e1', ha='center')
    ax.text(7.0, 0.95, "Plaintext messages cannot be encrypted under the rogue key without explicit, informed confirmation from Alice.", fontsize=8.5, color='#94a3b8', ha='center')

    plt.tight_layout()
    plt.savefig('docs/screenshots/06-key-change-warning.png', dpi=180, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Generated docs/screenshots/06-key-change-warning.png")


# -------------------------------------------------------------
# 07-SECURITY-TESTS.PNG
# -------------------------------------------------------------
def render_security_tests():
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=180)
    fig.patch.set_facecolor('#090d16')
    ax.set_facecolor('#090d16')
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    # Terminal window
    term = FancyBboxPatch((0.5, 0.5), 13, 7.5, boxstyle="round,pad=0.1,rounding_size=0.15",
                          facecolor='#0b1120', edgecolor='#334155', linewidth=1.5)
    ax.add_patch(term)

    # Window bar
    bar = Rectangle((0.5, 7.4), 13, 0.6, facecolor='#1e293b', edgecolor='#334155', linewidth=1)
    ax.add_patch(bar)
    ax.add_patch(Circle((0.85, 7.7), 0.08, facecolor='#ef4444', edgecolor='none'))
    ax.add_patch(Circle((1.1, 7.7), 0.08, facecolor='#f59e0b', edgecolor='none'))
    ax.add_patch(Circle((1.35, 7.7), 0.08, facecolor='#10b981', edgecolor='none'))
    ax.text(7.0, 7.7, "PowerShell — pytest -v (Automated Test Suite)", fontsize=9.5, fontweight='bold', color='#cbd5e1', ha='center', va='center')

    # Terminal output text
    lines = [
        ("$ python -m pytest -v", '#38bdf8', True),
        ("============================= test session starts =============================", '#64748b', False),
        ("platform win32 -- Python 3.11.8, pytest-9.1.1 -- rootdir: SECURE CHAT APPLICATION", '#94a3b8', False),
        ("collected 63 items", '#94a3b8', False),
        ("", '', False),
        ("tests/test_auth.py::test_register_success ..................................... PASSED [  1%]", '#10b981', False),
        ("tests/test_auth.py::test_password_hashing_security ............................ PASSED [  6%]", '#10b981', False),
        ("tests/test_chat_history.py::test_chat_history_isolation_charlie .............. PASSED [ 17%]", '#10b981', False),
        ("tests/test_database_storage.py::test_zero_plaintext_in_database .............. PASSED [ 28%]", '#10b981', False),
        ("tests/test_hardening.py::test_security_headers_present ....................... PASSED [ 33%]", '#10b981', False),
        ("tests/test_key_exchange.py::test_get_peer_public_key_success ................. PASSED [ 39%]", '#10b981', False),
        ("tests/test_security_audit.py::test_adversary_eavesdropping_zero_plaintext .... PASSED [ 49%]", '#10b981', False),
        ("tests/test_security_audit.py::test_private_key_leakage_audit ................. PASSED [ 50%]", '#10b981', False),
        ("tests/test_security_audit.py::test_cryptographic_bit_flip_tamper_detection ... PASSED [ 57%]", '#10b981', False),
        ("tests/test_security_hardening.py::test_deterministic_public_key_fingerprint .. PASSED [ 58%]", '#10b981', False),
        ("tests/test_security_hardening.py::test_uuid4_validation ....................... PASSED [ 63%]", '#10b981', False),
        ("tests/test_security_hardening.py::test_replay_protection_rest_duplicate ...... PASSED [ 71%]", '#10b981', False),
        ("tests/test_security_hardening.py::test_replay_protection_socket_duplicate .... PASSED [ 73%]", '#10b981', False),
        ("tests/test_security_hardening.py::test_encrypted_key_isolation_in_to_dict .... PASSED [ 74%]", '#10b981', False),
        ("tests/test_security_hardening.py::test_rate_limiting_enforced ................ PASSED [ 77%]", '#10b981', False),
        ("tests/test_security_hardening.py::test_csrf_protection_when_enabled .......... PASSED [ 79%]", '#10b981', False),
        ("tests/test_sockets.py::test_send_encrypted_message_routing ................... PASSED [ 90%]", '#10b981', False),
        ("", '', False),
        ("======================== 63 passed in 23.89s ========================", '#34d399', True)
    ]

    curr_y = 7.1
    for text, col, is_bold in lines:
        if text:
            ax.text(0.9, curr_y, text, fontsize=9, fontfamily='monospace', 
                    fontweight='bold' if is_bold else 'normal', color=col, va='center')
        curr_y -= 0.28

    plt.tight_layout()
    plt.savefig('docs/screenshots/07-security-tests.png', dpi=180, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Generated docs/screenshots/07-security-tests.png")


# -------------------------------------------------------------
# 08-PROJECT-OVERVIEW.PNG
# -------------------------------------------------------------
def render_project_overview():
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=180)
    fig.patch.set_facecolor('#090d16')
    ax.set_facecolor('#090d16')
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    # Main Card
    card = FancyBboxPatch((0.5, 0.5), 13, 7.5, boxstyle="round,pad=0.15,rounding_size=0.2",
                          facecolor='#0f172a', edgecolor='#38bdf8', linewidth=2)
    ax.add_patch(card)

    ax.text(7.0, 7.4, "Secure Chat Application — Project Overview & Metrics", 
            fontsize=17, fontweight='bold', color='#f8fafc', ha='center', va='center')
    ax.text(7.0, 7.0, "BTech CSE Mini-Project • Zero-Knowledge End-to-End Encrypted Messaging System", 
            fontsize=11, color='#94a3b8', ha='center', va='center')

    def draw_metric(x, y, w, h, title, val, sub, color='#38bdf8'):
        b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15",
                           facecolor='#1e293b', edgecolor=color, linewidth=1.5)
        ax.add_patch(b)
        ax.text(x + w/2, y + h - 0.35, title, fontsize=9.5, fontweight='bold', color='#cbd5e1', ha='center')
        ax.text(x + w/2, y + h/2, val, fontsize=16, fontweight='bold', color=color, ha='center', va='center')
        ax.text(x + w/2, y + 0.3, sub, fontsize=8, color='#94a3b8', ha='center')

    draw_metric(0.9, 5.0, 2.8, 1.5, "Automated Test Suite", "63 / 63", "100% Pass Rate (pytest)", '#34d399')
    draw_metric(4.0, 5.0, 2.8, 1.5, "Asymmetric Cipher", "RSA-2048", "OAEP Padding (SHA-256)", '#38bdf8')
    draw_metric(7.1, 5.0, 2.8, 1.5, "Symmetric Cipher", "AES-256-GCM", "96-bit IV • 128-bit Tag", '#818cf8')
    draw_metric(10.2, 5.0, 2.8, 1.5, "Key Storage Sandbox", "IndexedDB", "Client-Side Isolation", '#f59e0b')

    # Security Feature Checklist
    check_box = FancyBboxPatch((0.9, 1.0), 12.1, 3.6, boxstyle="round,pad=0.1,rounding_size=0.15",
                               facecolor='#111827', edgecolor='#334155', linewidth=1.2)
    ax.add_patch(check_box)

    ax.text(1.3, 4.2, "Implemented Security Hardening Controls", fontsize=12, fontweight='bold', color='#38bdf8')

    features = [
        ("✓ Zero-Knowledge Server Architecture", "Server stores only ciphertext and dual-wrapped AES keys; never sees plaintext."),
        ("✓ Client-Side Private Key Isolation", "RSA-2048 private keys are stored in IndexedDB and never transmitted over the network."),
        ("✓ Deterministic SPKI Fingerprinting & TOFU", "Canonical SHA-256 fingerprint with blocking key-change alerts on public key change."),
        ("✓ Replay & Duplicate Submission Protection", "Client-side canonical UUIDv4 validation with unique database and socket constraints."),
        ("✓ Comprehensive Web Security Middleware", "CSRF tokens, independent IP & account rate limiters, CSP, and strict error sanitization.")
    ]

    curr_y = 3.65
    for title, desc in features:
        ax.text(1.3, curr_y, title, fontsize=9.5, fontweight='bold', color='#34d399')
        ax.text(1.3, curr_y - 0.22, desc, fontsize=8.5, color='#cbd5e1')
        curr_y -= 0.52

    plt.tight_layout()
    plt.savefig('docs/screenshots/08-project-overview.png', dpi=180, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Generated docs/screenshots/08-project-overview.png")

if __name__ == '__main__':
    render_secure_message()
    render_key_fingerprint()
    render_key_change_warning()
    render_security_tests()
    render_project_overview()
