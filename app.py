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
    
    # Status Mærkat i Pop-up
    status_dk = str(row.get('Status', '')).strip()
    if status_dk and status_dk != 'nan':
        if "vej" in status_dk.lower():
            st.markdown(f"**Status:** ⏳ {status_dk}")
        else:
            st.markdown(f"**Status:** 🟢 {status_dk}")
            
    st.markdown(f"## {row.get('Mærke', '')} {row.get('Model', '')}")
    st.markdown(f"#### {row.get('Variant', '')}")
    st.write("")
    
    aarstal = str(row.get('Årgang', '-'))[:4]
    km_str = str(row.get('Odometer', '-'))
    
    # Henter Pris DKK
    try: pris_int = int(float(str(row.get('Pris DKK', '0')).replace('kr.', '').replace('.', '').replace(',', '').strip()))
    except: pris_int = 0
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
            
    with tab2: # TEKNISK DATA (DANSK)
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
    
    # KNAPPER I POP-UP (DANSK)
    vin = str(row.get('Stelnummer', 'Ukendt'))
    mærke_model = f"{row.get('Mærke', '')} {row.get('Model', '')}"
    
    modtagere = "matsc@maulbiler.dk,brmau@maulbiler.dk"
    emne = urllib.parse.quote(f"Køb af {mærke_model} (VIN: {vin})")
    tekst = urllib.parse.quote(f"Hej Mathias og Brian,\n\nJeg vil gerne købe bilen med stelnummer: {vin}")
    mail_link = f"mailto:{modtagere}?subject={emne}&body={tekst}"
    
    wa_text = urllib.parse.quote(f"Hej! Jeg vil gerne købe bilen med stelnummer: {vin}")
    wa_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={wa_text}"
    
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    btn_col1.markdown(f"<a href='{mail_link}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #2e7b32; color: white; border: none; padding: 10px; cursor: pointer; font-size: 15px; font-weight: bold;'>✉️ Send e-mail</button></a>", unsafe_allow_html=True)
    btn_col2.markdown(f"<a href='{wa_link}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #25D366; color: white; border: none; padding: 10px; cursor: pointer; font-size: 15px; font-weight: bold; color: white;'>💬 WhatsApp</button></a>", unsafe_allow_html=True)
    
    if btn_col3.button("🖨️ Print / PDF", use_container_width=True):
        st.info("⌨️ Tip: Tryk **CTRL + P** (eller **CMD + P** på Mac) for at gemme som PDF eller printe siden.")

# --- HOVEDPROGRAM ---
df_b2b = load_b2b_data()

if df_b2b is not None and not df_b2b.empty:
    # 1. VIS KUN AKTIVE BILER
    if 'Status.1' in df_b2b.columns:
        df_b2b = df_b2b[df_b2b['Status.1'].astype(str).str.strip().str.lower() == 'aktiv']
    elif 'Status' in df_b2b.columns and df_b2b.columns.to_list().count('Status') == 1:
         df_b2b = df_b2b[df_b2b['Status'].astype(str).str.strip().str.lower() == 'aktiv']
    
    # 2. VIS KUN ELBILER
    if 'Drivmiddel' in df_b2b.columns:
        df_b2b = df_b2b[df_b2b['Drivmiddel'].astype(str).str.contains('Elektrisk|El', case=False, na=False)]
    
    if df_b2b.empty:
        st.info("Der er i øjeblikket ingen aktive elbiler til salg på portalen.")
    else:
        # FORBERED DATA TIL SORTERING
        df_b2b['Sort_Price'] = pd.to_numeric(df_b2b['Pris DKK'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
        df_b2b['Sort_Year'] = pd.to_numeric(df_b2b['Årgang'].astype(str).str[:4], errors='coerce').fillna(0)
        df_b2b['Sort_Km'] = pd.to_numeric(df_b2b['Odometer'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(9999999)

        # TOP MENU
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
        
        # GRID OPSÆTNING
        cols_per_row = 3
        for i in range(0, len(df_b2b), cols_per_row):
            cols = st.columns(cols_per_row)
            chunk = df_b2b.iloc[i:i+cols_per_row]
            
            for col, (_, row) in zip(cols, chunk.iterrows()):
                with col:
                    with st.container(border=True):
                        
                        # Tjekker kolonnenavnet for Status (Da Pandas tilføjer .1 ved dobbelte navne)
                        status_col = 'Status' if 'Status' in row and not pd.isna(row['Status']) and row['Status'] != 'Aktiv' else ('Status.1' if 'Status.1' in row else '')
                        
                        # --- STATUS MÆRKAT I TOPPEN AF KORTET ---
                        status_dk = str(row.get('Status', '')).strip()
                        if status_dk and status_dk != 'nan' and status_dk != 'Aktiv':
                            if "vej" in status_dk.lower():
                                st.markdown(f"<div style='background-color:#fff3cd; color:#856404; padding:3px 8px; border-radius:3px; font-size:12px; font-weight:bold; width: fit-content; margin-bottom: 5px;'>⏳ {status_dk}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='background-color:#d4edda; color:#155724; padding:3px 8px; border-radius:3px; font-size:12px; font-weight:bold; width: fit-content; margin-bottom: 5px;'>🟢 {status_dk}</div>", unsafe_allow_html=True)

                        
                        # Billede
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
                        
                        # Viser DKK pris!
                        pris_int = row.get('Sort_Price', 0)
                        st.write("---")
                        if pris_int > 0: 
                            st.markdown(f"<h2 style='text-align: center; color: #2e7b32;'>kr. {int(pris_int):,}</h2>".replace(',', '.'), unsafe_allow_html=True)
                        else: 
                            st.markdown(f"<h2 style='text-align: center;'>Giv et bud</h2>", unsafe_allow_html=True)
                        
                        if st.button("📸 Se detaljer & billeder", key=f"view_{row.name}", use_container_width=True): 
                            show_car_details(row)
                        
                        # KNAPPER PÅ KORTET (DANSK)
                        vin = str(row.get('Stelnummer', 'Ukendt'))
                        mærke_model = f"{row.get('Mærke', '')} {row.get('Model', '')}"
                        
                        modtagere = "matsc@maulbiler.dk,brmau@maulbiler.dk"
                        emne = urllib.parse.quote(f"Køb af {mærke_model} (VIN: {vin})")
                        tekst = urllib.parse.quote(f"Hej Mathias og Brian,\n\nJeg vil gerne købe bilen med stelnummer: {vin}")
                        mail_link = f"mailto:{modtagere}?subject={emne}&body={tekst}"
                        
                        wa_text = urllib.parse.quote(f"Hej! Jeg vil gerne købe bilen med stelnummer: {vin}")
                        wa_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={wa_text}"
                        
                        c_btn1, c_btn2, c_btn3 = st.columns(3)
                        c_btn1.markdown(f"<a href='{mail_link}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #2e7b32; color: white; border: none; padding: 6px; cursor: pointer; font-size: 12px; font-weight: bold;'>✉️ Mail</button></a>", unsafe_allow_html=True)
                        c_btn2.markdown(f"<a href='{wa_link}' target='_blank'><button style='width: 100%; border-radius: 5px; background-color: #25D366; color: white; border: none; padding: 6px; cursor: pointer; font-size: 12px; font-weight: bold; color: white;'>💬 WA</button></a>", unsafe_allow_html=True)
                        
                        if c_btn3.button("🖨️ Print", key=f"print_{row.name}", use_container_width=True):
                            st.info("⌨️ **CTRL + P** (eller **CMD + P**)")
else:
    st.info("Der er i øjeblikket ingen aktive elbiler til salg på portalen.")
