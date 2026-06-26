"""
mail_bulk.py — Gmail bulk email sender (Streamlit).

Two modes via tabs:
  ✏️ Manual Input — define custom columns inline, paste data rows, type template
  📁 CSV Upload   — upload a CSV + TXT template (personalised per-row)

Manual Input supports multiple columns:
  Column names: email, name, city
  Data rows:    alice@example.com, Alice, Hyderabad
  Template:     Hello {name} from {city}! Your email is {email}.
  → first column is always the email column
"""

import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd


# ── shared helpers ─────────────────────────────────────────────────────────────

def _parse_columns(col_string: str) -> list[str]:
    return [c.strip().lower() for c in col_string.split(",") if c.strip()]


def _parse_manual_contacts(raw: str, columns: list[str]) -> list[dict]:
    """Parse comma-separated rows into list of dicts."""
    contacts = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        while len(parts) < len(columns):
            parts.append("")
        contact = {col: parts[i] for i, col in enumerate(columns)}
        contacts.append(contact)
    return contacts


def _personalise(template: str, row: dict) -> str:
    msg = template
    for key, val in row.items():
        msg = msg.replace(f"{{{key}}}", str(val))
    return msg


def _validate_emails(contacts: list[dict], email_col: str) -> tuple[list[dict], list[str]]:
    valid, warnings = [], []
    seen = set()
    for i, c in enumerate(contacts):
        email = c.get(email_col, "").strip()
        if not email:
            warnings.append(f"Row {i+1}: empty email — skipped")
            continue
        if "@" not in email or "." not in email:
            warnings.append(f"Row {i+1}: `{email}` looks invalid — skipped")
            continue
        if email in seen:
            warnings.append(f"Row {i+1}: duplicate `{email}` — skipped")
            continue
        seen.add(email)
        valid.append(c)
    return valid, warnings


def _smtp_connect(sender_email: str, sender_password: str):
    """Connect and login to Gmail SMTP. Returns server object."""
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(sender_email, sender_password)
    return server


def _run_bulk_email(server, sender_email: str, contacts: list[dict],
                    email_col: str, subject_template: str, body_template: str):
    """Core send loop: personalise → send → progress bar."""
    total    = len(contacts)
    errors   = 0
    progress = st.progress(0)
    status   = st.empty()

    for idx, contact in enumerate(contacts):
        recipient = contact[email_col]
        subject   = _personalise(subject_template, contact)
        body      = _personalise(body_template, contact)
        status.text(f"📤 [{idx+1}/{total}] Sending to {recipient}…")

        try:
            msg            = MIMEMultipart()
            msg["From"]    = sender_email
            msg["To"]      = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            server.sendmail(sender_email, recipient, msg.as_string())
            st.success(f"✅ {recipient}")
        except Exception as e:
            st.error(f"❌ {recipient} — {e}")
            errors += 1

        progress.progress((idx + 1) / total)

    status.text("✅ Done!")
    st.success(f"**Summary:** {total} attempted · {total - errors} sent · {errors} failed")


def _credentials_widget(key_prefix: str) -> tuple[str, str]:
    """Render Gmail credential inputs; return (email, password)."""
    st.subheader("🔐 Gmail Credentials")
    st.info(
        "Use a **Gmail App Password**, not your account password.  \n"
        "Generate at: Google Account → Security → 2-Step Verification → App passwords"
    )
    email    = st.text_input("Your Gmail address", placeholder="you@gmail.com", key=f"{key_prefix}_email")
    password = st.text_input("Gmail App Password", type="password",
                             placeholder="xxxx xxxx xxxx xxxx", key=f"{key_prefix}_pwd")
    return email, password


# ── main page ──────────────────────────────────────────────────────────────────

