import streamlit as st
import time
from database import get_all_users, get_all_tags, get_user_tags, assign_tag_to_user, remove_tag_from_user, create_tag


def render_admin_view(user):
    st.title("🛡️ Admin-Management")
    users, tags = get_all_users(), get_all_tags()

    # --- NUTZER-RECHTE PRÜFEN & LÖSCHEN ---
    st.subheader("🔍 Nutzer-Rechte prüfen & verwalten")
    if users:
        u_map = {u['email']: u['id'] for u in users}
        sel_u_check = st.selectbox("Nutzer auswählen zum Verwalten", list(u_map.keys()), key="admin_check_u")

        if sel_u_check:
            target_user_id = u_map[sel_u_check]
            current_user_tags = get_user_tags(target_user_id)

            if current_user_tags:
                st.write(f"Tags für **{sel_u_check}** (Klicke auf das ❌ zum Löschen):")
                # Spaltenlayout für die Tags
                tag_cols = st.columns(len(current_user_tags) + 1)
                for i, t_name in enumerate(current_user_tags):
                    # Eindeutiger Key für jeden Button
                    if tag_cols[i].button(f"❌ {t_name}", key=f"del_{sel_u_check}_{t_name}"):
                        success = remove_tag_from_user(target_user_id, t_name)
                        if success:
                            st.success(f"Tag '{t_name}' wurde erfolgreich entfernt!")
                            time.sleep(0.5)
                            st.rerun()  # Erzwingt das Neuladen der Liste
                        else:
                            st.error(
                                f"Fehler: Tag '{t_name}' konnte nicht gelöscht werden. Prüfe die Datenbank-Policies (RLS)!")
            else:
                st.warning("Dieser Nutzer hat aktuell keine zugewiesenen Tags.")

    st.divider()

    col1, col2 = st.columns(2)

    # --- RECHTE VERGEBEN ---
    with col1:
        st.subheader("➕ Rechte vergeben")
        if users and tags:
            t_map = {t['name']: t['id'] for t in tags}
            sel_u_assign = st.selectbox("Nutzer auswählen", list(u_map.keys()), key="admin_sel_u_assign")
            sel_t_assign = st.selectbox("Tag auswählen", list(t_map.keys()), key="admin_sel_t_assign")

            if st.button("Tag zuweisen"):
                if sel_u_assign and sel_t_assign:
                    assign_tag_to_user(u_map[sel_u_assign], t_map[sel_t_assign])
                    st.success(f"Tag '{sel_t_assign}' vergeben!")
                    time.sleep(0.5)
                    st.rerun()
        else:
            st.warning("Keine Nutzer oder Tags für die Zuweisung verfügbar.")

    # --- GLOBALE TAGS ERSTELLEN ---
    with col2:
        st.subheader("🌍 Globaler Tag erstellen")
        new_tag_name = st.text_input("Name des neuen Tags", key="admin_new_tag_input")
        if st.button("Tag permanent erstellen"):
            if new_tag_name:
                create_tag(new_tag_name, user.id)
                st.success(f"Tag '{new_tag_name}' wurde erstellt!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("Bitte gib einen Namen für den Tag ein.")