import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="Maul Biler - Elbiler B2B", layout="wide", page_icon="⚡")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

WHATSAPP_NUMBER = "4561438202"

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

@st.cache_data(ttl=60)
def load_b2b_data():
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

def fmt_kr(val):
    try:
        v = int(float(str(val)))
        return f"{v:,} kr.".replace(',', '.')
    except:
        return "Giv et bud"

def forventet_info(forv, koebsd):
    """Returnerer dict med dage og formaterede datoer, eller None."""
    if not forv or forv in ["None", ""]:
        return None
    try:
        forv_dt = datetime.strptime(forv[:10], "%Y-%m-%d")
        dage    = (forv_dt - datetime.today()).days
        koeb_fmt = ""
        if koebsd and koebsd not in ["None", ""]:
            try:
                dk_md = {1:'jan',2:'feb',3:'mar',4:'apr',5:'maj',6:'jun',
                         7:'jul',8:'aug',9:'sep',10:'okt',11:'nov',12:'dec'}
                kd = datetime.strptime(str(koebsd)[:10], "%Y-%m-%d")
                koeb_fmt = f"{kd.day}. {dk_md[kd.month]} {kd.year}"
            except:
                koeb_fmt = str(koebsd)[:10]
        dk_md2 = {1:'januar',2:'februar',3:'marts',4:'april',5:'maj',6:'juni',
                  7:'juli',8:'august',9:'september',10:'oktober',11:'november',12:'december'}
        forv_fmt = f"{forv_dt.day}. {dk_md2[forv_dt.month]} {forv_dt.year}"
        return {"dage": dage, "forv_fmt": forv_fmt, "koeb_fmt": koeb_fmt}
    except:
        return None

if 'cart' not in st.session_state:
    st.session_state['cart'] = {}

# ==========================================
# SIDEMENU
# ==========================================
with st.sidebar:
    st.header("📦 Din Pakke (Pakkekøb)")
    if not st.session_state['cart']:
        st.info("Tilføj biler til pakken for at give et samlet bud.")
    else:
        total_list  = 0
        total_bid   = 0
        cart_lines  = []
        st.write("**Dine bud pr. bil:**")
        for key, car in st.session_state['cart'].items():
            total_list += car['price_int']
            new_bid = st.number_input(
                f"{car['title']} (Liste: {fmt_kr(car['price_int'])})",
                min_value=0, value=int(car.get('bid_price', car['price_int'])),
                step=1000, key=f"bid_{key}"
            )
            st.session_state['cart'][key]['bid_price'] = new_bid
            total_bid += new_bid
            cart_lines.append(f"- {car['title']} (VIN: {car['vin']}) -> Mit bud: {fmt_kr(new_bid)}")
        st.write("---")
        st.write(f"**Samlet listepris:** {fmt_kr(total_list)}")
        st.write("**Dit samlede bud:**")
        st.markdown(f"<h3 style='color:#1D9E75;margin-top:-10px;'>{fmt_kr(total_bid)}</h3>", unsafe_allow_html=True)
        st.write("---")
        cars_str  = "\n".join(cart_lines)
        mail_body = f"Hej Mathias og Brian,\n\nJeg vil gerne give følgende bud på {len(st.session_state['cart'])} biler i en pakkehandel:\n\n{cars_str}\n\nSamlet bud: {fmt_kr(total_bid)}\n\nVenlig hilsen,"
        mail_link = f"mailto:matsc@maulbiler.dk,brmau@maulbiler.dk?subject=Samlet bud på {len(st.session_state['cart'])} biler&body={urllib.parse.quote(mail_body)}"
        wa_link   = f"https://wa.me/{WHATSAPP_NUMBER}?text={urllib.parse.quote(mail_body)}"
        st.markdown(f"<a href='{mail_link}' target='_blank'><button style='width:100%;border-radius:6px;background:#1D9E75;color:white;border:none;padding:10px;cursor:pointer;font-size:14px;font-weight:500;margin-bottom:8px;'>✉️ Send samlet bud (Mail)</button></a>", unsafe_allow_html=True)
        st.markdown(f"<a href='{wa_link}'   target='_blank'><button style='width:100%;border-radius:6px;background:#25D366;color:white;border:none;padding:10px;cursor:pointer;font-size:14px;font-weight:500;margin-bottom:16px;'>💬 Send samlet bud (WA)</button></a>", unsafe_allow_html=True)
        if st.button("🗑️ Ryd pakken", use_container_width=True):
            st.session_state['cart'] = {}
            st.rerun()

