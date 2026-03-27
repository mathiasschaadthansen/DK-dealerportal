import streamlit as st
import pandas as pd
import urllib.parse

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
# ⚙️ INDSTILLINGER (WHATSAPP NUMMER)
# ==========================================
WHATSAPP_NUMBER = "4561438202" 

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
        total_bid_price = 0
        cart_text_lines = []
        
        st.write("**Dine bud pr. bil:**")
        for key, car in st.session_state['cart'].items():
            total_list_price += car['price_int']
            
            # Hent nuværende bud (eller listepris som standard)
            current_bid = car.get('bid_price', car['price_int'])
            
            # Input-felt til forhandlerens eget bud
            listepris_str = f"kr. {car['price_int']:,}".replace(',', '.')
            new_bid = st.number_input(
                f"{car['title']} (Listepris: {listepris_str})",
                min_value=0,
                value=int(current_bid),
                step=1000,
                key=f"bid_{key}"
            )
            
            # Opdater kurven med det nye bud
            st.session_state['cart'][key]['bid_price'] = new_bid
            total_bid_price += new_bid
            
            # Formater bud til teksten
            bid_str = f"kr. {new_bid:,}".replace(',', '.')
            cart_text_lines.append(f"- {car['title']} (VIN: {car['vin']}) -> Mit bud: {bid_str}")
            
        st.write("---")
        st.write(f"**Samlet listepris:** kr. {total_list_price:,}".replace(',', '.'))
        st.write("**Dit samlede bud:**")
        st.markdown(f"<h3 style='color: #2e7b32; margin-top:-10px;'>kr. {total_bid_price:,}</h3>".replace(',', '.'), unsafe_allow_html=True)
        
        st.write("---")
        cars_str = "\n".join(cart_text_lines)
        total_bid_str = f"kr. {total_bid_price:,}".replace(',', '.')
        
        mail_body = f"Hej Mathias og Brian,\n\nJeg vil gerne give følgende bud på {len(st.session_state['cart'])} biler i en pakkehandel:\n\n{cars_str}\n\nSamlet bud: {total_bid_str}\n\nVenlig hilsen,"
        
        mail_link = f"mailto:matsc@maulbiler.dk,brmau@maulbiler.dk?subject=Samlet bud på {len(st.session_state['cart'])} biler&body={urllib.parse.quote(mail_body)}"
        wa_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={urllib.parse.quote(mail_body)}"
        
        st.markdown(f"<a href='{mail_link}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #2e7b32; color: white; border: none; padding: 10px; cursor: pointer; font-size: 14px; font-weight: bold; margin-bottom: 8px;'>✉️ Send samlet bud (Mail)</button></a>", unsafe_allow_html=True)
        st.markdown(f"<a href='{wa_link}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #25D366; color: white; border: none; padding: 10px; cursor: pointer; font-size: 14px; font-weight: bold; color: white; margin-bottom: 20px;'>💬 Send samlet bud (WA)</button></a>", unsafe_allow_html=True)
        
        if st.button("🗑️ Ryd pakken", use_container_width=True):
            st.session_state['cart'] = {}
            st.rerun()

st.title("⚡ Maul Biler - B2B Elbiler")
st.write("Velkommen til vores danske B2B portal. Her finder du vores aktuelle elbiler klar til handel.")

@st.cache_data(ttl=60)
def load_b2b_data():
    sheet_id = "1Tx8pe8tgo0qpoiTcrTo6kbVZwkx5_uMYaoeYf3mJP6M" 
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try: return pd.read_csv(url)
    except: return None

