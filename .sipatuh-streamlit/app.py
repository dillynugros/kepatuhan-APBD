import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# ==========================================
# 1. KONFIGURASI HALAMAN (HARUS PALING ATAS)
# ==========================================
st.set_page_config(
    page_title="SIPATUH - Kepatuhan Fiskal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. INJEKSI CUSTOM CSS (GAYA TAILWIND/HTML)
# ==========================================
st.markdown("""
<style>
    /* Mengurangi padding bawaan Streamlit agar lebih padat seperti web modern */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }
    
    /* Global Font Settings */
    html, body, [class*="css"]  {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #1e293b;
    }

    /* Sembunyikan elemen bawaan Streamlit yang mengganggu UI */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Styling Kartu (Metric Cards) meniru Tailwind di HTML */
    .metric-card-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        height: 100%;
    }
    
    .metric-card-container:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }

    .metric-title {
        font-size: 0.875rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 2.25rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }

    /* Styling Khusus untuk Kartu Status Kepatuhan (Indikator Border Kiri) */
    .status-card-aman {
        border-left: 6px solid #10b981;
    }
    
    .status-card-risiko {
        border-left: 6px solid #ef4444;
    }

    .status-card-peringatan {
        border-left: 6px solid #f59e0b;
    }

    /* Styling Sidebar Header */
    .sidebar-brand {
        font-size: 2rem;
        font-style: italic;
        font-weight: 900;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }
    
    .sidebar-subtitle {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        line-height: 1.4;
        margin-bottom: 2rem;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 1rem;
    }

    /* Kustomisasi Tabel Streamlit bawaan agar mirip desain HTML */
    [data-testid="stDataFrame"] {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI DATA
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1HdzT1xRkgftMuQYO1qeOLJpJj6po9zXdGZLwdG2Yagc/export?format=csv"
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Gagal mengambil data: {e}")
        return pd.DataFrame()

    df.columns = df.columns.str.strip().str.lower()
    if 'provinsi' in df.columns and 'pemda' not in df.columns:
        df.rename(columns={'provinsi': 'pemda'}, inplace=True)
        
    decode_region = {
        "banten": "Provinsi Banten", "provinsi banten": "Provinsi Banten",
        "tangerang selatan": "Kota Tangsel", "kota tangerang selatan": "Kota Tangsel",
        "kab tangerang": "Kab. Tangerang", "kabupaten tangerang": "Kab. Tangerang",
        "kab serang": "Kab. Serang", "kabupaten serang": "Kab. Serang",
        "lebak": "Kab. Lebak", "kab lebak": "Kab. Lebak", "kabupaten lebak": "Kab. Lebak",
        "pandeglang": "Kab. Pandeglang", "kab pandeglang": "Kab. Pandeglang", "kabupaten pandeglang": "Kab. Pandeglang",
        "cilegon": "Kota Cilegon", "kota cilegon": "Kota Cilegon",
        "kota serang": "Kota Serang", "kota tangerang": "Kota Tangerang"
    }
    
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
# 4. KOMPONEN CHART (LEBIH ELEGAN)
# ==========================================
def create_sleek_chart(data, x_col, y_col, title, threshold, is_max_limit=True):
    fig = go.Figure()
    
    # Penentuan Warna Berdasarkan Kepatuhan
    is_violation = data[y_col].iloc[-1] > threshold if is_max_limit else data[y_col].iloc[-1] < threshold
    
    if is_max_limit:
        main_color = '#ef4444' if is_violation else '#6366f1' # Merah jika pelanggaran, Indigo jika aman
        fill_color = 'rgba(239, 68, 68, 0.1)' if is_violation else 'rgba(99, 102, 241, 0.1)'
    else:
        main_color = '#f59e0b' if is_violation else '#4f46e5' # Kuning/Amber jika pelanggaran, Biru Tua jika aman
        fill_color = 'rgba(245, 158, 11, 0.1)' if is_violation else 'rgba(79, 70, 229, 0.1)'

    # Area Bawah Garis (Area Chart)
    fig.add_trace(go.Scatter(
        x=data[x_col], y=data[y_col],
        mode='lines+markers+text',
        name='Rasio',
        line=dict(color=main_color, width=3, shape='spline'), # Spline untuk kurva halus
        fill='tozeroy', fillcolor=fill_color,
        marker=dict(size=8, color='white', line=dict(width=2, color=main_color)),
        text=data[y_col].round(1).astype(str) + '%',
        textposition="top center",
        textfont=dict(size=12, color=main_color, family="Inter, sans-serif", weight="bold")
    ))
    
    # Garis Ambang Batas (Threshold)
    threshold_color = "#f43f5e" if is_max_limit else "#10b981"
    label_text = f"Batas {'Maksimal' if is_max_limit else 'Minimal'} {threshold}%"
    
    fig.add_hline(
        y=threshold, line_dash="dash", 
        line_color=threshold_color, line_width=2,
        annotation_text=label_text, 
        annotation_position="bottom right",
        annotation_font=dict(size=11, color=threshold_color, family="Inter, sans-serif", weight="bold")
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>", 
            font=dict(size=16, color='#1e293b', family="Inter, sans-serif"),
            y=0.95, x=0.02, xanchor='left', yanchor='top'
        ),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=10, r=20, t=60, b=20),
        xaxis=dict(showgrid=False, tickmode='linear', tickfont=dict(color='#64748b')),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', zeroline=False, range=[0, 80], tickfont=dict(color='#64748b')),
        height=320,
        hovermode="x unified"
    )
    return fig

# ==========================================
# 5. STRUKTUR UI UTAMA
# ==========================================
def main():
    with st.spinner("Memuat Data APBD..."):
        df_raw = load_data()
        
    if df_raw.empty:
        return
        
    df_summary = process_apbd_data(df_raw)
    list_pemda = sorted(df_summary['pemda'].unique().tolist())
    
    # -- SIDEBAR --
    with st.sidebar:
        st.markdown("""
            <div class='sidebar-brand'>
                <span style='color: #4f46e5;'>SI</span><span style='color: #0f172a;'>PATUH</span>
            </div>
            <div class='sidebar-subtitle'>
                Sistem Informasi Pemantauan Alokasi Tepat Undang-Undang HKPD
            </div>
        """, unsafe_allow_html=True)
        
        # Menggunakan styling bawaan namun dengan pilihan yang lebih clean
        selected_region = st.selectbox("Pilih Entitas Pemda", list_pemda)
        
        st.markdown("<div style='margin-top: 50vh;'></div>", unsafe_allow_html=True) # Spacer
        st.markdown("<p style='font-size: 0.7rem; color: #94a3b8; text-align: center;'>Bidang PPA II Kanwil DJPb Provinsi Banten<br>Monokrom Design System</p>", unsafe_allow_html=True)

    # Filter Data
    region_data = df_summary[df_summary['pemda'] == selected_region].sort_values('tahun')
    latest_data = region_data.iloc[-1]
    initial_data = region_data.iloc[0]
    
    cagr = 0
    if initial_data['total_belanja_t'] > 0 and len(region_data) > 1:
        years_diff = latest_data['tahun'] - initial_data['tahun']
        if years_diff > 0:
            cagr = ((latest_data['total_belanja_t'] / initial_data['total_belanja_t']) ** (1/years_diff) - 1) * 100

    # -- HEADER SECTION --
    st.markdown(f"""
        <div style='margin-bottom: 2rem;'>
            <h1 style='font-size: 2.5rem; font-weight: 900; color: #0f172a; margin: 0; padding: 0;'>{selected_region}</h1>
            <p style='color: #64748b; font-size: 1.1rem; font-weight: 500; margin: 0;'>Ringkasan Eksekutif Postur APBD Tahun {int(initial_data['tahun'])} - {int(latest_data['tahun'])}</p>
        </div>
    """, unsafe_allow_html=True)

    # -- ROW 1: SUMMARY METRICS --
    c1, c2, c3 = st.columns([1, 1, 1])
    
    with c1:
        st.markdown(f"""
        <div class='metric-card-container'>
            <div class='metric-title'>Total Belanja APBD {int(latest_data['tahun'])}</div>
            <div class='metric-value'>Rp {latest_data['total_belanja_t']:.2f} <span style='font-size: 1rem; color: #64748b; font-weight: 600;'>Triliun</span></div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        cagr_color = "#10b981" if cagr >= 0 else "#ef4444"
        cagr_icon = "📈" if cagr >= 0 else "📉"
        st.markdown(f"""
        <div class='metric-card-container'>
            <div class='metric-title'>CAGR Pertumbuhan</div>
            <div class='metric-value' style='color: {cagr_color};'>{cagr_icon} {cagr:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        # Menghitung rasio komposit sederhana untuk metrik ke-3 (bisa disesuaikan)
        status_teks = "AMAN" if (latest_data['rasio_pegawai'] <= 30 and latest_data['rasio_modal'] >= 40) else "PERLU ATENSI"
        status_warna = "#10b981" if status_teks == "AMAN" else "#ef4444"
        st.markdown(f"""
        <div class='metric-card-container' style='background-color: #f8fafc;'>
            <div class='metric-title'>Status Kepatuhan HKPD</div>
            <div class='metric-value' style='color: {status_warna}; font-size: 2rem;'>{status_teks}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # -- ROW 2: KPI KEPATUHAN HKPD --
    st.markdown("<h3 style='font-size: 1.25rem; font-weight: 800; color: #1e293b; margin-bottom: 1rem;'>Indikator Kepatuhan Rasio (Mandatory Spending)</h3>", unsafe_allow_html=True)
    
    kp1, kp2 = st.columns(2)
    p_ratio = latest_data['rasio_pegawai']
    m_ratio = latest_data['rasio_modal']
    
    with kp1:
        p_class = "status-card-aman" if p_ratio <= 30 else "status-card-risiko"
        icon_p = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>""" if p_ratio <= 30 else """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""
        
        st.markdown(f"""
        <div class='metric-card-container {p_class}'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div class='metric-title' style='margin:0;'>Rasio Belanja Pegawai</div>
                <div>{icon_p}</div>
            </div>
            <div style='margin-top: 1rem;'>
                <span style='font-size: 3.5rem; font-weight: 900; color: #0f172a; line-height: 1;'>{p_ratio:.1f}<span style='font-size: 2rem;'>%</span></span>
            </div>
            <div style='margin-top: 0.5rem; font-size: 0.875rem; color: #64748b; font-weight: 500;'>
                Batas Maksimal yang diizinkan: <b>30.0%</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kp2:
        m_class = "status-card-aman" if m_ratio >= 40 else "status-card-peringatan"
        icon_m = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>""" if m_ratio >= 40 else """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""

        st.markdown(f"""
        <div class='metric-card-container {m_class}'>
             <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div class='metric-title' style='margin:0;'>Rasio Belanja Infrastruktur (Modal)</div>
                <div>{icon_m}</div>
            </div>
            <div style='margin-top: 1rem;'>
                <span style='font-size: 3.5rem; font-weight: 900; color: #0f172a; line-height: 1;'>{m_ratio:.1f}<span style='font-size: 2rem;'>%</span></span>
            </div>
            <div style='margin-top: 0.5rem; font-size: 0.875rem; color: #64748b; font-weight: 500;'>
                Batas Minimal yang diwajibkan: <b>40.0%</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # -- ROW 3: GRAFIK TREND --
    st.markdown("<h3 style='font-size: 1.25rem; font-weight: 800; color: #1e293b; margin-bottom: 1rem;'>Tren Historis</h3>", unsafe_allow_html=True)
    
    # Bungkus grafik dalam div putih bergaya kartu menggunakan container Streamlit
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown("<div style='background: white; padding: 1rem; border-radius: 1rem; border: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.plotly_chart(create_sleek_chart(region_data, 'tahun', 'rasio_pegawai', 'Tren Belanja Pegawai', 30, True), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with ch2:
        st.markdown("<div style='background: white; padding: 1rem; border-radius: 1rem; border: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.plotly_chart(create_sleek_chart(region_data, 'tahun', 'rasio_modal', 'Tren Belanja Infrastruktur', 40, False), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # -- ROW 4: DATA TABEL (POSTUR) --
    st.markdown("<h3 style='font-size: 1.25rem; font-weight: 800; color: #1e293b; margin-bottom: 1rem;'>Analisis Detail Postur APBD</h3>", unsafe_allow_html=True)
    
    df_postur = df_raw[df_raw['pemda'] == selected_region]
    
    # Filter Tahun (Desain Inline)
    col_t1, col_t2, _ = st.columns([1, 1, 4])
    with col_t1:
        year_left = st.selectbox("Tahun Awal", options=sorted(df_postur['tahun'].dropna().unique()), index=max(0, len(df_postur['tahun'].unique())-2))
    with col_t2:
        year_right = st.selectbox("Tahun Akhir", options=sorted(df_postur['tahun'].dropna().unique()), index=max(0, len(df_postur['tahun'].unique())-1))

    if year_left and year_right:
        df_left = df_postur[df_postur['tahun'] == year_left].groupby(['kategori', 'akun'])['anggaran'].sum().reset_index()
        df_left = df_left.rename(columns={'anggaran': f'Nilai {int(year_left)}'})
        
        df_right = df_postur[df_postur['tahun'] == year_right].groupby(['kategori', 'akun'])['anggaran'].sum().reset_index()
        df_right = df_right.rename(columns={'anggaran': f'Nilai {int(year_right)}'})
        
        df_compare = pd.merge(df_left, df_right, on=['kategori', 'akun'], how='outer').fillna(0)
        
        df_compare['Pertumbuhan (%)'] = np.where(
            df_compare[f'Nilai {int(year_left)}'] > 0,
            ((df_compare[f'Nilai {int(year_right)}'] / df_compare[f'Nilai {int(year_left)}']) - 1) * 100,
            0
        )
        
        # Formatting untuk tampilan tabel
        df_display = df_compare.copy()
        df_display[f'Nilai {int(year_left)}'] = df_display[f'Nilai {int(year_left)}'].apply(lambda x: f"Rp {x:,.0f}".replace(',', '.'))
        df_display[f'Nilai {int(year_right)}'] = df_display[f'Nilai {int(year_right)}'].apply(lambda x: f"Rp {x:,.0f}".replace(',', '.'))
        df_display['Pertumbuhan (%)'] = df_display['Pertumbuhan (%)'].apply(lambda x: f"{x:+.1f}%")

        # Styling Tabel Streamlit menggunakan Pandas Styler
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=400
        )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        # Tombol Download Elegan
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Postur APBD')
            return output.getvalue()

        excel_data = convert_df_to_excel(df_compare) # Download data mentah (tanpa format string Rp)
        
        c_dl1, _ = st.columns([1, 4])
        with c_dl1:
            st.download_button(
                label="⬇️ Unduh Data Excel",
                data=excel_data,
                file_name=f"Postur_APBD_{selected_region.replace(' ', '_')}_{int(year_left)}_{int(year_right)}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
