import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import plotly.express as px
import urllib.parse
import hashlib

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="general410 Pro", 
    page_icon="🚰",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. FONCTION DE SÉCURITÉ (CRYPTAGE) ---
def crypter_mot_de_passe(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- 3. GESTION DU THÈME / APPARENCE ---
if 'theme' not in st.session_state:
    st.session_state['theme'] = "Clair (Blanc)"

css_themes = {
    "Clair (Blanc)": """
        <style>
            .stApp { background-color: #F8FAFC; color: #0F172A; }
            [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
            div[data-testid="metric-container"] { background-color: #FFFFFF; border: 1px solid #E2E8F0; color: #1E293B; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            [data-testid="stMetricValue"] { color: #1E293B !important; }
            [data-testid="stMetricLabel"] { color: #64748B !important; }
            div[data-testid="stForm"] { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }
            p, span, label, th, td { color: #0F172A !important; }
            .chat-msg-vendeur { background-color: #DCFCE7 !important; color: #14532D !important; }
            .chat-msg-admin { background-color: #E0F2FE !important; color: #0369A1 !important; }
            .chat-msg-vendeur b, .chat-msg-admin b, .chat-msg-vendeur small, .chat-msg-admin small { color: inherit !important; }
        </style>
    """,
    "Sombre": """
        <style>
            .stApp { background-color: #0F172A; color: #F8FAFC; }
            [data-testid="stSidebar"] { background-color: #1E293B !important; border-right: 1px solid #334155; }
            div[data-testid="metric-container"] { background-color: #1E293B; border: 1px solid #334155; color: #F8FAFC; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
            [data-testid="stMetricValue"] { color: #F8FAFC !important; }
            [data-testid="stMetricLabel"] { color: #94A3B8 !important; }
            div[data-testid="stForm"] { background-color: #1E293B; border: 1px solid #334155; border-radius: 12px; }
            p, span, label, th, td, h1, h2, h3, h4, h5, h6 { color: #F8FAFC !important; }
            .stDataFrame div { color: #F8FAFC !important; }
            .chat-msg-vendeur { background-color: #064E3B !important; color: #A7F3D0 !important; }
            .chat-msg-admin { background-color: #0C4A6E !important; color: #BAE6FD !important; }
            .chat-msg-vendeur b, .chat-msg-admin b, .chat-msg-vendeur small, .chat-msg-admin small { color: inherit !important; }
        </style>
    """,
    "Bleu Nuit": """
        <style>
            .stApp { background-color: #0A192F; color: #64FFDA; }
            [data-testid="stSidebar"] { background-color: #112240 !important; border-right: 1px solid #233554; }
            div[data-testid="metric-container"] { background-color: #112240; border: 1px solid #233554; color: #64FFDA; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }
            [data-testid="stMetricValue"] { color: #64FFDA !important; }
            [data-testid="stMetricLabel"] { color: #8892B0 !important; }
            div[data-testid="stForm"] { background-color: #112240; border: 1px solid #233554; border-radius: 12px; }
            p, span, label, th, td, h1, h2, h3, h4, h5, h6 { color: #CCD6F6 !important; }
            .chat-msg-vendeur { background-color: #022C22 !important; color: #64FFDA !important; }
            .chat-msg-admin { background-color: #0B192C !important; color: #38BDF8 !important; }
            .chat-msg-vendeur b, .chat-msg-admin b, .chat-msg-vendeur small, .chat-msg-admin small { color: inherit !important; }
        </style>
    """
}

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { font-size: 13px !important; text-transform: uppercase; }
    div[data-testid="metric-container"] { padding: 15px; border-radius: 12px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #0284C7; color: white; font-weight: 600; padding: 10px 20px; border: none; }
    .stButton>button:hover { background-color: #0369A1; color: white; }
    div[data-testid="stForm"] { padding: 25px; border-radius: 12px; }
    .alerte-vidange { background-color: #FEF3C7; border-left: 5px solid #D97706; padding: 12px; border-radius: 6px; color: #92400E; font-weight: bold; }
    .indicateur-ecart { font-size: 16px; font-weight: bold; padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px; }
    .whatsapp-btn { display: inline-block; background-color: #25D366; color: white !important; font-weight: bold; text-decoration: none; padding: 12px 20px; border-radius: 8px; text-align: center; width: 100%; margin-top: 10px; }
    .whatsapp-btn:hover { background-color: #128C7E; }
    .chat-box { background-color: rgba(0,0,0,0.03); border-radius: 10px; padding: 15px; max-height: 400px; overflow-y: auto; margin-bottom: 15px; border: 1px solid rgba(0,0,0,0.1); }
    .chat-msg { margin-bottom: 10px; padding: 8px 12px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown(css_themes[st.session_state['theme']], unsafe_allow_html=True)

# --- 4. BASE DE DONNÉES ---
conn = sqlite3.connect("general410.db", timeout=30.0, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("PRAGMA synchronous=NORMAL;")
conn.commit()

cursor.execute('CREATE TABLE IF NOT EXISTS parametres (id INTEGER PRIMARY KEY AUTOINCREMENT, taux_usd_fc REAL)')
cursor.execute('CREATE TABLE IF NOT EXISTS sites (id INTEGER PRIMARY KEY AUTOINCREMENT, nom_site TEXT UNIQUE)')
cursor.execute('CREATE TABLE IF NOT EXISTS utilisateurs (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT, site_associe TEXT)')
cursor.execute('''
CREATE TABLE IF NOT EXISTS rapports (
    id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, site TEXT, vendeur TEXT, index_matin REAL, index_soir REAL,
    consommation REAL, prix_m3 REAL, montant_fc REAL, montant_usd REAL, depenses_locales_fc REAL, commentaire_depense TEXT, heures_groupe REAL
)''')
cursor.execute('CREATE TABLE IF NOT EXISTS depenses_admin (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, poste TEXT, description TEXT, montant_fc REAL, auteur TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS banque (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, site TEXT, montant_fc REAL, banque_cible TEXT, auteur TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS chat_interne (id INTEGER PRIMARY KEY AUTOINCREMENT, date_heure TEXT, expediteur TEXT, role TEXT, message TEXT)')
conn.commit()

# --- SÉCURISATION ET HARMONISATION DES TABLES ---
for col, typ in [("montant_fc", "REAL DEFAULT 0.0"), ("montant_usd", "REAL DEFAULT 0.0"), ("heures_groupe", "REAL DEFAULT 0.0"), ("depenses_locales_fc", "REAL DEFAULT 0.0")]:
    try:
        cursor.execute(f"ALTER TABLE rapports ADD COLUMN {col} {typ};")
        conn.commit()
    except sqlite3.OperationalError:
        pass

try:
    cursor.execute("ALTER TABLE depenses_admin ADD COLUMN montant_fc REAL DEFAULT 0.0;")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE banque ADD COLUMN montant_fc REAL DEFAULT 0.0;")
    conn.commit()
except sqlite3.OperationalError:
    pass

# Initialisations par défaut
cursor.execute("SELECT COUNT(*) FROM parametres")
if cursor.fetchone()[0] == 0: 
    cursor.execute("INSERT INTO parametres (taux_usd_fc) VALUES (2850.0)")
    conn.commit()

cursor.execute("SELECT COUNT(*) FROM sites")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO sites (nom_site) VALUES ('Site Centre')")
    cursor.execute("INSERT INTO sites (nom_site) VALUES ('Site Kitambo')")
    conn.commit()

cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE LOWER(username) = 'gilbert'")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO utilisateurs (username, password, role, site_associe) VALUES ('Gilbert', ?, 'Super Admin', 'Tous')", (crypter_mot_de_passe('admin410'),))
    cursor.execute("INSERT INTO utilisateurs (username, password, role, site_associe) VALUES ('Manager1', ?, 'Manager', 'Tous')", (crypter_mot_de_passe('manager123'),))
    conn.commit()

cursor.execute("SELECT taux_usd_fc FROM parametres WHERE id = 1")
TAUX_JOUR = cursor.fetchone()[0]

# --- 5. FONCTIONS UTILITAIRES ---
def obtenir_dernier_index(site):
    cursor.execute("SELECT index_soir FROM rapports WHERE site = ? ORDER BY date DESC, id DESC LIMIT 1", (site,))
    res = cursor.fetchone()
    return float(res[0]) if res else 0.0

def obtenir_total_heures_groupe(site):
    cursor.execute("SELECT SUM(heures_groupe) FROM rapports WHERE site = ?", (site,))
    res = cursor.fetchone()[0]
    return float(res) if res else 0.0

def exporter_excel(df_relevies, df_depenses, df_banque):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_relevies.to_excel(writer, sheet_name='Registre Général', index=False)
        df_depenses.to_excel(writer, sheet_name='Dépenses Administrateurs', index=False)
        df_banque.to_excel(writer, sheet_name='Flux Banque', index=False)
    return output.getvalue()

# --- 6. INITIALISATION DES SESSIONS ---
if 'connecte' not in st.session_state: st.session_state['connecte'] = False
if 'username' not in st.session_state: st.session_state['username'] = ""
if 'role' not in st.session_state: st.session_state['role'] = ""
if 'site_associe' not in st.session_state: st.session_state['site_associe'] = ""
if 'show_whatsapp' not in st.session_state: st.session_state['show_whatsapp'] = False
if 'whatsapp_text' not in st.session_state: st.session_state['whatsapp_text'] = ""

# --- NETTOYAGE AGRESSIF DE L'ANCIEN CACHE POLLUÉ ---
# On élimine de la mémoire de Streamlit toutes les variables de session contenant "Gilbert" par erreur.
cles_a_purger = ["dash_period_filter_final_ultra_secure", "dash_period_filter", "period_filter"]
for cle in cles_a_purger:
    if cle in st.session_state:
        del st.session_state[cle]

# --- SIDEBAR ---
st.sidebar.markdown("<h2 style='text-align: center; color: #0284C7;'>🚰 general410 Pro</h2>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='text-align: center; font-size:12px; color:gray;'>Taux : 1 USD = {TAUX_JOUR:,.0f} FC</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.markdown("🎨 **Apparence / Thème**")
liste_themes = ["Clair (Blanc)", "Sombre", "Bleu Nuit"]
index_defaut = liste_themes.index(st.session_state['theme']) if st.session_state['theme'] in liste_themes else 0

theme_choisi = st.sidebar.selectbox(
    "Choisir le style", 
    options=liste_themes, 
    index=index_defaut,
    key="system_theme_selector_unique_key"
)
if theme_choisi != st.session_state['theme']:
    st.session_state['theme'] = theme_choisi
    st.rerun()

st.sidebar.markdown("---")

if not st.session_state['connecte']:
    with st.sidebar.form(key="formulaire_connexion_systeme_principal"):
        st.markdown("🔐 **Espace Connexion**")
        username_input = st.text_input("Nom d'utilisateur", key="auth_username_field_secure").strip()
        password_input = st.text_input("Mot de passe", type="password", key="auth_password_field_secure").strip()
        bouton_soumettre = st.form_submit_button("Se connecter")
        
        if bouton_soumettre:
            if username_input and password_input:
                hashed_input = crypter_mot_de_passe(password_input)
                cursor.execute("SELECT username, role, site_associe FROM utilisateurs WHERE LOWER(username) = LOWER(?) AND password = ?", (username_input, hashed_input))
                user = cursor.fetchone()
                if user:
                    st.session_state['connecte'] = True
                    st.session_state['username'] = user[0]
                    st.session_state['role'] = user[1]
                    st.session_state['site_associe'] = user[2]
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")
            else:
                st.error("Veuillez remplir les deux champs.")
else:
    with st.sidebar.container():
        st.markdown(f"👤 **Utilisateur :** `{st.session_state['username']}`")
        st.markdown(f"💼 **Rôle :** `{st.session_state['role']}`")
        if st.session_state['role'] == 'Vendeur':
            st.markdown(f"📍 **Forage :** `{st.session_state['site_associe']}`")
        st.markdown("---")
        if st.button("🚪 Se déconnecter", key="btn_global_logout"):
            st.session_state['connecte'] = False
            st.session_state['show_whatsapp'] = False
            st.rerun()

# --- APPLICATION PRINCIPALE ---
if st.session_state['connecte']:
    df_sites_db = pd.read_sql_query("SELECT * FROM sites", conn)
    liste_des_sites = list(df_sites_db['nom_site'].unique()) if not df_sites_db.empty else []
    
    # MODULE VENDEUR
    if st.session_state['role'] == 'Vendeur':
        tab_vendeur, tab_chat_v = st.columns([2, 1])
        with tab_vendeur:
            st.markdown(f"### 🚰 Enregistrement — **{st.session_state['site_associe']}**")
            site_actuel = st.session_state['site_associe']
            dernier_index_soir = obtenir_dernier_index(site_actuel)
            heures_cumulees = obtenir_total_heures_groupe(site_actuel)
            
            if (heures_cumulees % 50) >= 45 or ((heures_cumulees % 50) == 0 and heures_cumulees > 0):
                st.markdown(f"<div class='alerte-vidange'>⚠️ ALERTE TECHNIQUE : Le Groupe Électrogène totalise {heures_cumulees:.1f}h de marche. Vidange proche !</div><br>", unsafe_allow_html=True)
            
            with st.form("form_vendeur"):
                date_releve = st.date_input("Date du relevé", datetime.now().date())
                if dernier_index_soir > 0:
                    index_matin = float(dernier_index_soir)
                    st.info(f"📌 Index Matinal (Report automatique) : **{dernier_index_soir}**")
                else:
                    index_matin = st.number_input("Index Matinal (Initialisation)", min_value=0.0, value=0.0, step=0.1, key="vendeur_index_matin_init")
                    
                index_soir = st.number_input("Index Réel du Soir", min_value=float(index_matin), value=float(index_matin), step=0.1, key="vendeur_index_soir_input")
                prix_m3 = st.number_input("Prix appliqué par m³ (FC)", min_value=0.0, value=1200.0, step=50.0, key="vendeur_prix_m3_input")
                
                st.markdown("<h4 style='color: #0284C7; margin-top: 10px;'>💵 Versements Caisse Reçus</h4>", unsafe_allow_html=True)
                col_enc1, col_enc2 = st.columns(2)
                with col_enc1: encaisse_fc = st.number_input("Somme en Francs (FC)", min_value=0.0, value=0.0, step=500.0, key="vendeur_encaisse_fc_input")
                with col_enc2: encaisse_usd = st.number_input("Somme en Dollars (USD)", min_value=0.0, value=0.0, step=1.0, key="vendeur_encaisse_usd_input")
                
                st.markdown("<h4 style='color: #D97706; margin-top: 10px;'>🔧 Suivi Technique & Frais</h4>", unsafe_allow_html=True)
                heures_groupe = st.number_input("Heures de marche du Groupe (h)", min_value=0.0, value=0.0, step=0.5, key="vendeur_heures_groupe_input")
                depenses_locales = st.number_input("Dépenses locales (FC)", min_value=0.0, value=0.0, step=500.0, key="vendeur_depenses_locales_input")
                commentaire_depense = st.text_input("Raison de la dépense sur place", key="vendeur_comm_depense_input").replace("'", " ").strip()
                
                conso_live = max(0.0, index_soir - index_matin)
                recette_theorique = conso_live * prix_m3
                recette_reelle_declaree = encaisse_fc + (encaisse_usd * TAUX_JOUR)
                reste_net_caisse = recette_reelle_declaree - depenses_locales
                ecart_constate = recette_reelle_declaree - recette_theorique
                
                st.markdown("---")
                if ecart_constate == 0: st.markdown("<div class='indicateur-ecart' style='background-color: #DCFCE7; color: #166534;'>✅ Caisse Équilibrée (0 Écart)</div>", unsafe_allow_html=True)
                elif ecart_constate > 0: st.markdown(f"<div class='indicateur-ecart' style='background-color: #FEF9C3; color: #854D0E;'>📈 Surplus détecté : +{ecart_constate:,.0f} FC</div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='indicateur-ecart' style='background-color: #FEE2E2; color: #991B1B;'>⚠️ Manquant en caisse : {ecart_constate:,.0f} FC</div>", unsafe_allow_html=True)
                    
                valider = st.form_submit_button("🚀 Enregistrer le Relevé Journalier")
                if valider:
                    cursor.execute("SELECT id FROM rapports WHERE site = ? AND date = ?", (site_actuel, str(date_releve)))
                    if cursor.fetchone() is not None:
                        st.error(f"❌ Erreur : Un rapport existe déjà pour le {date_releve} sur ce site.")
                    elif index_soir < index_matin:
                        st.error("❌ L'index du soir ne peut pas être inférieur à l'index du matin.")
                    else:
                        cursor.execute("""
                            INSERT INTO rapports (date, site, vendeur, index_matin, index_soir, consommation, prix_m3, montant_fc, montant_usd, depenses_locales_fc, commentaire_depense, heures_groupe) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (str(date_releve), site_actuel, st.session_state['username'], index_matin, index_soir, conso_live, prix_m3, encaisse_fc, encaisse_usd, depenses_locales, commentaire_depense, heures_groupe))
                        conn.commit()
                        
                        msg_whatsapp = f"📝 *RAPPORT JOURNALIER - {site_actuel}*\n📅 *Date :* {date_releve}\n👤 *Vendeur :* {st.session_state['username']}\n----------------------------------------\n📊 *Consommation :* {conso_live:.1f} m³\n📈 *Recette Brute :* {recette_reelle_declaree:,.0f} FC\n🔧 *Dépenses Locales :* {depenses_locales:,.0f} FC\n📉 *Reste Net :* {reste_net_caisse:,.0f} FC\n⚠️ *Écart :* {ecart_constate:,.0f} FC"
                        st.session_state['whatsapp_text'] = urllib.parse.quote(msg_whatsapp, safe='')
                        st.session_state['show_whatsapp'] = True
                        st.success("✅ Données stockées avec succès !")
                        st.rerun()

            if st.session_state['show_whatsapp']:
                st.markdown(f'<a href="https://wa.me/?text={st.session_state["whatsapp_text"]}" target="_blank" class="whatsapp-btn">🟢 Partager le Rapport sur WhatsApp</a>', unsafe_allow_html=True)
                if st.button("Masquer le bouton de partage", key="btn_hide_whatsapp"):
                    st.session_state['show_whatsapp'] = False
                    st.rerun()

        with tab_chat_v:
            col_lbl, col_rf = st.columns([2, 1])
            col_lbl.markdown("#### 💬 Messagerie Directe")
            if col_rf.button("🔄", key="ref_chat_v"): st.rerun()
                
            df_chat = pd.read_sql_query("SELECT * FROM chat_interne ORDER BY id DESC LIMIT 30", conn)
            chat_container = "<div class='chat-box'>"
            for idx, row_c in df_chat.iloc[::-1].iterrows():
                classe_bulle = "chat-msg-vendeur" if row_c['role'] == 'Vendeur' else "chat-msg-admin"
                align = "text-align: right;" if row_c['expediteur'] == st.session_state['username'] else "text-align: left;"
                chat_container += f"<div class='chat-msg {classe_bulle}' style='{align}'><b>{row_c['expediteur']}</b> ({row_c['role']}) - <small>{row_c['date_heure']}</small> :<br>{row_c['message']}</div>"
            chat_container += "</div>"
            st.markdown(chat_container, unsafe_allow_html=True)
            
            with st.form("send_msg_vendeur", clear_on_submit=True):
                v_msg = st.text_input("Votre message...", placeholder="Écrire ici...", key="chat_input_vendeur_text").replace("'", " ").strip()
                if st.form_submit_button("✉️ Envoyer") and v_msg:
                    cursor.execute("INSERT INTO chat_interne (date_heure, expediteur, role, message) VALUES (?, ?, ?, ?)", (datetime.now().strftime('%Y-%m-%d %H:%M'), st.session_state['username'], 'Vendeur', v_msg))
                    conn.commit()
                    st.rerun()

    # MODULE ADMIN & MANAGEMENT
    else:
        onglet = st.tabs(["📉 Tableau de Bord", "💼 Saisies Structures & Banque", "👥 Configuration & Comptes", "💬 Messagerie Interne", "🛠️ Registres & Maintenance"])
        
        df_relevies = pd.read_sql_query("SELECT * FROM rapports", conn)
        df_depenses = pd.read_sql_query("SELECT * FROM depenses_admin", conn)
        df_banque = pd.read_sql_query("SELECT * FROM banque", conn)
        df_utilisateurs = pd.read_sql_query("SELECT * FROM utilisateurs", conn)
        
        # --- TAB 1 : DASHBOARD (CLÉ COMPLÈTEMENT RENOMMÉE POUR CHASSERS "GILBERT") ---
        with onglet[0]:
            st.markdown("### Suivi Analytique de Performance")
            col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
            with col_f1:
                tous_sites = ["Tous les sites"] + list(df_relevies['site'].unique()) if not df_relevies.empty else ["Tous les sites"]
                filtre_site = st.selectbox("Sélectionner un site", tous_sites, key="dash_site_filter_final_v4")
            
            with col_f2:
                # CHANGEMENT RADICAL DE NOM : On utilise "choix_de_la_periode_historique"
                # Cela force Streamlit à ignorer tout historique de cache corrompu.
                liste_periodes_dispo = ["Tout l'historique", "Appel de la Journée", "Semaine", "Mois", "Année"]
                filtre_periode = st.selectbox(
                    "Période du rapport", 
                    options=liste_periodes_dispo, 
                    index=0,
                    key="choix_de_la_periode_historique_v4"
                )
            
            with col_f3:
                excel_ready = exporter_excel(df_relevies, df_depenses, df_banque)
                st.download_button("📥 Télécharger Excel", data=excel_ready, file_name="general410_Rapport.xlsx", key="btn_download_excel_dash_v4")
            
            if not df_relevies.empty:
                df_relevies['date'] = pd.to_datetime(df_relevies['date'], errors='coerce')
                df_filtre = df_relevies.dropna(subset=['date']).copy()
                
                if filtre_site != "Tous les sites":
                    df_filtre = df_filtre[df_filtre['site'] == filtre_site]
                    
                aujourdhui = datetime.now().date()
                if filtre_periode == "Appel de la Journée": df_filtre = df_filtre[df_filtre['date'].dt.date == aujourdhui]
                elif filtre_periode == "Semaine": df_filtre = df_filtre[df_filtre['date'].dt.isocalendar().week == aujourdhui.isocalendar().week]
                elif filtre_periode == "Mois": df_filtre = df_filtre[df_filtre['date'].dt.month == aujourdhui.month]
                elif filtre_periode == "Année": df_filtre = df_filtre[df_filtre['date'].dt.year == aujourdhui.year]
                
                ventes_fc_brutes = df_filtre['montant_fc'].sum() if 'montant_fc' in df_filtre.columns else 0
                ventes_usd_brutes = df_filtre['montant_usd'].sum() if 'montant_usd' in df_filtre.columns else 0
                recettes_totale_convertie_fc = ventes_fc_brutes + (ventes_usd_brutes * TAUX_JOUR)
                
                df_filtre['recette_theorique'] = df_filtre['consommation'] * df_filtre['prix_m3']
                df_filtre['recette_reelle'] = df_filtre['montant_fc'] + (df_filtre['montant_usd'] * TAUX_JOUR)
                total_ecarts_cumules = (df_filtre['recette_reelle'] - df_filtre['recette_theorique']).sum()
                
                depenses_locales_totales = df_filtre['depenses_locales_fc'].sum() if 'depenses_locales_fc' in df_filtre.columns else 0
                depots_banque_tot = df_banque['montant_fc'].sum() if not df_banque.empty and 'montant_fc' in df_banque.columns else 0
                caisse_virtuelle = recettes_totale_convertie_fc - depenses_locales_totales - depots_banque_tot
                
                kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns([1, 1, 1, 1, 1])
                kpi1.metric("Recettes Globales (FC)", f"{recettes_totale_convertie_fc:,.0f} FC", f"{ventes_usd_brutes:,.0f} $ reçus")
                kpi2.metric("Dépenses Locales", f"{depenses_locales_totales:,.0f} FC")
                kpi3.metric("Transféré Banque", f"{depots_banque_tot:,.0f} FC")
                kpi4.metric("Solde Caisse Réel", f"{caisse_virtuelle:,.0f} FC")
                
                if total_ecarts_cumules >= 0:
                    kpi5.metric("Écart Global (Surplus)", f"+{total_ecarts_cumules:,.0f} FC")
                else:
                    kpi5.metric("Écart Global (Manquant)", f"{total_ecarts_cumules:,.0f} FC")
                
                st.markdown("---")
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    st.markdown("#### 📈 Recettes Financières par Forage (FC)")
                    if not df_filtre.empty and 'montant_fc' in df_filtre.columns:
                        df_barres = df_filtre.groupby('site')['recette_reelle'].sum().reset_index()
                        fig = px.bar(df_barres, x='site', y='recette_reelle', color='recette_reelle', color_continuous_scale='Blugrn', text_auto='.0f')
                        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=280)
                        st.plotly_chart(fig, use_container_width=True)
                    else: st.info("Aucun relevé sur cette période pour générer le graphique.")
                
                with col_g2:
                    st.markdown("#### 🍩 Répartition des Dépenses Administratives")
                    if not df_depenses.empty and 'montant_fc' in df_depenses.columns:
                        fig_pie = px.pie(df_depenses, values='montant_fc', names='poste', color_discrete_sequence=px.colors.sequential.RdBu)
                        fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else: st.info("Aucune dépense administrative enregistrée.")
                
                st.markdown("---")
                st.markdown("#### 📉 Suivi Temporel de la Production d'Eau ($m^3$)")
                if not df_filtre.empty:
                    df_suivi_eau = df_filtre.groupby(['date', 'site'])['consommation'].sum().reset_index()
                    fig_eau = px.line(df_suivi_eau, x='date', y='consommation', color='site', markers=True)
                    fig_eau.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=280)
                    st.plotly_chart(fig_eau, use_container_width=True)
                
                st.markdown("#### 📋 Registre Général Synthétique")
                df_filtre_table = df_filtre.copy()
                df_filtre_table['date'] = df_filtre_table['date'].dt.strftime('%Y-%m-%d')
                df_filtre_table['Recette_Globale_FC'] = df_filtre_table['recette_reelle']
                df_filtre_table['Reste_Net_Caisse_FC'] = df_filtre_table['Recette_Globale_FC'] - df_filtre_table['depenses_locales_fc']
                st.dataframe(df_filtre_table.sort_values(by="date", ascending=False), use_container_width=True)
            else: st.info("Aucune donnée disponible.")

        # --- TAB 2 : OPERATIONS FINANCIERES & HISTORIQUES ---
        with onglet[1]:
            st.markdown("### Mouvements de Fonds Spéciaux")
            col_s1, col_s2 = st.columns([1, 1])
            with col_s1:
                st.markdown("#### 🔧 Grosses Dépenses Administrateur Structurelles")
                with st.form("form_depense_admin"):
                    poste = st.selectbox("Poste de dépense", ["Achat Carburant Groupe", "Réparation Pompe / Plomberie", "Électricité & Raccordement", "Achat Pièces de rechange", "Autres Frais"], key="adm_poste_dep_select")
                    desc_admin = st.text_area("Détails et pièces justificatives", key="adm_desc_dep_text").replace("'", " ").strip()
                    montant_admin = st.number_input("Montant (FC)", min_value=0.0, step=1000.0, key="adm_montant_dep_num")
                    if st.form_submit_button("Enregistrer Frais Structure"):
                        cursor.execute("INSERT INTO depenses_admin (date, poste, description, montant_fc, auteur) VALUES (?, ?, ?, ?, ?)", (str(datetime.now().date()), poste, desc_admin, montant_admin, st.session_state['username']))
                        conn.commit()
                        st.success("Dépense enregistrée.")
                        st.rerun()
                
                st.markdown("📂 **Historique des dépenses administratives**")
                if not df_depenses.empty:
                    st.dataframe(df_depenses.sort_values(by="id", ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.info("Aucune dépense administrative enregistrée pour le moment.")

            with col_s2:
                st.markdown("#### 🏦 Versements / Dépôts en Banque")
                with st.form("form_banque"):
                    site_provenance = st.selectbox("Forage émetteur", list(df_relevies['site'].unique()) if not df_relevies.empty else ["Aucun Site"], key="bnq_site_em_select")
                    montant_banque = st.number_input("Somme versée (FC)", min_value=0.0, step=5000.0, key="bnq_montant_num")
                    banque_cible = st.text_input("Banque", value="Rawbank", key="bnq_cible_text").replace("'", " ").strip()
                    if st.form_submit_button("Confirmer le transfert Banque"):
                        cursor.execute("INSERT INTO banque (date, site, montant_fc, banque_cible, auteur) VALUES (?, ?, ?, ?, ?)", (str(datetime.now().date()), site_provenance, montant_banque, banque_cible, st.session_state['username']))
                        conn.commit()
                        st.success("Transfert validé.")
                        st.rerun()
                
                st.markdown("📂 **Historique des flux vers la Banque**")
                if not df_banque.empty:
                    st.dataframe(df_banque.sort_values(by="id", ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.info("Aucun dépôt bancaire enregistré pour le moment.")

        # --- TAB 3 : CONFIGURATION ---
        with onglet[2]:
            st.markdown("### ⚙️ Configuration & Paramètres Structurels")
            with st.form("form_taux"):
                nouveau_taux = st.number_input("Taux (1 USD = ? FC)", min_value=1000.0, value=TAUX_JOUR, step=10.0, key="cfg_taux_input_num")
                if st.form_submit_button("Sauvegarder le Taux"):
                    cursor.execute("UPDATE parametres SET taux_usd_fc = ? WHERE id = 1", (nouveau_taux,))
                    conn.commit()
                    st.success("Taux mis à jour.")
                    st.rerun()
            
            st.markdown("---")
            col_site1, col_site2 = st.columns([1, 2])
            with col_site1:
                st.markdown("#### ➕ Ajouter un Forage")
                with st.form("form_creer_site"):
                    nouveau_nom_site = st.text_input("Nom du Forage", key="cfg_add_site_name_text").replace("'", " ").strip()
                    if st.form_submit_button("Créer le Forage") and nouveau_nom_site:
                        try:
                            cursor.execute("INSERT INTO sites (nom_site) VALUES (?)", (nouveau_nom_site,))
                            conn.commit()
                            st.success("Site créé.")
                            st.rerun()
                        except sqlite3.IntegrityError: st.error("Ce site existe déjà.")
            with col_site2:
                st.markdown("#### 📋 Liste des Forages")
                if not df_sites_db.empty:
                    for idx_s, row_s in df_sites_db.iterrows():
                        with st.expander(f"📍 ID {row_s['id']} : {row_s['nom_site']}"):
                            with st.form(f"form_edit_site_{row_s['id']}"):
                                modif_nom_site = st.text_input("Modifier le nom", value=row_s['nom_site'], key=f"text_edit_site_name_{row_s['id']}").replace("'", " ").strip()
                                cb1, cb2 = st.columns(2)
                                if cb1.form_submit_button("💾 Sauvegarder", key=f"sv_{row_s['id']}"):
                                    cursor.execute("UPDATE sites SET nom_site = ? WHERE id = ?", (modif_nom_site, int(row_s['id'])))
                                    conn.commit()
                                    st.rerun()
                                if cb2.form_submit_button("🗑️ Supprimer", key=f"sp_{row_s['id']}"):
                                    cursor.execute("DELETE FROM sites WHERE id = ?", (int(row_s['id']),))
                                    conn.commit()
                                    st.rerun()

            st.markdown("---")
            col_c1, col_c2 = st.columns([1, 2])
            with col_c1:
                st.markdown("#### ➕ Créer un compte")
                with st.form("form_creation_compte"):
                    nouveau_username = st.text_input("Nom de l'agent", key="cfg_create_user_name_text").replace("'", " ").strip()
                    nouveau_password = st.text_input("Mot de passe", type="password", key="cfg_create_user_pass_text")
                    nouveau_role = st.selectbox("Rôle", ["Super Admin", "Manager", "Vendeur"], key="cfg_create_user_role_select")
                    site_lier = st.selectbox("Assignation Forage", ["Tous"] + liste_des_sites, key="cfg_create_user_site_select")
                    if st.form_submit_button("Créer l'utilisateur") and nouveau_username:
                        try:
                            secure_password = crypter_mot_de_passe(nouveau_password.strip())
                            cursor.execute("INSERT INTO utilisateurs (username, password, role, site_associe) VALUES (?, ?, ?, ?)", (nouveau_username, secure_password, nouveau_role, site_lier))
                            conn.commit()
                            st.success("Utilisateur créé avec mot de passe sécurisé.")
                            st.rerun()
                        except sqlite3.IntegrityError: st.error("Identifiant indisponible.")
            with col_c2:
                st.markdown("#### 📋 Comptes Actifs")
                for index, u_row in df_utilisateurs.iterrows():
                    with st.expander(f"👤 {u_row['username']} — [{u_row['role']}]"):
                        with st.form(f"edit_form_{u_row['id']}"):
                            edit_password = st.text_input("Changer le mot de passe (Laisser vide si inchangé)", type="password", key=f"text_edit_user_pass_{u_row['id']}")
                            edit_site = st.selectbox("Forage rattaché", ["Tous"] + liste_des_sites, index=0, key=f"select_edit_user_site_{u_row['id']}")
                            b_sauve, b_suppr = st.columns(2)
                            if b_sauve.form_submit_button("💾 Enregistrer", key=f"us_{u_row['id']}"):
                                if edit_password.strip() != "":
                                    secure_pass = crypter_mot_de_passe(edit_password.strip())
                                    cursor.execute("UPDATE utilisateurs SET password = ?, site_associe = ? WHERE id = ?", (secure_pass, edit_site, int(u_row['id'])))
                                else:
                                    cursor.execute("UPDATE utilisateurs SET site_associe = ? WHERE id = ?", (edit_site, int(u_row['id'])))
                                conn.commit()
                                st.success("Modifications enregistrées.")
                                st.rerun()
                            if b_suppr.form_submit_button("🗑️ Supprimer", key=f"ud_{u_row['id']}"):
                                if u_row['username'].lower() == 'gilbert': 
                                    st.error("Action interdite sur l'administrateur racine.")
                                else:
                                    cursor.execute("DELETE FROM utilisateurs WHERE id = ?", (int(u_row['id']),))
                                    conn.commit()
                                    st.rerun()

        # --- TAB 4 : MESSAGERIE ---
        with onglet[3]:
            col_ach1, col_ach2 = st.columns([2, 1])
            with col_ach1: st.markdown("### 💬 Centre de discussion avec les Vendeurs")
            with col_ach2:
                if st.button("🔄 Actualiser les messages", key="ref_chat_a"): st.rerun()
            
            col_ch1, col_ch2 = st.columns([2, 1])
            with col_ch1:
                df_chat_admin = pd.read_sql_query("SELECT * FROM chat_interne ORDER BY id DESC LIMIT 50", conn)
                admin_chat_box = "<div class='chat-box' style='max-height: 500px;'> "
                for idx, row_ca in df_chat_admin.iloc[::-1].iterrows():
                    classe_bulle = "chat-msg-vendeur" if row_ca['role'] == 'Vendeur' else "chat-msg-admin"
                    align = "text-align: right;" if row_ca['expediteur'] == st.session_state['username'] else "text-align: left;"
                    admin_chat_box += f"<div class='chat-msg {classe_bulle}' style='{align}'><b>{row_ca['expediteur']}</b> ({row_ca['role']}) - <small>{row_ca['date_heure']}</small> :<br>{row_ca['message']}</div>"
                admin_chat_box += "</div>"
                st.markdown(admin_chat_box, unsafe_allow_html=True)
                
                with st.form("send_msg_admin", clear_on_submit=True):
                    a_msg = st.text_input("Répondre aux équipes...", key="chat_admin_input_text_final_v4").replace("'", " ").strip()
                    if st.form_submit_button("✉️ Envoyer la réponse") and a_msg:
                        cursor.execute("INSERT INTO chat_interne (date_heure, expediteur, role, message) VALUES (?, ?, ?, ?)", (datetime.now().strftime('%Y-%m-%d %H:%M'), st.session_state['username'], st.session_state['role'], a_msg))
                        conn.commit()
                        st.rerun()

        # --- TAB 5 : MODERATION ---
        with onglet[4]:
            st.markdown("### Modérations du Registre & Maintenance")
            if not df_relevies.empty:
                for index, row in df_relevies.iterrows():
                    with st.expander(f"⚙️ Action Relevé ID {row['id']} — {row['site']}"):
                        if st.session_state['role'] == 'Super Admin':
                            if st.button(f"🗑️ Supprimer l'entrée {row['id']}", key=f"del_{row['id']}"):
                                cursor.execute("DELETE FROM rapports WHERE id = ?", (int(row['id']),))
                                conn.commit()
                                st.success("Entrée supprimée.")
                                st.rerun()
            else: st.info("Aucun historique disponible.")
                
            if st.session_state['role'] == 'Super Admin':
                st.markdown("---")
                st.markdown("<h3 style='color: #DC2626;'>⚠️ Zone de Danger</h3>", unsafe_allow_html=True)
                check_confirmation = st.checkbox("Je confirme vouloir effacer l'intégralité des données du logiciel", key="danger_zone_checkbox_confirm")
                if check_confirmation and st.button("🔥 Exécuter la réinitialisation totale", key="btn_execute_hard_reset"):
                    cursor.execute("DELETE FROM rapports;"); cursor.execute("DELETE FROM depenses_admin;"); cursor.execute("DELETE FROM banque;"); cursor.execute("DELETE FROM chat_interne;")
                    conn.commit()
                    st.success("Logiciel réinitialisé.")
                    st.rerun()
                    
    conn.close()
else:
    st.info("👋 Veuillez entrer vos accès dans la barre latérale pour ouvrir l'application mobile general410.")