# --- BILLEDE & DATA FREMVISER (POP-UP) ---
@st.dialog("📸 Se billeder & detaljer", width="large")
def show_car_details(row):
    
    status_dk = str(row.get('Status DK', row.get('Status.1', row.get('Status', '')))).strip()
    if status_dk and status_dk != 'nan' and status_dk != 'Aktiv':
        if "vej" in status_dk.lower():
            st.markdown(f"**Status:** ⏳ {status_dk}")
        else:
            st.markdown(f"**Status:** 🟢 {status_dk}")
            
    st.markdown(f"## {row.get('Mærke', '')} {row.get('Model', '')}")
    st.markdown(f"#### {row.get('Variant', '')}")
    st.write("")
    
    aarstal = str(row.get('Årgang', '-'))[:4]
    km_str = str(row.get('Odometer', '-'))
    
    try: 
        p_str = str(row.get('Pris DKK', '0')).strip()
        if p_str.endswith('.0'): p_str = p_str[:-2] 
        p_clean = "".join(filter(str.isdigit, p_str)) 
        pris_int = int(p_clean) if p_clean else 0
    except: 
        pris_int = 0
        
    pris_display = f"kr. {pris_int:,}".replace(',', '.') if pris_int > 0 else "Giv et bud"

    m1, m2, m3 = st.columns(3)
    m1.metric("Årgang", aarstal)
    m2.metric("Kilometer", km_str)
    m3.metric("Pris (DKK)", pris_display)
    
    st.write("---")
    
    tab1, tab2 = st.tabs(["📸 Billeder", "⚙️ Teknisk Data"])
    
    with tab1:
        img_string = str(row.get('Billede URL', ''))
        images = [url.strip() for url in img_string.split(',')] if img_string and img_string != 'nan' else []
        if images:
            for img in images:
                if img.startswith('http'):
                    st.image(img, use_container_width=True)
                    st.write("---")
        else:
            st.info("Ingen billeder tilgængelige endnu.")
            
    with tab2: 
        c1, c2 = st.columns(2)
        c1.write(f"**Mærke:** {row.get('Mærke', '-')}")
        c1.write(f"**Model:** {row.get('Model', '-')}")
        c1.write(f"**Variant:** {row.get('Variant', '-')}")
        c1.write(f"**Gearkasse:** {row.get('Gearkasse', '-')}")
        c1.write(f"**Drivmiddel:** {row.get('Drivmiddel', '-')}")
        c1.write(f"**Antal lakfelter:** {row.get('Antal lakfelter', '-')}")
        
        c2.write(f"**EURO norm:** {row.get('EURO norm', '-')}")
        c2.write(f"**CO2-udslip:** {row.get('CO2-udslip', '-')}")
        c2.write(f"**Reg. nr.:** {row.get('Reg. nr.', '-')}")
        c2.write(f"**Stelnummer:** {row.get('Stelnummer', '-')}")
        c2.write(f"**Lokation:** {row.get('Lokation', '-')}")
        
        c1.write("---")
        c2.write("---")
        c1.write(f"**Moms:** {row.get('Moms status', '-')}")
        c2.write(f"**Afgift:** {row.get('Afgift status', '-')}")
        
        st.write("---")
        st.write("**Udstyr & Bemærkninger:**")
        st.info(row.get('Udstyr/Bemærkninger', 'Ingen bemærkninger.'))
        
    st.write("---")
    
    vin = str(row.get('Stelnummer', 'Ukendt'))
    mærke_model = f"{row.get('Mærke', '')} {row.get('Model', '')}"
    modtagere = "matsc@maulbiler.dk,brmau@maulbiler.dk"
    
    emne_koeb = urllib.parse.quote(f"Køb af {mærke_model} (VIN: {vin})")
    tekst_koeb = urllib.parse.quote(f"Hej Mathias og Brian,\n\nJeg vil gerne købe bilen til den annoncerede pris.\n\nStelnummer: {vin}")
    mail_link_koeb = f"mailto:{modtagere}?subject={emne_koeb}&body={tekst_koeb}"
    
    emne_byd = urllib.parse.quote(f"Bud på {mærke_model} (VIN: {vin})")
    tekst_byd = urllib.parse.quote(f"Hej Mathias og Brian,\n\nJeg vil gerne give et bud på bilen.\n\nMit bud er: [Indtast dit bud her] kr.\n\nStelnummer: {vin}")
    mail_link_byd = f"mailto:{modtagere}?subject={emne_byd}&body={tekst_byd}"
    
    btn_col1, btn_col2 = st.columns(2)
    btn_col1.markdown(f"<a href='{mail_link_koeb}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #2e7b32; color: white; border: none; padding: 12px; cursor: pointer; font-size: 16px; font-weight: bold;'>🛒 Køb</button></a>", unsafe_allow_html=True)
    btn_col2.markdown(f"<a href='{mail_link_byd}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #555555; color: white; border: none; padding: 12px; cursor: pointer; font-size: 16px; font-weight: bold;'>⚖️ Byd</button></a>", unsafe_allow_html=True)

# --- HOVEDPROGRAM ---
df_b2b = load_b2b_data()

