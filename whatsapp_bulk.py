"""
whatsapp_bulk.py — WhatsApp bulk message sender (Streamlit).

Two modes via tabs:
  ✏️ Manual Input — define custom columns inline, paste data rows, type template
  📁 CSV Upload   — upload a CSV + TXT template (personalised per-row)

Manual Input supports multiple columns:
  Column names: phone, name, city
  Data rows:    +91XXXXXXXXXX, Alice, Hyderabad
  Template:     Hello {name} from {city}!
  → first column is always the phone number column
"""

import streamlit as st
import time
import tempfile
import os
from whats.whatsutils import send_whatsapp_message as sendmsg, get_browser
import pandas as pd

_DELAY_BETWEEN_MSGS = 3   # seconds between messages to avoid WhatsApp ban


# ── shared helpers ─────────────────────────────────────────────────────────────

def _parse_columns(col_string: str) -> list[str]:
    """Parse 'phone, name, city' → ['phone', 'name', 'city']"""
    return [c.strip().lower() for c in col_string.split(",") if c.strip()]


def _parse_manual_contacts(raw: str, columns: list[str]) -> list[dict]:
    """
    Parse comma-separated contact rows into list of dicts.
    Each line: value1, value2, value3 …  matching columns order.
    """
    contacts = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        # Pad with empty strings if fewer values than columns
        while len(parts) < len(columns):
            parts.append("")
        contact = {col: parts[i] for i, col in enumerate(columns)}
        contacts.append(contact)
    return contacts


def _personalise(template: str, row: dict) -> str:
    """Replace {column_name} placeholders with row values."""
    msg = template
    for key, val in row.items():
        msg = msg.replace(f"{{{key}}}", str(val))
    return msg


def _validate_contacts(contacts: list[dict], phone_col: str) -> tuple[list[dict], list[str]]:
    """Validate phone numbers; return (valid_contacts, warning_messages)."""
    valid, warnings = [], []
    seen = set()
    for i, contact in enumerate(contacts):
        phone = contact.get(phone_col, "").strip()
        if not phone:
            warnings.append(f"Row {i+1}: empty phone — skipped")
            continue
        if phone in seen:
            warnings.append(f"Row {i+1}: duplicate `{phone}` — skipped")
            continue
        seen.add(phone)
        if not phone.startswith("+"):
            warnings.append(
                f"Row {i+1}: `{phone}` has no country code (+91…) — skipped"
            )
            continue
        valid.append(contact)
    return valid, warnings


def _run_bulk_send(webd, contacts: list[dict], phone_col: str, template: str, image_path):
    """Core send loop: personalise → send → progress bar."""
    total     = len(contacts)
    errors    = 0
    progress  = st.progress(0)
    status    = st.empty()
    start     = time.time()

    for idx, contact in enumerate(contacts):
        phone = contact[phone_col]
        msg   = _personalise(template, contact)
        status.text(f"📤 [{idx+1}/{total}] Sending to {phone}…")

        if sendmsg(webd, phone, msg, image_path):
            st.success(f"✅ {phone}")
        else:
            st.error(f"❌ {phone} — failed")
            errors += 1

        progress.progress((idx + 1) / total)
        if idx < total - 1:
            time.sleep(_DELAY_BETWEEN_MSGS)

    elapsed = time.time() - start
    status.text("✅ Done!")
    st.success(
        f"**Summary:** {total} attempted · {total - errors} sent · {errors} failed  \n"
        f"⏱ {elapsed:.1f}s total · avg {elapsed / max(total,1):.1f}s per message"
    )


# ── main page ──────────────────────────────────────────────────────────────────

