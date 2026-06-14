import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="SIPATUH HKPD",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan yang lebih profesional dan mirip Tailwind
st.markdown("""
    <style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    .status-aman { color: #10b981; font-weight: bold; }
    .status-risiko { color: #ef4444; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FUNGSI PENGAMBILAN & PEMROSESAN DATA
# ==========================================
@st.cache_data(ttl=3600) # Cache data selama 1 jam
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1HdzT1xRkgftMuQYO1qeOLJpJj6po9zXdGZLwdG2Yagc/export?format=csv"
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Spreadsheet: {e}")
        return pd.DataFrame()

    # Normalisasi nama kolom
    df.columns = df.columns.str.strip().str.lower()
    
    if 'provinsi' in df.columns and 'pemda' not in df.columns:
        df.rename(columns={'provinsi': 'pemda'}, inplace=True)
        
    # Kamus dekode region sesuai JS
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
    
    # Pembersihan Data
    df['pemda'] = df['pemda'].astype(str).str.strip().str.lower().map(lambda x: decode_region.get(x, x.title()))
    df['anggaran'] = df['anggaran'].astype(str).str.replace(',', '', regex=False).str.replace(' ', '', regex=False)
    df['anggaran'] = pd.to_numeric(df['anggaran'], errors='coerce').fillna(0)
    df['tahun'] = pd.to_numeric(df['tahun'], errors='coerce')
    
    # Hapus baris yang tidak valid
    df = df.dropna(subset=['tahun', 'pemda', 'kategori'])
    df = df[df['anggaran'] != 0]
    
    return df

def process_apbd_data(df):
    # Buat mask pencarian
    df['kategori_lower'] = df['kategori'].astype(str).str.lower()
    df['akun_lower'] = df['akun'].astype(str).str.lower()
    
    belanja_mask = df['kategori_lower'].str.contains('belanja daerah', na=False)
    pegawai_mask = belanja_mask & df['akun_lower'].str.contains('pegawai', na=False)
    modal_mask = belanja_mask & df['akun_lower'].str.contains('modal', na=False)
    
    # Agregasi
    belanja_df = df[belanja_mask].groupby(['pemda', 'tahun'])['anggaran'].sum().reset_index(name='total_belanja')
    pegawai_df = df[pegawai_mask].groupby(['pemda', 'tahun'])['anggaran'].sum().reset_index(name='belanja_pegawai')
    modal_df = df[modal_mask].groupby(['pemda', 'tahun'])['anggaran'].sum().reset_index(name='belanja_modal')
    
    # Merge data
    summary = pd.merge(belanja_df, pegawai_df, on=['pemda', 'tahun'], how='left')
    summary = pd.merge(summary, modal_df, on=['pemda', 'tahun'], how='left').fillna(0)
    
    # Konversi ke Triliun & Hitung Rasio
    summary['total_belanja_t'] = summary['total_belanja'] / 1e12
    summary['belanja_pegawai_t'] = summary['belanja_pegawai'] / 1e12
    summary['belanja_modal_t'] = summary['belanja_modal'] / 1e12
    
    summary['rasio_pegawai'] = np.where(summary['total_belanja'] > 0, (summary['belanja_pegawai'] / summary['total_belanja']) * 100, 0)
    summary['rasio_modal'] = np.where(summary['total_belanja'] > 0, (summary['belanja_modal'] / summary['total_belanja']) * 100, 0)
    
    return summary

# ==========================================
# KOMPONEN CHART (PLOTLY)
# ==========================================
def create_trend_chart(data, x_col, y_col, title, threshold, is_max_limit=True):
    fig = go.Figure()
    
    # Garis Data Aktual
    color = '#ef4444' if is_max_limit else '#4f46e5' 
    if is_max_limit:
        is_violation = data[y_col].iloc[-1] > threshold if len(data) > 0 else False
        line_color = '#ef4444' if is_violation else '#6366f1'
    else:
        is_violation = data[y_col].iloc[-1] < threshold if len(data) > 0 else False
        line_color = '#f59e0b' if is_violation else '#4f46e5'

    fig.add_trace(go.Scatter(
        x=data[x_col], y=data[y_col],
        mode='lines+markers+text',
        name='Rasio',
        line=dict(color=line_color, width=4),
        marker=dict(size=10, color='white', line=dict(width=2, color=line_color)),
        text=data[y_col].round(1).astype(str) + '%',
        textposition="top center",
        textfont=dict(size=11, color=line_color, family="Arial Black")
    ))
    
    # Garis Ambang Batas (Threshold)
    fig.add_hline(
        y=threshold, line_dash="dash", 
        line_color="#fb7185" if is_max_limit else "#34d399", 
        annotation_text=f"Batas {'Maks' if is_max_limit else 'Min'} {threshold}%", 
        annotation_position="bottom right"
    )
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='#64748b')),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, tickmode='linear'),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', zeroline=False, range=[0, 80]),
        height=280
    )
    return fig

# ==========================================
# APLIKASI UTAMA
# ==========================================
def main():
    with st.spinner("Menyinkronkan Data dari Database APBD..."):
        df_raw = load_data()
        
    if df_raw.empty:
        return
        
    df_summary = process_apbd_data(df_raw)
    list_pemda = sorted(df_summary['pemda'].unique().tolist())
    
    # ==========================================
    # SIDEBAR
    # ==========================================
    with st.sidebar:
        st.markdown("""
            <h1 style='font-size: 24px; font-style: italic; font-weight: 900; letter-spacing: -1px;'>
                <span style='color: #4f46e5;'>SI</span><span style='color: #1e293b;'>PATUH</span>
                <span style='font-size: 10px; color: #6366f1; font-style: normal; vertical-align: top;'>v.1.0</span>
            </h1>
            <p style='font-size: 11px; color: #818cf8; font-weight: bold; line-height: 1.2; margin-bottom: 20px;'>
                Sistem Informasi Pemantauan Alokasi Tepat Undang-Undang HKPD
            </p>
        """, unsafe_allow_html=True)
        
        selected_region = st.radio("Pilih Pemerintah Daerah:", list_pemda)
        
        st.markdown("---")
        st.markdown("<p style='font-size: 10px; color: #94a3b8; text-align: center;'>Bidang PPA II Kanwil DJPb Provinsi Banten</p>", unsafe_allow_html=True)

    # Filter data berdasarkan Region
    region_data = df_summary[df_summary['pemda'] == selected_region].sort_values('tahun')
    
    if region_data.empty:
        st.warning(f"Data tidak tersedia untuk {selected_region}")
        return

    latest_data = region_data.iloc[-1]
    initial_data = region_data.iloc[0]
    
    # Hitung CAGR
    cagr = 0
    if initial_data['total_belanja_t'] > 0 and len(region_data) > 1:
        years_diff = latest_data['tahun'] - initial_data['tahun']
        if years_diff > 0:
            cagr = ((latest_data['total_belanja_t'] / initial_data['total_belanja_t']) ** (1/years_diff) - 1) * 100

    # ==========================================
    # HEADER METRICS
    # ==========================================
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    with col_header1:
        st.markdown(f"<h2 style='font-size: 36px; font-weight: 900; color: #0f172a; margin-bottom: 0;'>{selected_region}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #94a3b8; font-weight: bold; font-size: 14px;'>Periode {int(initial_data['tahun'])} - {int(latest_data['tahun'])}</p>", unsafe_allow_html=True)
    
    with col_header2:
        st.markdown(f"""
        <div class='metric-card'>
            <p style='font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin: 0;'>Total APBD {int(latest_data['tahun'])}</p>
            <h3 style='font-size: 24px; font-weight: 900; color: #0f172a; margin: 0;'>Rp {latest_data['total_belanja_t']:.2f} <span style='font-size: 12px; color: #94a3b8;'>Triliun</span></h3>
        </div>
        """, unsafe_allow_html=True)

    with col_header3:
        st.markdown(f"""
        <div class='metric-card'>
            <p style='font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin: 0;'>CAGR Pertumbuhan</p>
            <h3 style='font-size: 24px; font-weight: 900; color: #059669; margin: 0;'>{cagr:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # KPI KEPATUHAN HKPD
    # ==========================================
    col_kpi1, col_kpi2 = st.columns(2)
    
    p_ratio = latest_data['rasio_pegawai']
    m_ratio = latest_data['rasio_modal']
    
    p_aman = p_ratio <= 30
    m_aman = m_ratio >= 40

    with col_kpi1:
        status_color = "#10b981" if p_aman else "#ef4444"
        icon = "✅" if p_aman else "⚠️"
        st.markdown(f"""
        <div class='metric-card' style='border-left: 8px solid {status_color};'>
            <div style='display: flex; justify-content: space-between;'>
                <h4 style='font-size: 18px; font-weight: 900; text-transform: uppercase; margin:0;'>Belanja Pegawai</h4>
                <span>{icon}</span>
            </div>
            <div style='margin-top: 15px;'>
                <span style='font-size: 48px; font-weight: 900;'>{p_ratio:.1f}%</span>
                <span style='font-size: 14px; font-weight: bold; color: #94a3b8;'> / 30.0% Max</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        status_color = "#4f46e5" if m_aman else "#f59e0b"
        icon = "✅" if m_aman else "⚠️"
        st.markdown(f"""
        <div class='metric-card' style='border-left: 8px solid {status_color};'>
            <div style='display: flex; justify-content: space-between;'>
                <h4 style='font-size: 18px; font-weight: 900; text-transform: uppercase; margin:0;'>Belanja Modal</h4>
                <span>{icon}</span>
            </div>
            <div style='margin-top: 15px;'>
                <span style='font-size: 48px; font-weight: 900;'>{m_ratio:.1f}%</span>
                <span style='font-size: 14px; font-weight: bold; color: #94a3b8;'> / 40.0% Min</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # GRAFIK TREND
    # ==========================================
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.plotly_chart(
            create_trend_chart(region_data, 'tahun', 'rasio_pegawai', 'Rasio Belanja Pegawai (%)', 30, True), 
            use_container_width=True
        )

    with col_chart2:
        st.plotly_chart(
            create_trend_chart(region_data, 'tahun', 'rasio_modal', 'Proyeksi Rasio Belanja Infrastruktur (%)', 40, False), 
            use_container_width=True
        )

    # ==========================================
    # POSTUR APBD (TABEL PERBANDINGAN)
    # ==========================================
    st.markdown("<br><h3 style='font-weight: 900; text-transform: uppercase; color: #1e293b;'>Analisis Postur APBD</h3>", unsafe_allow_html=True)
    
    # Filter data mentah hanya untuk region yang dipilih
    df_postur = df_raw[df_raw['pemda'] == selected_region]
    
    col_filter1, col_filter2, _ = st.columns([1, 1, 3])
    with col_filter1:
        year_left = st.selectbox("Tahun Awal", options=sorted(df_postur['tahun'].dropna().unique()), index=max(0, len(df_postur['tahun'].unique())-2))
    with col_filter2:
        year_right = st.selectbox("Tahun Akhir", options=sorted(df_postur['tahun'].dropna().unique()), index=max(0, len(df_postur['tahun'].unique())-1))

    if year_left and year_right:
        # Agregasi data untuk tabel postur
        df_left = df_postur[df_postur['tahun'] == year_left].groupby(['kategori', 'akun'])['anggaran'].sum().reset_index()
        df_left = df_left.rename(columns={'anggaran': f'Nilai {int(year_left)}'})
        
        df_right = df_postur[df_postur['tahun'] == year_right].groupby(['kategori', 'akun'])['anggaran'].sum().reset_index()
        df_right = df_right.rename(columns={'anggaran': f'Nilai {int(year_right)}'})
        
        # Gabungkan data kiri dan kanan
        df_compare = pd.merge(df_left, df_right, on=['kategori', 'akun'], how='outer').fillna(0)
        
        # Hitung Growth
        df_compare['Pertumbuhan (%)'] = np.where(
            df_compare[f'Nilai {int(year_left)}'] > 0,
            ((df_compare[f'Nilai {int(year_right)}'] / df_compare[f'Nilai {int(year_left)}']) - 1) * 100,
            0
        )
        
        # Format tampilan Rupiah
        df_compare[f'Nilai {int(year_left)}'] = df_compare[f'Nilai {int(year_left)}'].apply(lambda x: f"Rp {x:,.0f}".replace(',', '.'))
        df_compare[f'Nilai {int(year_right)}'] = df_compare[f'Nilai {int(year_right)}'].apply(lambda x: f"Rp {x:,.0f}".replace(',', '.'))
        df_compare['Pertumbuhan (%)'] = df_compare['Pertumbuhan (%)'].apply(lambda x: f"{x:+.1f}%")

        st.dataframe(
            df_compare,
            use_container_width=True,
            hide_index=True
        )

        # Tombol Download Excel
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Postur APBD')
            processed_data = output.getvalue()
            return processed_data

        excel_data = convert_df_to_excel(df_compare)
        st.download_button(
            label="📥 Export to Excel",
            data=excel_data,
            file_name=f"Perbandingan_Postur_APBD_{selected_region}_{year_left}_vs_{year_right}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