# ==========================================
# DETAIL DIALOG
# ==========================================
@st.dialog("Se detaljer", width="large")
def show_car_details(row):
    vin          = safe(row.get('stelnummer')) or 'Ukendt'
    maerke_model = f"{safe(row.get('maerke'))} {safe(row.get('model'))}"
    modtagere    = "matsc@maulbiler.dk,brmau@maulbiler.dk"
    pris_int     = int(float(row.get('pris_dkk') or 0))
    fi           = forventet_info(safe(row.get('forventet_lager_dato')), safe(row.get('koebsdato')))

    # --- HEADER: titel + pris ---
    c_title, c_pris = st.columns([3, 2])
    with c_title:
        st.markdown(f"## {maerke_model}")
        st.markdown(f"*{safe(row.get('variant'))}*")
        st.caption(safe(row.get('stelnummer')))
    with c_pris:
        pris_str = fmt_kr(pris_int) if pris_int > 0 else "Giv et bud"
        farve    = "#1D9E75" if pris_int > 0 else "var(--color-text-primary)"
        st.markdown(f"<p style='font-size:28px;font-weight:500;color:{farve};text-align:right;margin:0;'>{pris_str}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:12px;color:var(--color-text-secondary);text-align:right;margin:0;'>{safe(row.get('moms_status'))} · {safe(row.get('afgift_status'))}</p>", unsafe_allow_html=True)

    st.write("---")

    # --- SPEC GRID ---
    s1, s2, s3, s4 = st.columns(4)
    for col, label, val in [
        (s1, "Årgang",    safe(row.get('aargang'))[:4]),
        (s2, "Kilometer", safe(row.get('odometer'))),
        (s3, "Gearkasse", safe(row.get('gearkasse'))),
        (s4, "Lakfelter", safe(row.get('lakfelter'))),
    ]:
        col.markdown(
            f"<div style='background:var(--color-background-secondary);border-radius:8px;padding:10px;text-align:center;'>"
            f"<p style='margin:0;font-size:11px;color:var(--color-text-tertiary);'>{label}</p>"
            f"<p style='margin:0;font-size:16px;font-weight:500;color:var(--color-text-primary);'>{val or '—'}</p>"
            f"</div>", unsafe_allow_html=True
        )

    # --- DATO PANEL ---
    if fi:
        st.write("")
        dage_tekst = f"{fi['dage']} dage" if fi['dage'] > 0 else ("I dag!" if fi['dage'] == 0 else f"Forsinket {abs(fi['dage'])}d")
        st.markdown(
            f"<div style='background:var(--color-background-info);border-radius:8px;padding:12px 16px;"
            f"display:flex;justify-content:space-between;align-items:center;'>"
            f"<div><p style='margin:0;font-size:11px;color:var(--color-text-info);'>Købsdato</p>"
            f"<p style='margin:0;font-size:14px;font-weight:500;color:var(--color-text-info);'>{fi['koeb_fmt'] or '—'}</p></div>"
            f"<div style='text-align:center;'><p style='margin:0;font-size:11px;color:var(--color-text-info);'>Tid til ankomst</p>"
            f"<p style='margin:0;font-size:14px;font-weight:500;color:var(--color-text-info);'>{dage_tekst}</p></div>"
            f"<div style='text-align:right;'><p style='margin:0;font-size:11px;color:var(--color-text-info);'>Forventet på lager</p>"
            f"<p style='margin:0;font-size:14px;font-weight:500;color:var(--color-text-info);'>{fi['forv_fmt']}</p></div>"
            f"</div>", unsafe_allow_html=True
        )

    st.write("")

    # --- TEKNISK DATA + UDSTYR ---
    ct, cu = st.columns(2)
    with ct:
        st.markdown("**Teknisk data**")
        rows_tech = [
            ("Drivmiddel",   safe(row.get('drivmiddel'))),
            ("EURO norm",    safe(row.get('euro_norm'))),
            ("CO2-udslip",   safe(row.get('co2'))),
            ("Reg. nr.",     safe(row.get('reg_nr'))),
            ("Lokation",     safe(row.get('lokation'))),
            ("Moms",         safe(row.get('moms_status'))),
            ("Afgift",       safe(row.get('afgift_status'))),
        ]
        for label, val in rows_tech:
            if val:
                cl, cv = st.columns([1, 1])
                cl.caption(label)
                cv.markdown(f"<p style='text-align:right;font-size:13px;margin:0;'>{val}</p>", unsafe_allow_html=True)
    with cu:
        st.markdown("**Udstyr & bemærkninger**")
        udstyr = safe(row.get('udstyr'))
        if udstyr:
            st.markdown(f"<p style='font-size:13px;color:var(--color-text-secondary);line-height:1.7;'>{udstyr}</p>", unsafe_allow_html=True)
        else:
            st.caption("Ingen bemærkninger.")

    # --- BILLEDER ---
    img_string = safe(row.get('billede_url'))
    images     = [u.strip() for u in img_string.split(',') if u.strip().startswith('http')]
    if images:
        st.write("---")
        st.markdown("**Billeder**")
        img_cols = st.columns(min(len(images), 3))
        for idx, img in enumerate(images):
            with img_cols[idx % 3]:
                st.image(img, use_container_width=True)

    # --- SKADESBILLEDER ---
    skade_str  = safe(row.get('skadesbilleder_url'))
    skade_imgs = [u.strip() for u in skade_str.split(',') if u.strip().startswith('http')]
    if skade_imgs:
        st.write("")
        st.markdown(
            "<div style='background:var(--color-background-danger);border-radius:8px;padding:10px 14px;margin-bottom:8px;'>"
            "<p style='margin:0;font-size:12px;font-weight:500;color:var(--color-text-danger);'>Noterede skader</p>"
            "</div>", unsafe_allow_html=True
        )
        sk_cols = st.columns(min(len(skade_imgs), 3))
        for idx, img in enumerate(skade_imgs):
            with sk_cols[idx % 3]:
                st.image(img, use_container_width=True)

    # --- PDF ---
    pdf_url = safe(row.get('udstyrsliste_pdf'))
    if pdf_url:
        st.write("")
        st.markdown(
            f"<a href='{pdf_url}' target='_blank'>"
            f"<button style='width:100%;padding:10px;font-size:13px;border-radius:6px;"
            f"border:1px solid var(--color-border-info);color:var(--color-text-info);"
            f"background:var(--color-background-info);cursor:pointer;'>"
            f"Åbn udstyrsliste (PDF)</button></a>",
            unsafe_allow_html=True
        )

    # --- KNAPPER ---
    st.write("---")
    vin_key    = vin
    pris_disp  = fmt_kr(pris_int) if pris_int > 0 else "Giv et bud"
    mail_koeb  = f"mailto:{modtagere}?subject={urllib.parse.quote(f'Køb af {maerke_model} (VIN: {vin})')}&body={urllib.parse.quote(f'Hej Mathias og Brian,\n\nJeg vil gerne købe bilen til den annoncerede pris.\n\nStelnummer: {vin}')}"

    kb1, kb2 = st.columns(2)
    # Tilføj til pakke
    if vin_key in st.session_state['cart']:
        if kb1.button("➖ Fjern fra pakke", key=f"dlg_rm_{vin}", width='stretch'):
            del st.session_state['cart'][vin_key]
            st.rerun()
    else:
        if kb1.button("+ Tilføj til pakke", key=f"dlg_add_{vin}", width='stretch'):
            st.session_state['cart'][vin_key] = {
                'title': maerke_model, 'price_int': pris_int,
                'price_str': pris_disp, 'vin': vin, 'bid_price': pris_int,
            }
            st.rerun()
    kb2.markdown(
        f"<a href='{mail_koeb}' target='_blank'>"
        f"<button style='width:100%;padding:10px;font-size:14px;border-radius:6px;"
        f"border:none;background:#1D9E75;color:white;cursor:pointer;font-weight:500;'>"
        f"Køb</button></a>",
        unsafe_allow_html=True
    )