if df_b2b is not None and not df_b2b.empty:
    
    status_cols = [c for c in df_b2b.columns if 'Status' in c and c not in ['Moms status', 'Afgift status', 'Status DK']]
    if status_cols:
        active_col = status_cols[-1] 
        df_b2b = df_b2b[df_b2b[active_col].astype(str).str.strip().str.lower() == 'aktiv']
    
    if 'Drivmiddel' in df_b2b.columns:
        df_b2b = df_b2b[df_b2b['Drivmiddel'].astype(str).str.strip().str.lower().isin(['elektrisk', 'el', 'elbil', 'elbiler'])]
    
    if df_b2b.empty:
        st.info("Der er i øjeblikket ingen aktive elbiler til salg på portalen.")
    else:
        df_b2b['Sort_Price'] = pd.to_numeric(df_b2b['Pris DKK'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
        df_b2b['Sort_Year'] = pd.to_numeric(df_b2b['Årgang'].astype(str).str[:4], errors='coerce').fillna(0)
        df_b2b['Sort_Km'] = pd.to_numeric(df_b2b['Odometer'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(9999999)

        c_search, c_moms, c_afgift, c_sort = st.columns(4)
        
        search_q = c_search.text_input("🔍 Søg mærke/model")
        
        moms_opts = ["Alle"] + list(df_b2b['Moms status'].dropna().unique()) if 'Moms status' in df_b2b.columns else ["Alle"]
        moms_q = c_moms.selectbox("🏷️ Moms", moms_opts)
        
        afgift_opts = ["Alle"] + list(df_b2b['Afgift status'].dropna().unique()) if 'Afgift status' in df_b2b.columns else ["Alle"]
        afgift_q = c_afgift.selectbox("⚖️ Afgift", afgift_opts)
        
        sort_opts_map = {
            "Nyeste tilføjet (Standard)": "default",
            "Pris: Lav til Høj": "price_asc",
            "Pris: Høj til Lav": "price_desc",
            "Årgang: Nyeste først": "year_desc",
            "Kilometer: Lavest først": "km_asc"
        }
        sort_q_label = c_sort.selectbox("🔽 Sorter efter", list(sort_opts_map.keys()))
        sort_q = sort_opts_map[sort_q_label]

        if search_q: df_b2b = df_b2b[df_b2b.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]
        if moms_q != "Alle": df_b2b = df_b2b[df_b2b['Moms status'] == moms_q]
        if afgift_q != "Alle": df_b2b = df_b2b[df_b2b['Afgift status'] == afgift_q]
        
        if sort_q == "price_asc": df_b2b = df_b2b.sort_values('Sort_Price', ascending=True)
        elif sort_q == "price_desc": df_b2b = df_b2b.sort_values('Sort_Price', ascending=False)
        elif sort_q == "year_desc": df_b2b = df_b2b.sort_values('Sort_Year', ascending=False)
        elif sort_q == "km_asc": df_b2b = df_b2b.sort_values('Sort_Km', ascending=True)

        st.write("---")
        
        cols_per_row = 3
        for i in range(0, len(df_b2b), cols_per_row):
            cols = st.columns(cols_per_row)
            chunk = df_b2b.iloc[i:i+cols_per_row]
            
            for col, (_, row) in zip(cols, chunk.iterrows()):
                with col:
                    with st.container(border=True):
                        
                        status_dk = str(row.get('Status DK', row.get('Status.1', row.get('Status', '')))).strip()
                        if status_dk and status_dk != 'nan' and status_dk != 'Aktiv':
                            if "vej" in status_dk.lower():
                                st.markdown(f"<div style='background-color:#fff3cd; color:#856404; padding:3px 8px; border-radius:3px; font-size:12px; font-weight:bold; width: fit-content; margin-bottom: 5px;'>⏳ {status_dk}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='background-color:#d4edda; color:#155724; padding:3px 8px; border-radius:3px; font-size:12px; font-weight:bold; width: fit-content; margin-bottom: 5px;'>🟢 {status_dk}</div>", unsafe_allow_html=True)
                        
                        img_string = str(row.get('Billede URL', ''))
                        first_img = img_string.split(',')[0].strip() if img_string and img_string != 'nan' else ''
                        if pd.notna(first_img) and first_img.startswith('http'): 
                            st.image(first_img, use_container_width=True)
                        else: 
                            st.image("https://via.placeholder.com/400x250?text=Intet+billede", use_container_width=True)
                        
                        st.markdown(f"### {row.get('Mærke', '')} {row.get('Model', '')}")
                        st.markdown(f"*{row.get('Variant', '')}*")
                        st.write("")
                        
                        aarstal = str(row.get('Årgang', '-'))[:4]
                        km_str = str(row.get('Odometer', '-'))
                        gear = str(row.get('Gearkasse', '-'))
                        fuel = str(row.get('Drivmiddel', '-'))
                        
                        st.markdown(f"📅 **{aarstal}** &nbsp; | &nbsp; 🛣️ **{km_str}** <br> 🕹️ **{gear}** &nbsp; | &nbsp; ⚡ **{fuel}**", unsafe_allow_html=True)
                        st.markdown(f"🏷️ {row.get('Moms status', '-')} &nbsp; | &nbsp; ⚖️ {row.get('Afgift status', '-')}")
                        
                        pris_int = row.get('Sort_Price', 0)
                        st.write("---")
                        pris_display = f"kr. {int(pris_int):,}".replace(',', '.') if pris_int > 0 else "Giv et bud"
                        if pris_int > 0: 
                            st.markdown(f"<h2 style='text-align: center; color: #2e7b32; font-weight: bold;'>{pris_display}</h2>", unsafe_allow_html=True)
                        else: 
                            st.markdown(f"<h2 style='text-align: center;'>{pris_display}</h2>", unsafe_allow_html=True)
                        
                        if st.button("📸 Se detaljer & billeder", key=f"view_{row.name}", use_container_width=True): 
                            show_car_details(row)
                        
                        vin = str(row.get('Stelnummer', 'Ukendt'))
                        mærke_model = f"{row.get('Mærke', '')} {row.get('Model', '')}"
                        modtagere = "matsc@maulbiler.dk,brmau@maulbiler.dk"
                        
                        emne_koeb = urllib.parse.quote(f"Køb af {mærke_model} (VIN: {vin})")
                        tekst_koeb = urllib.parse.quote(f"Hej Mathias og Brian,\n\nJeg vil gerne købe bilen til den annoncerede pris.\n\nStelnummer: {vin}")
                        mail_link_koeb = f"mailto:{modtagere}?subject={emne_koeb}&body={tekst_koeb}"
                        
                        emne_byd = urllib.parse.quote(f"Bud på {mærke_model} (VIN: {vin})")
                        tekst_byd = urllib.parse.quote(f"Hej Mathias og Brian,\n\nJeg vil gerne give et bud på bilen.\n\nMit bud er: [Indtast dit bud her] kr.\n\nStelnummer: {vin}")
                        mail_link_byd = f"mailto:{modtagere}?subject={emne_byd}&body={tekst_byd}"
                        
                        c_btn1, c_btn2 = st.columns(2)
                        c_btn1.markdown(f"<a href='{mail_link_koeb}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #2e7b32; color: white; border: none; padding: 6px; cursor: pointer; font-size: 14px; font-weight: bold;'>🛒 Køb</button></a>", unsafe_allow_html=True)
                        c_btn2.markdown(f"<a href='{mail_link_byd}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #555555; color: white; border: none; padding: 6px; cursor: pointer; font-size: 14px; font-weight: bold;'>⚖️ Byd</button></a>", unsafe_allow_html=True)
                        
                        # --- PAKKE TILFØJ/FJERN KNAP ---
                        st.write("")
                        vin_key = vin if vin != 'Ukendt' else str(row.name)
                        if vin_key in st.session_state['cart']:
                            if st.button("➖ Fjern fra pakke", key=f"rm_{row.name}", use_container_width=True):
                                del st.session_state['cart'][vin_key]
                                st.rerun()
                        else:
                            if st.button("➕ Tilføj til pakke", key=f"add_{row.name}", use_container_width=True):
                                st.session_state['cart'][vin_key] = {
                                    'title': mærke_model,
                                    'price_int': int(pris_int), # Sikrer at den er integer til udregning
                                    'price_str': pris_display,
                                    'vin': vin,
                                    'bid_price': int(pris_int) # Standardbuddet er listeprisen
                                }
                                st.rerun()

else:
    st.info("Der er i øjeblikket ingen aktive elbiler til salg på portalen.")
