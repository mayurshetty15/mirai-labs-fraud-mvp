"""Queue-first Streamlit analyst console."""

from html import escape
import importlib.util
from pathlib import Path
from typing import Any

import requests
import streamlit as st
import streamlit.components.v1 as components

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TIME_UTILS_PATH = PROJECT_ROOT / "app" / "time_utils.py"
_time_utils_spec = importlib.util.spec_from_file_location(
    "mirai_time_utils", TIME_UTILS_PATH
)
if _time_utils_spec is None or _time_utils_spec.loader is None:
    raise ImportError(f"Unable to load time utilities from {TIME_UTILS_PATH}")
_time_utils = importlib.util.module_from_spec(_time_utils_spec)
_time_utils_spec.loader.exec_module(_time_utils)
format_dataset_date = _time_utils.format_dataset_date
format_dataset_time = _time_utils.format_dataset_time

API_URL = "http://localhost:8001"


def api_get(path: str) -> Any:
    response = requests.get(f"{API_URL}{path}", timeout=120)
    response.raise_for_status()
    return response.json()


def inject_fintech_theme() -> None:
    """Apply a clean, professional fintech dashboard theme with strong contrast."""
    st.markdown(
        """
        <style>
            :root {
                --bg: #F8FAFC;
                --surface: #FFFFFF;
                --surface-soft: #F8FAFC;
                --border: #E2E8F0;
                --navy: #0F172A;
                --blue: #2563EB;
                --teal: #0F766E;
                --green: #16A34A;
                --amber: #D97706;
                --red: #DC2626;
                --purple: #7C3AED;
                --text: #0F172A;
                --secondary: #64748B;
                --muted: #94A3B8;
                --shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 22px rgba(15, 23, 42, 0.04);
                --radius: 12px;
            }

            html, body, [data-testid="stAppViewContainer"] {
                background: var(--bg);
                color: var(--text);
            }

            .stApp {
                background: var(--bg);
                color: var(--text);
            }

            .block-container {
                max-width: 1480px;
                padding: 1.1rem 1.5rem 2.5rem;
            }

            .stApp {
                font-family: "Aptos Display", "Segoe UI", sans-serif;
            }

                [data-testid="stToolbar"],
                [data-testid="stDecoration"],
                [data-testid="stStatusWidget"],
                #MainMenu,
                footer {
                    display: none !important;
                }

                header {
                    visibility: hidden;
                    height: 0;
                }

            .app-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                background: linear-gradient(120deg, #122033 0%, #173B4D 58%, #0E7490 100%);
                color: #FFFFFF;
                border-radius: 18px;
                padding: 1.15rem 1.35rem;
                margin-bottom: 1.25rem;
                box-shadow: 0 14px 30px rgba(18, 32, 51, 0.18);
            }

            .brand-lockup {
                display: flex;
                align-items: center;
                gap: 0.85rem;
            }

            .brand-mark {
                display: grid;
                place-items: center;
                width: 42px;
                height: 42px;
                border-radius: 13px;
                background: #F97316;
                color: #FFFFFF;
                font-weight: 800;
                font-size: 1.05rem;
                box-shadow: 0 5px 14px rgba(249, 115, 22, 0.3);
            }

            .brand-name {
                font-size: 1.05rem;
                font-weight: 800;
                letter-spacing: 0.01em;
            }

            .brand-subtitle {
                margin-top: 0.12rem;
                color: #B8D5DC;
                font-size: 0.75rem;
            }

            .live-status {
                display: flex;
                align-items: center;
                gap: 0.45rem;
                color: #D9F99D;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }

            .live-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #A3E635;
                box-shadow: 0 0 0 0 rgba(163, 230, 53, 0.5);
                animation: pulse-dot 1.6s infinite ease-out;
            }

            @keyframes pulse-dot {
                0% {
                    box-shadow: 0 0 0 0 rgba(163, 230, 53, 0.5);
                }
                70% {
                    box-shadow: 0 0 0 8px rgba(163, 230, 53, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(163, 230, 53, 0);
                }
            }

            .workspace-heading {
                margin-bottom: 1rem;
            }

            .workspace-heading .eyebrow {
                color: #0E7490;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.13em;
                text-transform: uppercase;
            }

            .workspace-heading h1 {
                color: var(--navy) !important;
                font-size: clamp(1.8rem, 3vw, 2.65rem);
                line-height: 1.05;
                margin: 0.35rem 0 0.45rem;
                letter-spacing: -0.045em;
            }

            .workspace-heading p {
                color: var(--secondary);
                margin: 0;
                max-width: 680px;
                font-size: 0.95rem;
            }

            .search-panel {
                background: linear-gradient(145deg, #E9F8F7 0%, #F5FBFC 100%);
                border: 1px solid #B8E3E1;
                border-radius: 16px;
                padding: 1.1rem;
                box-shadow: 0 10px 24px rgba(18, 32, 51, 0.06);
                margin-top: 0.2rem;
            }

            .search-panel .kicker {
                color: #0E7490;
                font-size: 0.7rem;
                font-weight: 800;
                letter-spacing: 0.1em;
                text-transform: uppercase;
            }

            .search-panel h2 {
                color: var(--navy) !important;
                font-size: 1.18rem;
                margin: 0.35rem 0 0.2rem;
            }

            .search-panel p {
                color: var(--secondary);
                font-size: 0.82rem;
                line-height: 1.5;
                margin: 0 0 0.7rem;
            }

            .st-key-search_card label {
                color: #71717A !important;
                font-size: 0.8rem !important;
                font-weight: 600 !important;
                letter-spacing: 0.04em !important;
                margin-bottom: 8px !important;
                text-transform: uppercase;
            }

            .st-key-search_card input {
                background: #FFFFFF !important;
                border: 1.5px solid #E4E4E7 !important;
                border-radius: 10px !important;
                color: #18181B !important;
                font-size: 1rem !important;
                min-height: 46px !important;
                padding: 14px 16px !important;
                transition: all 200ms ease !important;
            }

            .st-key-search_card input::placeholder {
                color: #A1A1AA !important;
                font-style: normal !important;
                opacity: 1 !important;
            }

            .st-key-search_card input:focus {
                border-color: #0F766E !important;
                box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12) !important;
                outline: none !important;
            }

            .empty-state {
                position: relative;
                overflow: hidden;
                min-height: 340px;
                display: flex;
                align-items: center;
                background: linear-gradient(135deg, #FFFFFF 0%, #F0F9FA 100%);
                border: 1px solid #D8E7EA;
                border-radius: 18px;
                padding: 2.4rem;
                box-shadow: 0 12px 28px rgba(18, 32, 51, 0.06);
            }

            .empty-state::after {
                content: "";
                position: absolute;
                width: 190px;
                height: 190px;
                right: -55px;
                top: -55px;
                border: 28px solid rgba(14, 116, 144, 0.08);
                border-radius: 50%;
            }

            .empty-state .icon {
                display: grid;
                place-items: center;
                width: 54px;
                height: 54px;
                border-radius: 16px;
                background: #DFF6F5;
                color: #0E7490;
                font-size: 1.55rem;
                margin-bottom: 1rem;
            }

            .empty-state h2 {
                color: var(--navy) !important;
                font-size: 1.55rem;
                margin: 0 0 0.5rem;
            }

            .empty-state p {
                color: var(--secondary);
                line-height: 1.65;
                max-width: 500px;
                margin: 0;
            }

            .empty-state .hint {
                display: inline-block;
                margin-top: 1.2rem;
                color: #9A3412;
                background: #FFF7ED;
                border: 1px solid #FED7AA;
                border-radius: 999px;
                padding: 0.42rem 0.7rem;
                font-size: 0.75rem;
                font-weight: 700;
            }

            .loading-state {
                min-height: 520px;
                padding: 2rem 1.25rem;
                border: 1px solid #E4E4E7;
                border-radius: 16px;
                background: #FFFFFF;
                box-shadow: 0 10px 24px rgba(18, 32, 51, 0.05);
            }

            .loading-center {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 175px;
                text-align: center;
            }

            .loading-spinner {
                width: 40px;
                height: 40px;
                border: 3px solid #E4E4E7;
                border-top-color: #0F766E;
                border-right-color: #0F766E;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }

            .loading-message {
                color: #71717A;
                font-size: 0.95rem;
                margin-top: 1rem;
                animation: loadingMessageFade 1.2s ease-in-out infinite alternate;
            }

            .loading-skeleton-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                opacity: 0.55;
            }

            .loading-skeleton-card {
                min-height: 104px;
                border: 1px solid #E4E4E7;
                border-radius: 12px;
                background: linear-gradient(90deg, #F4F4F5 25%, #FFFFFF 50%, #F4F4F5 75%);
                background-size: 200% 100%;
                animation: skeletonPulse 1.5s ease-in-out infinite;
            }

            .loading-skeleton-wide {
                min-height: 126px;
                margin-top: 0.9rem;
                border: 1px solid #E4E4E7;
                border-radius: 12px;
                background: linear-gradient(90deg, #F4F4F5 25%, #FFFFFF 50%, #F4F4F5 75%);
                background-size: 200% 100%;
                animation: skeletonPulse 1.5s ease-in-out infinite;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            @keyframes loadingMessageFade {
                from { opacity: 0.55; }
                to { opacity: 1; }
            }

            @keyframes skeletonPulse {
                0%, 100% { background-position: 200% 0; opacity: 0.4; }
                50% { background-position: -200% 0; opacity: 0.7; }
            }

            .metric-card,
            .signal-card,
            .ai-panel,
            .history-empty {
                animation: caseFadeIn 200ms ease both;
            }

            @keyframes caseFadeIn {
                from { opacity: 0; transform: translateY(4px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .section-title {
                color: var(--navy);
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                margin: 1.35rem 0 0.65rem;
            }

            .stButton > button {
                background: #FFFFFF !important;
                color: var(--navy) !important;
                border: 1px solid var(--border) !important;
                border-radius: 10px !important;
                font-weight: 600 !important;
                min-height: 44px !important;
                width: 100% !important;
                box-shadow: none !important;
            }

            .stButton > button:hover {
                background: #EFF6FF !important;
                color: var(--blue) !important;
                border-color: #93C5FD !important;
            }

            .stButton > button:focus {
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18) !important;
                outline: none !important;
            }

            .stButton > button[kind="secondary"] {
                background: #FFFFFF !important;
                color: var(--navy) !important;
                border: 1px solid var(--border) !important;
            }

            .stButton > button[kind="secondary"]:hover {
                background: #F8FAFC !important;
                color: var(--navy) !important;
            }

            .stButton > button[kind="secondary"][aria-label*="Block"],
            .stButton > button[kind="secondary"][name*="Block"] {
                color: var(--red) !important;
                border: 1px solid #FCA5A5 !important;
            }

            .stButton > button[kind="secondary"][aria-label*="Block"]:hover,
            .stButton > button[kind="secondary"][name*="Block"]:hover {
                background: #FEF2F2 !important;
                color: #991B1B !important;
            }

            .stButton > button[kind="primary"] {
                background: var(--blue) !important;
                color: #FFFFFF !important;
                border-color: var(--blue) !important;
            }

            .stButton > button[kind="primary"]:hover {
                background: #1D4ED8 !important;
                color: #FFFFFF !important;
                border-color: #1D4ED8 !important;
            }

            .stButton > button[aria-label*="Allow"],
            .stButton > button[title*="Allow"] {
                background: #15803D !important;
                color: #FFFFFF !important;
                border-color: #15803D !important;
            }

            .stButton > button[aria-label*="Allow"]:hover,
            .stButton > button[title*="Allow"]:hover {
                background: #166534 !important;
                color: #FFFFFF !important;
                border-color: #166534 !important;
            }

            .stButton > button[aria-label*="Block"],
            .stButton > button[title*="Block"] {
                background: #DC2626 !important;
                color: #FFFFFF !important;
                border-color: #DC2626 !important;
            }

            .stButton > button[aria-label*="Block"]:hover,
            .stButton > button[title*="Block"]:hover {
                background: #B91C1C !important;
                color: #FFFFFF !important;
                border-color: #B91C1C !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.stButton) div[data-testid="column"]:nth-child(2) .stButton > button {
                background: #15803D !important;
                color: #FFFFFF !important;
                border-color: #15803D !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.stButton) div[data-testid="column"]:nth-child(2) .stButton > button:hover {
                background: #166534 !important;
                color: #FFFFFF !important;
                border-color: #166534 !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.stButton) div[data-testid="column"]:nth-child(3) .stButton > button {
                background: #DC2626 !important;
                color: #FFFFFF !important;
                border-color: #DC2626 !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.stButton) div[data-testid="column"]:nth-child(3) .stButton > button:hover {
                background: #B91C1C !important;
                color: #FFFFFF !important;
                border-color: #B91C1C !important;
            }

            .st-key-decision-actions [data-testid="stColumn"]:nth-child(2) .stButton > button {
                background: #15803D !important;
                color: #FFFFFF !important;
                border-color: #15803D !important;
            }

            .st-key-decision-actions [data-testid="stColumn"]:nth-child(2) .stButton > button:hover {
                background: #166534 !important;
                color: #FFFFFF !important;
                border-color: #166534 !important;
            }

            .st-key-decision-actions [data-testid="stColumn"]:nth-child(3) .stButton > button {
                background: #DC2626 !important;
                color: #FFFFFF !important;
                border-color: #DC2626 !important;
            }

            .st-key-decision-actions [data-testid="stColumn"]:nth-child(3) .stButton > button:hover {
                background: #B91C1C !important;
                color: #FFFFFF !important;
                border-color: #B91C1C !important;
            }

            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea {
                background: var(--surface-soft);
                border: 1px solid var(--border);
                border-radius: 10px;
                color: var(--navy);
            }

            .stAlert {
                border-radius: 12px;
            }

            .stSuccess {
                border-left: 4px solid var(--green);
            }

            .stWarning {
                border-left: 4px solid var(--amber);
            }

            .stError {
                border-left: 4px solid var(--red);
            }

            .metric-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                box-shadow: var(--shadow);
                padding: 1rem 1rem 0.9rem;
                min-height: 110px;
            }

            .metric-label {
                font-size: 0.7rem;
                color: var(--muted);
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 0.45rem;
            }

            .metric-value {
                color: var(--navy);
                font-size: 1.1rem;
                font-weight: 600;
                line-height: 1.4;
                word-break: break-word;
            }

            .metric-value.large {
                font-size: 1.4rem;
                font-weight: 700;
            }

            .queue-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 0.8rem 0.9rem;
                margin-bottom: 0.6rem;
                box-shadow: var(--shadow);
            }

            .queue-card.selected {
                border-color: rgba(37, 99, 235, 0.6);
                background: rgba(37, 99, 235, 0.04);
            }

            .queue-top-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.3rem;
            }

            .risk-badge {
                display: inline-block;
                font-size: 0.62rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                border-radius: 999px;
                padding: 0.26rem 0.5rem;
                border: 1px solid transparent;
            }

            .risk-badge.block {
                background: #FEF2F2;
                color: var(--red);
                border-color: #FECACA;
            }

            .risk-badge.review {
                background: #FFFBEB;
                color: var(--amber);
                border-color: #FDE68A;
            }

            .risk-badge.allow {
                background: #F0FDF4;
                color: var(--green);
                border-color: #BBF7D0;
            }

            .queue-amount {
                font-weight: 700;
                color: var(--navy);
            }

            .queue-card-id {
                font-weight: 600;
                color: var(--navy);
                margin-bottom: 0.2rem;
            }

            .queue-meta {
                color: var(--secondary);
                font-size: 0.75rem;
            }

            .queue-open-button > div > button {
                min-height: 38px !important;
                font-size: 0.82rem !important;
            }

            .signal-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-left: 4px solid var(--border);
                border-radius: 12px;
                padding: 0.9rem 0.9rem 0.8rem;
                box-shadow: var(--shadow);
                min-height: 116px;
            }

            .signal-card.triggered {
                border-left-color: var(--red);
                background: #FEF2F2;
            }

            .signal-label {
                font-size: 0.7rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-weight: 700;
                color: var(--secondary);
            }

            .signal-value {
                margin-top: 0.5rem;
                font-size: 1.2rem;
                font-weight: 700;
                color: var(--navy);
            }

            .signal-pill {
                display: inline-block;
                margin-top: 0.7rem;
                padding: 0.22rem 0.52rem;
                border-radius: 999px;
                font-size: 0.62rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .signal-pill.triggered {
                background: #FECACA;
                color: var(--red);
            }

            .signal-pill.neutral {
                background: #F1F5F9;
                color: var(--secondary);
            }

            .ai-panel {
                background: rgba(124, 58, 237, 0.03);
                border: 1px solid rgba(124, 58, 237, 0.15);
                border-radius: 12px;
                padding: 1rem 1.1rem;
                box-shadow: var(--shadow);
            }

            .ai-panel h4 {
                color: var(--purple) !important;
                font-size: 0.72rem !important;
                letter-spacing: 0.08em !important;
                text-transform: uppercase !important;
                margin-bottom: 0.6rem !important;
            }

            .ai-panel p {
                margin: 0;
                color: var(--secondary);
                line-height: 1.7;
            }

            .ai-metric {
                display: inline-block;
                background: rgba(124, 58, 237, 0.05);
                color: var(--navy);
                padding: 0.35rem 0.5rem;
                border-radius: 8px;
                font-size: 0.8rem;
                font-weight: 600;
                margin-right: 0.4rem;
                margin-top: 0.7rem;
            }

            .case-fact {
                display: inline-block;
                background: #FFFFFF;
                border: 1px solid #D8E7EA;
                color: #173B4D;
                padding: 0.38rem 0.55rem;
                border-radius: 8px;
                font-size: 0.78rem;
                font-weight: 700;
                margin: 0.7rem 0.4rem 0 0;
            }

            .history-empty {
                background: var(--surface);
                border: 1px dashed var(--border);
                border-radius: 12px;
                text-align: center;
                padding: 1.25rem 1rem;
                box-shadow: var(--shadow);
            }

            .history-empty .icon {
                display: block;
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
            }

            .history-empty .title {
                font-size: 1rem;
                font-weight: 700;
                color: var(--navy);
                margin-bottom: 0.2rem;
            }

            .history-empty .copy {
                color: var(--secondary);
            }

            @keyframes historyAttention {
                0% { box-shadow: 0 0 0 0 rgba(64, 221, 196, 0.6); }
                45% { box-shadow: 0 0 0 7px rgba(64, 221, 196, 0.18), 0 0 28px rgba(64, 221, 196, 0.28); }
                100% { box-shadow: 0 0 0 0 rgba(64, 221, 196, 0); }
            }

            .st-key-history-page-button .stButton > button,
            .st-key-history-page-button .stButton > button[kind="secondary"] {
                animation: historyAttention 1.5s ease-out 1;
                background: #0f9f9a !important;
                border: 1px solid #40ddc4 !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                min-height: 44px !important;
                padding: 12px 24px !important;
                transition: background 160ms ease, border-color 160ms ease, transform 160ms ease !important;
            }

            .st-key-history-page-button .stButton > button:hover,
            .st-key-history-page-button .stButton > button[kind="secondary"]:hover {
                background: #087f7a !important;
                border-color: #65e6cd !important;
                color: #ffffff !important;
                transform: translateY(-1px);
            }

            .st-key-back-to-case-button {
                margin: 0 0 1.25rem;
            }

            .st-key-back-to-case-button .stButton > button,
            .st-key-back-to-case-button .stButton > button[kind="secondary"] {
                background: #0f9f9a !important;
                border: 1px solid #40ddc4 !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                min-height: 44px !important;
                padding: 12px 24px !important;
                transition: background 160ms ease, border-color 160ms ease, transform 160ms ease !important;
                width: auto !important;
            }

            .st-key-back-to-case-button .stButton > button:hover,
            .st-key-back-to-case-button .stButton > button[kind="secondary"]:hover {
                background: #087f7a !important;
                border-color: #65e6cd !important;
                color: #ffffff !important;
                transform: translateY(-1px);
            }

            .st-key-back-to-case-button .stButton > button:focus,
            .st-key-back-to-case-button .stButton > button[kind="secondary"]:focus {
                box-shadow: 0 0 0 3px rgba(64, 221, 196, 0.2) !important;
            }

            .decision-banner {
                border-radius: 12px;
                padding: 0.95rem 1.1rem;
                margin: 0.8rem 0 1rem;
                border-left: 4px solid;
                font-weight: 700;
                line-height: 1.35;
            }

            .decision-banner .subtext {
                display: block;
                margin-top: 0.15rem;
                font-size: 0.78rem;
                font-weight: 600;
                opacity: 0.78;
            }

            .decision-banner.allow {
                background: #F0FDF4;
                border-left-color: var(--green);
                color: #166534;
            }

            .decision-banner.review {
                background: #FFFBEB;
                border-left-color: var(--amber);
                color: #92400E;
            }

            .decision-banner.block {
                background: #FEF2F2;
                border-left-color: var(--red);
                color: #991B1B;
            }

            .override-banner {
                background: #FFF7ED;
                border: 1px solid #FDBA74;
                border-left: 4px solid #F97316;
                border-radius: 12px;
                color: #9A3412;
                font-size: 0.9rem;
                font-weight: 700;
                margin: 0.8rem 0;
                padding: 0.9rem 1rem;
            }

            @media (max-width: 900px) {
                .block-container {
                    padding-left: 0.85rem;
                    padding-right: 0.85rem;
                }
            }

            /* Midnight control-room layer — deliberately higher contrast than the
               default Streamlit treatment, with light motion used only for status. */
            :root {
                --bg: #080c18;
                --surface: rgba(18, 25, 46, 0.78);
                --surface-soft: #10172b;
                --border: rgba(160, 174, 215, 0.16);
                --navy: #f4f6ff;
                --blue: #7c73ff;
                --teal: #40ddc4;
                --green: #51d18a;
                --amber: #f7b955;
                --red: #ff667d;
                --purple: #ad8cff;
                --text: #f4f6ff;
                --secondary: #aab5d1;
                --muted: #7783a4;
                --shadow: 0 22px 55px rgba(0, 0, 0, 0.24);
                --radius: 16px;
            }

            html, body, [data-testid="stAppViewContainer"], .stApp {
                background:
                    radial-gradient(circle at 76% -10%, rgba(94, 79, 255, 0.25), transparent 30rem),
                    radial-gradient(circle at 5% 38%, rgba(23, 203, 176, 0.12), transparent 28rem),
                    #080c18;
                color: var(--text);
            }

            .block-container {
                max-width: 1540px;
                padding-top: 1.6rem;
            }

            .app-header {
                position: relative;
                overflow: hidden;
                min-height: 76px;
                padding: 1rem 1.3rem;
                margin-bottom: 2.8rem;
                border: 1px solid rgba(182, 190, 255, 0.18);
                border-radius: 20px;
                background: linear-gradient(110deg, rgba(22, 28, 55, 0.92), rgba(15, 23, 45, 0.78));
                box-shadow: var(--shadow);
            }

            .app-header::before {
                content: "";
                position: absolute;
                inset: 0 0 0 auto;
                width: 44%;
                background: linear-gradient(90deg, transparent, rgba(124, 115, 255, 0.13));
                pointer-events: none;
            }

            .brand-lockup, .live-status { position: relative; z-index: 1; }

            .brand-mark {
                width: 46px;
                height: 46px;
                border-radius: 15px;
                background: linear-gradient(135deg, #0f9f9a 0%, #2563eb 100%);
                color: #ffffff;
                box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.14), 0 10px 24px rgba(15, 159, 154, 0.28);
            }

            .brand-name { font-size: 1.12rem; letter-spacing: 0.015em; }
            .brand-subtitle { color: #9ba8cb; }
            .live-status {
                padding: 0.48rem 0.72rem;
                color: #91f6d3;
                border: 1px solid rgba(81, 209, 138, 0.22);
                border-radius: 999px;
                background: rgba(81, 209, 138, 0.08);
            }
            .live-dot { background: #51d18a; }

            .workspace-heading {
                position: relative;
                padding: 0 0 1.8rem;
                border-bottom: 1px solid var(--border);
                margin-bottom: 1.5rem;
            }
            .workspace-heading::after {
                content: "SECURE ANALYST FLOW  /  01";
                position: absolute;
                right: 0;
                bottom: 1.95rem;
                color: #7f8bb0;
                font-size: 0.65rem;
                font-weight: 800;
                letter-spacing: 0.16em;
            }
            .workspace-heading .eyebrow { color: #65e6cd; }
            .workspace-heading h1 {
                color: #fbfcff !important;
                font-size: clamp(2rem, 3.5vw, 3.45rem);
                max-width: 790px;
                margin-top: 0.42rem;
                letter-spacing: -0.06em;
            }
            .workspace-heading h1 em {
                font-style: normal;
                background: linear-gradient(100deg, #62e3c9, #a892ff);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
            }
            .workspace-heading p { color: #aeb9d3; max-width: 620px; font-size: 1rem; }

            /* Motion is used as feedback, not decoration. Every animation is
               disabled for visitors who request reduced motion. */
            [data-testid="stAppViewContainer"]::before {
                content: "";
                position: fixed;
                z-index: 0;
                width: 30rem;
                height: 30rem;
                top: 22%;
                right: -14rem;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(116, 100, 255, 0.14), transparent 67%);
                filter: blur(8px);
                pointer-events: none;
                animation: ambientDrift 14s ease-in-out infinite alternate;
            }
            .block-container { position: relative; z-index: 1; }
            @keyframes ambientDrift {
                from { transform: translate3d(0, -20px, 0) scale(0.94); }
                to { transform: translate3d(-90px, 85px, 0) scale(1.12); }
            }
            @keyframes entrance {
                from { opacity: 0; transform: translateY(14px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes softPulse {
                0%, 100% { box-shadow: 0 0 0 0 rgba(98, 227, 201, 0.26); }
                55% { box-shadow: 0 0 0 12px rgba(98, 227, 201, 0); }
            }
            @keyframes orbitalSpin { to { transform: rotate(360deg); } }
            @keyframes scanSweep {
                from { transform: translateX(-145%) skewX(-18deg); }
                to { transform: translateX(500%) skewX(-18deg); }
            }
            @keyframes dotWave {
                0%, 60%, 100% { transform: translateY(0); opacity: 0.35; }
                30% { transform: translateY(-4px); opacity: 1; }
            }
            @keyframes edgeTravel {
                0%, 100% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
            }
            @keyframes cardEnter {
                from { opacity: 0; transform: translateY(18px) rotateX(-4deg) rotateY(3deg); }
                to { opacity: 1; transform: translateY(0) rotateX(0) rotateY(0); }
            }
            @keyframes cardFloat {
                0%, 100% { transform: translateY(0) rotateX(0) rotateY(0); }
                50% { transform: translateY(-4px) rotateX(0.5deg) rotateY(-0.5deg); }
            }
            @keyframes cardShimmer {
                0%, 26% { transform: translateX(-180%) skewX(-20deg); }
                58%, 100% { transform: translateX(410%) skewX(-20deg); }
            }
            .app-header { animation: entrance 460ms cubic-bezier(.2,.8,.2,1) both; }
            .workspace-heading { animation: entrance 560ms 70ms cubic-bezier(.2,.8,.2,1) both; }
            .search-panel { animation: cardEnter 650ms 130ms cubic-bezier(.2,.8,.2,1) both, cardFloat 7s 900ms ease-in-out infinite; }

            .search-panel {
                position: relative;
                overflow: hidden;
                isolation: isolate;
                box-sizing: border-box;
                aspect-ratio: 1.586 / 1;
                min-height: 0;
                padding: 1.45rem;
                border: 1px solid rgba(139, 150, 255, 0.42);
                border-radius: 24px;
                background: radial-gradient(circle at 100% 0%, rgba(66, 222, 197, 0.24), transparent 31%), linear-gradient(132deg, #29335b 0%, #18213f 48%, #0d152c 100%);
                box-shadow: 0 22px 42px rgba(0, 0, 0, 0.28), inset 0 1px rgba(255, 255, 255, 0.1);
                transform-style: preserve-3d;
            }
            .search-panel::after {
                content: "";
                position: absolute;
                z-index: 0;
                width: 210px;
                height: 210px;
                right: -115px;
                top: -98px;
                border: 28px solid rgba(87, 222, 196, 0.15);
                border-radius: 50%;
            }
            .search-panel::before {
                content: "";
                position: absolute;
                z-index: 0;
                inset: 0;
                width: 34%;
                background: linear-gradient(105deg, transparent, rgba(161, 251, 229, 0.16), transparent);
                transform: translateX(-180%) skewX(-20deg);
                animation: cardShimmer 5.8s 1.6s ease-in-out infinite;
                pointer-events: none;
            }
            .search-panel > * { position: relative; z-index: 1; }
            .search-panel .kicker { color: #79efd6; }
            .card-topline { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; }
            .card-brand { display: inline-flex; align-items: center; gap: 0.42rem; color: #f3f7ff; font-size: 0.69rem; font-weight: 850; letter-spacing: 0.13em; text-transform: uppercase; }
            .card-brand-mark { width: 17px; height: 17px; border: 2px solid #67ead1; border-radius: 50%; box-shadow: 7px 0 0 -2px rgba(173, 140, 255, 0.92); }
            .card-network { color: rgba(229, 236, 255, 0.68); font-size: 0.58rem; font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase; }
            .card-chip-row { display: flex; align-items: center; justify-content: space-between; margin-top: 1.3rem; }
            .card-chip { position: relative; width: 45px; height: 33px; overflow: hidden; border: 1px solid rgba(255, 226, 151, 0.76); border-radius: 7px; background: linear-gradient(135deg, #f7d988, #c9954b); box-shadow: inset 0 0 0 1px rgba(117, 71, 28, 0.22), 0 5px 12px rgba(0, 0, 0, 0.2); }
            .card-chip::before, .card-chip::after { content: ""; position: absolute; background: rgba(111, 72, 35, 0.4); }
            .card-chip::before { top: 0; bottom: 0; left: 50%; width: 1px; box-shadow: -12px 0 0 rgba(111, 72, 35, 0.35), 12px 0 0 rgba(111, 72, 35, 0.35); }
            .card-chip::after { left: 0; right: 0; top: 50%; height: 1px; box-shadow: 0 -9px 0 rgba(111, 72, 35, 0.3), 0 9px 0 rgba(111, 72, 35, 0.3); }
            .card-contactless { position: relative; width: 32px; height: 32px; transform: rotate(90deg); }
            .card-contactless span, .card-contactless::before, .card-contactless::after { content: ""; position: absolute; inset: 6px 3px; border: 1.5px solid rgba(161, 245, 225, 0.78); border-top-color: transparent; border-bottom-color: transparent; border-radius: 50%; }
            .card-contactless::before { inset: 2px -2px; }
            .card-contactless::after { inset: 10px 8px; }
            .card-number { margin-top: 1.65rem; color: #f5f7ff; font-family: "SFMono-Regular", Consolas, monospace; font-size: clamp(0.95rem, 1.5vw, 1.15rem); font-weight: 700; letter-spacing: 0.16em; text-shadow: 0 1px 8px rgba(0, 0, 0, 0.25); }
            .card-caption-row { display: flex; align-items: end; justify-content: space-between; gap: 0.75rem; margin-top: 0.75rem; }
            .card-caption { color: #94a4c8; font-size: 0.54rem; font-weight: 800; letter-spacing: 0.13em; line-height: 1.45; text-transform: uppercase; }
            .card-caption strong { display: block; color: #e7edff; font-size: 0.66rem; letter-spacing: 0.08em; }
            .search-steps { display: flex; gap: 0.35rem; flex-wrap: wrap; margin-top: 1.1rem; padding-top: 0.85rem; border-top: 1px solid rgba(174, 189, 232, 0.17); }
            .search-step { display: inline-flex; align-items: center; gap: 0.35rem; color: #8492b6; font-size: 0.61rem; font-weight: 800; letter-spacing: 0.07em; text-transform: uppercase; }
            .search-step b { display: grid; place-items: center; width: 17px; height: 17px; border: 1px solid rgba(156, 166, 215, 0.26); border-radius: 50%; color: #aeb9d3; font-size: 0.55rem; }
            .search-step.active { color: #9cf1dc; }
            .search-step.active b { border-color: rgba(101, 230, 205, 0.62); color: #65e6cd; background: rgba(101, 230, 205, 0.1); }
            .search-step:nth-child(2) { animation: entrance 440ms 230ms both; }
            .search-step:nth-child(3) { animation: entrance 440ms 320ms both; }
            .st-key-search_card label { color: #aeb9d3 !important; }
            .st-key-search_card input, .stTextInput > div > div > input, .stTextArea > div > div > textarea {
                background: rgba(7, 12, 27, 0.74) !important;
                border-color: rgba(154, 166, 215, 0.24) !important;
                color: #f7f8ff !important;
            }
            .st-key-search_card input:focus {
                border-color: #65e6cd !important;
                box-shadow: 0 0 0 3px rgba(64, 221, 196, 0.14) !important;
            }
            .st-key-search_card.is-searching input {
                border-color: #65e6cd !important;
                box-shadow: 0 0 0 3px rgba(64, 221, 196, 0.14), 0 12px 26px rgba(5, 9, 21, 0.35) !important;
            }
            .stButton > button {
                background: rgba(21, 29, 53, 0.92) !important;
                color: #e7ebff !important;
                border-color: rgba(156, 169, 220, 0.25) !important;
                border-radius: 11px !important;
                transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease !important;
            }
            .stButton > button:hover {
                color: #fff !important;
                background: rgba(35, 45, 78, 0.96) !important;
                border-color: rgba(124, 115, 255, 0.68) !important;
                transform: translateY(-2px);
                box-shadow: 0 9px 20px rgba(0, 0, 0, 0.22) !important;
            }
            .stButton > button[kind="primary"] {
                background: linear-gradient(110deg, #7067f5, #9281ff) !important;
                border-color: transparent !important;
                box-shadow: 0 9px 22px rgba(105, 94, 245, 0.28) !important;
            }
            .stButton > button[kind="primary"]:hover { background: linear-gradient(110deg, #7b72ff, #a18dff) !important; }
            .st-key-find-card button {
                position: relative;
                overflow: hidden;
                letter-spacing: 0.015em !important;
                background: linear-gradient(110deg, #6258e8, #8e7dfd, #4bd8c3, #6258e8) !important;
                background-size: 240% 100% !important;
                animation: edgeTravel 5.5s ease-in-out infinite;
            }
            .st-key-find-card button::before {
                content: "";
                position: absolute;
                inset: 0 auto 0 -42%;
                width: 32%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.48), transparent);
                transform: skewX(-22deg);
                animation: scanSweep 3.8s 1.4s ease-in-out infinite;
            }
            .st-key-find-card button::after {
                content: "•••";
                position: relative;
                margin-left: 0.48rem;
                color: rgba(255,255,255,0.65);
                letter-spacing: 0.12em;
                animation: dotWave 1.4s ease-in-out infinite;
            }
            .st-key-decision-actions [data-testid="stColumn"]:nth-child(2) .stButton > button {
                background: linear-gradient(110deg, #168a68, #32b884) !important;
                border-color: transparent !important;
            }
            .st-key-decision-actions [data-testid="stColumn"]:nth-child(3) .stButton > button {
                background: linear-gradient(110deg, #b43d5b, #e65d74) !important;
                border-color: transparent !important;
            }

            .metric-card, .signal-card, .ai-panel, .history-empty {
                background: linear-gradient(145deg, rgba(26, 35, 62, 0.86), rgba(13, 19, 37, 0.85));
                border-color: rgba(154, 166, 215, 0.16);
                box-shadow: var(--shadow);
                border-radius: 16px;
            }
            .metric-card, .signal-card { transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease; }
            .metric-card:nth-child(1), .signal-card:nth-child(1) { animation-delay: 40ms; }
            .metric-card:nth-child(2), .signal-card:nth-child(2) { animation-delay: 100ms; }
            .metric-card:nth-child(3), .signal-card:nth-child(3) { animation-delay: 160ms; }
            .metric-card { min-height: 118px; }
            .metric-card:hover, .signal-card:hover { border-color: rgba(124, 115, 255, 0.48); transform: translateY(-2px); }
            .metric-label, .signal-label { color: #8996ba; }
            .metric-value, .signal-value { color: #fbfcff; }
            .signal-card.triggered { background: linear-gradient(145deg, rgba(91, 31, 56, 0.7), rgba(36, 19, 37, 0.9)); border-left-color: #ff667d; }
            .signal-pill.triggered { background: rgba(255, 102, 125, 0.18); color: #ff9aaa; }
            .signal-pill.neutral { background: rgba(138, 151, 190, 0.14); color: #b4c0e2; }
            .ai-panel { background: linear-gradient(120deg, rgba(71, 47, 125, 0.38), rgba(14, 22, 43, 0.94)); border-color: rgba(179, 140, 255, 0.24); }
            .ai-panel h4 { color: #c3a9ff !important; }
            .ai-panel p, .history-empty .copy { color: #aeb9d3; }
            .case-fact { background: rgba(6, 12, 27, 0.45); border-color: rgba(159, 143, 238, 0.22); color: #dce1fb; }
            .history-empty .title, h2, h3, .queue-card-id, .queue-amount { color: #f5f7ff !important; }
            .decision-banner { border-radius: 14px; border: 1px solid; border-left-width: 4px; }
            .decision-banner.allow { background: rgba(37, 121, 78, 0.18); border-color: rgba(81, 209, 138, 0.28); color: #95f5bd; }
            .decision-banner.review { background: rgba(157, 105, 22, 0.16); border-color: rgba(247, 185, 85, 0.3); color: #ffd480; }
            .decision-banner.block { background: rgba(132, 38, 65, 0.2); border-color: rgba(255, 102, 125, 0.3); color: #ffa5b3; }

            /* The decision is the primary analyst moment: this module sits above
               the data grid and makes the recommendation scannable in seconds. */
            .decision-command {
                position: relative;
                overflow: hidden;
                display: grid;
                grid-template-columns: auto minmax(0, 1fr) auto;
                align-items: center;
                gap: 1.15rem;
                margin: 0 0 1.15rem;
                padding: 1.15rem 1.25rem;
                border: 1px solid;
                border-radius: 20px;
                box-shadow: var(--shadow);
                animation: entrance 460ms 80ms cubic-bezier(.2,.8,.2,1) both;
                scroll-margin-top: 1.25rem;
            }
            .decision-command::after {
                content: "";
                position: absolute;
                top: 0;
                right: -5%;
                width: 42%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06));
                transform: skewX(-18deg);
                pointer-events: none;
            }
            .decision-command.allow { background: linear-gradient(110deg, rgba(19, 98, 70, 0.64), rgba(12, 30, 39, 0.92)); border-color: rgba(81, 209, 138, 0.34); }
            .decision-command.review { background: linear-gradient(110deg, rgba(123, 83, 23, 0.6), rgba(35, 28, 26, 0.92)); border-color: rgba(247, 185, 85, 0.36); }
            .decision-command.block { background: linear-gradient(110deg, rgba(117, 35, 60, 0.67), rgba(39, 19, 32, 0.93)); border-color: rgba(255, 102, 125, 0.38); }
            .decision-seal {
                position: relative;
                display: grid;
                place-items: center;
                width: 62px;
                height: 62px;
                border: 1px solid currentColor;
                border-radius: 50%;
                font-size: 1.28rem;
                font-weight: 900;
            }
            .decision-seal::after { content: ""; position: absolute; inset: -7px; border: 1px dashed currentColor; border-radius: 50%; opacity: 0.58; animation: orbitalSpin 12s linear infinite; }
            .decision-command.allow .decision-seal { color: #8df4bb; background: rgba(81, 209, 138, 0.1); }
            .decision-command.review .decision-seal { color: #ffd57d; background: rgba(247, 185, 85, 0.1); }
            .decision-command.block .decision-seal { color: #ff9aac; background: rgba(255, 102, 125, 0.1); }
            .decision-command-copy { min-width: 0; position: relative; z-index: 1; }
            .decision-command-label { display: block; color: #c0c9df; font-size: 0.63rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; }
            .decision-command-title { margin: 0.18rem 0 0.2rem; color: #fff; font-size: clamp(1.25rem, 2vw, 1.65rem); font-weight: 850; letter-spacing: -0.04em; }
            .decision-command-copy p { max-width: 600px; margin: 0; color: #c0c9df; font-size: 0.82rem; line-height: 1.45; }

            .empty-state {
                min-height: 406px;
                background: linear-gradient(125deg, rgba(24, 32, 59, 0.94), rgba(11, 17, 33, 0.94));
                border-color: rgba(153, 161, 224, 0.19);
                border-radius: 20px;
                box-shadow: var(--shadow);
            }
            .empty-state::before {
                content: "";
                position: absolute;
                width: 410px;
                height: 410px;
                right: -160px;
                bottom: -270px;
                background: radial-gradient(circle, rgba(99, 91, 255, 0.3), transparent 67%);
            }
            .empty-state::after { border-color: rgba(86, 228, 199, 0.14); }
            .empty-state .icon { position: relative; background: linear-gradient(145deg, #7169f5, #46d8c1); color: #07101d; box-shadow: 0 12px 26px rgba(78, 218, 194, 0.2); animation: softPulse 2.4s ease-out infinite; }
            .empty-state .icon::after { content: ""; position: absolute; inset: -8px; border: 1px solid rgba(98, 227, 201, 0.35); border-radius: 20px; animation: orbitalSpin 6s linear infinite; }
            .empty-state h2 { color: #fbfcff !important; font-size: 1.8rem; }
            .empty-state p { color: #b7c1da; }
            .empty-state .hint { color: #9af2d9; background: rgba(64, 221, 196, 0.1); border-color: rgba(64, 221, 196, 0.25); }
            .welcome-signals { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-top: 1.25rem; }
            .welcome-signals span { color: #c5cdea; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; padding: 0.48rem 0.65rem; border: 1px solid rgba(171, 183, 233, 0.19); border-radius: 999px; background: rgba(10, 16, 33, 0.42); }
            .welcome-signals span { animation: entrance 500ms both; }
            .welcome-signals span:nth-child(1) { animation-delay: 170ms; }
            .welcome-signals span:nth-child(2) { animation-delay: 250ms; }
            .welcome-signals span:nth-child(3) { animation-delay: 330ms; }

            .case-focus {
                position: relative;
                overflow: hidden;
                display: flex;
                align-items: center;
                gap: 1rem;
                min-height: 104px;
                padding: 1rem 1.15rem;
                margin: 0 0 1.15rem;
                border: 1px solid rgba(147, 138, 255, 0.24);
                border-radius: 18px;
                background: linear-gradient(110deg, rgba(49, 43, 101, 0.75), rgba(14, 23, 45, 0.94) 54%, rgba(21, 55, 73, 0.68));
                box-shadow: var(--shadow);
                animation: entrance 400ms cubic-bezier(.2,.8,.2,1) both;
            }
            .case-focus::after { content: ""; position: absolute; inset: 0; width: 18%; background: linear-gradient(90deg, transparent, rgba(132, 252, 223, 0.1), transparent); animation: scanSweep 4.7s 500ms ease-in-out infinite; pointer-events: none; }
            .case-orbit {
                position: relative;
                display: grid;
                place-items: center;
                flex: 0 0 52px;
                width: 52px;
                height: 52px;
                border: 1px solid rgba(101, 230, 205, 0.42);
                border-radius: 50%;
                color: #8af3db;
                font-size: 1.15rem;
            }
            .case-orbit::before { content: ""; position: absolute; width: 66px; height: 66px; border: 1px dashed rgba(168, 145, 255, 0.55); border-radius: 50%; animation: orbitalSpin 12s linear infinite; }
            .case-focus-copy { min-width: 0; flex: 1; }
            .case-focus-eyebrow { color: #81eed6; font-size: 0.63rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; }
            .case-focus-title { overflow: hidden; color: #f8f9ff; font-size: 1.1rem; font-weight: 750; letter-spacing: -0.02em; text-overflow: ellipsis; white-space: nowrap; }
            .case-focus-meta { color: #aab6d3; font-size: 0.77rem; margin-top: 0.18rem; }
            .case-focus-amount { position: relative; z-index: 1; text-align: right; color: #fff; font-size: 1.28rem; font-weight: 800; letter-spacing: -0.03em; }
            .case-focus-amount span { display: block; color: #9ba9c9; font-size: 0.63rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }

            .loading-state { background: linear-gradient(145deg, rgba(25, 34, 61, 0.9), rgba(10, 16, 31, 0.9)); border-color: rgba(152, 164, 217, 0.18); }
            .loading-message { color: #b9c5e1; }
            .loading-skeleton-card, .loading-skeleton-wide { border-color: rgba(152, 164, 217, 0.16); background: linear-gradient(90deg, rgba(55, 66, 103, 0.4) 25%, rgba(119, 107, 235, 0.28) 50%, rgba(55, 66, 103, 0.4) 75%); }
            [data-testid="stDataFrame"] { border: 1px solid rgba(152, 164, 217, 0.16); border-radius: 14px; overflow: hidden; }
            [data-testid="stCaptionContainer"] { color: #7f8bad !important; }

            .theme-switch-row { margin: -1.55rem 0 1.1rem; }
            .theme-switch-row [data-testid="stHorizontalBlock"] { align-items: center; }
            .st-key-light_mode { display: flex; justify-content: flex-end; }
            .st-key-light_mode label { color: #aeb9d3 !important; font-size: 0.72rem !important; font-weight: 800 !important; letter-spacing: 0.08em !important; text-transform: uppercase; }
            .st-key-light_mode [data-testid="stWidgetLabel"] { margin-bottom: 0 !important; }

            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
            }

            @media (max-width: 900px) {
                .app-header { margin-bottom: 1.8rem; }
                .workspace-heading::after { display: none; }
                .workspace-heading h1 { font-size: 2.2rem; }
                .empty-state { min-height: 320px; padding: 1.5rem; }
                .decision-command { grid-template-columns: auto minmax(0, 1fr); }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_light_mode(enabled: bool) -> None:
    """Layer a high-contrast daylight palette over the analyst workspace."""
    st.markdown(
        """
        <style>
            /* light-mode-theme */
            :root {
                --bg: #F5F7FB;
                --surface: #FFFFFF;
                --surface-soft: #F8FAFC;
                --border: #DCE3F0;
                --navy: #10213F;
                --text: #10213F;
                --secondary: #5F6F8D;
                --muted: #7B8BA7;
                --shadow: 0 14px 30px rgba(23, 44, 80, 0.09);
            }

            html, body, [data-testid="stAppViewContainer"], .stApp {
                background: radial-gradient(circle at 88% -6%, rgba(102, 130, 255, 0.16), transparent 26rem), #F5F7FB;
                color: var(--text);
            }
            [data-testid="stAppViewContainer"]::before { background: radial-gradient(circle, rgba(61, 190, 170, 0.12), transparent 67%); }
            .app-header {
                color: #142444;
                border-color: #D7E0F1;
                background: linear-gradient(110deg, #FFFFFF 0%, #EEF3FF 100%);
                box-shadow: 0 14px 30px rgba(23, 44, 80, 0.11);
            }
            .app-header::before { background: linear-gradient(90deg, transparent, rgba(95, 105, 235, 0.08)); }
            .app-header .brand-name { color: #142444; }
            .app-header .brand-subtitle { color: #4F6180; }
            .live-status { color: #14775E; border-color: #BCE9D9; background: #EFFBF6; }
            .workspace-heading { border-color: #DCE3F0; }
            .workspace-heading::after, [data-testid="stCaptionContainer"] { color: #627493 !important; }
            .workspace-heading .eyebrow { color: #087F75; }
            .workspace-heading h1, h2, h3, .queue-card-id, .queue-amount { color: #10213F !important; }
            .workspace-heading p { color: #465A7C; }
            [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color: #4B5F80; }
            .st-key-light_mode {
                padding: 0.35rem 0.65rem;
                border: 1px solid #C9D5E9;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.9);
                box-shadow: 0 5px 13px rgba(35, 57, 99, 0.08);
            }
            .st-key-light_mode *, .st-key-light_mode label, .st-key-light_mode [data-testid="stWidgetLabel"] { color: #344866 !important; }
            .st-key-light_mode [data-testid="stTooltipIcon"] svg { fill: #617390 !important; }
            .st-key-search_card label { color: #405574 !important; }
            .st-key-search_card input, .stTextInput > div > div > input, .stTextArea > div > div > textarea {
                background: #FFFFFF !important;
                border-color: #AEBED7 !important;
                color: #10213F !important;
            }
            .st-key-search_card input::placeholder { color: #667A9B !important; }
            .stButton > button { background: #FFFFFF !important; color: #243756 !important; border-color: #B7C6DE !important; }
            .stButton > button:hover { background: #F1F5FF !important; color: #273FB6 !important; border-color: #94A7E8 !important; box-shadow: 0 8px 18px rgba(46, 70, 138, 0.12) !important; }
            .stButton > button[kind="primary"], .st-key-find-card button { color: #FFFFFF !important; background: linear-gradient(110deg, #4C57C8, #6976E6) !important; }
            .st-key-find-card button,
            .st-key-find-card button * {
                color: #FFFFFF !important;
                -webkit-text-fill-color: #FFFFFF !important;
            }
            .st-key-find-card button:disabled {
                color: #FFFFFF !important;
                opacity: 1 !important;
                filter: none !important;
            }
            .st-key-find-card button:disabled * {
                color: #FFFFFF !important;
                -webkit-text-fill-color: #FFFFFF !important;
            }
            .metric-card, .signal-card, .ai-panel, .history-empty, .loading-state, .empty-state {
                background: #FFFFFF;
                border-color: #DCE3F0;
                box-shadow: 0 12px 26px rgba(23, 44, 80, 0.07);
            }
            .metric-label, .signal-label { color: #5C6F8E; }
            .metric-value, .signal-value, .history-empty .title { color: #10213F !important; }
            .metric-card:hover, .signal-card:hover { border-color: #9BA9EE; }
            .signal-card.triggered { background: #FFF5F7; border-left-color: #E85B77; }
            .signal-pill.triggered { background: #FFE7EC; color: #B33150; }
            .signal-pill.neutral { background: #EEF2F8; color: #586987; }
            .ai-panel { background: linear-gradient(120deg, #F6F3FF, #FFFFFF); border-color: #D8D0FA; }
            .ai-panel h4 { color: #5C49BD !important; }
            .ai-panel p, .history-empty .copy { color: #4B5F80 !important; }
            .case-fact { background: #F5F7FB; border-color: #DCE3F0; color: #344562; }
            .empty-state::before { background: radial-gradient(circle, rgba(99, 91, 255, 0.13), transparent 67%); }
            .empty-state::after { border-color: rgba(29, 137, 158, 0.12); }
            .empty-state .icon { color: #FFFFFF; }
            .empty-state h2 { color: #10213F !important; }
            .empty-state p { color: #4B5F80; }
            .empty-state .hint { color: #087568; background: #E8FBF5; border-color: #A8E9D8; }
            .welcome-signals span { color: #405574; border-color: #CBD7E9; background: #F8FAFD; }
            .decision-command { box-shadow: 0 12px 26px rgba(23, 44, 80, 0.09); }
            .decision-command.allow { background: linear-gradient(110deg, #EAFBF3, #FFFFFF); border-color: #BCE9D9; }
            .decision-command.review { background: linear-gradient(110deg, #FFF8E8, #FFFFFF); border-color: #F5D48B; }
            .decision-command.block { background: linear-gradient(110deg, #FFF1F4, #FFFFFF); border-color: #F2B8C5; }
            .decision-command-title { color: #10213F; }
            .decision-command-label, .decision-command-copy p { color: #465A7C; }
            .case-focus { background: linear-gradient(110deg, #F0F2FF, #FFFFFF 54%, #EDFDFC); border-color: #CBD4F5; box-shadow: 0 12px 26px rgba(23, 44, 80, 0.08); }
            .case-focus-title, .case-focus-amount { color: #10213F; }
            .case-focus-meta, .case-focus-amount span { color: #4B5F80; }
            .loading-message { color: #4B5F80; }
            .loading-skeleton-card, .loading-skeleton-wide { border-color: #DCE3F0; background: linear-gradient(90deg, #EEF2F8 25%, #FFFFFF 50%, #EEF2F8 75%); }
            [data-testid="stDataFrame"] { border-color: #DCE3F0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_theme_switch() -> None:
    """Toggle the daylight stylesheet without triggering a Streamlit rerun."""
    components.html(
        """
        <style>
            body { margin: 0; background: transparent; font-family: sans-serif; }
            button {
                align-items: center;
                display: flex;
                gap: 0.55rem;
                border: 1px solid rgba(174, 185, 211, 0.35);
                border-radius: 999px;
                background: rgba(18, 25, 46, 0.82);
                color: #f4f6ff;
                cursor: pointer;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                padding: 0.7rem 0.9rem;
                text-transform: uppercase;
            }
            button:hover { border-color: #65e6cd; }
            .track {
                position: relative;
                width: 34px;
                height: 20px;
                border-radius: 999px;
                background: #65718e;
                transition: background 160ms ease;
            }
            .knob {
                position: absolute;
                top: 3px;
                left: 3px;
                width: 14px;
                height: 14px;
                border-radius: 50%;
                background: #ffffff;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
                transition: transform 160ms ease;
            }
            button.light .track { background: #0f9f9a; }
            button.light .knob { transform: translateX(14px); }
        </style>
        <button id="theme-switch" type="button" aria-label="Switch to light mode">
            <span class="track"><span class="knob"></span></span>
            <span class="label">Light mode</span>
        </button>
        <script>
        (() => {
            const hostDocument = window.parent.document;
            const button = document.getElementById("theme-switch");
            const lightStylesheet = Array.from(hostDocument.querySelectorAll("style"))
                .find((style) => style.textContent.includes("light-mode-theme"));
            if (!lightStylesheet) return;

            const applyTheme = (light) => {
                lightStylesheet.media = light ? "all" : "not all";
                button.classList.toggle("light", light);
                button.querySelector(".label").textContent = light ? "Dark mode" : "Light mode";
                button.setAttribute("aria-label", light ? "Switch to dark mode" : "Switch to light mode");
                window.localStorage.setItem("mirai-light-mode", light ? "1" : "0");
            };

            let light = window.localStorage.getItem("mirai-light-mode") === "1";
            applyTheme(light);
            button.addEventListener("click", () => {
                light = !light;
                applyTheme(light);
            });
        })();
        </script>
        """,
        height=48,
        scrolling=False,
    )


def animate_card_id_placeholder() -> None:
    """Animate examples in the native Streamlit card-ID input placeholder."""
    components.html(
        """
        <script>
        (() => {
            const phrases = [
                "Enter card ID e.g. card_b39a7255",
                "Search by card ID to investigate"
            ];
            const hostDocument = window.parent.document;
            const findInput = () => hostDocument.querySelector('.st-key-search_card input');

            const attach = (input) => {
                if (!input || input.dataset.placeholderAnimator === "ready") return;
                input.dataset.placeholderAnimator = "ready";

                let stopped = false;
                let timer;
                let phraseIndex = 0;
                let characterIndex = 0;
                let deleting = false;

                const stop = () => {
                    stopped = true;
                    window.clearTimeout(timer);
                };

                const start = () => {
                    if (input.value || document.activeElement === input) return;
                    stopped = false;
                    characterIndex = 0;
                    deleting = false;
                    tick();
                };

                const tick = () => {
                    if (stopped || input.value || document.activeElement === input) return;
                    const phrase = phrases[phraseIndex];
                    input.placeholder = phrase.slice(0, characterIndex);

                    if (!deleting && characterIndex < phrase.length) {
                        characterIndex += 1;
                        timer = window.setTimeout(tick, 40);
                        return;
                    }

                    if (!deleting) {
                        deleting = true;
                        timer = window.setTimeout(tick, 1800);
                        return;
                    }

                    if (characterIndex > 0) {
                        characterIndex -= 1;
                        timer = window.setTimeout(tick, 25);
                        return;
                    }

                    deleting = false;
                    phraseIndex = (phraseIndex + 1) % phrases.length;
                    timer = window.setTimeout(tick, 250);
                };

                const inputShell = input.closest('.st-key-search_card');
                input.addEventListener('focus', () => {
                    if (inputShell) inputShell.classList.add('is-searching');
                    stop();
                });
                input.addEventListener('input', stop);
                input.addEventListener('blur', () => {
                    if (inputShell) inputShell.classList.remove('is-searching');
                    if (!input.value) start();
                });
                start();
            };

            const observer = new hostDocument.defaultView.MutationObserver(() => attach(findInput()));
            observer.observe(hostDocument.body, {childList: true, subtree: true});
            attach(findInput());
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )


def render_loading_state(target: Any) -> None:
    """Render the in-place transaction and history loading state."""
    target.markdown(
        """
        <div class="loading-state">
            <div class="loading-center">
                <div class="loading-spinner" aria-label="Loading transaction"></div>
                <div class="loading-message">Pulling transaction history...</div>
            </div>
            <div class="loading-skeleton-grid" aria-hidden="true">
                <div class="loading-skeleton-card"></div>
                <div class="loading-skeleton-card"></div>
                <div class="loading-skeleton-card"></div>
            </div>
            <div class="loading-skeleton-grid" aria-hidden="true" style="margin-top: 0.9rem;">
                <div class="loading-skeleton-card"></div>
                <div class="loading-skeleton-card"></div>
                <div class="loading-skeleton-card"></div>
            </div>
            <div class="loading-skeleton-wide" aria-hidden="true"></div>
            <div class="loading-skeleton-wide" aria-hidden="true"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_queue(queue: list[dict[str, Any]]) -> None:
    if not queue:
        st.info("No scored transactions are currently in the queue.")
        return

    for item in queue:
        card_id = item.get("card_id", "unknown")
        selected = st.session_state.get("case") and st.session_state.case.get("card_id") == card_id
        decision = (item.get("decision") or "review").lower()
        badge_class = decision if decision in {"allow", "block", "review"} else "review"
        selected_class = " selected" if selected else ""
        st.markdown(
            f"<div class='queue-card{selected_class}'>"
            f"<div class='queue-top-row'><span class='risk-badge {badge_class}'>{badge_class.upper()}</span>"
            f"<span class='queue-amount'>${float(item.get('amount', 0.0)):.2f}</span></div>"
            f"<div class='queue-card-id'>{card_id}</div>"
            f"<div class='queue-meta'>Risk score {float(item.get('gbt_score', 0.0)):.3f} &middot; "
            f"Velocity {item.get('velocity_count', item.get('velocity', 0))}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='queue-open-button'>", unsafe_allow_html=True)
        open_case = st.button(
            "Open transaction",
            key=f"queue-{item.get('transaction_id', card_id)}",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        if open_case:
            try:
                st.session_state.case = api_get(f"/transaction/{card_id}")
            except requests.RequestException as error:
                st.error(f"Transaction lookup failed: {error}")


def render_summary_cards(case: dict[str, Any]) -> None:
    values = [
        ("Amount", f"${float(case['amount']):.2f}", True),
        ("Date", format_dataset_date(case["time"]), True),
        ("Time", format_dataset_time(case["time"]), True),
        ("Card", case["card_id"], False),
    ]
    for col, (label, value, large) in zip(st.columns(4), values):
        with col:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value {'large' if large else ''}'>{value}</div></div>",
                unsafe_allow_html=True,
            )

    cols = st.columns(3)
    for col, (label, value) in zip(cols, [
        ("Device", case["device_id"]),
        ("Purchaser Domain", case["purchaser_email_domain"]),
        ("Recipient Domain", case["recipient_email_domain"]),
    ]):
        with col:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>",
                unsafe_allow_html=True,
            )


def render_risk_signals(case: dict[str, Any]) -> None:
    st.subheader("Risk Signals")
    cols = st.columns(3)
    signals = [
        ("Velocity", int(case.get("velocity_count", 0) or 0), bool(case.get("rules_flag"))),
        ("Card History", len(case.get("card_history", []) or []), bool(case.get("card_history"))),
        ("Device Graph", 0, bool(case.get("graph_flag"))),
    ]
    for col, (label, value, triggered) in zip(cols, signals):
        with col:
            st.markdown(
                f"<div class='signal-card {'triggered' if triggered else 'neutral'}'>"
                f"<div class='signal-label'>{label}</div>"
                f"<div class='signal-value'>{value}</div>"
                f"<div class='signal-pill {'triggered' if triggered else 'neutral'}'>{'Triggered' if triggered else 'No signal'}</div>"
                "</div>",
                unsafe_allow_html=True,
            )


def render_explanation(case: dict[str, Any]) -> None:
    st.subheader("Why was this transaction flagged?")
    st.markdown(
        "<div class='ai-panel'>"
        "<h4>Primary signal</h4>"
        f"<p>{case.get('plain_summary', 'No plain-language summary is available.')}</p>"
        "<div>"
            f"<span class='case-fact'>Velocity: {int(case.get('velocity_count', 0) or 0)} in 60 seconds</span>"
            f"<span class='case-fact'>Device links: {int(case.get('device_card_count', 0) or 0)}</span>"
            f"<span class='case-fact'>{'Anomaly detected' if case.get('anomaly_flag') else 'No anomaly detected'}</span>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_card_history_contents(case: dict[str, Any]) -> None:
    history = [
        row
        for row in case.get("card_history", [])
        if row.get("transaction_id") != case.get("transaction_id")
    ]
    if not history:
        st.markdown(
            "<div class='history-empty'>"
            "<span class='icon'>◷</span>"
            "<div class='title'>No previous transactions found</div>"
            "<div class='copy'>No historical activity is available for this card.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    history = sorted(history, key=lambda row: float(row.get("time", 0.0)), reverse=True)
    history_view = st.selectbox(
        "History view",
        ("Most Recent", "Show All", "Fraud Only"),
        key=f"history-view-{case.get('transaction_id', case.get('card_id', 'case'))}",
    )
    if history_view == "Most Recent":
        history = history[:50]
    elif history_view == "Fraud Only":
        history = [row for row in history if int(row.get("class_label", 0) or 0) == 1]

    if not history:
        st.markdown(
            "<div class='history-empty'>"
            "<span class='icon'>◷</span>"
            "<div class='title'>No previous transactions found</div>"
            "<div class='copy'>No historical activity is available for this card.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    st.dataframe(
        [
            {
                "Date": format_dataset_date(float(row.get("time", 0.0))),
                "Time": format_dataset_time(float(row.get("time", 0.0))),
                "Amount": float(row.get("amount", 0.0)),
                "Decision": (row.get("decision") or "pending").upper(),
                "Email domains": f"{row.get('purchaser_email_domain', '')} -> {row.get('recipient_email_domain', '')}",
            }
            for row in history
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_card_history_page(case: dict[str, Any]) -> None:
    """Render Card History as the only visible page-level view."""
    with st.container(key="back-to-case-button"):
        if st.button("← Back to Case", key="back-to-case", type="secondary"):
            st.session_state.current_view = "case_overview"
            st.rerun()
    st.title("Card History")
    render_card_history_contents(case)


def decision_badge(case: dict[str, Any]) -> None:
    """Present the model decision as the first, high-priority case outcome."""
    normalized = str(case.get("decision") or "review").lower()
    if normalized not in {"allow", "block", "review"}:
        normalized = "review"
    copy = {
        "allow": "No material fraud pattern was detected. Confirm the recommendation or continue reviewing the transaction context.",
        "review": "Signals need analyst attention before this transaction can proceed. Review the evidence below, then record your decision.",
        "block": "High-risk behavior was detected. Review the linked signals before confirming a block or applying an override.",
    }[normalized]
    glyph = {"allow": "&#10003;", "review": "!", "block": "&#10005;"}[normalized]
    st.markdown(
        f"<section class='decision-command {normalized}' aria-label='System decision: {normalized}'>"
        f"<div class='decision-seal' aria-hidden='true'>{glyph}</div>"
        "<div class='decision-command-copy'>"
        "<span class='decision-command-label'>System decision</span>"
        f"<div class='decision-command-title'>{normalized.upper()}</div>"
        f"<p>{copy}</p></div>"
        "</section>",
        unsafe_allow_html=True,
    )


def focus_system_decision() -> None:
    """Bring the first decision result into view after a successful lookup."""
    components.html(
        """
        <script>
        (() => {
            const hostDocument = window.parent.document;
            let attempts = 0;
            const focusDecision = () => {
                const decision = hostDocument.querySelector('.decision-command');
                if (decision) {
                    decision.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    return;
                }
                attempts += 1;
                if (attempts < 12) window.setTimeout(focusDecision, 80);
            };
            window.setTimeout(focusDecision, 90);
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )


def render_case_focus(case: dict[str, Any]) -> None:
    """Render the animated visual anchor for an opened investigation."""
    decision = str(case.get("decision") or "review").upper()
    card_id = escape(str(case.get("card_id") or "Unknown card"))
    amount = float(case.get("amount", 0.0) or 0.0)
    st.markdown(
        "<div class='case-focus'>"
        "<div class='case-orbit' aria-hidden='true'>&#9670;</div>"
        "<div class='case-focus-copy'>"
        "<div class='case-focus-eyebrow'>Active investigation</div>"
        f"<div class='case-focus-title'>{card_id}</div>"
        f"<div class='case-focus-meta'>Decision engine status: {escape(decision)}</div>"
        "</div>"
        f"<div class='case-focus-amount'>${amount:,.2f}<span>Transaction amount</span></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_case_overview_page(case: dict[str, Any]) -> None:
    """Render the transaction overview and analyst decision controls."""
    decision_badge(case)
    render_case_focus(case)
    st.subheader("Transaction Summary")
    render_summary_cards(case)
    render_risk_signals(case)
    render_explanation(case)
    history_count = len(case.get("card_history", []) or [])
    with st.container(key="history-page-button"):
        if st.button(
            f"View Full Card History ({history_count} transactions)",
            key="open-history-page",
            use_container_width=True,
        ):
            st.session_state.current_view = "card_history"
            st.rerun()

    st.subheader("Analyst Decision")
    with st.container(key="decision-actions"):
        action_1, action_2, action_3 = st.columns(3)
        with action_1:
            if st.button("Confirm system decision", type="primary", use_container_width=True):
                submit_decision(case, case.get("decision", "review"))
        with action_2:
            if st.button("Override: allow", type="secondary", use_container_width=True):
                st.session_state.override = "allow"
        with action_3:
            if st.button("Override: block", type="secondary", use_container_width=True):
                st.session_state.override = "block"

    override = st.session_state.get("override")
    if override:
        st.markdown(
            f"<div class='override-banner'>Override selected: {override.upper()}</div>",
            unsafe_allow_html=True,
        )
        reason = st.text_area("Override reason (required)", key="override_reason")
        if st.button("Submit Override", type="primary", use_container_width=True):
            if not reason.strip():
                st.error("Provide a reason before submitting an override.")
            else:
                submit_decision(case, override, reason.strip())


def submit_decision(case: dict[str, Any], decision: str, reason: str = "") -> None:
    response = requests.post(
        f"{API_URL}/decision",
        json={
            "transaction_id": case["transaction_id"],
            "analyst_decision": decision,
            "override_reason": reason or None,
        },
        timeout=30,
    )
    response.raise_for_status()
    st.success(f"Analyst decision saved: {decision.upper()}")
    st.session_state.case = None
    st.session_state.override = None
    st.rerun()


st.set_page_config(page_title="MiRai Analyst Console", page_icon="shield", layout="wide")
if "light_mode" not in st.session_state:
    st.session_state.light_mode = False
if "current_view" not in st.session_state:
    st.session_state.current_view = "case_overview"
inject_fintech_theme()
inject_light_mode(True)

st.markdown(
    "<div class='app-header'>"
    "<div class='brand-lockup'><div class='brand-mark'>M</div>"
    "<div><div class='brand-name'>MiRai Fraud Intelligence</div>"
    "<div class='brand-subtitle'>Analyst decision workspace &middot; Protected environment</div></div></div>"
    "<div class='live-status'><span class='live-dot'></span>Monitoring active</div>"
    "</div>",
    unsafe_allow_html=True,
)
theme_spacer, theme_control = st.columns([0.8, 0.2])
with theme_control:
    render_theme_switch()
st.markdown(
    "<div class='workspace-heading'><div class='eyebrow'>Investigation workspace</div>"
    "<h1>Make every decision<br/>with <em>clarity.</em></h1>"
    "<p>Search a card to surface the complete decision context, risk signals, history, and the best next action&mdash;all in one focused review.</p></div>",
    unsafe_allow_html=True,
)

left, main = st.columns([0.28, 0.72], gap="large")
main_content = main.container(key="main-content")
with left:
    st.markdown(
        "<div class='search-panel' aria-label='Masked MiRai analyst card'>"
        "<div class='card-topline'><div class='card-brand'><span class='card-brand-mark' aria-hidden='true'></span>MiRai</div>"
        "<span class='card-network'>Secure insight</span></div>"
        "<div class='card-chip-row'><span class='card-chip' aria-hidden='true'></span>"
        "<span class='card-contactless' aria-hidden='true'><span></span></span></div>"
        "<div class='card-number' aria-label='Masked demonstration card number'>••••&nbsp;&nbsp;••••&nbsp;&nbsp;••••&nbsp;&nbsp;••••</div>"
        "<div class='card-caption-row'><div class='card-caption'>Analyst console<strong>MiRai Intelligence</strong></div>"
        "<div class='card-caption'>Valid thru<strong>MM / YY</strong></div>"
        "<div class='card-caption'>CVV<strong>•••</strong></div></div></div>",
        unsafe_allow_html=True,
    )
    search_card = st.text_input("Search by card ID", key="search_card", placeholder="")
    animate_card_id_placeholder()
    search_requested = st.button("Begin investigation", key="find-card", type="primary", use_container_width=True) and bool(search_card.strip())

if search_requested:
    render_loading_state(main_content)
    try:
        st.session_state.case = api_get(f"/transaction/{search_card.strip()}")
    except requests.RequestException as error:
        with main_content:
            st.error(f"Card lookup failed: {error}")
    else:
        st.session_state.current_view = "case_overview"
        st.session_state.focus_decision = True
        st.rerun()

with main_content:
    case = st.session_state.get("case")
    if case:
        if st.session_state.current_view == "card_history":
            render_card_history_page(case)
        else:
            render_case_overview_page(case)
    else:
        st.markdown(
            "<div class='empty-state'><div><div class='icon'>&#9673;</div>"
            "<h2>Your review desk is ready.</h2>"
            "<p>Enter a card ID on the left to open a case. You will see the transaction profile, model signals, card history, and analyst controls here.</p>"
            "<div class='welcome-signals'><span>Real-time signals</span><span>Explainable scoring</span><span>Analyst control</span></div>"
            "<span class='hint'>Start with a card ID</span></div></div>",
            unsafe_allow_html=True,
        )

if st.session_state.pop("focus_decision", False) and st.session_state.get("case"):
    focus_system_decision()