def send_gmail_bulk_message():
    st.title("📧 Gmail Bulk Message Sender")

    tab_manual, tab_csv = st.tabs(["✏️ Manual Input", "📁 CSV Upload"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — MANUAL INPUT  (multi-column)
    # ══════════════════════════════════════════════════════════════════════════
    with tab_manual:
        sender_email, sender_password = _credentials_widget("manual")

        st.markdown("---")
        st.subheader("✏️ Type / Paste Contact Data & Message")

        st.markdown("**Step 1 — Define your columns** (first column = email address):")
        col_input = st.text_input(
            "Column names (comma-separated)",
            value="email, name",
            placeholder="email, name, city, plan",
            key="manual_cols",
            help="First column must be the email column. Use these names as {placeholder} in template.",
        )
        columns   = _parse_columns(col_input)
        email_col = columns[0] if columns else "email"

        if len(columns) > 1:
            st.info(
                f"📌 **Email column:** `{email_col}` · "
                f"**Extra columns:** {', '.join(f'`{c}`' for c in columns[1:])}  \n"
                f"Placeholders: {', '.join(f'`{{{c}}}`' for c in columns)}"
            )
        else:
            st.info(f"📌 **Email column:** `{email_col}` · Use `{{{email_col}}}` in your template.")

        st.markdown(f"**Step 2 — Paste contact data** (one per line, comma-separated):  \nFormat: `{', '.join(f'<{c}>' for c in columns)}`")
        data_raw = st.text_area(
            "Contact Data",
            placeholder="\n".join([
                f"alice@example.com{', value' * (len(columns)-1)}",
                f"bob@example.com{', value' * (len(columns)-1)}",
            ]),
            height=200,
            key="manual_data",
        )

        st.markdown("**Step 3 — Subject line:**")
        placeholder_hint = ", ".join(f"`{{{c}}}`" for c in columns)
        st.caption(f"Supports placeholders: {placeholder_hint}")
        subject_template = st.text_input(
            "Subject",
            placeholder=f"Hello {{{columns[1] if len(columns) > 1 else email_col}}}!",
            key="manual_subject",
        )

        st.markdown("**Step 4 — Write your message template:**")
        st.caption(f"Supports placeholders: {placeholder_hint}")
        body_template = st.text_area(
            "Message Template",
            placeholder=f"Hi {{{columns[1] if len(columns) > 1 else email_col}}},\n\nThis message was personalised just for {{{email_col}}}.\n\nBest regards",
            height=200,
            key="manual_body",
        )

        # ── Live preview ──────────────────────────────────────────────────────
        if data_raw.strip() and body_template.strip() and columns:
            contacts = _parse_manual_contacts(data_raw, columns)
            valid, warnings = _validate_emails(contacts, email_col)

            for w in warnings:
                st.warning(w)

            skipped = len(contacts) - len(valid)
            if len(contacts) > 500:
                st.error("❌ More than 500 contacts — Gmail daily limit is ~500 emails.")
                return

            st.info(
                f"📊 **{len(valid)}** valid recipient(s)"
                + (f" · {skipped} skipped" if skipped else "")
            )

            if valid:
                st.subheader("👁️ Preview — first contact")
                preview_subj = _personalise(subject_template or "(no subject)", valid[0])
                preview_body = _personalise(body_template, valid[0])
                st.markdown(f"**Subject:** {preview_subj}")
                st.code(preview_body, language=None)
                with st.expander("🔍 Column values for first contact"):
                    for col, val in valid[0].items():
                        st.write(f"**{col}** → `{val}`")

        st.markdown("---")

        if st.button("📤 Send to All", type="primary", key="manual_send_btn"):
            missing = []
            if not sender_email:  missing.append("Gmail address")
            if not sender_password: missing.append("App Password")
            if not data_raw.strip(): missing.append("contact data")
            if not body_template.strip(): missing.append("message template")
            if missing:
                st.error(f"❌ Please fill in: {', '.join(missing)}")
                return

            contacts = _parse_manual_contacts(data_raw, columns)
            valid, warnings = _validate_emails(contacts, email_col)
            for w in warnings:
                st.warning(w)
            if not valid:
                st.error("❌ No valid email addresses found.")
                return
            if len(valid) > 500:
                st.error("❌ More than 500 contacts — reduce to stay within Gmail limit.")
                return

            server = None
            try:
                server = _smtp_connect(sender_email, sender_password)
                st.success("🔗 Connected to Gmail SMTP — sending…")
                _run_bulk_email(server, sender_email, valid, email_col,
                                subject_template, body_template)
            except smtplib.SMTPAuthenticationError:
                st.error("❌ Authentication failed — use a Gmail **App Password**, not your regular password.")
            except Exception as e:
                st.error(f"❌ SMTP error: {e}")
            finally:
                if server:
                    try: server.quit()
                    except Exception: pass

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — CSV UPLOAD
    # ══════════════════════════════════════════════════════════════════════════
    with tab_csv:
        sender_email_csv, sender_password_csv = _credentials_widget("csv")

        st.markdown("---")
        st.subheader("📁 CSV + Template File Upload")

        with st.expander("ℹ️ How to prepare files", expanded=False):
            st.markdown("""
            **CSV File** — must have an `email` column:
            ```
            email,name,plan
            alice@example.com,Alice,Pro
            bob@example.com,Bob,Free
            ```
            **Template File (.txt)** — use `{column_name}` as placeholders:
            ```
            Hi {name}! Your {plan} plan details are below.
            ```
            """)

        col1, col2 = st.columns(2)
        with col1:
            file = st.file_uploader("📊 CSV file", type=["csv"], key="csv_file")
        with col2:
            template_file = st.file_uploader("📝 Message template (.txt)", type=["txt"], key="csv_template")

        if file is None or template_file is None:
            st.info("⬆️ Upload both a CSV file and a message template to continue.")
            return

        csv_body = template_file.read().decode("utf-8")
        filedata = pd.read_csv(file)
        filedata.columns = [c.strip().lower() for c in filedata.columns]

        if "email" not in filedata.columns:
            st.error("❌ CSV must have an `email` column.")
            return

        filedata = filedata.dropna(subset=["email"])
        filedata = filedata[filedata["email"].str.contains("@", na=False)]

        if len(filedata) == 0:
            st.error("❌ No valid email addresses found in CSV.")
            return
        if len(filedata) > 500:
            st.error("❌ CSV has more than 500 rows — Gmail daily limit is ~500 emails.")
            return

        st.dataframe(filedata.head(7))
        columns_csv = filedata.columns.tolist()

        csv_subject = st.text_input(
            "Subject",
            placeholder="Hello {name}!",
            key="csv_subject",
            help="Supports {column_name} placeholders",
        )

        st.subheader("🔧 Template Field Mapping")
        st.caption("Optionally rename column → placeholder in template.")
        memo = {}
        for col in columns_csv:
            text = st.text_input(f"Placeholder for `{col}`", value=col, key=f"csv_memo_{col}")
            if text.strip():
                memo[col] = text.strip()

        # Preview
        st.subheader("👁️ Preview — first contact")
        if len(filedata) > 0:
            row0 = filedata.iloc[0]
            row_dict = {memo.get(col, col): str(row0[col]) for col in columns_csv if col in row0.index}
            st.markdown(f"**Subject:** {_personalise(csv_subject or '(no subject)', row_dict)}")
            st.code(_personalise(csv_body, row_dict), language=None)

        st.markdown("---")

        if st.button("📤 Send Bulk Emails", type="primary", key="csv_send_btn"):
            missing = []
            if not sender_email_csv: missing.append("Gmail address")
            if not sender_password_csv: missing.append("App Password")
            if not csv_subject: missing.append("subject")
            if missing:
                st.error(f"❌ Please fill in: {', '.join(missing)}")
                return

            # Build contacts list using memo mapping
            contacts_csv = []
            for _, row in filedata.iterrows():
                contact = {memo.get(col, col): str(row.get(col, "")) for col in columns_csv}
                contacts_csv.append(contact)

            email_col_mapped = memo.get("email", "email")

            server = None
            try:
                server = _smtp_connect(sender_email_csv, sender_password_csv)
                st.success("🔗 Connected to Gmail SMTP — sending…")
                _run_bulk_email(server, sender_email_csv, contacts_csv,
                                email_col_mapped, csv_subject, csv_body)
            except smtplib.SMTPAuthenticationError:
                st.error("❌ Authentication failed — use a Gmail **App Password**, not your regular password.")
            except Exception as e:
                st.error(f"❌ SMTP error: {e}")
            finally:
                if server:
                    try: server.quit()
                    except Exception: pass