"""Visual system. User-provided values are never interpolated into this CSS."""
import streamlit as st


def apply_styles() -> None:
    st.html("""<style>
    :root {--forest:#124D3D;--ink:#162D28;--muted:#566B65;--line:#DDE6E1;}
    .stApp {background:#F5F7F8;}
    .stAppDeployButton {display:none;}
    [class*="st-key-surface_"] {background:#FFF;border-color:var(--line) !important;border-radius:16px !important;box-shadow:0 3px 12px #173E2E05;}
    .block-container {max-width:1260px;padding-top:2rem;padding-bottom:4rem;}
    h1,h2,h3 {color:var(--ink);letter-spacing:-.035em;}
    h1 {font-size:2.45rem !important;font-weight:750 !important;}
    h2 {font-size:1.5rem !important;}
    h3 {font-size:1.15rem !important;}
    p,li {line-height:1.6;}
    [data-testid="stSidebar"] {background:#FFF;border-right:1px solid var(--line);}
    [data-testid="stSidebar"] .block-container {padding-top:2rem;}
    [data-testid="stSidebar"] [role="radiogroup"] {gap:.45rem;}
    [data-testid="stSidebar"] [role="radiogroup"] label {padding:.55rem .7rem;border-radius:9px;width:100%;}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#E6F1EB;}
    [data-testid="stVerticalBlockBorderWrapper"]>div {border-radius:16px;}
    [data-testid="stVerticalBlockBorderWrapper"] {box-shadow:0 3px 12px #173E2E05;}
    [data-testid="stMetric"] {background:white;border:1px solid var(--line);padding:1rem 1.2rem;border-radius:13px;}
    [data-testid="stMetricValue"] {font-size:2rem;font-weight:650;color:var(--forest);}
    .stButton button,.stDownloadButton button {border-radius:9px;min-height:2.6rem;font-weight:600;}
    .stButton button:focus-visible {outline:3px solid #369878;outline-offset:3px;}
    [data-testid="stForm"] {background:white;border-color:var(--line);border-radius:16px;padding:1.4rem;}
    .brand {display:flex;align-items:center;gap:.7rem;margin:0 0 1.8rem;}
    .brand-mark {display:grid;place-items:center;background:var(--forest);color:white;font-size:1.4rem;font-weight:800;width:42px;height:42px;border-radius:12px;}
    .brand-name {font-size:1.6rem;font-weight:800;letter-spacing:.06em;}
    .brand-sub {font-size:.8rem;color:var(--muted);}
    .eyebrow {font-size:.8rem;letter-spacing:.14em;text-transform:uppercase;color:#47665B;font-weight:700;margin-bottom:.5rem;}
    .intro {color:var(--muted);font-size:1.05rem;max-width:740px;margin:-.3rem 0 1.5rem;}
    .rail {border-left:3px solid #A9C9B6;padding:.2rem 0 .2rem 1rem;margin:1.5rem 0;color:var(--muted);font-size:.9rem;}
    .tags {display:flex;flex-wrap:wrap;gap:.45rem;margin:.2rem 0 .7rem;}
    .tag {display:inline-block;padding:.22rem .6rem;border-radius:6px;background:#EAF2EE;color:#235540;font-size:.8rem;font-weight:600;}
    .tag.status {background:#EDF1F7;color:#3D5573;}
    .tag.demo {background:#F4F0E5;color:#695C32;}
    .card-title {font-size:1.28rem;font-weight:700;letter-spacing:-.025em;line-height:1.35;margin:.2rem 0 .5rem;}
    .meta {color:var(--muted);font-size:.86rem;margin:.3rem 0 .75rem;}
    .body-copy {white-space:pre-wrap;overflow-wrap:anywhere;color:#2C453D;font-size:1rem;}
    .card-copy {color:#4A6058;font-size:.96rem;line-height:1.6;margin:0 0 .8rem;}
    .paper {padding:.8rem 0;}
    .timeline {list-style:none;display:flex;flex-wrap:wrap;padding:0;gap:.5rem;margin:1rem 0;}
    .timeline li {flex:1;min-width:115px;padding:.6rem .7rem;border-top:3px solid #D8E1DD;color:#60736B;font-size:.85rem;}
    .timeline li.done {border-color:#267855;color:#20583F;}
    .timeline li.current {background:#E8F2EC;font-weight:700;border-radius:0 0 8px 8px;}
    .step {font-size:.72rem;display:block;letter-spacing:.08em;margin-bottom:.15rem;}
    .footer {color:#61736B;font-size:.8rem;border-top:1px solid var(--line);padding-top:1rem;margin-top:2rem;}
    [data-testid="stImage"] img {border-radius:12px;}
    @media(max-width:760px) {
      .block-container {padding:1.4rem 1rem 3rem;}
      h1 {font-size:2rem !important;}
      [data-testid="stMetric"] {padding:.8rem;}
      .timeline li {min-width:100px;}
    }
    </style>""")
