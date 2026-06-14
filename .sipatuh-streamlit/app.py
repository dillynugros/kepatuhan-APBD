import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# ==========================================
# 1. KONFIGURASI HALAMAN & THEME OVERRIDE
# ==========================================
st.set_page_config(
    page_title="Dashboard Kepatuhan Fiskal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeksi CSS Tingkat Lanjut (Meniru Tailwind)
st.markdown("""
<style>
    /* Import Google Font (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* Override Global Font & Background App (slate-50) */
    html, body, [class*="css"] {
        font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #f8fafc; 
    }
    
    /* Override Sidebar (white border-right) */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* Mengurangi Padding Atas Bawaan Streamlit */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px !important; /* Membatasi lebar agar persis seperti max-w-5xl di HTML */
    }

    /* Menyembunyikan Elemen Header/Footer Bawaan */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* Kustomisasi Selectbox (Dropdown) Streamlit */
    div[data-baseweb="select"] > div {
        border-radius: 12px;
        border-color: #e2e8f0;
        background-color: #ffffff;
        font-weight: 600;
        color: #1e293b;
    }
    
    /* Kustomisasi DataFrame Streamlit */
    [data-testid="stDataFrame"] {
        border-radius: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KOMPONEN UI KUSTOM (HTML/CSS)
# ==========================================
def render_header_metric(title, value, subtitle="", is_cagr=False):
    """Merender kartu metrik kecil di pojok kanan atas"""
    val_color = "#059669" if is_cagr else "#0f172a"
    return f"""
    <div style="background-color: #ffffff; padding: 1rem 1.25rem; border-radius: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);">
        <p style="font-size: 9px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin: 0 0 4px 0;">{title}</p>
        <p style="font-size: 24px; font-weight: 900; color: {val_color}; margin: 0; letter-spacing: -0.05em;">{value} <span style="font-size: 10px; color: #94a3b8; letter-spacing: normal;">{subtitle}</span></p>
    </div>
    """

def render_kpi_card(title, ratio, limit_val, is_max_limit=True):
    """Merender kartu KPI besar dengan Progress Bar mirip HTML Tailwind"""
    if is_max_limit:
        is_safe = ratio <= limit_val
        safe_color = "#10b981" # emerald-500
        danger_color = "#ef4444" # rose-500
        limit_text = f"Max {limit_val:.1f}%"
    else:
        is_safe = ratio >= limit_val
        safe_color = "#4f46e5" # indigo-500
        danger_color = "#f59e0b" # amber-500
        limit_text = f"Min {limit_val:.1f}%"

    active_color = safe_color if is_safe else danger_color
    icon = "✅" if is_safe else "⚠️"
    progress_width = min(ratio, 100)

    return f"""
    <div style="background-color: #ffffff; padding: 2rem; border-radius: 2.5rem; border: 1px solid #e2e8f0; position: relative; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <div style="position: absolute; top: 0; left: 0; width: 8px; height: 100%; background-color: {active_color};"></div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; padding-left: 10px;">
            <h4 style="font-size: 1.125rem; font-weight: 900; color: #1e293b; text-transform: uppercase; margin: 0; letter-spacing: -0.025em;">{title}</h4>
            <span style="font-size: 1.25rem;">{icon}</span>
        </div>
        <div style="display: flex; align-items: baseline; gap: 4px; margin-bottom: 1.5rem; padding-left: 10px;">
            <span style="font-size: 3.75rem; font-weight: 900; color: #0f172a; letter-spacing: -0.05em; line-height: 1;">{ratio:.1f}%</span>
            <span style="font-size: 0.75rem; font-weight: 700; color: #94a3b8;">/ {limit_text}</span>
        </div>
        <div style="width: 100%; background-color: #f1f5f9; height: 12px; border-radius: 9999px; overflow: hidden; margin-left: 10px; width: calc(100% - 10px);">
            <div style="height: 100%; background-color: {active_color}; width: {progress_width}%; transition: width 1s ease-in-out;"></div>
        </div>
    </div>
    """

# ==========================================
# 3. FUNGSI DATA
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1HdzT1xRkgftMuQYO1qeOLJpJj6po9zXdGZLwdG2Yagc/export?format=csv"
    try:
        df = pd.read_csv(url)
    except Exception:
        return pd.DataFrame()

    df.columns = df.columns.str.strip().str.lower()
    if 'provinsi' in df.columns and 'pemda' not in df.columns:
        df.rename(columns={'provinsi': 'pemda'}, inplace=True)
        
    decode_region = {
        "banten": "Provinsi Banten", "kota tangerang selatan": "Kota Tangsel",
        "kabupaten tangerang": "Kab. Tangerang", "kabupaten serang": "Kab. Serang",
        "kabupaten lebak": "Kab. Lebak", "kabupaten pandeglang": "Kab. Pandeglang",
        "kota cilegon": "Kota Cilegon", "kota serang": "Kota Serang", "kota tangerang": "Kota Tangerang"
    }
    
    # Reverse mapping fallback
    for k, v in list(decode_region.items()):
        decode_region[k.replace('kabupaten ', 'kab ')] = v

    df['pemda'] = df['pemda'].astype(str).str.strip().str.lower().map(lambda x: decode_region.get(x, x.title()))
    df['anggaran'] = df['anggaran'].astype(str).str.replace(',', '', regex=False).str.replace(' ', '', regex=False)
    df['anggaran'] = pd.to_numeric(df['anggaran'], errors='coerce').fillna(0)
    df['tahun'] = pd.to_numeric(df['tahun'], errors='coerce')
    
    df = df.dropna(subset=['tahun', 'pemda', 'kategori'])
    df = df[df['anggaran'] != 0]
    return df

def process_apbd_data(df):
    df['kategori_lower'] = df['kategori'].astype(str).str.lower()
    df['akun_lower'] = df['akun'].astype(str).str.lower()
    
    belanja_mask = df['kategori_lower'].str.contains('belanja daerah', na=False)
    pegawai_mask = belanja_mask & df['akun_lower'].str.contains('pegawai', na=False)
    modal_mask = belanja_mask & df['akun_lower'].str.contains('modal', na=False)
    
    belanja_df = df[belanja_mask].groupby(['pemda', 'tahun'])['anggaran'].sum().reset_index(name='total_belanja')
    pegawai_df = df[pegawai_mask].groupby(['pemda', 'tahun'])['anggaran'].sum().reset_index(name='belanja_pegawai')
    modal_df = df[modal_mask].groupby(['pemda', 'tahun'])['anggaran'].sum().reset_index(name='belanja_modal')
    
    summary = pd.merge(belanja_df, pegawai_df, on=['pemda', 'tahun'], how='left')
    summary = pd.merge(summary, modal_df, on=['pemda', 'tahun'], how='left').fillna(0)
    
    summary['total_belanja_t'] = summary['total_belanja'] / 1e12
    summary['rasio_pegawai'] = np.where(summary['total_belanja'] > 0, (summary['belanja_pegawai'] / summary['total_belanja']) * 100, 0)
    summary['rasio_modal'] = np.where(summary['total_belanja'] > 0, (summary['belanja_modal'] / summary['total_belanja']) * 100, 0)
    
    return summary

# ==========================================
# 4. CHART PLOTLY (TRANSPARAN & CLEAN)
# ==========================================
def create_perfect_chart(data, x_col, y_col, title, threshold, is_max_limit=True):
    fig = go.Figure()
    
    is_violation = data[y_col].iloc[-1] > threshold if is_max_limit else data[y_col].iloc[-1] < threshold
    
    if is_max_limit:
        main_color = '#ef4444' if is_violation else '#6366f1'
    else:
        main_color = '#f59e0b' if is_violation else '#4f46e5'

    fig.add_trace(go.Scatter(
        x=data[x_col], y=data[y_col],
        mode='lines+markers+text',
        line=dict(color=main_color, width=4, shape='spline'),
        marker=dict(size=12, color='#ffffff', line=dict(width=3, color=main_color)),
        text=data[y_col].round(1).astype(str) + '%',
        textposition="top center",
        textfont=dict(size=11, color=main_color, family="Inter", weight="900"),
        hoverinfo='skip'
    ))
    
    threshold_color = "#fb7185" if is_max_limit else "#34d399"
    
    fig.add_hline(
        y=threshold, line_dash="dash", line_width=2, line_color=threshold_color,
        annotation_text=f"TARGET {'MAX' if is_max_limit else 'MIN'} {threshold}%", 
        annotation_position="bottom right",
        annotation_font=dict(size=10, color=threshold_color, family="Inter", weight="bold")
    )
    
    fig.update_layout(
        title=dict(text=f"<span style='font-size: 12px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em;'>{title}</span>", y=0.9, x=0.05, xanchor='left', yanchor='top'),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=20, t=50, b=10),
        xaxis=dict(showgrid=False, tickfont=dict(family="Inter", weight="bold", color="#cbd5e1"), showline=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickfont=dict(family="Inter", weight="bold", color="#cbd5e1"), range=[0, 80], zeroline=False),
        height=260, showlegend=False
    )
    return fig

# ==========================================
# 5. STRUKTUR APLIKASI
# ==========================================
def main():
    with st.spinner("Membaca Database APBD..."):
        df_raw = load_data()
        
    if df_raw.empty:
        st.error("Gagal terhubung ke Database. Pastikan link Spreadsheet valid.")
        return
        
    df_summary = process_apbd_data(df_raw)
    list_pemda = sorted(df_summary['pemda'].unique().tolist())
    
    # -- SIDEBAR KUSTOM --
    with st.sidebar:
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <h1 style="font-size: 1.5rem; font-weight: 900; font-style: italic; color: #0f172a; margin: 0; letter-spacing: -0.05em;">
                    <span style="color: #4f46e5;">SI</span>PATUH <span style="font-size: 10px; font-style: normal; color: #6366f1; vertical-align: super;">v.1.0</span>
                </h1>
                <p style="font-size: 10px; font-weight: 800; color: #818cf8; margin: 0; line-height: 1.2;">Sistem Informasi Pemantauan Alokasi Tepat Undang-Undang HKPD</p>
                <p style="font-size: 9px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 8px;">Bidang PPA II Kanwil DJPb Provinsi Banten</p>
            </div>
        """, unsafe_allow_html=True)
        
        selected_region = st.selectbox("Pilih Pemda", list_pemda, label_visibility="collapsed")

    region_data = df_summary[df_summary['pemda'] == selected_region].sort_values('tahun')
    if region_data.empty: return
    latest_data = region_data.iloc[-1]
    initial_data = region_data.iloc[0]
    
    cagr = 0
    if initial_data['total_belanja_t'] > 0 and len(region_data) > 1:
        cagr = ((latest_data['total_belanja_t'] / initial_data['total_belanja_t']) ** (1/(latest_data['tahun'] - initial_data['tahun'])) - 1) * 100

    # -- HEADER LAYOUT --
    st.markdown("""<div style="display: flex; align-items: center; gap: 6px; margin-bottom: 12px;">
        <span style="background-color: #e0e7ff; color: #4f46e5; padding: 4px 10px; border-radius: 8px; font-size: 10px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em;">🗺️ Dashboard Kepatuhan UU HKPD</span>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2.5, 1, 1])
    with c1:
        st.markdown(f"<h2 style='font-size: 2.5rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.05em; line-height: 1;'>{selected_region}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #94a3b8; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 8px;'>📅 Periode {int(initial_data['tahun'])} - {int(latest_data['tahun'])}</p>", unsafe_allow_html=True)
    with c2:
        st.markdown(render_header_metric(f"Total APBD {int(latest_data['tahun'])}", f"Rp {latest_data['total_belanja_t']:.2f}", "Triliun"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_header_metric("CAGR Pertumbuhan", f"{cagr:.1f}%", is_cagr=True), unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # -- KPI CARDS --
    k1, k2 = st.columns(2)
    with k1:
        st.markdown(render_kpi_card("Belanja Pegawai", latest_data['rasio_pegawai'], 30.0, True), unsafe_allow_html=True)
    with k2:
        st.markdown(render_kpi_card("Belanja Modal", latest_data['rasio_modal'], 40.0, False), unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # -- CHARTS ROW --
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown("<div style='background-color: #ffffff; padding: 1.5rem; border-radius: 2rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        st.plotly_chart(create_perfect_chart(region_data, 'tahun', 'rasio_pegawai', 'Rasio Belanja Pegawai', 30, True), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with ch2:
        st.markdown("<div style='background-color: #ffffff; padding: 1.5rem; border-radius: 2rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        st.plotly_chart(create_perfect_chart(region_data, 'tahun', 'rasio_modal', 'Proyeksi Rasio Belanja Infrastruktur', 40, False), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)

    # -- TABEL POSTUR APBD --
    st.markdown("""
        <div style="background-color: #ffffff; padding: 2.5rem; border-radius: 2.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);">
            <h3 style="font-size: 1.25rem; font-weight: 900; color: #1e293b; text-transform: uppercase; letter-spacing: -0.025em; margin-top: 0;">Postur APBD</h3>
    """, unsafe_allow_html=True)
    
    df_postur = df_raw[df_raw['pemda'] == selected_region]
    
    col_t1, col_t2, col_t3 = st.columns([2, 2, 8])
    with col_t1:
        year_left = st.selectbox("Tahun Awal", options=sorted(df_postur['tahun'].dropna().unique()), index=max(0, len(df_postur['tahun'].unique())-2), key="yl")
    with col_t2:
        year_right = st.selectbox("Tahun Akhir", options=sorted(df_postur['tahun'].dropna().unique()), index=max(0, len(df_postur['tahun'].unique())-1), key="yr")

    if year_left and year_right:
        df_left = df_postur[df_postur['tahun'] == year_left].groupby(['kategori', 'akun'])['anggaran'].sum().reset_index()
        df_right = df_postur[df_postur['tahun'] == year_right].groupby(['kategori', 'akun'])['anggaran'].sum().reset_index()
        
        df_compare = pd.merge(df_left, df_right, on=['kategori', 'akun'], how='outer', suffixes=('_l', '_r')).fillna(0)
        df_compare['Pertumbuhan'] = np.where(df_compare['anggaran_l'] > 0, ((df_compare['anggaran_r'] / df_compare['anggaran_l']) - 1) * 100, 0)
        
        # Formatting untuk UI
        df_display = df_compare.copy()
        df_display.rename(columns={'kategori': 'KATEGORI', 'akun': 'AKUN'}, inplace=True)
        df_display[f'NILAI {int(year_left)}'] = df_display['anggaran_l'].apply(lambda x: f"Rp {x:,.0f}".replace(',', '.'))
        df_display[f'NILAI {int(year_right)}'] = df_display['anggaran_r'].apply(lambda x: f"Rp {x:,.0f}".replace(',', '.'))
        df_display['GROWTH'] = df_display['Pertumbuhan'].apply(lambda x: f"{x:+.1f}%")
        
        st.dataframe(
            df_display[['KATEGORI', 'AKUN', f'NILAI {int(year_left)}', f'NILAI {int(year_right)}', 'GROWTH']],
            use_container_width=True, hide_index=True, height=350
        )
        
        def convert_df(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Postur APBD')
            return output.getvalue()

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Export Data Excel",
            data=convert_df(df_compare[['kategori', 'akun', 'anggaran_l', 'anggaran_r', 'Pertumbuhan']]),
            file_name=f"Postur_APBD_{selected_region.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
