import streamlit as st
import time
from database import (
    get_all_users,
    get_all_tags,
    get_user_tags,
    assign_tag_to_user,
    remove_tag_from_user,
    create_tag,
    delete_tag,  # <--- NEU IMPORTIERT
)

# Re-use the shared CSS from views.py
try:
    from views.views import inject_css
except ImportError:
    def inject_css():
        pass  # Fallback if called standalone


def _tag_pill(label: str) -> str:
    """Returns an inline HTML tag pill."""
    return (
        f"<span style='"
        f"display:inline-block; background:var(--accent-soft); color:var(--accent);"
        f"border-radius:99px; padding:4px 14px; font-size:0.75rem;"
        f"font-weight:600; margin:4px 6px 12px 0; letter-spacing:0.02em;'>"
        f"{label}</span>"
    )


def render_admin_view(user):
    """
    Modern Admin console.
    Two sections: Manage user rights (add/remove tags seamlessly) & Create/Delete system tags.
    """
    inject_css()

    st.markdown("## 🛡️ Admin-Konsole")
    st.markdown(
        "<p style='color:var(--text-muted);font-size:0.9rem;margin-top:-0.5rem;'>"
        "Nutzerrechte verwalten und Tags für das gesamte System organisieren."
        "</p>",
        unsafe_allow_html=True,
    )

    users = get_all_users()
    tags = get_all_tags()

    # Mapping für leichtere ID-Zuordnung
    u_map = {u["email"]: u["id"] for u in users} if users else {}
    t_map = {t["name"]: int(t["id"]) for t in tags} if tags else {}

    if not users:
        st.info("Keine Nutzer gefunden.")
        return

    st.markdown("<hr style='border-color:var(--border); margin:1.5rem 0;'>", unsafe_allow_html=True)

    # ── Zwei-Spalten-Layout ────────────────────────────────────────
    col_manage, col_create = st.columns([0.55, 0.45], gap="large")

    # ── Spalte 1: Nutzer-Rechte (Tags zuweisen / entfernen) ──
    with col_manage:
        st.markdown("### 👤 Nutzer-Rechte")
        st.caption("Wähle einen Nutzer, um seine Tags zu bearbeiten.")

        selected_email = st.selectbox(
            "Nutzer",
            list(u_map.keys()),
            key="admin_user_select",
            label_visibility="collapsed"
        )

        if selected_email:
            target_id = u_map[selected_email]
            current_tags = get_user_tags(target_id)

            with st.form(key=f"user_tags_form_{target_id}"):
                new_selected_tags = st.multiselect(
                    "Tags:",
                    options=list(t_map.keys()),
                    default=current_tags,
                    label_visibility="collapsed"
                )

                submit_user_tags = st.form_submit_button("💾 Änderungen speichern", use_container_width=True)

                if submit_user_tags:
                    tags_to_add = set(new_selected_tags) - set(current_tags)
                    tags_to_remove = set(current_tags) - set(new_selected_tags)

                    # Verhindern, dass man sich selbst den Admin-Tag wegnimmt (Schutzmaßnahme)
                    if "admin" in tags_to_remove and selected_email == user.email:
                        st.error("Du kannst dir nicht selbst den Admin-Tag entziehen!")
                    else:
                        success = True
                        for t_name in tags_to_add:
                            assign_tag_to_user(target_id, t_map[t_name])
                        for t_name in tags_to_remove:
                            remove_ok = remove_tag_from_user(target_id, t_name)
                            if not remove_ok: success = False

                        if success:
                            st.success(f"Tags für {selected_email} aktualisiert!")
                            time.sleep(0.8)
                            st.rerun()
                        else:
                            st.error("Fehler beim Speichern (RLS-Policy prüfen).")

    # ── Spalte 2: Neue Tags erstellen & System-Tags löschen ──
    with col_create:
        st.markdown("### 🏷️ System-Tags")
        st.caption("Erstelle neue oder verwalte bestehende Tags.")

        with st.form(key="create_tag_form", clear_on_submit=True):
            new_tag_name = st.text_input(
                "Tag-Name",
                placeholder="z. B. projekt-alpha",
                label_visibility="collapsed"
            )
            submit_new_tag = st.form_submit_button("✚ Tag erstellen", use_container_width=True)

            if submit_new_tag:
                name = new_tag_name.strip()
                if not name:
                    st.warning("Bitte einen Tag-Namen eingeben.")
                else:
                    res = create_tag(name, user.id)
                    if res == "exists":
                        st.warning(f"Tag **{name}** existiert bereits.")
                    elif res:
                        st.success(f"Tag **{name}** erstellt!")
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.error("Fehler beim Erstellen des Tags.")

        if tags:
            st.markdown(
                "<p style='font-size:0.8rem; color:var(--text-muted); margin:1.5rem 0 0.5rem;'>Vorhandene System-Tags:</p>",
                unsafe_allow_html=True
            )
            pills_html = "".join(_tag_pill(t["name"]) for t in tags)
            st.markdown(f"<div>{pills_html}</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            # --- NEU: Tag löschen (im Expander versteckt für ein aufgeräumtes UI) ---
            # Wir filtern 'admin' und 'basic' aus, damit diese nie gelöscht werden können
            deletable_tags = [t for t in t_map.keys() if t not in ["admin", "basic"]]

            if deletable_tags:
                with st.expander("🗑️ Tag löschen"):
                    st.markdown(
                        "<p style='font-size:0.8rem; color:var(--error); margin-bottom:8px;'>"
                        "<b>Achtung:</b> Dies entfernt den Tag permanent bei allen Nutzern und Transkripten."
                        "</p>", unsafe_allow_html=True
                    )

                    tag_to_delete = st.selectbox(
                        "Welchen Tag möchtest du löschen?",
                        deletable_tags,
                        key="delete_tag_select",
                        label_visibility="collapsed"
                    )

                    if st.button("Unwiderruflich löschen"):
                        success = delete_tag(t_map[tag_to_delete])
                        if success:
                            st.success(f"Tag '{tag_to_delete}' wurde erfolgreich gelöscht.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Fehler beim Löschen des Tags.")