def send_whatsapp_bulk_message():
    st.title("📨 WhatsApp Bulk Message Sender")

    browser_choice = st.selectbox("🌐 Browser", ["Chrome", "Edge", "Firefox"])

    image_file = st.file_uploader(
        "🖼️ Attach Image (optional — sent to all recipients)",
        type=["jpg", "jpeg", "png", "gif", "webp"],
    )

    st.markdown("---")

    tab_manual, tab_csv = st.tabs(["✏️ Manual Input", "📁 CSV Upload"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — MANUAL INPUT  (multi-column)
    # ══════════════════════════════════════════════════════════════════════════
    with tab_manual:
        st.subheader("✏️ Type / Paste Contact Data & Message")

        st.markdown("""
        **Step 1 — Define your columns** (first column = phone number):
        """)
        col_input = st.text_input(
            "Column names (comma-separated)",
            value="phone, name",
            placeholder="phone, name, city, date",
            key="manual_cols",
            help="First column must be the phone number column. Use these names as {placeholder} in your template.",
        )
        columns = _parse_columns(col_input)
        phone_col = columns[0] if columns else "phone"

        if len(columns) > 1:
            st.info(
                f"📌 **Phone column:** `{phone_col}` · "
                f"**Extra columns:** {', '.join(f'`{c}`' for c in columns[1:])}  \n"
                f"Use `{{{phone_col}}}`, {', '.join(f'`{{{c}}}`' for c in columns[1:])} in your template."
            )
        else:
            st.info(f"📌 **Phone column:** `{phone_col}` · Use `{{{phone_col}}}` in your template.")

        st.markdown(f"""
        **Step 2 — Paste contact data** (one contact per line, comma-separated):  
        Format: `{', '.join(f'<{c}>' for c in columns)}`
        """)
        data_raw = st.text_area(
            "Contact Data",
            placeholder="\n".join([
                f"+91XXXXXXXXXX{', value' * (len(columns)-1)}",
                f"+91XXXXXXXXXX{', value' * (len(columns)-1)}",
            ]),
            height=200,
            key="manual_data",
        )

        st.markdown("**Step 3 — Write your message template:**")
        placeholder_hint = ", ".join(f"`{{{c}}}`" for c in columns)
        st.caption(f"Available placeholders: {placeholder_hint}")
        message_template = st.text_area(
            "Message Template",
            placeholder=f"Hello {{{columns[1] if len(columns) > 1 else phone_col}}}! This is a message for {{{phone_col}}}.",
            height=160,
            key="manual_message",
        )

        # ── Live preview ──────────────────────────────────────────────────────
        if data_raw.strip() and message_template.strip() and columns:
            contacts = _parse_manual_contacts(data_raw, columns)
            valid, warnings = _validate_contacts(contacts, phone_col)

            for w in warnings:
                st.warning(w)

            skipped = len(contacts) - len(valid)
            st.info(
                f"📊 **{len(valid)}** valid contact(s)"
                + (f" · {skipped} skipped" if skipped else "")
            )

            if valid:
                st.subheader("👁️ Preview — first contact")
                preview = _personalise(message_template, valid[0])
                st.code(preview, language=None)
                # Show the substituted values
                with st.expander("🔍 Column values for first contact"):
                    for col, val in valid[0].items():
                        st.write(f"**{col}** → `{val}`")

        st.markdown("---")

        if st.button("🚀 Send to All", type="primary", key="manual_send_btn"):
            if not data_raw.strip():
                st.error("❌ Please enter contact data.")
                return
            if not message_template.strip():
                st.error("❌ Please enter a message template.")
                return
            if not columns:
                st.error("❌ Please define at least one column.")
                return

            contacts = _parse_manual_contacts(data_raw, columns)
            valid, warnings = _validate_contacts(contacts, phone_col)
            for w in warnings:
                st.warning(w)
            if not valid:
                st.error("❌ No valid contacts found.")
                return

            _do_send(webd_builder=lambda: get_browser(browser_choice),
                     contacts=valid, phone_col=phone_col,
                     template=message_template, image_file=image_file)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — CSV UPLOAD
    # ══════════════════════════════════════════════════════════════════════════
    with tab_csv:
        st.subheader("📁 CSV + Template File Upload")

        with st.expander("ℹ️ How to prepare your files", expanded=False):
            st.markdown("""
            **CSV File** — any columns you like:
            ```
            phone,name,date
            +91XXXXXXXXXX,Alice,Monday
            +91XXXXXXXXXX,Bob,Tuesday
            ```
            **Template File (.txt)** — use `{column_name}` as placeholders:
            ```
            Hello {name}, your appointment is on {date}.
            ```
            """)

        col1, col2 = st.columns(2)
        with col1:
            file = st.file_uploader("📊 CSV file", type=["csv"], key="csv_file")
        with col2:
            template_file = st.file_uploader("📝 Message template (.txt)", type=["txt"], key="csv_template")

        if template_file is None or file is None:
            st.info("⬆️ Upload both a CSV file and a message template to continue.")
            return

        csv_template = template_file.read().decode("utf-8")
        filedata = pd.read_csv(file)
        filedata.columns = [c.strip().lower() for c in filedata.columns]
        st.dataframe(filedata.head(7))

        columns_csv = filedata.columns.tolist()

        phonecolumn = st.selectbox(
            "Column containing phone numbers",
            options=columns_csv,
            key="csv_phonecolumn",
        )

        filedata = filedata.dropna(subset=[phonecolumn])

        st.markdown("---")
        st.subheader("🔧 Template Field Mapping")
        st.caption("Optionally rename column placeholders in the template.")
        memo = {}
        for col in columns_csv:
            text = st.text_input(f"Placeholder for `{col}`", value=col, key=f"csv_memo_{col}")
            if text.strip():
                memo[col] = text.strip()

        st.subheader("👁️ Preview — first contact")
        if len(filedata) > 0:
            row0 = filedata.iloc[0]
            preview_csv = csv_template
            for col, placeholder in memo.items():
                if col in row0.index:
                    preview_csv = preview_csv.replace(f"{{{placeholder}}}", str(row0[col]))
            st.code(preview_csv, language=None)

        st.markdown("---")

        if st.button("🚀 Send Bulk Messages", type="primary", key="csv_send_btn"):
            valid_rows = []
            for _, row in filedata.iterrows():
                phone = str(row[phonecolumn]).strip()
                if not phone.startswith("+"):
                    st.warning(f"⚠️ `{phone}` has no country code — skipping.")
                    continue
                valid_rows.append(row)

            if not valid_rows:
                st.error("❌ No valid recipients.")
                return

            # Convert to list of dicts using memo mapping
            contacts_csv = []
            for row in valid_rows:
                contact = {}
                for col, placeholder in memo.items():
                    contact[placeholder] = str(row.get(col, ""))
                # ensure phone key exists
                phone_placeholder = memo.get(phonecolumn, phonecolumn)
                contacts_csv.append(contact)

            _do_send(webd_builder=lambda: get_browser(browser_choice),
                     contacts=contacts_csv, phone_col=memo.get(phonecolumn, phonecolumn),
                     template=csv_template, image_file=image_file)


def _do_send(webd_builder, contacts, phone_col, template, image_file):
    """Shared browser launch + send loop used by both tabs."""
    tmp_file   = None
    image_path = None
    webd       = None

    try:
        if image_file:
            suffix     = os.path.splitext(image_file.name)[1]
            tmp_file   = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp_file.write(image_file.read())
            tmp_file.flush()
            tmp_file.close()
            image_path = tmp_file.name

        webd = webd_builder()
        webd.get("https://web.whatsapp.com")
        webd.maximize_window()

        with st.spinner("⏳ Waiting for WhatsApp Web to load (10 s)…"):
            time.sleep(10)

        _run_bulk_send(webd, contacts, phone_col, template, image_path)

    except FileNotFoundError as e:
        st.error(f"❌ Browser profile error: {e}")
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        if webd:
            try:
                webd.quit()
            except Exception:
                pass
        if image_path and os.path.exists(image_path):
            os.unlink(image_path)
