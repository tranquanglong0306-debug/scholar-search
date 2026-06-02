# ui/styles.py
# CSS tùy chỉnh cho giao diện Streamlit — Dark Academia theme

CUSTOM_CSS = """
<style>
/* ============================================================
   Google Fonts
   ============================================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

/* ============================================================
   Root Variables
   ============================================================ */
:root {
    --bg-primary: #0f1117;
    --bg-secondary: #1a1d27;
    --bg-card: #1e2130;
    --bg-card-hover: #252840;
    --accent-primary: #6c63ff;
    --accent-secondary: #a78bfa;
    --accent-green: #34d399;
    --accent-orange: #fb923c;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border-color: #2d3250;
    --border-accent: rgba(108, 99, 255, 0.25);
    --shadow-card: 0 4px 20px rgba(0,0,0,0.4);
    --shadow-card-hover: 0 10px 30px rgba(108, 99, 255, 0.15);
    --radius: 12px;
    --radius-sm: 8px;
    --font-body: 'Inter', sans-serif;
    --font-heading: 'Playfair Display', serif;
}

/* ============================================================
   Animations & Keyframes (Optimized for Snappier/Smoother Feel)
   ============================================================ */
@keyframes cardEntrance {
    from {
        opacity: 0;
        transform: translateY(12px); /* Giảm từ 24px xuống 12px cho cảm giác trượt nhẹ nhàng hơn */
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pageFadeIn {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulseBorder {
    0% { border-color: var(--border-color); }
    50% { border-color: var(--accent-primary); }
    100% { border-color: var(--border-color); }
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* ============================================================
   Base Layout
   ============================================================ */
html, body, .stApp {
    background-color: var(--bg-primary) !important;
    font-family: var(--font-body) !important;
    color: var(--text-primary) !important;
}

/* Page fade-in effect - Removed to eliminate flickering during Streamlit runs */
.main .block-container {
    padding: 1.5rem 2rem 3rem !important;
    max-width: 1200px !important;
}

/* ============================================================
   Header / Hero
   ============================================================ */
.scholar-header {
    background: linear-gradient(135deg, #1a1d27 0%, #252840 50%, #1a1d27 100%);
    border: 1px solid var(--border-accent);
    border-radius: var(--radius);
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
}

.scholar-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at center,
        rgba(108, 99, 255, 0.08) 0%, transparent 60%);
    pointer-events: none;
}

.scholar-header h1 {
    font-family: var(--font-heading) !important;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #a78bfa, #6c63ff, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem !important;
}

.scholar-header p {
    color: var(--text-secondary) !important;
    font-size: 1rem !important;
    margin: 0 !important;
}

/* ============================================================
   Article Cards & Animations
   ============================================================ */
.article-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: 
        transform 0.4s cubic-bezier(0.16, 1, 0.3, 1),
        border-color 0.4s cubic-bezier(0.16, 1, 0.3, 1),
        box-shadow 0.4s cubic-bezier(0.16, 1, 0.3, 1),
        background-color 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.article-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--accent-primary);
    box-shadow: var(--shadow-card-hover), 0 0 0 1px rgba(108,99,255,0.1);
    transform: translateY(-3px);
}

.article-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, var(--accent-primary), var(--accent-secondary));
    border-radius: 3px 0 0 3px;
    transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.article-card:hover::before {
    width: 5px;
}

/* Class to trigger staggered fade-in of cards - optimized to 0.25s */
.animate-card {
    opacity: 0;
    animation: cardEntrance 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.article-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    line-height: 1.4;
}

.article-title a {
    color: var(--text-primary) !important;
    text-decoration: none !important;
    transition: color 0.2s ease;
}

.article-title a:hover {
    color: var(--accent-secondary) !important;
}

.article-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.6rem;
    align-items: center;
}

.meta-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    transition: transform 0.2s ease;
}

.meta-badge:hover {
    transform: scale(1.05);
}

.badge-year {
    background: rgba(108, 99, 255, 0.15);
    color: var(--accent-secondary);
    border: 1px solid rgba(108, 99, 255, 0.3);
}

.badge-source {
    background: rgba(52, 211, 153, 0.1);
    color: var(--accent-green);
    border: 1px solid rgba(52, 211, 153, 0.25);
}

.badge-citations {
    background: rgba(251, 146, 60, 0.1);
    color: var(--accent-orange);
    border: 1px solid rgba(251, 146, 60, 0.25);
}

.article-authors {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-bottom: 0.4rem;
}

.article-journal {
    font-size: 0.82rem;
    color: var(--text-muted);
    font-style: italic;
}

.abstract-text {
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.65;
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-color);
}

/* ============================================================
   Citation Box
   ============================================================ */
.citation-box {
    background: #13151f;
    border: 1px solid var(--border-accent);
    border-radius: var(--radius-sm);
    padding: 1rem 1.25rem;
    font-size: 0.875rem;
    line-height: 1.7;
    color: var(--text-primary);
    font-family: 'Georgia', serif;
    margin-top: 0.5rem;
    position: relative;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.3);
}

.citation-box::before {
    content: '"';
    position: absolute;
    top: -10px; left: 16px;
    font-size: 3rem;
    color: var(--accent-primary);
    opacity: 0.4;
    font-family: Georgia, serif;
    line-height: 1;
}

/* ============================================================
   Stats Bar
   ============================================================ */
.stats-bar {
    display: flex;
    gap: 1.25rem;
    padding: 0.75rem 1.25rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    margin-bottom: 1.25rem;
    flex-wrap: wrap;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    color: var(--text-secondary);
}

.stat-number {
    font-weight: 600;
    color: var(--accent-secondary);
}

/* ============================================================
   Sidebar
   ============================================================ */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-color) !important;
}

[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--accent-secondary) !important;
    font-size: 0.9rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem !important;
}

/* Add custom animations to sidebar items on hover */
[data-testid="stSidebar"] .stButton > button {
    transition: all 0.25s ease !important;
}

/* ============================================================
   Buttons (Premium Feel Micro-interactions)
   ============================================================ */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-primary), #8b5cf6) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    font-family: var(--font-body) !important;
    padding: 0.5rem 1.4rem !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 2px 8px rgba(108, 99, 255, 0.15) !important;
    transition: 
        transform 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important,
        box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important,
        border-color 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important,
        filter 0.2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(108, 99, 255, 0.3) !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
    filter: brightness(1.08) !important;
}

.stButton > button:active {
    transform: translateY(0px) !important;
    box-shadow: 0 2px 6px rgba(108, 99, 255, 0.15) !important;
}

/* Danger / Remove button styling override */
.btn-danger > button {
    background: rgba(239, 68, 68, 0.1) !important;
    color: #f87171 !important;
    border: 1px solid rgba(239, 68, 68, 0.25) !important;
    box-shadow: none !important;
}

.btn-danger > button:hover {
    background: rgba(239, 68, 68, 0.2) !important;
    border-color: #ef4444 !important;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15) !important;
    color: white !important;
}

/* ============================================================
   Inputs & Selects
   ============================================================ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-body) !important;
    transition: 
        border-color 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important,
        box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important,
        background-color 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.25) !important;
    background-color: var(--bg-card-hover) !important;
}

/* ============================================================
   Tabs (Fluid Slide Indicators)
   ============================================================ */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: var(--radius-sm) !important;
    padding: 6px !important;
    gap: 6px !important;
    border: 1px solid var(--border-color) !important;
}

.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;
    border-radius: 6px !important;
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.5rem 1.2rem !important;
    transition: 
        color 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important,
        background-color 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
    background-color: rgba(255, 255, 255, 0.03) !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--accent-primary), #8b5cf6) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(108, 99, 255, 0.25) !important;
}

/* ============================================================
   Info / Success / Warning boxes
   ============================================================ */
.stAlert {
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-body) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
}

/* ============================================================
   Divider
   ============================================================ */
hr {
    border-color: var(--border-color) !important;
    margin: 1.5rem 0 !important;
    opacity: 0.6;
}

/* ============================================================
   Download buttons
   ============================================================ */
.stDownloadButton > button {
    background: linear-gradient(135deg, #059669, #34d399) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 8px rgba(52, 211, 153, 0.2) !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(52, 211, 153, 0.35) !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
}

/* ============================================================
   Metric components
   ============================================================ */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
    padding: 1rem !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}

/* ============================================================
   No results / empty state
   ============================================================ */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: var(--text-muted);
}

.empty-state .icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    display: block;
}

.empty-state p {
    font-size: 1rem;
    color: var(--text-muted);
}

/* ============================================================
   Scrollbar
   ============================================================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 3px;
    transition: background-color 0.2s ease;
}
::-webkit-scrollbar-thumb:hover { background: var(--accent-primary); }

/* ============================================================
   Custom Glassmorphic Spinner
   ============================================================ */
.stSpinner {
    background: rgba(30, 33, 48, 0.7) !important;
    border: 1px solid var(--border-accent) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border-radius: var(--radius) !important;
    padding: 1.25rem 2rem !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
    margin: 1.5rem 0 !important;
    display: flex !important;
    align-items: center !important;
    gap: 1.25rem !important;
    animation: pageFadeIn 0.3s ease-out forwards;
}

/* Customizing the spinner circle */
.stSpinner > div:first-child {
    width: 2.25rem !important;
    height: 2.25rem !important;
    border: 3px solid rgba(108, 99, 255, 0.15) !important;
    border-top: 3px solid var(--accent-primary) !important;
    border-right: 3px solid var(--accent-secondary) !important;
    border-radius: 50% !important;
}

/* Customize the spinner text */
.stSpinner p, .stSpinner label, .stSpinner span {
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    font-family: var(--font-body) !important;
    letter-spacing: 0.02em !important;
    margin: 0 !important;
}

/* ============================================================
   Tag clouds
   ============================================================ */
.tag-cloud { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
.tag {
    background: rgba(108, 99, 255, 0.1);
    color: var(--accent-secondary);
    border: 1px solid rgba(108, 99, 255, 0.2);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-weight: 500;
    transition: all 0.2s ease;
}

.tag:hover {
    background: rgba(108, 99, 255, 0.2);
    border-color: var(--accent-primary);
    transform: translateY(-1px);
}
</style>
"""


def inject_css() -> str:
    """Trả về CSS để inject vào Streamlit qua st.markdown()."""
    return CUSTOM_CSS