# ==========================================
# TITEL + FILTRE
# ==========================================
st.title("⚡ Maul Biler - B2B Elbiler")
st.write("Velkommen til vores danske B2B portal. Her finder du vores aktuelle elbiler klar til handel.")

df = load_b2b_data()

if df is None or df.empty:
    st.info("Der er i øjeblikket ingen aktive elbiler til salg på portalen.")
    st.stop()

df['Sort_Price'] = pd.to_numeric(df['pris_dkk'], errors='coerce').fillna(0)
df['Sort_Year']  = pd.to_numeric(df['aargang'].astype(str).str[:4], errors='coerce').fillna(0)
df['Sort_Km']    = pd.to_numeric(df['odometer'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(9999999)

c_search, c_moms, c_afgift, c_sort = st.columns(4)
search_q    = c_search.text_input("🔍 Søg mærke/model")
moms_opts   = ["Alle"] + sorted(df['moms_status'].dropna().unique().tolist())
afgift_opts = ["Alle"] + sorted(df['afgift_status'].dropna().unique().tolist())
moms_q      = c_moms.selectbox("🏷️ Moms",   moms_opts)
afgift_q    = c_afgift.selectbox("⚖️ Afgift", afgift_opts)
sort_map    = {
    "Nyeste tilføjet":    "default",
    "Pris: Lav til Høj":  "price_asc",
    "Pris: Høj til Lav":  "price_desc",
    "Årgang: Nyeste":     "year_desc",
    "Kilometer: Lavest":  "km_asc",
}
sort_q = sort_map[c_sort.selectbox("🔽 Sorter efter", list(sort_map.keys()))]

if search_q:  df = df[df.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]
if moms_q   != "Alle": df = df[df['moms_status']   == moms_q]
if afgift_q != "Alle": df = df[df['afgift_status'] == afgift_q]
if sort_q == "price_asc":   df = df.sort_values('Sort_Price', ascending=True)
elif sort_q == "price_desc": df = df.sort_values('Sort_Price', ascending=False)
elif sort_q == "year_desc":  df = df.sort_values('Sort_Year',  ascending=False)
elif sort_q == "km_asc":     df = df.sort_values('Sort_Km',    ascending=True)

st.write("---")
st.caption(f"Viser **{len(df)}** elbiler")

# ==========================================
# KORTVISNING
# ==========================================
for i in range(0, len(df), 3):
    cols  = st.columns(3)
    chunk = df.iloc[i:i+3]

    for col, (_, row) in zip(cols, chunk.iterrows()):
        with col:
            with st.container(border=True):
                pris_int  = int(float(row.get('Sort_Price', 0)))
                vin       = safe(row.get('stelnummer')) or str(row.name)
                fi        = forventet_info(safe(row.get('forventet_lager_dato')), safe(row.get('koebsdato')))

                # --- STATUS + DAGE BADGE ---
                status_dk = safe(row.get('status_dk'))
                b_left = b_right = ""
                if status_dk and status_dk.lower() not in ['aktiv', 'på lager', '']:
                    if "vej" in status_dk.lower():
                        b_left = f"<div style='background:#fff3cd;color:#856404;font-size:11px;font-weight:500;padding:3px 8px;border-radius:4px;display:inline-block;'>⏳ {status_dk}</div>"
                    else:
                        b_left = f"<div style='background:var(--color-background-success);color:var(--color-text-success);font-size:11px;font-weight:500;padding:3px 8px;border-radius:4px;display:inline-block;'>🟢 {status_dk}</div>"
                if fi:
                    dage = fi['dage']
                    if dage < 0:
                        b_right = "<div style='background:var(--color-background-danger);color:var(--color-text-danger);font-size:11px;font-weight:500;padding:3px 8px;border-radius:4px;display:inline-block;'>Forsinket</div>"
                    elif dage == 0:
                        b_right = "<div style='background:var(--color-background-success);color:var(--color-text-success);font-size:11px;font-weight:500;padding:3px 8px;border-radius:4px;display:inline-block;'>I dag!</div>"
                    else:
                        b_right = f"<div style='background:var(--color-background-info);color:var(--color-text-info);font-size:11px;font-weight:500;padding:3px 8px;border-radius:4px;display:inline-block;'>{dage}d</div>"

                if b_left or b_right:
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>"
                        f"{b_left}{b_right}</div>",
                        unsafe_allow_html=True
                    )

                # --- BILLEDE ---
                first_img = safe(row.get('billede_url', '')).split(',')[0].strip()
                if first_img.startswith('http'):
                    st.image(first_img, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/400x250?text=Intet+billede", use_container_width=True)

                # --- TITEL ---
                st.markdown(f"<p style='margin:12px 0 2px;font-size:17px;font-weight:500;color:var(--color-text-primary);'>{safe(row.get('maerke'))} {safe(row.get('model'))}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin:0 0 4px;font-size:13px;color:var(--color-text-secondary);'>{safe(row.get('variant'))}</p>", unsafe_allow_html=True)
                if safe(row.get('stelnummer')):
                    st.markdown(f"<p style='margin:0 0 10px;font-size:12px;color:var(--color-text-tertiary);font-family:monospace;'>🔑 {safe(row.get('stelnummer'))}</p>", unsafe_allow_html=True)

                # --- SPEC GRID ---
                st.markdown(
                    f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:10px;'>"
                    f"<div style='background:var(--color-background-secondary);border-radius:6px;padding:7px;text-align:center;'><p style='margin:0;font-size:10px;color:var(--color-text-tertiary);'>Årgang</p><p style='margin:0;font-size:13px;font-weight:500;color:var(--color-text-primary);'>{safe(row.get('aargang'))[:4]}</p></div>"
                    f"<div style='background:var(--color-background-secondary);border-radius:6px;padding:7px;text-align:center;'><p style='margin:0;font-size:10px;color:var(--color-text-tertiary);'>Km</p><p style='margin:0;font-size:13px;font-weight:500;color:var(--color-text-primary);'>{safe(row.get('odometer'))}</p></div>"
                    f"<div style='background:var(--color-background-secondary);border-radius:6px;padding:7px;text-align:center;'><p style='margin:0;font-size:10px;color:var(--color-text-tertiary);'>Gear</p><p style='margin:0;font-size:13px;font-weight:500;color:var(--color-text-primary);'>{'Aut.' if 'uto' in safe(row.get('gearkasse')).lower() else safe(row.get('gearkasse'))[:5]}</p></div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # --- DATO PANEL ---
                if fi:
                    st.markdown(
                        f"<div style='background:var(--color-background-info);border-radius:8px;padding:9px 12px;"
                        f"display:flex;justify-content:space-between;margin-bottom:10px;'>"
                        f"<div><p style='margin:0;font-size:10px;color:var(--color-text-info);'>Købsdato</p>"
                        f"<p style='margin:0;font-size:12px;font-weight:500;color:var(--color-text-info);'>{fi['koeb_fmt'] or '—'}</p></div>"
                        f"<div style='text-align:right;'><p style='margin:0;font-size:10px;color:var(--color-text-info);'>Forventet lager</p>"
                        f"<p style='margin:0;font-size:12px;font-weight:500;color:var(--color-text-info);'>{fi['forv_fmt']}</p></div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # --- UDSTYR ---
                udstyr = safe(row.get('udstyr'))
                if udstyr:
                    st.markdown(
                        f"<div style='background:var(--color-background-secondary);border-radius:8px;"
                        f"padding:9px 12px;border-left:3px solid var(--color-border-secondary);margin-bottom:10px;'>"
                        f"<p style='margin:0 0 3px;font-size:10px;color:var(--color-text-tertiary);'>Udstyr & bemærkninger</p>"
                        f"<p style='margin:0;font-size:12px;color:var(--color-text-secondary);line-height:1.5;'>{udstyr[:120]}{'...' if len(udstyr)>120 else ''}</p>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # --- PRIS ---
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"border-top:0.5px solid var(--color-border-tertiary);padding:10px 0 8px;'>"
                    f"<p style='margin:0;font-size:11px;color:var(--color-text-secondary);'>{safe(row.get('moms_status'))} · {safe(row.get('afgift_status'))}</p>"
                    f"<p style='margin:0;font-size:20px;font-weight:500;color:{'#1D9E75' if pris_int > 0 else 'var(--color-text-primary)'};'>"
                    f"{fmt_kr(pris_int) if pris_int > 0 else 'Giv et bud'}</p>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # --- KNAPPER: Se detaljer + Køb/Byd ---
                ck1, ck2 = st.columns(2)
                if ck1.button("Se detaljer", key=f"view_{row.name}", width='stretch'):
                    show_car_details(row)

                maerke_model = f"{safe(row.get('maerke'))} {safe(row.get('model'))}"
                mail_koeb = f"mailto:matsc@maulbiler.dk,brmau@maulbiler.dk?subject={urllib.parse.quote(f'Køb af {maerke_model} (VIN: {vin})')}&body={urllib.parse.quote(f'Hej Mathias og Brian,\n\nJeg vil gerne købe bilen til den annoncerede pris.\n\nStelnummer: {vin}')}"
                ck2.markdown(
                    f"<a href='{mail_koeb}' target='_blank'>"
                    f"<button style='width:100%;padding:8px;font-size:13px;border-radius:6px;"
                    f"border:none;background:#1D9E75;color:white;cursor:pointer;font-weight:500;'>"
                    f"Køb</button></a>",
                    unsafe_allow_html=True
                )

                # --- TILFØJ TIL PAKKE (stor, fuld bredde) ---
                if vin in st.session_state['cart']:
                    if st.button("➖ Fjern fra pakke", key=f"rm_{row.name}", use_container_width=True):
                        del st.session_state['cart'][vin]
                        st.rerun()
                else:
                    if st.button("+ Tilføj til pakke", key=f"add_{row.name}", use_container_width=True):
                        st.session_state['cart'][vin] = {
                            'title':     maerke_model,
                            'price_int': pris_int,
                            'price_str': fmt_kr(pris_int),
                            'vin':       vin,
                            'bid_price': pris_int,
                        }
                        st.rerun()
