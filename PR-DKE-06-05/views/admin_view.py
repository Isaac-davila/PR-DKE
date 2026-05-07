import streamlit as st
from database import (
    get_all_users,
    get_all_tags,
    get_user_tags,
    assign_tag_to_user,
    remove_tag_from_user,
    create_tag,
    delete_tag_globally,
)


def render_admin_view(user):
    """
    Renders the admin management console.
    Only reachable if the user has the 'admin' role tag.
    """
    st.title("🛡️ Admin-Management")

    users = get_all_users()
    tags = get_all_tags()

    u_map = {u["email"]: u["id"] for u in users} if users else {}
    t_map = {t["name"]: t["id"] for t in tags} if tags else {}

    col1, col2 = st.columns(2)

    # ------------------------------------------------------------------
    # Column 1 — User tag assignment / removal
    # ------------------------------------------------------------------
    with col1:
        st.subheader("👥 User-Tags")
        if not users:
            st.info("Keine Nutzer gefunden.")
        else:
            sel_user = st.selectbox(
                "Nutzer wählen", list(u_map.keys()), key="admin_user_select"
            )
            target_id = u_map[sel_user]
            current_tags = get_user_tags(target_id)

            if current_tags:
                st.write("Zugewiesene Tags (klicken zum Entfernen):")
                for t_name in current_tags:
                    if st.button(f"❌ {t_name}", key=f"del_{target_id}_{t_name}"):
                        remove_tag_from_user(target_id, t_name)
                        st.rerun()
            else:
                st.info("Diesem Nutzer sind keine Tags zugewiesen.")

    # ------------------------------------------------------------------
    # Column 2 — Global tag creation / deletion
    # ------------------------------------------------------------------
    with col2:
        st.subheader("🌍 Globale Tags")

        if tags:
            tag_to_del = st.selectbox(
                "Tag löschen", [t["name"] for t in tags], key="admin_global_tag_del"
            )
            if st.button("🗑️ Global löschen", key="admin_global_del_btn"):
                delete_tag_globally(t_map[tag_to_del])
                st.rerun()
        else:
            st.info("Keine Tags vorhanden.")

        st.divider()
        new_tag = st.text_input("Neuer Tag", key="admin_new_tag_input")
        if st.button("Erstellen", key="admin_create_btn"):
            tag_name = new_tag.strip()
            if not tag_name:
                st.warning("Bitte einen Tag-Namen eingeben.")
            else:
                res = create_tag(tag_name)
                if res == "exists":
                    st.warning(f"Tag '{tag_name}' existiert bereits.")
                elif res:
                    st.success(f"Tag '{tag_name}' wurde erstellt.")
                    st.rerun()
                else:
                    st.error("Fehler beim Erstellen des Tags.")

    # ------------------------------------------------------------------
    # Tag assignment section
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("➕ Tag zuweisen")

    if not users:
        st.info("Keine Nutzer vorhanden.")
    elif not tags:
        st.info("Keine Tags vorhanden. Bitte zuerst einen Tag erstellen.")
    else:
        col_u, col_t = st.columns(2)
        with col_u:
            u_assign = st.selectbox(
                "Nutzer", list(u_map.keys()), key="admin_assign_u"
            )
        with col_t:
            t_assign = st.selectbox(
                "Tag", list(t_map.keys()), key="admin_assign_t"
            )

        if st.button("Speichern", key="admin_assign_btn"):
            assign_tag_to_user(u_map[u_assign], t_map[t_assign])
            st.success(f"Tag '{t_assign}' wurde '{u_assign}' zugewiesen.")
            st.rerun()