import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="SIPATUH · Dashboard Kepatuhan Fiskal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. INJEKSI CSS PREMIUM
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif !important;
    }

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f0f4ff 0%, #f8fafc 50%, #faf5ff 100%);
    }

    /* ---- SIDEBAR ---- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 60%, #0f172a 100%);
        border-right: none !important;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }

    /* Selectbox di sidebar */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 14px !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        backdrop-filter: blur(10px);
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] svg {
        fill: #a5b4fc !important;
    }

    /* ---- MAIN CONTENT ---- */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }

    /* Sembunyikan elemen bawaan */
    header { visibility: hidden; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    /* ---- SELECTBOX di main (Postur APBD) ---- */
    div[data-baseweb="select"] > div {
        border-radius: 12px;
        border-color: #e2e8f0;
        background-color: #ffffff;
        font-weight: 700;
        color: #1e293b;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    /* ---- DATAFRAME ---- */
    [data-testid="stDataFrame"] {
        border-radius: 1.25rem;
        overflow: hidden;
        border: none !important;
    }
    [data-testid="stDataFrame"] > div {
        border-radius: 1.25rem;
        overflow: hidden;
        border: 1px solid #e2e8f0 !important;
    }

    /* ---- DOWNLOAD BUTTON ---- */
    [data-testid="stDownloadButton"] button {
        background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 0.6rem 1.5rem !important;
        letter-spacing: 0.025em !important;
        box-shadow: 0 4px 15px rgba(79,70,229,0.35) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(79,70,229,0.45) !important;
    }

    /* ---- SPINNER ---- */
    [data-testid="stSpinner"] {
        color: #6366f1 !important;
    }

    /* ---- LABEL SELECTBOX POSTUR ---- */
    .postur-label {
        font-size: 11px;
        font-weight: 800;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. KOMPONEN UI KUSTOM
# ==========================================

def render_sidebar_content(list_pemda, selected=None):
    """Sidebar premium dengan branding full"""
    st.markdown("""
        <div style="padding: 2rem 1.25rem 1.5rem 1.25rem;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:1.75rem;">
                <div style="width:42px; height:42px; background:linear-gradient(135deg,#6366f1,#818cf8); border-radius:12px;
                            display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0;
                            box-shadow: 0 4px 12px rgba(99,102,241,0.5);">
                    📊
                </div>
                <div>
                    <p style="font-size:1.35rem; font-weight:900; font-style:italic; color:#ffffff !important; 
                               margin:0; letter-spacing:-0.04em; line-height:1;">
                        <span style="color:#818cf8 !important;">SI</span>PATUH
                        <span style="font-size:9px; font-style:normal; color:#6366f1 !important; 
                                     vertical-align:super; font-weight:800; background:rgba(99,102,241,0.2);
                                     padding:2px 5px; border-radius:4px; margin-left:2px;">v1.0</span>
                    </p>
                    <p style="font-size:8.5px; font-weight:800; color:#818cf8 !important; margin:2px 0 0 0; line-height:1.3;">
                        Monitoring Alokasi UU HKPD
                    </p>
                </div>
            </div>

            <div style="height:1px; background:linear-gradient(90deg, rgba(99,102,241,0.5), transparent); margin-bottom:1.5rem;"></div>

            <div style="background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1); 
                         border-radius:14px; padding:1rem 1.1rem; margin-bottom:1.75rem; backdrop-filter:blur(10px);">
                <p style="font-size:8px; font-weight:900; color:#6366f1 !important; text-transform:uppercase; 
                           letter-spacing:0.12em; margin:0 0 6px 0;">Unit Kerja</p>
                <p style="font-size:11px; font-weight:700; color:#e2e8f0 !important; margin:0; line-height:1.4;">
                    Bidang PPA II<br>
                    <span style="color:#94a3b8 !important; font-weight:600;">Kanwil DJPb Prov. Banten</span>
                </p>
            </div>

            <p style="font-size:9px; font-weight:900; color:#6366f1 !important; text-transform:uppercase; 
                       letter-spacing:0.12em; margin:0 0 8px 0;">📍 Pilih Pemerintah Daerah</p>
        </div>
    """, unsafe_allow_html=True)


def render_header_metric(title, value, subtitle="", is_cagr=False):
    val_color = "#10b981" if is_cagr else "#1e293b"
    bg_color = "linear-gradient(135deg, #ecfdf5, #d1fae5)" if is_cagr else "#ffffff"
    border_color = "#a7f3d0" if is_cagr else "#e2e8f0"
    return f"""
    <div style="background:{bg_color}; padding:1.1rem 1.25rem; border-radius:1.5rem; 
                border:1px solid {border_color}; box-shadow:0 4px 12px rgba(0,0,0,0.06); height:100%;">
        <p style="font-size:8.5px; font-weight:900; color:{'#059669' if is_cagr else '#94a3b8'}; 
                  text-transform:uppercase; letter-spacing:0.1em; margin:0 0 6px 0;">{title}</p>
        <p style="font-size:26px; font-weight:900; color:{val_color}; margin:0; letter-spacing:-0.05em; line-height:1;">
            {value}
            <span style="font-size:10px; color:{'#6ee7b7' if is_cagr else '#94a3b8'}; 
                         font-weight:700; letter-spacing:normal; margin-left:3px;">{subtitle}</span>
        </p>
    </div>
    """


def render_kpi_card(title, ratio, limit_val, is_max_limit=True):
    if is_max_limit:
        is_safe = ratio <= limit_val
        safe_color  = "#10b981"
        danger_color = "#ef4444"
        limit_text  = f"Max {limit_val:.0f}%"
        safe_bg     = "linear-gradient(135deg,#ecfdf5,#d1fae5)"
        danger_bg   = "linear-gradient(135deg,#fff1f2,#ffe4e6)"
        safe_border = "#a7f3d0"
        danger_border = "#fecaca"
    else:
        is_safe = ratio >= limit_val
        safe_color  = "#4f46e5"
        danger_color = "#f59e0b"
        limit_text  = f"Min {limit_val:.0f}%"
        safe_bg     = "linear-gradient(135deg,#eef2ff,#e0e7ff)"
        danger_bg   = "linear-gradient(135deg,#fffbeb,#fef3c7)"
        safe_border = "#c7d2fe"
        danger_border = "#fde68a"

    active_color  = safe_color  if is_safe else danger_color
    active_bg     = safe_bg     if is_safe else danger_bg
    active_border = safe_border if is_safe else danger_border
    status_label  = "PATUH ✓" if is_safe else "PERHATIAN !"
    status_bg     = "rgba(16,185,129,0.15)" if is_safe else "rgba(239,68,68,0.12)"
    status_clr    = active_color
    progress      = min(ratio, 100)
    glow_color    = active_color + "33"  # 20% opacity hex

    return f"""
    <div style="background:{active_bg}; padding:2rem 2rem 1.75rem 2rem; border-radius:2rem; 
                border:1.5px solid {active_border}; position:relative; overflow:hidden; 
                box-shadow: 0 8px 24px {glow_color}, 0 2px 6px rgba(0,0,0,0.04);
                transition: transform 0.2s;">
        <div style="position:absolute; top:0; left:0; width:6px; height:100%; 
                    background:linear-gradient(180deg, {active_color}, {active_color}88);"></div>
        <div style="position:absolute; top:-30px; right:-30px; width:120px; height:120px; 
                    border-radius:50%; background:{active_color}0d;"></div>

        <div style="padding-left:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem;">
                <h4 style="font-size:0.7rem; font-weight:900; color:#475569; text-transform:uppercase; 
                            margin:0; letter-spacing:0.1em;">{title}</h4>
                <span style="background:{status_bg}; color:{status_clr}; padding:4px 10px; 
                             border-radius:20px; font-size:9px; font-weight:900; 
                             text-transform:uppercase; letter-spacing:0.08em;">{status_label}</span>
            </div>

            <div style="display:flex; align-items:baseline; gap:6px; margin-bottom:1.25rem;">
                <span style="font-size:3.5rem; font-weight:900; color:#0f172a; 
                             letter-spacing:-0.05em; line-height:1;">{ratio:.1f}%</span>
                <span style="font-size:0.75rem; font-weight:700; color:#94a3b8;">/ {limit_text}</span>
            </div>

            <div style="width:100%; background:rgba(255,255,255,0.6); height:10px; 
                         border-radius:9999px; overflow:hidden;">
                <div style="height:100%; background:linear-gradient(90deg,{active_color},{active_color}cc); 
                             width:{progress}%; border-radius:9999px;
                             box-shadow: 0 0 8px {active_color}66;"></div>
            </div>
        </div>
    </div>
    """


def render_section_title(icon, title, subtitle=""):
    return f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:1.25rem;">
        <div style="width:36px; height:36px; background:linear-gradient(135deg,#4f46e5,#818cf8); 
                     border-radius:10px; display:flex; align-items:center; justify-content:center; 
                     font-size:16px; flex-shrink:0; box-shadow:0 4px 10px rgba(79,70,229,0.3);">{icon}</div>
        <div>
            <h3 style="font-size:1rem; font-weight:900; color:#1e293b; margin:0; letter-spacing:-0.025em;">{title}</h3>
            {"" if not subtitle else f'<p style="font-size:11px; color:#94a3b8; font-weight:600; margin:2px 0 0 0;">{subtitle}</p>'}
        </div>
    </div>
    """


# ==========================================
# 4. FUNGSI DATA
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
    modal_mask   = belanja_mask & df['akun_lower'].str.contains('modal', na=False)

    belanja_df = df[belanja_mask].groupby(['pemda', 'tahun'])['anggaran'].sum().reset_index(name='total_belanja')
    pegawai_df = df[pegawai_mask].groupby(['pemda', 'tahun'])['anggaran'].sum().reset_index(name='belanja_pegawai')
    modal_df   = df[modal_mask].groupby(['pemda', 'tahun'])['anggaran'].sum().reset_index(name='belanja_modal')

    summary = pd.merge(belanja_df, pegawai_df, on=['pemda', 'tahun'], how='left')
    summary = pd.merge(summary, modal_df, on=['pemda', 'tahun'], how='left').fillna(0)

    summary['total_belanja_t'] = summary['total_belanja'] / 1e12
    summary['rasio_pegawai'] = np.where(summary['total_belanja'] > 0, (summary['belanja_pegawai'] / summary['total_belanja']) * 100, 0)
    summary['rasio_modal']   = np.where(summary['total_belanja'] > 0, (summary['belanja_modal']   / summary['total_belanja']) * 100, 0)
    return summary


# ==========================================
# 5. CHART PLOTLY
# ==========================================
def create_chart(data, x_col, y_col, title, threshold, is_max_limit=True):
    fig = go.Figure()
    is_violation = data[y_col].iloc[-1] > threshold if is_max_limit else data[y_col].iloc[-1] < threshold

    if is_max_limit:
        main_color = '#ef4444' if is_violation else '#6366f1'
        fill_color = 'rgba(239,68,68,0.06)' if is_violation else 'rgba(99,102,241,0.06)'
    else:
        main_color = '#f59e0b' if is_violation else '#10b981'
        fill_color = 'rgba(245,158,11,0.06)' if is_violation else 'rgba(16,185,129,0.06)'

    # Area fill
    fig.add_trace(go.Scatter(
        x=data[x_col], y=data[y_col],
        mode='lines',
        line=dict(width=0),
        fill='tozeroy',
        fillcolor=fill_color,
        hoverinfo='skip',
        showlegend=False
    ))

    # Main line
    fig.add_trace(go.Scatter(
        x=data[x_col], y=data[y_col],
        mode='lines+markers+text',
        line=dict(color=main_color, width=3.5, shape='spline'),
        marker=dict(size=11, color='#ffffff', line=dict(width=3, color=main_color)),
        text=data[y_col].round(1).astype(str) + '%',
        textposition="top center",
        textfont=dict(size=11, color=main_color, family="Inter", weight="bold"),
        hovertemplate='<b>%{x}</b><br>%{y:.1f}%<extra></extra>'
    ))

    threshold_color = "#fb7185" if is_max_limit else "#34d399"
    fig.add_hline(
        y=threshold, line_dash="dot", line_width=2, line_color=threshold_color,
        annotation_text=f"{'MAX' if is_max_limit else 'MIN'} {threshold}%",
        annotation_position="bottom right",
        annotation_font=dict(size=9, color=threshold_color, family="Inter", weight="bold")
    )

    fig.update_layout(
        title=dict(
            text=f"<span style='font-size:11px; font-weight:900; color:#94a3b8; text-transform:uppercase; letter-spacing:0.1em;'>{title}</span>",
            y=0.95, x=0.02, xanchor='left', yanchor='top'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=20, t=50, b=10),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(family="Inter", size=11, color="#cbd5e1"),
            showline=False, zeroline=False
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#f1f5f9', gridwidth=1,
            tickfont=dict(family="Inter", size=11, color="#cbd5e1"),
            range=[0, max(data[y_col].max() * 1.3, threshold * 1.4)],
            zeroline=False
        ),
        height=270, showlegend=False,
        hoverlabel=dict(
            bgcolor='#1e293b', bordercolor='#334155',
            font=dict(family='Inter', size=12, color='#f8fafc')
        )
    )
    return fig


# ==========================================
# 6. STRUKTUR APLIKASI
# ==========================================
def main():
    with st.spinner("🔄 Memuat data APBD dari sumber..."):
        df_raw = load_data()

    if df_raw.empty:
        st.error("❌ Gagal terhubung ke Database. Pastikan link Spreadsheet valid dan dapat diakses.")
        return

    df_summary  = process_apbd_data(df_raw)
    list_pemda  = sorted(df_summary['pemda'].unique().tolist())

    # ---- SIDEBAR ----
    with st.sidebar:
        render_sidebar_content(list_pemda)

        selected_region = st.selectbox(
            "Pilih Pemda", list_pemda,
            label_visibility="collapsed"
        )

        # Info navigasi
        st.markdown("""
            <div style="padding:1.5rem 1.25rem 0 1.25rem;">
                <div style="height:1px; background:linear-gradient(90deg,rgba(99,102,241,0.4),transparent); margin-bottom:1.5rem;"></div>
                <p style="font-size:8.5px; font-weight:800; color:#475569 !important; text-transform:uppercase; 
                           letter-spacing:0.1em; margin:0 0 12px 0;">Menu Analisis</p>
        """, unsafe_allow_html=True)

        for item in ["📊 Rasio Belanja Pegawai", "🏗️ Rasio Belanja Modal", "📈 Tren Historis", "🗂️ Postur APBD"]:
            st.markdown(f"""
            <div style="padding:9px 12px; border-radius:12px; margin-bottom:6px; 
                         background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.15); cursor:pointer;">
                <span style="font-size:12px; font-weight:700; color:#a5b4fc !important;">{item}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
                <div style="margin-top:auto; padding-top:2rem;">
                    <p style="font-size:8px; color:#334155 !important; text-align:center; font-weight:600;">
                        © 2026 Kanwil DJPb Provinsi Banten
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ---- DATA UNTUK REGION ----
    region_data  = df_summary[df_summary['pemda'] == selected_region].sort_values('tahun')
    if region_data.empty:
        return
    latest_data  = region_data.iloc[-1]
    initial_data = region_data.iloc[0]

    cagr = 0
    if initial_data['total_belanja_t'] > 0 and len(region_data) > 1:
        n = latest_data['tahun'] - initial_data['tahun']
        if n > 0:  # PERBAIKAN: Mencegah ZeroDivisionError
            cagr = ((latest_data['total_belanja_t'] / initial_data['total_belanja_t']) ** (1/n) - 1) * 100

    # ---- HEADER BADGE ----
    st.markdown("""
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:1.25rem;">
        <span style="background:linear-gradient(135deg,#4f46e5,#6366f1); color:#ffffff; padding:5px 14px; 
                     border-radius:20px; font-size:10px; font-weight:900; text-transform:uppercase; 
                     letter-spacing:0.1em; box-shadow:0 3px 10px rgba(79,70,229,0.4);">
            🗺️ Dashboard Kepatuhan UU HKPD
        </span>
        <span style="background:#f1f5f9; color:#64748b; padding:5px 12px; border-radius:20px; 
                     font-size:10px; font-weight:700; border:1px solid #e2e8f0;">
            Wilayah Provinsi Banten
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ---- HEADER ROW ----
    c1, c2, c3 = st.columns([2.5, 1, 1])
    with c1:
        st.markdown(f"""
        <div style="padding:0.25rem 0;">
            <h2 style="font-size:2.75rem; font-weight:900; color:#0f172a; margin:0; 
                        letter-spacing:-0.05em; line-height:1;">{selected_region}</h2>
            <p style="color:#94a3b8; font-size:11px; font-weight:700; text-transform:uppercase; 
                       letter-spacing:0.07em; margin:10px 0 0 0;">
                📅 Periode Data: {int(initial_data['tahun'])} – {int(latest_data['tahun'])}
            </p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(render_header_metric(
            f"Total APBD {int(latest_data['tahun'])}",
            f"Rp {latest_data['total_belanja_t']:.2f}", "Triliun"
        ), unsafe_allow_html=True)
    with c3:
        st.markdown(render_header_metric(
            "CAGR Belanja", f"{cagr:.1f}%", "per tahun", is_cagr=True
        ), unsafe_allow_html=True)

    st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)

    # ---- KPI CARDS ----
    st.markdown(render_section_title("📐", "Indikator Kepatuhan Fiskal", f"Tahun {int(latest_data['tahun'])} · Data Terkini"), unsafe_allow_html=True)
    k1, k2 = st.columns(2)
    with k1:
        st.markdown(render_kpi_card("Belanja Pegawai", latest_data['rasio_pegawai'], 30.0, True), unsafe_allow_html=True)
    with k2:
        st.markdown(render_kpi_card("Belanja Modal / Infrastruktur", latest_data['rasio_modal'], 40.0, False), unsafe_allow_html=True)

    st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)

    # ---- CHARTS ----
    st.markdown(render_section_title("📈", "Tren Historis Rasio Belanja", "Seluruh periode data yang tersedia"), unsafe_allow_html=True)
    ch1, ch2 = st.columns(2)
    chart_style = "background:#ffffff; padding:1.5rem; border-radius:1.75rem; border:1px solid #e2e8f0; box-shadow:0 4px 16px rgba(0,0,0,0.05);"

    with ch1:
        st.markdown(f"<div style='{chart_style}'>", unsafe_allow_html=True)
        st.plotly_chart(
            create_chart(region_data, 'tahun', 'rasio_pegawai', 'Rasio Belanja Pegawai', 30, True),
            use_container_width=True, config={'displayModeBar': False}
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with ch2:
        st.markdown(f"<div style='{chart_style}'>", unsafe_allow_html=True)
        st.plotly_chart(
            create_chart(region_data, 'tahun', 'rasio_modal', 'Rasio Belanja Modal / Infrastruktur', 40, False),
            use_container_width=True, config={'displayModeBar': False}
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)

    # ---- POSTUR APBD ----
    st.markdown(f"""
    <div style="background:#ffffff; padding:2.5rem; border-radius:2rem; border:1px solid #e2e8f0;
                box-shadow:0 4px 16px rgba(0,0,0,0.05);">
        {render_section_title("🗂️", "Postur APBD", f"Perbandingan anggaran per tahun · {selected_region}")}
    """, unsafe_allow_html=True)

    df_postur = df_raw[df_raw['pemda'] == selected_region]
    tahun_opts = sorted(df_postur['tahun'].dropna().unique())

    col_t1, col_t2, col_spacer = st.columns([1.5, 1.5, 5])
    with col_t1:
        st.markdown('<p class="postur-label">📅 Tahun Awal</p>', unsafe_allow_html=True)
        year_left = st.selectbox("Tahun Awal", options=tahun_opts,
                                 index=max(0, len(tahun_opts)-2), key="yl", label_visibility="collapsed")
    with col_t2:
        st.markdown('<p class="postur-label">📅 Tahun Akhir</p>', unsafe_allow_html=True)
        year_right = st.selectbox("Tahun Akhir", options=tahun_opts,
                                  index=max(0, len(tahun_opts)-1), key="yr", label_visibility="collapsed")

    if year_left and year_right:
        df_left  = df_postur[df_postur['tahun'] == year_left].groupby(['kategori', 'akun'])['anggaran'].sum().reset_index()
        df_right = df_postur[df_postur['tahun'] == year_right].groupby(['kategori', 'akun'])['anggaran'].sum().reset_index()

        df_compare = pd.merge(df_left, df_right, on=['kategori', 'akun'], how='outer', suffixes=('_l', '_r')).fillna(0)
        df_compare['Pertumbuhan'] = np.where(
            df_compare['anggaran_l'] > 0,
            ((df_compare['anggaran_r'] / df_compare['anggaran_l']) - 1) * 100, 0
        )

        df_display = df_compare.copy()
        df_display.rename(columns={'kategori': 'KATEGORI', 'akun': 'AKUN'}, inplace=True)
        df_display[f'NILAI {int(year_left)}']  = df_display['anggaran_l'].apply(lambda x: f"Rp {x:,.0f}".replace(',', '.'))
        df_display[f'NILAI {int(year_right)}'] = df_display['anggaran_r'].apply(lambda x: f"Rp {x:,.0f}".replace(',', '.'))
        df_display['GROWTH']                   = df_display['Pertumbuhan'].apply(lambda x: f"{x:+.1f}%")

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        st.dataframe(
            df_display[['KATEGORI', 'AKUN', f'NILAI {int(year_left)}', f'NILAI {int(year_right)}', 'GROWTH']],
            use_container_width=True, hide_index=True, height=340
        )

        def convert_df(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Postur APBD')
            return output.getvalue()

        st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)
        cola, colb = st.columns([1, 4])
        with cola:
            st.download_button(
                label="⬇️ Export Excel",
                data=convert_df(df_compare[['kategori', 'akun', 'anggaran_l', 'anggaran_r', 'Pertumbuhan']]),
                file_name=f"Postur_APBD_{selected_region.replace(' ', '_')}_{int(year_left)}_vs_{int(year_right)}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---- FOOTER ----
    st.markdown("""
    <div style="margin-top:3rem; padding:1.5rem 0; border-top:1px solid #e2e8f0; 
                display:flex; justify-content:space-between; align-items:center;">
        <p style="font-size:11px; color:#94a3b8; font-weight:600; margin:0;">
            <span style="font-weight:900; color:#6366f1;">SIPATUH</span> · Sistem Informasi Pemantauan Alokasi Tepat UU HKPD
        </p>
        <p style="font-size:10px; color:#cbd5e1; font-weight:600; margin:0;">
            Bidang PPA II · Kanwil DJPb Provinsi Banten · v1.0
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
