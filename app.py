import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client

st.set_page_config(page_title="Maul Biler - Elbiler B2B", layout="wide", page_icon="⚡")

hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# ⚙️ INDSTILLINGER
# ==========================================
WHATSAPP_NUMBER = "4561438202"

# ==========================================
# 🔌 SUPABASE FORBINDELSE
# ==========================================
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

@st.cache_data(ttl=60)
def load_b2b_data():
    """Henter kun aktive elbiler fra Supabase b2b_lager."""
    try:
        res = supabase.table("b2b_lager") \
            .select("*") \
            .eq("status", "Aktiv") \
            .eq("drivmiddel", "Elektrisk") \
            .execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Kunne ikke hente data: {e}")
        return pd.DataFrame()

def safe(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()

# ==========================================
# 🛒 SESSION STATE (PAKKEKØB / KURV)
# ==========================================
if 'cart' not in st.session_state:
    st.session_state['cart'] = {}

# ==========================================
# 📦 SIDEMENU (DIN PAKKE)
# ==========================================
with st.sidebar:
    st.header("📦 Din Pakke (Pakkekøb)")
    if not st.session_state['cart']:
        st.info("Klik på '➕ Tilføj til pakke' under bilerne for at samle et parti og give et samlet bud.")
    else:
        total_list_price = 0
        total_bid_price  = 0
        cart_text_lines  = []

        st.write("**Dine bud pr. bil:**")
        for key, car in st.session_state['cart'].items():
            total_list_price += car['price_int']
            current_bid = car.get('bid_price', car['price_int'])
            listepris_str = f"kr. {car['price_int']:,}".replace(',', '.')
            new_bid = st.number_input(
                f"{car['title']} (Listepris: {listepris_str})",
                min_value=0, value=int(current_bid), step=1000,
                key=f"bid_{key}"
            )
            st.session_state['cart'][key]['bid_price'] = new_bid
            total_bid_price += new_bid
            bid_str = f"kr. {new_bid:,}".replace(',', '.')
            cart_text_lines.append(f"- {car['title']} (VIN: {car['vin']}) -> Mit bud: {bid_str}")

        st.write("---")
        st.write(f"**Samlet listepris:** kr. {total_list_price:,}".replace(',', '.'))
        st.write("**Dit samlede bud:**")
        st.markdown(f"<h3 style='color:#2e7b32;margin-top:-10px;'>kr. {total_bid_price:,}</h3>".replace(',', '.'), unsafe_allow_html=True)
        st.write("---")

        cars_str      = "\n".join(cart_text_lines)
        total_bid_str = f"kr. {total_bid_price:,}".replace(',', '.')
        mail_body = (
            f"Hej Mathias og Brian,\n\n"
            f"Jeg vil gerne give følgende bud på {len(st.session_state['cart'])} biler i en pakkehandel:\n\n"
            f"{cars_str}\n\nSamlet bud: {total_bid_str}\n\nVenlig hilsen,"
        )
        mail_link = f"mailto:matsc@maulbiler.dk,brmau@maulbiler.dk?subject=Samlet bud på {len(st.session_state['cart'])} biler&body={urllib.parse.quote(mail_body)}"
        wa_link   = f"https://wa.me/{WHATSAPP_NUMBER}?text={urllib.parse.quote(mail_body)}"

        st.markdown(f"<a href='{mail_link}' target='_blank'><button style='width:100%;border-radius:5px;background:#2e7b32;color:white;border:none;padding:10px;cursor:pointer;font-size:14px;font-weight:bold;margin-bottom:8px;'>✉️ Send samlet bud (Mail)</button></a>", unsafe_allow_html=True)
        st.markdown(f"<a href='{wa_link}'   target='_blank'><button style='width:100%;border-radius:5px;background:#25D366;color:white;border:none;padding:10px;cursor:pointer;font-size:14px;font-weight:bold;margin-bottom:20px;'>💬 Send samlet bud (WA)</button></a>", unsafe_allow_html=True)

        if st.button("🗑️ Ryd pakken", use_container_width=True):
            st.session_state['cart'] = {}
            st.rerun()

# ==========================================
# TITEL
# ==========================================
st.title("⚡ Maul Biler - B2B Elbiler")
st.write("Velkommen til vores danske B2B portal. Her finder du vores aktuelle elbiler klar til handel.")

# ==========================================
# 🔍 DETAIL-DIALOG
# ==========================================
@st.dialog("📸 Se billeder & detaljer", width="large")
def show_car_details(row):
    status_dk = safe(row.get('status_dk'))
    if status_dk and status_dk.lower() not in ['aktiv', '']:
        if "vej" in status_dk.lower():
            st.markdown(f"**Status:** ⏳ {status_dk}")
        else:
            st.markdown(f"**Status:** 🟢 {status_dk}")

    st.markdown(f"## {safe(row.get('maerke'))} {safe(row.get('model'))}")
    st.markdown(f"#### {safe(row.get('variant'))}")
    st.write("")

    pris_int = int(row.get('pris_dkk') or 0)
    pris_display = f"kr. {pris_int:,}".replace(',', '.') if pris_int > 0 else "Giv et bud"

    m1, m2, m3 = st.columns(3)
    m1.metric("Årgang",    safe(row.get('aargang')))
    m2.metric("Kilometer", safe(row.get('odometer')))
    m3.metric("Pris (DKK)", pris_display)

    st.write("---")

    pdf_url      = safe(row.get('udstyrsliste_pdf'))
    skade_string = safe(row.get('skadesbilleder_url'))
    has_pdf      = bool(pdf_url)
    has_skader   = bool(skade_string)

    if has_pdf or has_skader:
        tab1, tab2, tab3 = st.tabs(["📸 Billeder", "⚙️ Teknisk Data", "⚠️ Skader & Udstyr"])
    else:
        tab1, tab2 = st.tabs(["📸 Billeder", "⚙️ Teknisk Data"])

    with tab1:
        img_string = safe(row.get('billede_url'))
        images = [u.strip() for u in img_string.split(',')] if img_string else []
        if images:
            for img in images:
                if img.startswith('http'):
                    st.image(img, use_container_width=True)
                    st.write("---")
        else:
            st.info("Ingen billeder tilgængelige endnu.")

    with tab2:
        c1, c2 = st.columns(2)
        c1.write(f"**Mærke:** {safe(row.get('maerke'))}")
        c1.write(f"**Model:** {safe(row.get('model'))}")
        c1.write(f"**Variant:** {safe(row.get('variant'))}")
        c1.write(f"**Gearkasse:** {safe(row.get('gearkasse'))}")
        c1.write(f"**Drivmiddel:** {safe(row.get('drivmiddel'))}")
        c1.write(f"**Antal lakfelter:** {safe(row.get('lakfelter'))}")
        c2.write(f"**EURO norm:** {safe(row.get('euro_norm'))}")
        c2.write(f"**CO2-udslip:** {safe(row.get('co2'))}")
        c2.write(f"**Reg. nr.:** {safe(row.get('reg_nr'))}")
        c2.write(f"**Stelnummer:** {safe(row.get('stelnummer'))}")
        c2.write(f"**Lokation:** {safe(row.get('lokation'))}")
        c1.write("---")
        c2.write("---")
        c1.write(f"**Moms:** {safe(row.get('moms_status'))}")
        c2.write(f"**Afgift:** {safe(row.get('afgift_status'))}")
        st.write("---")
        st.write("**Udstyr & Bemærkninger:**")
        udstyr_val = safe(row.get('udstyr'))
        st.info(udstyr_val if udstyr_val else "Ingen bemærkninger.")

    if has_pdf or has_skader:
        with tab3:
            if has_pdf:
                st.subheader("📄 Udstyrsliste")
                st.markdown(f"<a href='{pdf_url}' target='_blank'><button style='width:100%;border-radius:5px;background:#3b82f6;color:white;border:none;padding:10px;cursor:pointer;font-size:15px;font-weight:bold;margin-bottom:20px;'>Åbn Udstyrsliste (PDF)</button></a>", unsafe_allow_html=True)
            if has_skader:
                st.subheader("⚠️ Noterede Skader")
                st.info("Billeder herunder viser de specifikke kosmetiske skader noteret på bilen.")
                for img in [u.strip() for u in skade_string.split(',')]:
                    if img.startswith('http'):
                        st.image(img, use_container_width=True)
                        st.write("---")

    st.write("---")
    vin          = safe(row.get('stelnummer')) or 'Ukendt'
    maerke_model = f"{safe(row.get('maerke'))} {safe(row.get('model'))}"
    modtagere    = "matsc@maulbiler.dk,brmau@maulbiler.dk"

    mail_link_koeb = f"mailto:{modtagere}?subject={urllib.parse.quote(f'Køb af {maerke_model} (VIN: {vin})')}&body={urllib.parse.quote(f'Hej Mathias og Brian,\n\nJeg vil gerne købe bilen til den annoncerede pris.\n\nStelnummer: {vin}')}"
    mail_link_byd  = f"mailto:{modtagere}?subject={urllib.parse.quote(f'Bud på {maerke_model} (VIN: {vin})')}&body={urllib.parse.quote(f'Hej Mathias og Brian,\n\nJeg vil gerne give et bud på bilen.\n\nMit bud er: [Indtast dit bud her] kr.\n\nStelnummer: {vin}')}"

    btn1, btn2 = st.columns(2)
    btn1.markdown(f"<a href='{mail_link_koeb}' target='_blank'><button style='width:100%;border-radius:5px;background:#2e7b32;color:white;border:none;padding:12px;cursor:pointer;font-size:16px;font-weight:bold;'>🛒 Køb</button></a>", unsafe_allow_html=True)
    btn2.markdown(f"<a href='{mail_link_byd}'  target='_blank'><button style='width:100%;border-radius:5px;background:#555555;color:white;border:none;padding:12px;cursor:pointer;font-size:16px;font-weight:bold;'>⚖️ Byd</button></a>", unsafe_allow_html=True)

# ==========================================
# HOVEDPROGRAM
# ==========================================
df = load_b2b_data()

if df is not None and not df.empty:

    # Sorteringskolonner
    df['Sort_Price'] = pd.to_numeric(df['pris_dkk'], errors='coerce').fillna(0)
    df['Sort_Year']  = pd.to_numeric(df['aargang'].astype(str).str[:4], errors='coerce').fillna(0)
    df['Sort_Km']    = pd.to_numeric(df['odometer'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(9999999)

    # --- FILTRE ---
    c_search, c_moms, c_afgift, c_sort = st.columns(4)
    search_q = c_search.text_input("🔍 Søg mærke/model")

    moms_opts   = ["Alle"] + sorted(df['moms_status'].dropna().unique().tolist())
    afgift_opts = ["Alle"] + sorted(df['afgift_status'].dropna().unique().tolist())
    moms_q   = c_moms.selectbox("🏷️ Moms",   moms_opts)
    afgift_q = c_afgift.selectbox("⚖️ Afgift", afgift_opts)

    sort_opts_map = {
        "Nyeste tilføjet (Standard)": "default",
        "Pris: Lav til Høj":          "price_asc",
        "Pris: Høj til Lav":          "price_desc",
        "Årgang: Nyeste først":        "year_desc",
        "Kilometer: Lavest først":     "km_asc",
    }
    sort_q = sort_opts_map[c_sort.selectbox("🔽 Sorter efter", list(sort_opts_map.keys()))]

    if search_q:  df = df[df.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]
    if moms_q   != "Alle": df = df[df['moms_status']   == moms_q]
    if afgift_q != "Alle": df = df[df['afgift_status'] == afgift_q]

    if sort_q == "price_asc":  df = df.sort_values('Sort_Price', ascending=True)
    elif sort_q == "price_desc": df = df.sort_values('Sort_Price', ascending=False)
    elif sort_q == "year_desc":  df = df.sort_values('Sort_Year',  ascending=False)
    elif sort_q == "km_asc":     df = df.sort_values('Sort_Km',    ascending=True)

    st.write("---")

    # --- KORT VISNING ---
    cols_per_row = 3
    for i in range(0, len(df), cols_per_row):
        cols  = st.columns(cols_per_row)
        chunk = df.iloc[i:i + cols_per_row]

        for col, (_, row) in zip(cols, chunk.iterrows()):
            with col:
                with st.container(border=True):

                    # Status-badge
                    status_dk = safe(row.get('status_dk'))
                    if status_dk and status_dk.lower() not in ['aktiv', 'på lager', '']:
                        if "vej" in status_dk.lower():
                            st.markdown(f"<div style='background:#fff3cd;color:#856404;padding:3px 8px;border-radius:3px;font-size:12px;font-weight:bold;width:fit-content;margin-bottom:5px;'>⏳ {status_dk}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='background:#d4edda;color:#155724;padding:3px 8px;border-radius:3px;font-size:12px;font-weight:bold;width:fit-content;margin-bottom:5px;'>🟢 {status_dk}</div>", unsafe_allow_html=True)

                    # Cover-billede
                    first_img = safe(row.get('billede_url', '')).split(',')[0].strip()
                    if first_img.startswith('http'):
                        st.image(first_img, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/400x250?text=Intet+billede", use_container_width=True)

                    # Titel
                    st.markdown(f"### {safe(row.get('maerke'))} {safe(row.get('model'))}")
                    st.markdown(f"*{safe(row.get('variant'))}*")

                    # Stelnummer (NY)
                    stel = safe(row.get('stelnummer'))
                    if stel:
                        st.caption(f"🔑 {stel}")

                    st.write("")

                    # Tekniske specs
                    aarstal = safe(row.get('aargang'))[:4]
                    km_str  = safe(row.get('odometer'))
                    gear    = safe(row.get('gearkasse'))
                    fuel    = safe(row.get('drivmiddel'))
                    st.markdown(f"📅 **{aarstal}** &nbsp; | &nbsp; 🛣️ **{km_str}** <br> 🕹️ **{gear}** &nbsp; | &nbsp; ⚡ **{fuel}**", unsafe_allow_html=True)
                    st.markdown(f"🏷️ {safe(row.get('moms_status'))} &nbsp; | &nbsp; ⚖️ {safe(row.get('afgift_status'))}")

                    # Udstyr/Bemærkninger (NY)
                    udstyr_val = safe(row.get('udstyr'))
                    if udstyr_val:
                        with st.expander("🔧 Udstyr & bemærkninger"):
                            st.write(udstyr_val)

                    # Pris
                    pris_int = int(row.get('Sort_Price', 0))
                    st.write("---")
                    pris_display = f"kr. {pris_int:,}".replace(',', '.') if pris_int > 0 else "Giv et bud"
                    if pris_int > 0:
                        st.markdown(f"<h2 style='text-align:center;color:#2e7b32;font-weight:bold;'>{pris_display}</h2>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<h2 style='text-align:center;'>{pris_display}</h2>", unsafe_allow_html=True)

                    # Detalje-knap
                    if st.button("📸 Se detaljer & billeder", key=f"view_{row.name}", use_container_width=True):
                        show_car_details(row)

                    # Køb / Byd knapper
                    vin          = stel or str(row.name)
                    maerke_model = f"{safe(row.get('maerke'))} {safe(row.get('model'))}"
                    modtagere    = "matsc@maulbiler.dk,brmau@maulbiler.dk"

                    mail_link_koeb = f"mailto:{modtagere}?subject={urllib.parse.quote(f'Køb af {maerke_model} (VIN: {vin})')}&body={urllib.parse.quote(f'Hej Mathias og Brian,\n\nJeg vil gerne købe bilen til den annoncerede pris.\n\nStelnummer: {vin}')}"
                    mail_link_byd  = f"mailto:{modtagere}?subject={urllib.parse.quote(f'Bud på {maerke_model} (VIN: {vin})')}&body={urllib.parse.quote(f'Hej Mathias og Brian,\n\nJeg vil gerne give et bud på bilen.\n\nMit bud er: [Indtast dit bud her] kr.\n\nStelnummer: {vin}')}"

                    c_btn1, c_btn2 = st.columns(2)
                    c_btn1.markdown(f"<a href='{mail_link_koeb}' target='_blank'><button style='width:100%;border-radius:5px;background:#2e7b32;color:white;border:none;padding:6px;cursor:pointer;font-size:14px;font-weight:bold;'>🛒 Køb</button></a>", unsafe_allow_html=True)
                    c_btn2.markdown(f"<a href='{mail_link_byd}'  target='_blank'><button style='width:100%;border-radius:5px;background:#555555;color:white;border:none;padding:6px;cursor:pointer;font-size:14px;font-weight:bold;'>⚖️ Byd</button></a>", unsafe_allow_html=True)

                    # Pakkekøb
                    st.write("")
                    vin_key = vin
                    if vin_key in st.session_state['cart']:
                        if st.button("➖ Fjern fra pakke", key=f"rm_{row.name}", use_container_width=True):
                            del st.session_state['cart'][vin_key]
                            st.rerun()
                    else:
                        if st.button("➕ Tilføj til pakke", key=f"add_{row.name}", use_container_width=True):
                            st.session_state['cart'][vin_key] = {
                                'title':     maerke_model,
                                'price_int': pris_int,
                                'price_str': pris_display,
                                'vin':       vin,
                                'bid_price': pris_int,
                            }
                            st.rerun()
else:
    st.info("Der er i øjeblikket ingen aktive elbiler til salg på portalen.")
