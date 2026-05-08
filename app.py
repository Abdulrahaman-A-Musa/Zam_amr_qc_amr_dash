# ================================================================
# SARMAAN Supervisory Dashboard · Zamfara State AMR Survey 2026
# ================================================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests, io, re, math, urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from streamlit_folium import st_folium
    import folium
    _FOLIUM = True
except Exception:
    _FOLIUM = False

st.set_page_config(
    page_title="SARMAAN Supervisory Dashboard",
    page_icon="🏥", layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""<style>
[data-testid="stAppViewContainer"]{background:#f1f5f9}
[data-testid="stHeader"]{background:transparent}
.stTabs [data-baseweb="tab-list"]{gap:8px;background:white;border-radius:10px;padding:8px;
  box-shadow:0 1px 4px rgba(0,0,0,.06);margin-bottom:16px}
.stTabs [data-baseweb="tab"]{height:48px;border-radius:6px;font-weight:700;font-size:.9rem;color:#64748b}
.stTabs [aria-selected="true"]{background:linear-gradient(120deg,#0f2d5e,#1a5ca8)!important;color:white!important}
div[data-testid="stMetricValue"]{font-size:2rem!important;font-weight:900!important;color:#0f2d5e!important}
div[data-testid="stMetricLabel"]{font-size:.72rem!important;font-weight:700!important;
  text-transform:uppercase!important;letter-spacing:.5px!important;color:#64748b!important}
div[data-testid="metric-container"]{background:white;border-radius:10px;
  padding:16px!important;box-shadow:0 1px 4px rgba(0,0,0,.07)}
.pill-ok{display:inline-block;background:#dcfce7;color:#15803d;border-radius:12px;
  padding:2px 10px;font-size:.7rem;font-weight:700}
.pill-no{display:inline-block;background:#fee2e2;color:#b91c1c;border-radius:12px;
  padding:2px 10px;font-size:.7rem;font-weight:700}
.card-title{font-size:.88rem;font-weight:800;color:#0f2d5e;margin-bottom:12px;
  padding-left:10px;border-left:4px solid #3b82f6;display:block}
.banner{background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #3b82f6;
  border-radius:8px;padding:10px 16px;margin-bottom:12px;font-size:.83rem;color:#1e40af;line-height:1.6}
.mtx th{background:#0f2d5e;color:white;padding:8px 12px;text-align:center;
  white-space:nowrap;font-size:.76rem}
.mtx th:first-child{text-align:left}
.mtx td{padding:7px 12px;border-bottom:1px solid #e2e8f0;font-size:.79rem;text-align:center}
.mtx td:first-child{text-align:left;font-weight:700}
.mtx tr:hover td{background:#f8fafc}
</style>""", unsafe_allow_html=True)

# ── CONSTANTS ──────────────────────────────────────────────
ALL_LGAS = ['Zurmi','Bakura','Birnin Magaji','Gusau','Kaura Namoda',
            'Talata Mafara','Gummi','Tsafe','Shinkafi','Maradun','Bukkuyum','Maru']

KOBO_LC_URL = ('https://kf.kobotoolbox.org/api/v2/assets/'
               'ahdDePjwfyqm54j2Y6ovzW/export-settings/'
               'esvZDrAQQps5Y7VyoPHDHSm/data.xlsx')
KOBO_QC_URL = ('https://kf.kobotoolbox.org/api/v2/assets/'
               'aNR4xTJXwRQXwkKaNwZqJE/export-settings/'
               'esFNEaa3FuKUnGfaoKp5xtT/data.xlsx')

DL  = {'2026-05-02':'May 2','2026-05-04':'May 4','2026-05-05':'May 5'}
DLF = {'2026-05-02':'May 2 · ToT (Kano EOC)',
       '2026-05-04':'May 4 · Transit',
       '2026-05-05':'May 5 · Deploy Training'}
LGA_CLR = {'Zurmi':'#ef4444','Bakura':'#f97316','Birnin Magaji':'#f59e0b',
           'Gusau':'#84cc16','Kaura Namoda':'#10b981','Talata Mafara':'#14b8a6',
           'Gummi':'#06b6d4','Tsafe':'#0ea5e9','Shinkafi':'#3b82f6',
           'Maradun':'#6366f1','Bukkuyum':'#8b5cf6','Maru':'#a855f7'}
CACHE_TTL = 3600

DEMO = [
 {'date':'2026-05-02','lga':'Zurmi','time':'09:15','survey':'AMR','acts':['Training','Field Coordination','Supervision & QA'],'loc':'Outside LGA','dist':209.92,'reason':'Training day at EOC in Kano State','wards':0,'settle':0,'hh':0,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Bakura','time':'09:19','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':312.48,'reason':'Training of Trainers venue in Kano for the SARMAAN activity','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Birnin Magaji','time':'09:30','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':180.47,'reason':'Not in LGA – ToT at Kano EOC; DCs equipped with devices and role-plays completed','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Gusau','time':'09:30','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':208.60,'reason':'Day 1 of Training of Trainers in Kano State','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Kaura Namoda','time':'09:30','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':202.01,'reason':'At Abdullahi Wase Specialist Hospital, Nasarawa LGA, Kano – 2-day ToT','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Talata Mafara','time':'09:18','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':268.77,'reason':'At EOC, Abdullahi Wase Specialist Hospital – ToT training at Kano','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Gummi','time':'09:17','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':355.80,'reason':'Training day at Kano EOC – arrival of NIMR team, eHA team, LCs; SARMAAN project overview','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Tsafe','time':'09:22','survey':'AMR','acts':['Field Coordination'],'loc':'Outside LGA','dist':184.15,'reason':'Training at EOC, Abdullahi Wase Specialist Hospital, Nassarawa LGA – field coordination overview','wards':0,'settle':0,'hh':0,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Shinkafi','time':'09:32','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':260.42,'reason':'Training at Kano EOC','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Maradun','time':'09:42','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':232.83,'reason':'In Kano for ToT – familiarised with modifications on the AMR survey form','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-02','lga':'Bukkuyum','time':'18:31','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':301.12,'reason':'ToT program at Kano EOC – CFR & Kobo AMR data collections, data validation training','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9937,'longitude':8.5171},
 {'date':'2026-05-04','lga':'Zurmi','time':'07:41','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':200.36,'reason':'Transit from Kano to Zamfara','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.8500,'longitude':7.2833},
 {'date':'2026-05-04','lga':'Kaura Namoda','time':'07:57','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':191.92,'reason':'On transit to Zamfara state','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.5833,'longitude':6.8333},
 {'date':'2026-05-04','lga':'Maradun','time':'07:57','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':222.74,'reason':'Arrival day – LCs moving from Kano to Zamfara for AMR baseline','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.3500,'longitude':6.3500},
 {'date':'2026-05-04','lga':'Birnin Magaji','time':'08:00','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':170.48,'reason':'Travel Day – in transit to Zamfara deployment site','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.5500,'longitude':6.8500},
 {'date':'2026-05-04','lga':'Gusau','time':'08:10','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':197.35,'reason':'On transit from Kano to Gusau, Zamfara','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.1704,'longitude':6.6599},
 {'date':'2026-05-04','lga':'Tsafe','time':'08:12','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':172.97,'reason':'On transit from Kano to Zamfara – obtained Zamfara State mass transit','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':11.9500,'longitude':6.9167},
 {'date':'2026-05-04','lga':'Bakura','time':'08:03','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':301.90,'reason':'On transit to state of deployment – departure day from Kano','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.4667,'longitude':5.8667},
 {'date':'2026-05-04','lga':'Talata Mafara','time':'08:17','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':258.50,'reason':'On transit to Zamfara – at Rijia Zaki park in Kano awaiting departure','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.5500,'longitude':6.0667},
 {'date':'2026-05-04','lga':'Bukkuyum','time':'08:20','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':290.14,'reason':'Journey from Kano to Gusau after ToT program at Kano EOC','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.0833,'longitude':5.9500},
 {'date':'2026-05-04','lga':'Gummi','time':'08:27','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':344.98,'reason':'All LCs deployed to Zamfara state after completion of ToT in Kano','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.1500,'longitude':5.7167},
 {'date':'2026-05-04','lga':'Maru','time':'18:52','survey':'AMR','acts':['Transit'],'loc':'Outside LGA','dist':128.18,'reason':'On transit – app gave issues when taking GPS coordinates','wards':None,'settle':None,'hh':None,'dev':1,'sec':False,'devNote':'App GPS capture issue when taking coordinates','secNote':'','latitude':12.3333,'longitude':6.4000},
 {'date':'2026-05-05','lga':'Kaura Namoda','time':'17:03','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':27.32,'reason':'On Training Ground at Gusau EOC','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.5950,'longitude':6.8450},
 {'date':'2026-05-05','lga':'Gummi','time':'17:06','survey':'AMR','acts':['Training'],'loc':'Outside LGA','dist':149.50,'reason':'At Gusau EOC – preparations for AMR training activity and design of work plan','wards':None,'settle':None,'hh':None,'dev':0,'sec':False,'devNote':'','secNote':'','latitude':12.1704,'longitude':6.6599},
]

COMMUNITY_MAPPING = {
 "Anka|Yarsabaya|Tungar Bayi":20,"Anka|Yarsabaya|Daki Takwas":14,
 "Anka|Dangaladima|Hayin Tasha A":18,"Anka|Dangaladima|Limanchi":15,
 "Anka|Waramu|Shiyar Sabon Gari Waramu":16,"Anka|Waramu|Shiyar Galadima T Dangyaya":17,
 "Anka|Galadima|Shiyar Bagaruwa":34,"Anka|Galadima|Galadunchi 1":58,
 "Anka|Magaji|Sabon Garin Alin Garka B":93,"Anka|Magaji|Anka Emirates Idp Camp":25,
 "Bakura|Yargeda|Kabawa Tsohuwa":27,"Bakura|Yargeda|Bakin Masallaci Yargeda":27,
 "Bakura|Damri|Gidan Dikko":12,"Bakura|Damri|Gidan Malamai":29,
 "Bakura|Birnin Tudu|Shiyar Sarkin Malammai":26,"Bakura|Birnin Tudu|Malawama":21,
 "Bakura|Dankadu|Gidan Kade":52,"Bakura|Dankadu|Rumbar Ardo":42,
 "Bakura|Bakura|Duguzawa":35,"Bakura|Bakura|Shiyar Orphan And Less Previlege (O L P C":39,
 "Birnin Magaji/Kiyaw|Modomawa East|Gidan Dunya":31,"Birnin Magaji/Kiyaw|Modomawa East|Yar Dole A":24,
 "Birnin Magaji/Kiyaw|Modomawa East|G Kaiwa":24,"Birnin Magaji/Kiyaw|N Godel West|Tsahar Shehu A":66,
 "Birnin Magaji/Kiyaw|N Godel West|Shiyar Sarkin Diya West":43,"Birnin Magaji/Kiyaw|N Godel West|Shiyar Sarkin Diya North":45,
 "Birnin Magaji/Kiyaw|N Godel West|Shiyar Ajiya":43,"Birnin Magaji/Kiyaw|Birnin Magaji|Tsamiyar Dutsi":22,
 "Birnin Magaji/Kiyaw|Birnin Magaji|Shiyar Liman Makera":28,"Birnin Magaji/Kiyaw|Modomawa West|G Ande":5,
 "Birnin Magaji/Kiyaw|Modomawa West|Dadin Huntu C":22,
 "Bukkuyum|Yashi|Tega":44,"Bukkuyum|Yashi|Gangare":48,
 "Bukkuyum|Zauma|Baraya Hakimi":16,"Bukkuyum|Zauma|Basansan Shiyar Mamman Gunta":22,
 "Bukkuyum|Bukkuyum|Low Cost Yamma":23,"Bukkuyum|Bukkuyum|Dangaladima Gidan Zartu":34,
 "Bukkuyum|Kyaram|Marke":22,"Bukkuyum|Kyaram|Zugu Kanwuri":58,
 "Bukkuyum|Adabka|Shiyar Madawaki Adabka":33,"Bukkuyum|Adabka|Bakin Kasuwa":10,
 "Bungudu|Furfuri Kwaikwai|Bakin Dumau":25,"Bungudu|Furfuri Kwaikwai|Gidan Jikan Kunne":28,
 "Bungudu|Tofa|Gidan Dan Birgi":31,"Bungudu|Tofa|Bukkokin Mai Ganga":13,
 "Bungudu|Bungudu|Gidan Malammai 11":31,"Bungudu|Bungudu|Mallamawa 11":45,
 "Bungudu|Kotorkoshi|Tazame Daji":31,"Bungudu|Kotorkoshi|Gulubba":56,
 "Bungudu|Samawa|Sabon Garin Gidan Maitsaune":19,"Bungudu|Samawa|Birnin Gyade 1":33,
 "Gummi|Falale|Balkwai A":58,"Gummi|Falale|Kabawar Hausawa":28,
 "Gummi|Uban Dawaki|Yargijiya":45,"Gummi|Uban Dawaki|Bunkuche":19,
 "Gummi|Rafi|Makera Fari":29,"Gummi|Rafi|Lemawa Ubankasa":31,
 "Gummi|Gyalange|Unguwar Hassan Ta Arewa":22,"Gummi|Gyalange|Bayan Gida":27,
 "Gummi|Gamo|Unwala":29,"Gummi|Gamo|Gamo Yamma B 2":22,
 "Gusau|Rijiya|Bulunku Almajiri School":30,"Gusau|Rijiya|Tsunami Garejin Mai Lena":37,
 "Gusau|Rijiya|Tsunami Area":37,"Gusau|Tudun Wada|Malale Gidan Kaji":38,
 "Gusau|Tudun Wada|Yarmaibakware":27,"Gusau|Galadima|Unguwar Matawalle Ruggar Fulani":19,
 "Gusau|Galadima|Unguwar Yarima Bayan Gidan Kaji":32,"Gusau|Mayana|Hayin Asibitin Shagari":40,
 "Gusau|Mayana|Zawuyya Babba":38,"Gusau|Sabon Gari|Hizburahim":31,
 "Gusau|Sabon Gari|Emir Of Dansadau Area":18,
 "Kaura Namoda|Sakajiki|Yamutsawa":60,"Kaura Namoda|Sakajiki|Kadade G Bugaje":14,
 "Kaura Namoda|Kyambarawa|Kasuwardaji Yammachi":11,"Kaura Namoda|Kyambarawa|Kyanbarawa Injin Gabas":11,
 "Kaura Namoda|Kungurki|Unguwar Kanawa B":17,"Kaura Namoda|Kungurki|Shiyar Marafa":60,
 "Kaura Namoda|Gabake|Shiyar Magayaki":49,"Kaura Namoda|Gabake|Getso":47,
 "Kaura Namoda|Sarkin Mafara-Sarkin Baura|Kofar Modomawa B":27,"Kaura Namoda|Sarkin Mafara-Sarkin Baura|Poly Quarters":14,
 "Maradun|Maradun South|Aci Adunkule":27,"Maradun|Maradun South|Bakin Tasha":40,
 "Maradun|Maradun South|Baiche A":23,"Maradun|Maradun South|Woman Center":20,
 "Maradun|Maradun South|Mallamawa":78,"Maradun|Dosara Birnin Kaya|Taludu":12,
 "Maradun|Maradun North|Gumawa Maradun B":20,"Maradun|Maradun North|Shiyar Mayaki":23,
 "Maradun|Maradun North|Gumawa Maradun A":23,"Maradun|Maradun North|Kofar Kyarawa":44,
 "Maru|Maru|Gida Goma":40,"Maru|Maru|Gss Maru":36,"Maru|Maru|Sagi":36,
 "Maru|Ruwan Doruma|Kadaddaba Y":35,"Maru|Ruwan Doruma|Yar Duwa":34,"Maru|Ruwan Doruma|Unguwar Muazu":35,
 "Maru|Mayanchi|Unguwar Lemu":47,"Maru|Mayanchi|Durumin Namahe":29,
 "Maru|Dankurmi|Gari":9,"Maru|Dankurmi|Ruggar":9,
 "Shinkafi|Jangeru|Baiche C":27,"Shinkafi|Jangeru|Baiche B":27,
 "Shinkafi|Shinkafi South|Maberaya South A":34,"Shinkafi|Shinkafi South|Bayan Asibiti":27,
 "Shinkafi|Shanawa|Shiyar Baraya A":28,"Shinkafi|Shanawa|Shiyar Baraya C":37,
 "Shinkafi|Birnin Yero|Sabon Gari 1":32,"Shinkafi|Birnin Yero|Sabon Gari 2":32,
 "Shinkafi|Shinkafi North|Gidan Gwaba":34,"Shinkafi|Shinkafi North|Government Secondary School Shinkafi":35,
 "Talata Mafara|Ruwan Bore-Mirkidi|Shiyar Alhaji Bako":34,"Talata Mafara|Ruwan Bore-Mirkidi|Sabuwar Dagoje":33,
 "Talata Mafara|Kagara|Shiyar Liman Ilyasu":32,"Talata Mafara|Kagara|Tsaune Shiyar Musa Rafi":24,
 "Talata Mafara|Morai|Shiyar Ajiya D":28,"Talata Mafara|Morai|Shiyar Marafa D":41,
 "Talata Mafara|Gusari-Garbadu|Yarkuka B":42,"Talata Mafara|Gusari-Garbadu|Tudun Makera":28,
 "Talata Mafara|Sauna Ruwan Gora|Inwala":18,"Talata Mafara|Sauna Ruwan Gora|Tsanun Yamma":29,
 "Tsafe|Yandoton Daji|Awalar Yandoto":12,"Tsafe|Yandoton Daji|Birnin Ruwa":12,
 "Tsafe|Yandoton Daji|Dan Kasheshe":39,"Tsafe|Bilbis|Kucheri Gabas":12,
 "Tsafe|Bilbis|Magazu Yamma":24,"Tsafe|Bilbis|Magazu Gabas":60,
 "Tsafe|Chediya|Hayin Tumbi Inec":61,"Tsafe|Chediya|Aliya Community 1":9,
 "Tsafe|Tsafe Central|Shiyar Nomau":40,"Tsafe|Tsafe Central|Shiyar Yandoto":41,
 "Zurmi|Boko|Sagi Bakin Kotu":31,"Zurmi|Boko|Kadawa B":31,"Zurmi|Boko|Kadawa 1":31,
 "Zurmi|Dauran Birnin Tsaba|Dauran Marna":31,"Zurmi|Dauran Birnin Tsaba|Dauran Shiyar Yan Ruwa":27,
 "Zurmi|Moriki|Sabon Gari 4 Moriki":36,"Zurmi|Moriki|Ggcs Moriki":31,
 "Zurmi|Kanwa|Sabon Gari Jabanda 1":31,"Zurmi|Kanwa|Gidan A'I Kanwa":31,"Zurmi|Kanwa|Sabon Gari Jabanda 3":31,
}

# ── SESSION STATE ──────────────────────────────────────────
def _init():
    defs = dict(
        logged_in=False, current_user=None, user_role=None,
        selected_project='lc_supervisory',
        records=list(DEMO), lc_source='Demo Data', lc_fetch_time=None,
        qc_data=None, qc_fetch_time=None,
        active_dates=['all'], active_lga='all',
        col_override_lga='', col_override_date='',
        lc_status='Using embedded demo data.',
        qc_status='Click "Load QC Data" to fetch from KoboToolbox.',
        show_map=False,
    )
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── HELPERS ────────────────────────────────────────────────
def normalize_lga(raw):
    c = str(raw or '').strip().replace('_', ' ')
    if not c: return None
    exact = next((l for l in ALL_LGAS if l.lower() == c.lower()), None)
    if exact: return exact
    part = next((l for l in ALL_LGAS if c.lower() in l.lower() or l.lower() in c.lower()), None)
    if part: return part
    return ' '.join(w.capitalize() for w in c.split())

def parse_any_date(raw):
    if not raw: return None
    s = str(raw).strip()
    for pat, fmt in [
        (r'^(\d{4})-(\d{2})-(\d{2})', lambda m: f"{m[1]}-{m[2]}-{m[3]}"),
        (r'^(\d{4})/(\d{2})/(\d{2})', lambda m: f"{m[1]}-{m[2]}-{m[3]}"),
        (r'^(\d{2})/(\d{2})/(\d{4})', lambda m: f"{m[3]}-{m[2]}-{m[1]}"),
        (r'^(\d{2})-(\d{2})-(\d{4})', lambda m: f"{m[3]}-{m[2]}-{m[1]}"),
        (r'^(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: f"{m[3]}-{m[1].zfill(2)}-{m[2].zfill(2)}"),
    ]:
        m = re.match(pat, s)
        if m: return fmt(m.groups())
    return None

def to_bool(v):
    return str(v or '').strip().lower() in ('yes', '1', 'true')

def to_int(v):
    try: return int(v) if v not in (None, '') else None
    except: return None

def _best(headers, lh, *patterns):
    for p in patterns:
        try: return headers[lh.index(p.lower())]
        except ValueError: pass
    for p in patterns:
        for i, h in enumerate(lh):
            if p.lower() in h: return headers[i]
    return None

def detect_col_map(headers):
    lh = [h.lower() for h in headers]
    B = lambda *p: _best(headers, lh, *p)
    ov_lga  = st.session_state.col_override_lga
    ov_date = st.session_state.col_override_date
    def exact(n):
        if not n: return None
        try: return headers[lh.index(n.lower())]
        except: return None
    return dict(
        lga=exact(ov_lga) or B('auth_lc_lgalabel','Select your LGA','active_lga','lga_name','lgacoordinator','lga'),
        date=exact(ov_date) or B('today','date of report','date','_submission_time','start'),
        time=B('time of form','starttime','start_time','time'),
        dist=B('distance_loc_lga','distance from','distance_km','distance'),
        result=B('result','location_status','inside_outside'),
        reason=B('reason for being outside','reason_outside','outside_reason'),
        wards=B('number of wards covered','wards covered','wards_covered','num_wards'),
        settle=B('number of settlements covered','settlements covered','settlements_covered'),
        hh=B('total households visited','households visited','hh_visited','total_hh'),
        dev=B('were there any device or technical issues','device_issues','technical_issues'),
        devNote=B('describe the device or technical issues','device issue description','device_note'),
        sec=B('were there any security or access incidents','security_incidents','security'),
        secNote=B('describe what happened','security description','security_note'),
        lat=B('capture gps location (latitude & longitude)_latitude','_latitude','gps_latitude','latitude'),
        lng=B('capture gps location (latitude & longitude)_longitude','_longitude','gps_longitude','longitude'),
        act_training=B('survey data collection training','act_training','training'),
        act_transit=B("type(s) of activities carried out today/transit",'act_transit','transit'),
        act_field=B('field coordination and implementation','act_field','field coordination'),
        act_supervision=B('supervision and quality assurance','act_supervision','supervision'),
        act_data=B('data monitoring and reporting','act_data','data monitoring'),
        act_stakeholder=B('stakeholder engagement and advocacy','act_stakeholder','stakeholder'),
        act_team=B('team management and support','act_team','team management'),
        act_problem=B('problem solving and escalation','act_problem','problem solving'),
        act_logistics=B('logistics and planning','act_logistics','logistics'),
        actRaw=B("type(s) of activities carried out today",'activity_type','activities'),
    )

def filter_label_rows(df):
    def is_real(row):
        for col in ('_id','_submission_time','_uuid'):
            if str(row.get(col,'')).strip(): return True
        st_val = str(row.get('starttime','')).strip()
        if st_val: return bool(re.match(r'^\d', st_val))
        for col in ('active_lga','auth_lc_lgalabel','auth_lc_lganame'):
            if str(row.get(col,'')).strip(): return True
        if parse_any_date(str(row.get('today',''))): return True
        if parse_any_date(str(row.get('Date of Report',''))): return True
        return False
    return df[df.apply(is_real, axis=1)]

def parse_kobo_record(row, cm):
    # LGA
    lga_raw = str(row.get(cm['lga'],'') if cm['lga'] else '').strip()
    if not lga_raw:
        for k in ('auth_lc_lgalabel','auth_lc_lganame','active_lga','lga','LGA'):
            v = str(row.get(k,'')).strip()
            if v: lga_raw = v; break
    if not lga_raw:
        for k in row.index if hasattr(row,'index') else row.keys():
            if 'lga' in str(k).lower():
                v = str(row.get(k,'')).strip()
                if v: lga_raw = v; break
    if not lga_raw: return None
    lga = normalize_lga(lga_raw)

    # Date
    date_raw = str(row.get(cm['date'],'') if cm['date'] else '').strip()
    date = parse_any_date(date_raw)
    if not date:
        for col in ('_submission_time','start','end','today'):
            date = parse_any_date(str(row.get(col,'')))
            if date: break
    if not date: return None

    # Time
    time_raw = str(row.get(cm['time'],'') if cm['time'] else '').strip()
    time = time_raw[:5] if time_raw else ''

    # Activities
    acts = []
    act_cols = [('Training',cm['act_training']),('Transit',cm['act_transit']),
                ('Field Coordination',cm['act_field']),('Supervision & QA',cm['act_supervision']),
                ('Data Monitoring',cm['act_data']),('Stakeholder Engagement',cm['act_stakeholder']),
                ('Team Management',cm['act_team']),('Problem Solving',cm['act_problem']),
                ('Logistics',cm['act_logistics'])]
    for name, col in act_cols:
        if col:
            v = row.get(col,'')
            if v in (1,'1',True,'yes','Yes'): acts.append(name)
    if not acts and cm['actRaw']:
        raw = str(row.get(cm['actRaw'],'')).lower()
        for kw, name in [('training','Training'),('transit','Transit'),('field','Field Coordination'),
                         ('supervision','Supervision & QA'),('data','Data Monitoring'),
                         ('stakeholder','Stakeholder Engagement'),('team','Team Management'),
                         ('problem','Problem Solving'),('logistics','Logistics')]:
            if kw in raw: acts.append(name)
    if not acts: acts = ['Other']

    dist   = float(row.get(cm['dist'],0) if cm['dist'] else 0) or 0.0
    result = str(row.get(cm['result'],'') if cm['result'] else '').lower()
    loc    = 'Outside LGA' if (dist > 2 or 'outside' in result) else 'Inside LGA'
    reason = str(row.get(cm['reason'],'') if cm['reason'] else '')
    wards  = to_int(row.get(cm['wards']) if cm['wards'] else None)
    settle = to_int(row.get(cm['settle']) if cm['settle'] else None)
    hh     = to_int(row.get(cm['hh']) if cm['hh'] else None)
    dev    = 1 if to_bool(row.get(cm['dev']) if cm['dev'] else '') else 0
    devNote= str(row.get(cm['devNote'],'') if cm['devNote'] else '')
    sec    = to_bool(row.get(cm['sec']) if cm['sec'] else '')
    secNote= str(row.get(cm['secNote'],'') if cm['secNote'] else '')
    lat    = float(row.get(cm['lat'],0) if cm['lat'] else 0) or None
    lng    = float(row.get(cm['lng'],0) if cm['lng'] else 0) or None

    return dict(date=date,lga=lga,time=time,survey='AMR',acts=acts,
                loc=loc,dist=dist,reason=reason,wards=wards,settle=settle,hh=hh,
                dev=dev,sec=sec,devNote=devNote,secNote=secNote,latitude=lat,longitude=lng)

def parse_xlsx_bytes(data_bytes, source_name):
    try:
        df = pd.read_excel(io.BytesIO(data_bytes), engine='openpyxl', dtype=str)
        df = df.fillna('')
        # Drop g_polygon-style sheets (already handled by sheet picking above)
        df = filter_label_rows(df)
        if df.empty: return [], 'No data rows found after filtering label rows.'
        headers = list(df.columns)
        cm = detect_col_map(headers)
        records = [r for r in (parse_kobo_record(row, cm) for _, row in df.iterrows()) if r]
        return records, f'✓ {len(records)} records loaded from {source_name}'
    except Exception as e:
        return [], f'Error: {e}'

def parse_xlsx_workbook_bytes(data_bytes, source_name):
    """Pick first non-polygon sheet, then parse."""
    try:
        xl = pd.ExcelFile(io.BytesIO(data_bytes), engine='openpyxl')
        sheet = next((s for s in xl.sheet_names
                      if 'polygon' not in s.lower() and 'g_poly' not in s.lower()),
                     xl.sheet_names[0])
        df = xl.parse(sheet, dtype=str).fillna('')
        df = filter_label_rows(df)
        if df.empty: return [], 'No data rows found after filtering label rows.'
        cm = detect_col_map(list(df.columns))
        records = [r for r in (parse_kobo_record(row, cm) for _, row in df.iterrows()) if r]
        return records, f'✓ {len(records)} records from sheet "{sheet}" · {source_name}'
    except Exception as e:
        return [], f'Error reading Excel: {e}'

def fetch_kobo(url, label):
    try:
        resp = requests.get(url, verify=False, timeout=60,
                            headers={'User-Agent':'SARMAAN-Dashboard/1.0',
                                     'Accept':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*'})
        if not resp.ok:
            return [], f'HTTP {resp.status_code}: {resp.reason}'
        return parse_xlsx_workbook_bytes(resp.content, label)
    except Exception as e:
        return [], f'Fetch error: {e}'

def cache_stale(fetch_time):
    if fetch_time is None: return True
    return (datetime.now() - fetch_time).total_seconds() > CACHE_TTL

def get_filtered():
    recs = st.session_state.records
    role = st.session_state.user_role
    user = st.session_state.current_user
    ad   = st.session_state.active_dates
    al   = st.session_state.active_lga
    if role == 'lga':
        recs = [r for r in recs if r['lga'].lower() == user.lower()]
    date_ok = lambda r: ad == ['all'] or r['date'] in ad
    lga_ok  = lambda r: al == 'all' or r['lga'].lower() == al.lower()
    return [r for r in recs if date_ok(r) and lga_ok(r)]

def all_dates():
    return sorted(set(r['date'] for r in st.session_state.records))

def records_csv(data):
    lines = ['Date,LGA,Time,Survey,Activities,Location Status,Distance (km),Reason Outside LGA,'
             'Wards,Settlements,Households Visited,Device Issues,Security Incident,Device Notes,Security Notes']
    for r in data:
        def q(v): return f'"{str(v).replace(chr(34),chr(34)*2)}"'
        lines.append(','.join(q(x) for x in [
            r['date'],r['lga'],r['time'],r['survey'],'; '.join(r['acts']),
            r['loc'],f"{r['dist']:.1f}",r['reason'],
            r['wards'] if r['wards'] is not None else '',
            r['settle'] if r['settle'] is not None else '',
            r['hh'] if r['hh'] is not None else '',
            r['dev'],'Yes' if r['sec'] else 'No',r['devNote'],r['secNote']
        ]))
    return '\n'.join(lines)

# ── LOGIN ──────────────────────────────────────────────────
def login_page():
    col = st.columns([1,1.4,1])[1]
    with col:
        st.markdown("""
        <div style="text-align:center;margin-bottom:24px">
          <h1 style="font-size:2.2rem;color:#0f2d5e;font-weight:900;letter-spacing:1px">SARMAAN</h1>
          <p style="color:#64748b;font-size:.88rem">Supervisory Dashboard · Zamfara AMR 2026</p>
        </div>""", unsafe_allow_html=True)

        with st.form('login_form', clear_on_submit=False):
            username = st.text_input('Username / LGA Name',
                placeholder="Enter LGA name or 'admin' for full access")
            project = st.selectbox('Select Project', ['','LC Supervisory Dashboard','QC Monitoring Page'],
                format_func=lambda x: '-- Choose Project --' if x == '' else x)
            submitted = st.form_submit_button('Sign In', use_container_width=True)

        if submitted:
            if not project:
                st.error('Please select a project.')
                return
            u = username.strip()
            if u.lower() == 'admin':
                st.session_state.current_user = 'admin'
                st.session_state.user_role    = 'admin'
                st.session_state.active_lga   = 'all'
            else:
                match = next((l for l in ALL_LGAS if l.lower() == u.lower()), None)
                if not match:
                    st.error('Invalid username. Enter a valid LGA name or "admin".')
                    return
                st.session_state.current_user = match
                st.session_state.user_role    = 'lga'
                st.session_state.active_lga   = match

            st.session_state.selected_project = ('lc_supervisory'
                if 'LC' in project else 'qc_monitoring')
            st.session_state.logged_in = True
            st.rerun()

        st.markdown("""
        <div style="margin-top:20px;padding-top:16px;border-top:1px solid #e2e8f0;
             font-size:.78rem;color:#64748b;line-height:1.7">
        <strong style="color:#0f2d5e">Quick Login:</strong><br>
        • <strong>LGA Coordinators:</strong> Enter your LGA name (e.g. Zurmi, Gusau)<br>
        • <strong>Administrators:</strong> Enter "admin"<br>
        <small>Valid LGAs: Zurmi, Bakura, Birnin Magaji, Gusau, Kaura Namoda, Talata Mafara,
        Gummi, Tsafe, Shinkafi, Maradun, Bukkuyum, Maru</small>
        </div>""", unsafe_allow_html=True)

# ── LC SUPERVISORY ─────────────────────────────────────────
def lc_header():
    role = st.session_state.user_role
    user = st.session_state.current_user
    recs = st.session_state.records
    dates = all_dates()
    dr = ((DL.get(dates[0],dates[0]) + (' – ' + DL.get(dates[-1],dates[-1]) if len(dates)>1 else '')) + ' 2026') if dates else ''

    c1,c2 = st.columns([3,1])
    with c1:
        lga_txt = '' if role=='admin' else f' – {user}'
        st.markdown(f"""
        <div style="background:linear-gradient(120deg,#0f2d5e,#1a5ca8);color:white;
             padding:20px 28px;border-radius:10px;margin-bottom:8px">
          <div style="display:flex;align-items:center;gap:14px">
            <span style="background:rgba(255,255,255,.22);border-radius:8px;padding:6px 12px;
                  font-size:1.05rem;font-weight:900;letter-spacing:1px">SARMAAN</span>
            <div>
              <h2 style="margin:0;font-size:1.25rem;font-weight:800">
                LC Supervisory Dashboard{lga_txt}</h2>
              <p style="margin:0;font-size:.77rem;opacity:.78">
                LGA Coordinator Daily Field Reports · Zamfara State · AMR Survey 2026</p>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        user_lbl = 'Administrator' if role=='admin' else f'{user} Coordinator'
        st.markdown(f"""
        <div style="background:rgba(15,45,94,.08);border-radius:8px;padding:12px 16px;font-size:.78rem">
          <div>📊 AMR Survey &nbsp;|&nbsp; 📍 Zamfara</div>
          <div style="margin-top:4px">📅 {dr}</div>
          <div style="margin-top:4px;color:#1a5ca8;font-weight:600">👤 {user_lbl}</div>
          <div style="margin-top:4px">
            <span style="background:#dcfce7;color:#15803d;border-radius:12px;padding:2px 8px;
                  font-size:.72rem;font-weight:700">✓ Live: {len(recs)} records</span>
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button('🔓 Logout', key='lc_logout'):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

def lc_data_source():
    with st.expander('⚙ Data Source: KoboToolbox Live API', expanded=False):
        st.markdown("**Method 1 — Auto-Fetch from KoboToolbox**")
        col1, col2 = st.columns([3,1])
        with col2:
            if st.button('↻ Fetch Latest Data', use_container_width=True, key='lc_fetch_btn'):
                with st.spinner('Fetching from KoboToolbox…'):
                    recs, msg = fetch_kobo(KOBO_LC_URL, 'KoboToolbox')
                if recs:
                    st.session_state.records    = recs
                    st.session_state.lc_source  = f'KoboToolbox ({datetime.now().strftime("%H:%M")})'
                    st.session_state.lc_fetch_time = datetime.now()
                    st.session_state.lc_status  = msg
                    st.success(msg); st.rerun()
                else:
                    st.error(msg)

        st.markdown("**Method 2 — Upload CSV or Excel File**")
        uploaded = st.file_uploader('Drop CSV or XLSX here', type=['csv','xlsx'],
                                    key='lc_upload', label_visibility='collapsed')
        if uploaded:
            if uploaded.name.endswith('.xlsx'):
                recs, msg = parse_xlsx_workbook_bytes(uploaded.read(), uploaded.name)
            else:
                text = uploaded.read().decode('utf-8', errors='replace')
                df = pd.read_csv(io.StringIO(text), dtype=str).fillna('')
                df = filter_label_rows(df)
                cm = detect_col_map(list(df.columns))
                recs = [r for r in (parse_kobo_record(row,cm) for _,row in df.iterrows()) if r]
                msg = f'✓ {len(recs)} records from {uploaded.name}'
            if recs:
                st.session_state.records   = recs
                st.session_state.lc_source = uploaded.name
                st.session_state.lc_fetch_time = datetime.now()
                st.session_state.lc_status = msg
                st.success(msg); st.rerun()
            else:
                st.error(msg)

        st.markdown("**Column Name Overrides** *(only if LGA column not auto-detected)*")
        c1,c2 = st.columns(2)
        with c1:
            ov_lga = st.text_input('LGA Column Name', value=st.session_state.col_override_lga,
                                   placeholder='e.g. auth_lc_lgalabel')
        with c2:
            ov_date = st.text_input('Date Column Name', value=st.session_state.col_override_date,
                                    placeholder='e.g. today')
        if st.button('💾 Save Overrides', key='save_overrides'):
            st.session_state.col_override_lga  = ov_lga
            st.session_state.col_override_date = ov_date
            st.success('Overrides saved — re-upload file to apply.')

        st.info(st.session_state.lc_status)

def phase_timeline():
    st.markdown("""
    <div style="background:white;border-radius:10px;padding:16px 24px;
         box-shadow:0 1px 4px rgba(0,0,0,.07);margin-bottom:16px;
         display:flex;align-items:center;gap:0;overflow-x:auto">
      <div style="display:flex;flex-direction:column;align-items:center;gap:6px;min-width:90px">
        <div style="width:20px;height:20px;border-radius:50%;background:#22c55e;border:3px solid #16a34a"></div>
        <div style="font-size:.72rem;font-weight:700;color:#16a34a;text-align:center">May 2<br><small>ToT · Kano EOC</small></div>
      </div>
      <div style="flex:1;height:3px;background:#16a34a;min-width:30px"></div>
      <div style="display:flex;flex-direction:column;align-items:center;gap:6px;min-width:90px">
        <div style="width:20px;height:20px;border-radius:50%;background:#22c55e;border:3px solid #16a34a"></div>
        <div style="font-size:.72rem;font-weight:700;color:#16a34a;text-align:center">May 4<br><small>Transit (Kano→ZA)</small></div>
      </div>
      <div style="flex:1;height:3px;background:#16a34a;min-width:30px"></div>
      <div style="display:flex;flex-direction:column;align-items:center;gap:6px;min-width:90px">
        <div style="width:20px;height:20px;border-radius:50%;background:#3b82f6;border:3px solid #1a5ca8;box-shadow:0 0 0 4px rgba(59,130,246,.2)"></div>
        <div style="font-size:.72rem;font-weight:700;color:#1a5ca8;text-align:center">May 5<br><small>Deploy Training</small></div>
      </div>
      <div style="flex:1;height:3px;background:#e2e8f0;min-width:30px"></div>
      <div style="display:flex;flex-direction:column;align-items:center;gap:6px;min-width:90px">
        <div style="width:20px;height:20px;border-radius:50%;background:#e2e8f0;border:3px solid #cbd5e1"></div>
        <div style="font-size:.72rem;font-weight:700;color:#94a3b8;text-align:center">May 6+<br><small>Field Work</small></div>
      </div>
    </div>""", unsafe_allow_html=True)

def context_banner():
    role = st.session_state.user_role
    user = st.session_state.current_user
    if role == 'lga':
        txt = (f"<strong>{user} LGA Report View:</strong> You are viewing data specific to your LGA. "
               f"This dashboard shows your daily field reports, activities, and compliance status.")
    else:
        txt = ("<strong>Phase Context:</strong>&nbsp; "
               "<strong>May 2</strong> = Training of Trainers (ToT) at Abdullahi Wase Specialist Hospital, Kano EOC &nbsp;|&nbsp; "
               "<strong>May 4</strong> = Transit day — all LCs travelling from Kano to Zamfara &nbsp;|&nbsp; "
               "<strong>May 5</strong> = Deployment-site preparation and training at Gusau EOC. "
               "&nbsp;<strong>Being outside the assigned LGA is expected and authorised during this entire pre-field phase.</strong>")
    st.markdown(f'<div class="banner">ℹ {txt}</div>', unsafe_allow_html=True)

def lc_filters():
    dates = all_dates()
    role  = st.session_state.user_role
    c1,c2,c3 = st.columns([2,2,1])
    with c1:
        date_opts = ['All Days'] + [DLF.get(d,d) for d in dates]
        date_sel  = st.selectbox('📅 Date', date_opts, key='date_filter')
        if date_sel == 'All Days':
            st.session_state.active_dates = ['all']
        else:
            rev = {v:k for k,v in DLF.items()}
            st.session_state.active_dates = [rev.get(date_sel, date_sel)]
    with c2:
        if role == 'admin':
            loaded_lgas = sorted(set(r['lga'] for r in st.session_state.records))
            lga_opts = ['All LGAs'] + loaded_lgas
            lga_sel  = st.selectbox('📍 LGA', lga_opts, key='lga_filter')
            st.session_state.active_lga = 'all' if lga_sel == 'All LGAs' else lga_sel
    with c3:
        data = get_filtered()
        csv_bytes = records_csv(data).encode()
        st.download_button('⬇ Download CSV', csv_bytes,
                           file_name='SARMAAN_Reports.csv', mime='text/csv',
                           use_container_width=True, key='dl_all')

def lc_kpis(data):
    role = st.session_state.user_role
    dates = st.session_state.active_dates
    if dates == ['all']: dates = all_dates()
    loaded_lgas = sorted(set(r['lga'] for r in st.session_state.records))
    lga_list = loaded_lgas if st.session_state.active_lga == 'all' else [st.session_state.active_lga]
    expected  = len(lga_list) * len(dates)
    submitted = len(data)
    missing   = max(0, expected - submitted)
    rate      = round(submitted/expected*100) if expected else 0
    outside   = sum(1 for r in data if r['loc']=='Outside LGA')
    avg_dist  = f"{sum(r['dist'] for r in data)/len(data):.1f}" if data else '—'
    dev_count = sum(r['dev'] for r in data)
    sec_count = sum(1 for r in data if r['sec'])

    if role == 'admin':
        cols = st.columns(7)
        metrics = [
            ('📍 LGAs Monitored', len(loaded_lgas), f'{len(loaded_lgas)} reporting'),
            ('📋 Reports Submitted', submitted, f'{rate}% of {expected} expected'),
            ('⚠ Missing Reports', missing, 'All reported' if missing==0 else 'Not yet reported'),
            ('📌 Outside Assigned LGA', f'{outside}/{submitted}', 'Expected – training & transit'),
            ('📏 Avg Distance', f'{avg_dist} km', 'training / transit activity'),
            ('💻 Device Issues', dev_count, 'None logged' if dev_count==0 else 'See Issues tab'),
            ('🔒 Security Incidents', sec_count, 'None reported' if sec_count==0 else 'See Issues tab'),
        ]
    else:
        cols = st.columns(6)
        metrics = [
            ('📋 Your Reports', submitted, f'of {expected} expected'),
            ('⚠ Missing', missing, 'Complete' if missing==0 else 'Pending'),
            ('📌 Outside LGA', f'{outside}/{submitted}', 'During training/transit'),
            ('📏 Avg Distance', f'{avg_dist} km', 'from your LGA'),
            ('💻 Device Issues', dev_count, 'None' if dev_count==0 else 'Reported'),
            ('🔒 Security', sec_count, 'None' if sec_count==0 else 'Reported'),
        ]
    for col,(lbl,val,sub) in zip(cols,metrics):
        with col:
            st.metric(label=lbl, value=str(val), delta=sub,
                      delta_color='off')

def compliance_matrix(data):
    role = st.session_state.user_role
    if role != 'admin': return
    st.markdown('<span class="card-title">Submission Compliance Matrix</span>', unsafe_allow_html=True)
    dates = st.session_state.active_dates
    if dates == ['all']: dates = all_dates()
    loaded_lgas = sorted(set(r['lga'] for r in st.session_state.records))

    th_date = ''.join(f'<th>{DL.get(d,d)}</th>' for d in dates)
    tot_th  = '<th>Total</th>' if len(dates)>1 else ''
    rows_html = ''
    for lga in loaded_lgas:
        cells = ''
        count = 0
        for d in dates:
            hit = any(r['lga']==lga and r['date']==d for r in data)
            if hit: count+=1
            cells += f'<td>{"<span class=pill-ok>✓ Submitted</span>" if hit else "<span class=pill-no>✗ Missing</span>"}</td>'
        tot_td = f'<td><strong>{count}/{len(dates)}</strong></td>' if len(dates)>1 else ''
        rows_html += f'<tr><td style="font-weight:700">{lga}</td>{cells}{tot_td}</tr>'

    html = (f'<div style="overflow-x:auto"><table class="mtx">'
            f'<thead><tr><th style="text-align:left">LGA</th>{th_date}{tot_th}</tr></thead>'
            f'<tbody>{rows_html}</tbody></table></div>')
    st.markdown(html, unsafe_allow_html=True)

    # LGA report card selector
    lga_names = sorted(set(r['lga'] for r in data))
    if lga_names:
        sel = st.selectbox('📋 View LGA Report Card', [''] + lga_names,
                           format_func=lambda x: '— select an LGA —' if x=='' else x,
                           key='lga_rc_sel')
        if sel:
            lga_report_card(sel, data)

def lga_report_card(lga, data):
    lga_recs = [r for r in data if r['lga']==lga]
    if not lga_recs:
        st.warning(f'No records for {lga}'); return
    with st.expander(f'📋 {lga} LGA Report Card', expanded=True):
        dates   = sorted(set(r['date'] for r in lga_recs))
        total   = len(lga_recs)
        rate    = round(total/len(dates)*100) if dates else 0
        outside = sum(1 for r in lga_recs if r['loc']=='Outside LGA')
        avg_d   = f"{sum(r['dist'] for r in lga_recs)/total:.1f}" if total else '—'
        dev_c   = sum(r['dev'] for r in lga_recs)
        sec_c   = sum(1 for r in lga_recs if r['sec'])
        period  = ((DL.get(dates[0],dates[0]))+((' – '+DL.get(dates[-1],dates[-1])) if len(dates)>1 else ''))+' 2026'

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0f2d5e,#1a5ca8);color:white;
             padding:20px 24px;border-radius:8px;margin-bottom:16px;border-bottom:4px solid #d97706">
          <h3 style="margin:0">{lga} LGA Report Card</h3>
          <p style="margin:4px 0 0;opacity:.85;font-size:.85rem">
            📅 {period} · Zamfara State AMR Survey 2026</p>
        </div>""", unsafe_allow_html=True)

        c1,c2,c3,c4,c5,c6 = st.columns(6)
        for col,(lbl,val) in zip([c1,c2,c3,c4,c5,c6],[
            ('Total Reports',total),('Compliance',f'{rate}%'),
            ('Outside LGA',outside),('Avg Dist',f'{avg_d} km'),
            ('Device Issues',dev_c),('Security',sec_c)]):
            col.metric(lbl, val)

        # Activity breakdown
        act_counts = {}
        for r in lga_recs:
            for a in r['acts']: act_counts[a] = act_counts.get(a,0)+1
        st.markdown('**Activity Breakdown**')
        act_cols = st.columns(min(len(act_counts),5))
        for col,(act,cnt) in zip(act_cols, act_counts.items()):
            col.metric(act, cnt)

        # Timeline
        st.markdown('**Daily Reports Timeline**')
        for r in lga_recs:
            c_date, c_detail = st.columns([1,4])
            with c_date:
                d = r['date']
                st.markdown(f"""<div style="background:#f8fafc;border-radius:6px;padding:8px;
                    text-align:center;border:1px solid #e2e8f0">
                  <div style="font-size:1.4rem;font-weight:900;color:#0f2d5e">{d[8:]}</div>
                  <div style="font-size:.7rem;color:#64748b">{DL.get(d,d)}</div>
                </div>""", unsafe_allow_html=True)
            with c_detail:
                acts_str = ', '.join(r['acts'])
                loc_col  = '#16a34a' if r['loc']=='Inside LGA' else '#dc2626'
                st.markdown(f"""<div style="background:#f8fafc;border-radius:6px;padding:10px 14px;
                    border-left:3px solid #3b82f6">
                  <strong>{r['time']}</strong> · {acts_str}<br>
                  <span style="color:{loc_col};font-size:.82rem">{r['loc']}</span>
                  &nbsp;·&nbsp;<span style="font-size:.82rem">{r['dist']:.1f} km</span>
                  {('<br><em style="font-size:.8rem;color:#64748b">'+r['reason']+'</em>') if r['reason'] else ''}
                </div>""", unsafe_allow_html=True)

        # Issues
        issues = [r for r in lga_recs if r['dev']>0 or r['sec']]
        if not issues:
            st.success('✅ No device or security issues reported.')
        else:
            st.warning(f'⚠ {len(issues)} issue(s) reported')
            for r in issues:
                if r['dev']>0: st.error(f"🔧 Device issue ({DL.get(r['date'],r['date'])}): {r['devNote'] or 'Device technical issue reported'}")
                if r['sec']:   st.error(f"🚨 Security incident ({DL.get(r['date'],r['date'])}): {r['secNote'] or 'Security incident reported'}")

        csv_bytes = records_csv(lga_recs).encode()
        st.download_button(f'⬇ Download {lga} CSV', csv_bytes,
                           file_name=f"SARMAAN_{lga.replace(' ','_')}_Report.csv",
                           mime='text/csv', key=f'dl_{lga}')

def lc_charts(data):
    dates = st.session_state.active_dates
    if dates == ['all']: dates = all_dates()
    loaded_lgas = sorted(set(r['lga'] for r in st.session_state.records))
    lga_list = loaded_lgas if st.session_state.active_lga=='all' else [st.session_state.active_lga]

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<span class="card-title">Daily Submissions vs Expected</span>', unsafe_allow_html=True)
        sub  = [sum(1 for r in data if r['date']==d) for d in dates]
        miss = [max(0, len(lga_list)-s) for s in sub]
        fig = go.Figure()
        fig.add_bar(x=[DLF.get(d,d) for d in dates], y=sub,  name='Submitted', marker_color='#22c55e')
        fig.add_bar(x=[DLF.get(d,d) for d in dates], y=miss, name='Missing',   marker_color='#fca5a5')
        fig.update_layout(barmode='stack', height=280, margin=dict(t=10,b=10,l=10,r=10),
                          legend=dict(orientation='h',y=1.1), yaxis_title='Reports',
                          paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<span class="card-title">Activity Type Breakdown</span>', unsafe_allow_html=True)
        act_counts: dict = {}
        for r in data:
            key = 'Transit' if 'Transit' in r['acts'] else 'Training' if 'Training' in r['acts'] else r['acts'][0]
            act_counts[key] = act_counts.get(key,0)+1
        clrs = {'Training':'#3b82f6','Transit':'#8b5cf6','Field Coordination':'#10b981',
                'Supervision & QA':'#f59e0b','Other':'#94a3b8'}
        fig2 = go.Figure(go.Pie(
            labels=list(act_counts.keys()), values=list(act_counts.values()),
            hole=0.4, marker_colors=[clrs.get(k,'#94a3b8') for k in act_counts],
        ))
        fig2.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10),
                           legend=dict(orientation='h',y=-0.1),
                           paper_bgcolor='white')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<span class="card-title">Distance from Assigned LGA – by LGA & Date (km)</span>', unsafe_allow_html=True)
    date_clrs = {'2026-05-02':'#3b82f6','2026-05-04':'#8b5cf6','2026-05-05':'#10b981'}
    fig3 = go.Figure()
    for i,d in enumerate(dates):
        vals = []
        for lga in lga_list:
            r = next((x for x in data if x['lga']==lga and x['date']==d), None)
            vals.append(round(r['dist'],1) if r else None)
        fig3.add_bar(name=DLF.get(d,d), x=lga_list, y=vals,
                     marker_color=date_clrs.get(d,['#f59e0b','#ef4444','#06b6d4'][i%3]))
    fig3.update_layout(barmode='group', height=300, margin=dict(t=10,b=10,l=10,r=10),
                       yaxis_title='km', paper_bgcolor='white', plot_bgcolor='white',
                       legend=dict(orientation='h',y=1.05))
    st.plotly_chart(fig3, use_container_width=True)

def lc_map(data):
    st.session_state.show_map = st.toggle('🗺 Show Field Visit Locations Map',
                                           value=st.session_state.show_map, key='map_toggle')
    if not st.session_state.show_map: return
    pts = [r for r in data if r.get('latitude') and r.get('longitude')]
    if not pts: st.info('No GPS coordinates in current data.'); return

    if not _FOLIUM:
        st.warning('Install streamlit-folium for map support: pip install streamlit-folium folium')
        return

    m = folium.Map(location=[12.17, 6.66], zoom_start=8,
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                   attr='Esri')
    folium.TileLayer('OpenStreetMap', name='Street Map').add_to(m)

    for r in pts:
        clr = LGA_CLR.get(r['lga'],'#64748b')
        popup = (f"<b style='color:{clr}'>{r['lga']}</b><br>"
                 f"<b>Date:</b> {DL.get(r['date'],r['date'])}<br>"
                 f"<b>Time:</b> {r['time']}<br>"
                 f"<b>Location:</b> {r['loc']}<br>"
                 f"<b>Distance:</b> {r['dist']:.1f} km<br>"
                 f"<b>Activities:</b> {', '.join(r['acts'])}"
                 + (f"<br><b>Reason:</b> {r['reason']}" if r['reason'] else ''))
        folium.CircleMarker(
            location=[float(r['latitude']), float(r['longitude'])],
            radius=8, color='white', weight=2,
            fill=True, fill_color=clr, fill_opacity=0.85,
            popup=folium.Popup(popup, max_width=280)
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, height=480, use_container_width=True)

def lc_tables(data):
    st.markdown('<span class="card-title">Report Detail Log</span>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(['All Reports','Outside LGA – Reasons','Device & Security Issues'])

    with t1:
        rows = [{'Date':DL.get(r['date'],r['date']),'LGA':r['lga'],'Time':r['time'],
                 'Activities':', '.join(r['acts']),'Location':r['loc'],
                 'Distance (km)':f"{r['dist']:.1f}",
                 'Wards':r['wards'] if r['wards'] is not None else '—',
                 'Settlements':r['settle'] if r['settle'] is not None else '—',
                 'HHs':r['hh'] if r['hh'] is not None else '—',
                 'Device Issues':r['dev'],'Security':'Yes' if r['sec'] else 'No'} for r in data]
        if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else: st.info('No records match the current filter.')

    with t2:
        outside = [r for r in data if r['loc']=='Outside LGA']
        rows2 = [{'Date':DL.get(r['date'],r['date']),'LGA':r['lga'],'Time':r['time'],
                  'Distance (km)':f"{r['dist']:.1f}",'Reason':r['reason']} for r in outside]
        if rows2: st.dataframe(pd.DataFrame(rows2), use_container_width=True, hide_index=True)
        else: st.success('All reports are within assigned LGA.')

    with t3:
        issues = [r for r in data if r['dev']>0 or r['sec']]
        rows3 = [{'Date':DL.get(r['date'],r['date']),'LGA':r['lga'],'Time':r['time'],
                  'Device Issues':r['dev'],'Security':'Yes' if r['sec'] else 'No',
                  'Notes':' | '.join(filter(None,[r['devNote'],r['secNote']]))} for r in issues]
        if rows3: st.dataframe(pd.DataFrame(rows3), use_container_width=True, hide_index=True)
        else: st.success('No device or security issues in current filter.')

def lc_supervisory_page():
    # Auto-fetch on first load if cache stale
    if cache_stale(st.session_state.lc_fetch_time) and st.session_state.records == list(DEMO):
        with st.spinner('Auto-fetching latest data from KoboToolbox…'):
            recs, msg = fetch_kobo(KOBO_LC_URL, 'KoboToolbox (auto)')
        if recs:
            st.session_state.records       = recs
            st.session_state.lc_source     = 'KoboToolbox (auto)'
            st.session_state.lc_fetch_time = datetime.now()
            st.session_state.lc_status     = msg

    lc_header()
    lc_data_source()
    phase_timeline()
    context_banner()
    lc_filters()
    data = get_filtered()
    st.markdown('---')
    lc_kpis(data)
    st.markdown('---')
    if st.session_state.user_role == 'admin':
        compliance_matrix(data)
        st.markdown('---')
    c1, c2 = st.columns(2)
    with c1: lc_charts(data)
    lc_map(data)
    lc_tables(data)

# ── QC MONITORING ──────────────────────────────────────────
def qc_header():
    role = st.session_state.user_role
    user = st.session_state.current_user
    lga_txt = '- All LGAs' if role=='admin' else f'- {user}'
    c1,c2 = st.columns([3,1])
    with c1:
        st.markdown(f"""
        <div style="background:linear-gradient(120deg,#0f2d5e,#1a5ca8);color:white;
             padding:20px 28px;border-radius:10px;margin-bottom:8px">
          <div style="display:flex;align-items:center;gap:14px">
            <span style="background:rgba(255,255,255,.22);border-radius:8px;padding:6px 12px;
                  font-size:1.05rem;font-weight:900;letter-spacing:1px">SARMAAN</span>
            <div>
              <h2 style="margin:0;font-size:1.25rem;font-weight:800">
                QC Monitoring Dashboard {lga_txt}</h2>
              <p style="margin:0;font-size:.77rem;opacity:.78">
                Quality Control & Data Validation · Zamfara State · AMR Survey 2026</p>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        qc_data = st.session_state.qc_data
        n = len(qc_data) if qc_data is not None else 0
        st.markdown(f"""
        <div style="background:rgba(15,45,94,.08);border-radius:8px;padding:12px 16px;font-size:.78rem">
          <div>📊 AMR Survey QC · Zamfara</div>
          <div style="margin-top:4px;color:#1a5ca8;font-weight:600">
            👤 {'Administrator' if role=='admin' else user+' Coordinator'}</div>
          <div style="margin-top:4px">
            <span style="background:#{'dcfce7' if n>0 else 'fef3c7'};
              color:#{'15803d' if n>0 else '92400e'};border-radius:12px;
              padding:2px 8px;font-size:.72rem;font-weight:700">
              {'✓ '+str(n)+' records' if n>0 else '⏳ No data loaded'}</span>
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button('🔓 Logout', key='qc_logout'):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

def qc_data_source():
    with st.expander('⚙ QC Data Source', expanded=True):
        c1,c2 = st.columns([3,1])
        with c2:
            if st.button('↻ Load QC Data', use_container_width=True, key='qc_fetch'):
                with st.spinner('Fetching QC data from KoboToolbox…'):
                    recs, msg = fetch_kobo(KOBO_QC_URL, 'QC KoboToolbox')
                if recs:
                    # Store raw dicts as DataFrame-friendly list
                    st.session_state.qc_data       = recs  # raw dicts list, not parsed LC records
                    st.session_state.qc_fetch_time = datetime.now()
                    st.session_state.qc_status     = msg
                    st.success(msg); st.rerun()
                else:
                    # recs is empty — try fetching raw DataFrame
                    try:
                        resp = requests.get(KOBO_QC_URL, verify=False, timeout=60,
                                           headers={'User-Agent':'SARMAAN-Dashboard/1.0'})
                        if resp.ok:
                            xl = pd.ExcelFile(io.BytesIO(resp.content), engine='openpyxl')
                            sheet = next((s for s in xl.sheet_names
                                          if 'polygon' not in s.lower()), xl.sheet_names[0])
                            df = xl.parse(sheet, dtype=str).fillna('')
                            df_clean = filter_label_rows(df)
                            if not df_clean.empty:
                                st.session_state.qc_data       = df_clean.to_dict('records')
                                st.session_state.qc_fetch_time = datetime.now()
                                st.session_state.qc_status     = f'✓ {len(df_clean)} records loaded'
                                st.success(st.session_state.qc_status); st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error(msg)
                    except Exception as e:
                        st.error(f'Fetch error: {e}')
        with c1:
            st.info(st.session_state.qc_status)

        uploaded = st.file_uploader('Or upload QC Excel/CSV', type=['csv','xlsx'],
                                    key='qc_upload', label_visibility='visible')
        if uploaded:
            try:
                if uploaded.name.endswith('.xlsx'):
                    xl = pd.ExcelFile(io.BytesIO(uploaded.read()), engine='openpyxl')
                    sheet = next((s for s in xl.sheet_names
                                  if 'polygon' not in s.lower()), xl.sheet_names[0])
                    df = xl.parse(sheet, dtype=str).fillna('')
                else:
                    df = pd.read_csv(uploaded, dtype=str).fillna('')
                df = filter_label_rows(df)
                if not df.empty:
                    st.session_state.qc_data       = df.to_dict('records')
                    st.session_state.qc_fetch_time = datetime.now()
                    st.session_state.qc_status     = f'✓ {len(df)} records from {uploaded.name}'
                    st.success(st.session_state.qc_status); st.rerun()
                else:
                    st.error('No data rows found in uploaded file.')
            except Exception as e:
                st.error(f'Upload error: {e}')

def _gv(rec, *keys):
    for k in keys:
        v = rec.get(k,'')
        if v: return v
    return ''

def process_qc_metrics(data):
    lgas,wards,communities,enumerators = set(),set(),set(),set()
    total_children=total_mothers=approved=pending=rejected=duplicates=0
    hh_ids = {}
    for r in data:
        lga   = _gv(r,'Confirm your LGA','Q3. Local Government Area')
        ward  = _gv(r,'Confirm your ward','Q4. Ward')
        comm  = _gv(r,'Confirm your community','Q5. Community Name')
        enum  = _gv(r,'username','enum_name')
        vs    = _gv(r,'_validation_status','validation_status').lower().strip()
        hh_id = _gv(r,'unique_code','Household ID','_id')
        if lga: lgas.add(lga)
        if ward: wards.add(ward)
        if comm: communities.add(comm)
        if enum: enumerators.add(enum)
        total_children += int(r.get('Q47. Children 0-59m',0) or 0)
        total_mothers  += int(r.get('Q50. Mothers/caregivers enrolled',0) or 0)
        if 'approv' in vs and 'not' not in vs: approved+=1
        elif 'reject' in vs or 'not approv' in vs: rejected+=1
        else: pending+=1
        if hh_id: hh_ids[hh_id] = hh_ids.get(hh_id,0)+1
    duplicates = sum(c for c in hh_ids.values() if c>1)
    return dict(total=len(data),lgas=len(lgas),wards=len(wards),
                communities=len(communities),enumerators=len(enumerators),
                children=total_children,mothers=total_mothers,
                approved=approved,pending=pending,rejected=rejected,
                duplicates=duplicates)

def qc_kpi_cards(m):
    st.markdown('<span class="card-title">📊 Key Performance Indicators</span>', unsafe_allow_html=True)
    cols = st.columns(5)
    for col,(lbl,val,clr) in zip(cols,[
        ('Total Submissions', m['total'],   '#3b82f6'),
        ('LGAs Covered',      m['lgas'],    '#10b981'),
        ('Wards Covered',     m['wards'],   '#14b8a6'),
        ('Communities',       m['communities'],'#f97316'),
        ('Enumerators',       m['enumerators'],'#8b5cf6'),
    ]):
        with col:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{clr},{clr}cc);color:white;
                 padding:20px;border-radius:12px;box-shadow:0 4px 12px {clr}44;text-align:center">
              <div style="font-size:.72rem;opacity:.9;margin-bottom:4px;text-transform:uppercase;
                   letter-spacing:.5px">{lbl}</div>
              <div style="font-size:2.5rem;font-weight:800;letter-spacing:-1px">{val:,}</div>
            </div>""", unsafe_allow_html=True)

def qc_validation_cards(m):
    st.markdown('<span class="card-title">✅ Validation Status</span>', unsafe_allow_html=True)
    cols = st.columns(3)
    items = [
        ('✓ APPROVED',   m['approved'], '#16a34a','#dcfce7','Ready for Analysis'),
        ('⏳ PENDING',    m['pending'],  '#d97706','#fef3c7','Awaiting Review'),
        ('✗ REJECTED',   m['rejected'], '#dc2626','#fee2e2','Requires Action'),
    ]
    for col,(lbl,val,clr,bg,sub) in zip(cols,items):
        with col:
            st.markdown(f"""
            <div style="background:white;padding:20px;border-radius:12px;
                 border-left:5px solid {clr};box-shadow:0 2px 8px rgba(0,0,0,.08)">
              <div style="font-size:.7rem;color:#64748b;font-weight:600;
                   text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">{lbl}</div>
              <div style="font-size:2.5rem;font-weight:800;color:{clr};margin:0 0 8px">{val:,}</div>
              <span style="background:{bg};color:{clr};padding:4px 12px;
                    border-radius:20px;font-size:.78rem;font-weight:600">{sub}</span>
            </div>""", unsafe_allow_html=True)

def qc_community_coverage(data):
    st.markdown('<span class="card-title">🏘 Community Coverage Analysis</span>', unsafe_allow_html=True)
    cov = {}
    for r in data:
        lga  = _gv(r,'Confirm your LGA','Q3. Local Government Area').strip()
        ward = _gv(r,'Confirm your ward','Q4. Ward').strip()
        comm = _gv(r,'Confirm your community','Q5. Community Name').strip()
        key  = f'{lga}|{ward}|{comm}'
        cov[key] = cov.get(key,{'lga':lga,'ward':ward,'comm':comm,'actual':0})
        cov[key]['actual'] += 1

    rows = []
    total_plan=total_actual=0
    at_target=0
    for key,item in sorted(cov.items(), key=lambda x:(x[1]['lga'],x[1]['ward'])):
        planned = COMMUNITY_MAPPING.get(key, item['actual'])
        pct     = round(item['actual']/planned*100,1) if planned else 0
        status  = '✅ Complete' if pct>=100 else '⏳ On Track' if pct>=80 else '⚠ Behind'
        clr     = '#16a34a' if pct>=100 else '#d97706' if pct>=80 else '#dc2626'
        total_plan   += planned
        total_actual += item['actual']
        if pct>=100: at_target+=1
        rows.append({'LGA':item['lga'],'Ward':item['ward'],'Community':item['comm'],
                     'Planned':planned,'Actual':item['actual'],
                     'Coverage %':f'{pct}%','Status':status,'_clr':clr})

    # Summary metrics
    overall = round(total_actual/total_plan*100) if total_plan else 0
    m_cols = st.columns(4)
    for col,(lbl,val) in zip(m_cols,[
        ('Total Planned HH',f'{total_plan:,}'),
        ('Total Reached HH',f'{total_actual:,}'),
        ('Overall Coverage', f'{overall}%'),
        ('Communities @ Target',f'{at_target}/{len(cov)}')
    ]):
        col.metric(lbl, val)

    # Filter
    all_lga_names = sorted(set(r['LGA'] for r in rows))
    f_lga = st.selectbox('Filter by LGA', ['All LGAs']+all_lga_names, key='cov_lga_filter')
    filtered = [r for r in rows if f_lga=='All LGAs' or r['LGA']==f_lga]

    df_show = pd.DataFrame([{k:v for k,v in r.items() if k!='_clr'} for r in filtered])
    st.dataframe(df_show, use_container_width=True, hide_index=True)

def qc_issues_table(data):
    st.markdown('<span class="card-title">🚨 Detailed QC Issues</span>', unsafe_allow_html=True)
    issues = []
    for r in data:
        lga   = _gv(r,'Confirm your LGA','Q3. Local Government Area')
        ward  = _gv(r,'Confirm your ward','Q4. Ward')
        comm  = _gv(r,'Confirm your community','Q5. Community Name')
        hh_id = _gv(r,'unique_code','Household ID','_id')
        enum  = _gv(r,'username','enum_name')
        vs    = _gv(r,'_validation_status','validation_status') or 'Pending Review'

        # GPS check
        gps_lat = r.get('_Q9. GPS coordinates (capture from device)_latitude','') or r.get('latitude','')
        gps_lon = r.get('_Q9. GPS coordinates (capture from device)_longitude','') or r.get('longitude','')
        if not gps_lat and not gps_lon:
            issues.append({'LGA':lga,'Ward':ward,'Community':comm,'HH ID':hh_id,
                           'Enumerator':enum,'Validation Status':vs,'Issue Type':'Missing GPS Coordinates'})

        # Children without mothers
        ch = int(r.get('Q47. Children 0-59m',0) or 0)
        mo = int(r.get('Q50. Mothers/caregivers enrolled',0) or 0)
        if ch>0 and mo==0:
            issues.append({'LGA':lga,'Ward':ward,'Community':comm,'HH ID':hh_id,
                           'Enumerator':enum,'Validation Status':vs,'Issue Type':'Children Without Mothers'})

        # Duplicate HH
        hh_count = sum(1 for x in data if _gv(x,'unique_code','Household ID','_id')==hh_id and hh_id)
        if hh_count>1:
            issues.append({'LGA':lga,'Ward':ward,'Community':comm,'HH ID':hh_id,
                           'Enumerator':enum,'Validation Status':vs,'Issue Type':'Duplicate Household ID'})

        # Validation rejected
        vs_l = vs.lower()
        if 'reject' in vs_l or 'not approv' in vs_l:
            issues.append({'LGA':lga,'Ward':ward,'Community':comm,'HH ID':hh_id,
                           'Enumerator':enum,'Validation Status':vs,'Issue Type':'Validation Rejected'})

        # Education-occupation mismatch
        edu = r.get('Q13. What is the highest level of school you attended?','')
        occ = r.get('Q15. What is your main occupation?','')
        if edu=='No Formal Education' and occ=='Professional/technical/managerial':
            issues.append({'LGA':lga,'Ward':ward,'Community':comm,'HH ID':hh_id,
                           'Enumerator':enum,'Validation Status':vs,'Issue Type':'Education-Occupation Mismatch'})

        # Azithromycin flag
        azm = _gv(r,'Q57. Did any of your children receive azithromycin?',
                    'Q57. Did any of your children receive azithromycin')
        if azm in ("Yes","Don't know","Don't Know"):
            issues.append({'LGA':lga,'Ward':ward,'Community':comm,'HH ID':hh_id,
                           'Enumerator':enum,'Validation Status':vs,'Issue Type':'Azithromycin Received/Unknown'})

        # Incorrect phone flag
        phone_flag = r.get('🛑 Incorrect phone date/time','')
        if phone_flag:
            issues.append({'LGA':lga,'Ward':ward,'Community':comm,'HH ID':hh_id,
                           'Enumerator':enum,'Validation Status':vs,'Issue Type':'Incorrect Phone Date/Time'})

    if not issues:
        st.success(f'No QC issues detected across {len(data)} records.'); return

    st.info(f'**{len(issues)} issues** flagged across all records.')

    # Filters
    fc1,fc2,fc3 = st.columns(3)
    with fc1:
        f_lga  = st.selectbox('Filter by LGA',['All']+sorted(set(i['LGA'] for i in issues)),key='qi_lga')
    with fc2:
        f_type = st.selectbox('Filter by Issue Type',['All']+sorted(set(i['Issue Type'] for i in issues)),key='qi_type')
    with fc3:
        f_vs   = st.selectbox('Filter by Validation Status',['All']+sorted(set(i['Validation Status'] for i in issues)),key='qi_vs')

    filtered = [i for i in issues
                if (f_lga  == 'All' or i['LGA']               == f_lga)
                and (f_type == 'All' or i['Issue Type']        == f_type)
                and (f_vs   == 'All' or i['Validation Status'] == f_vs)]

    st.dataframe(pd.DataFrame(filtered), use_container_width=True, hide_index=True)

    csv_bytes = pd.DataFrame(filtered).to_csv(index=False).encode()
    st.download_button('⬇ Download Issues CSV', csv_bytes,
                       'qc_issues.csv', 'text/csv', key='dl_qc_issues')


def qc_data_alerts(m):
    st.markdown('<span class="card-title">⚠ Data Quality Alerts</span>', unsafe_allow_html=True)
    cols = st.columns(3)
    items = [
        ('Duplicate Households', m['duplicates'], '#ef4444', '#fee2e2',
         'Duplicate household IDs found' if m['duplicates'] else 'No duplicates detected'),
        ('Total Children (0-59m)', m['children'], '#3b82f6', '#dbeafe',
         'Children recorded across all HHs'),
        ('Total Mothers/Caregivers', m['mothers'], '#8b5cf6', '#ede9fe',
         'Mothers/caregivers enrolled'),
    ]
    for col, (lbl, val, clr, bg, sub) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div style="background:{bg};padding:18px 20px;border-radius:10px;
                 border-left:4px solid {clr}">
              <div style="font-size:.72rem;color:{clr};font-weight:700;
                   text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">{lbl}</div>
              <div style="font-size:2.2rem;font-weight:800;color:{clr}">{val:,}</div>
              <div style="font-size:.75rem;color:#64748b;margin-top:4px">{sub}</div>
            </div>""", unsafe_allow_html=True)


def qc_monitoring_page():
    qc_header()
    st.divider()
    qc_data_source()

    data = st.session_state.get('qc_data', [])

    # Auto-fetch on first load if no data
    if not data and not st.session_state.get('qc_auto_tried'):
        st.session_state.qc_auto_tried = True
        role = st.session_state.get('user_role', '')
        if role == 'admin':
            with st.spinner('Auto-fetching QC data…'):
                result, msg = fetch_kobo(KOBO_QC_URL, 'QC')
                if result is not None:
                    st.session_state.qc_data       = result
                    st.session_state.qc_fetch_time = datetime.now()
                    st.session_state.qc_status     = f'✓ {len(result)} records loaded'
                    data = result
                    st.rerun()

    if not data:
        st.info('No QC data loaded yet. Use the fetch button or upload a file above.')
        return

    m = process_qc_metrics(data)

    qc_kpi_cards(m)
    st.divider()
    qc_validation_cards(m)
    st.divider()
    qc_data_alerts(m)
    st.divider()
    qc_community_coverage(data)
    st.divider()
    qc_issues_table(data)
    st.divider()

    # Download all QC data
    csv_all = pd.DataFrame(data).to_csv(index=False).encode()
    st.download_button('⬇ Download All QC Data (CSV)', csv_all,
                       'qc_data_all.csv', 'text/csv', key='dl_qc_all')


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    _init()
    if not st.session_state.logged_in:
        login_page()
        return
    tab_lc, tab_qc = st.tabs([
        '📋 LC Supervisory Dashboard',
        '🔍 QC Monitoring Page',
    ])
    with tab_lc:
        lc_supervisory_page()
    with tab_qc:
        qc_monitoring_page()


if __name__ == '__main__':
    main()
