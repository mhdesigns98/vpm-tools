"""
Chartbeat Weekly Analytics Dashboard

Reads weekly CSV exports from CHARTBEAT_DATA_DIR and renders a live dashboard.
Drop a new CSV into the folder and refresh to update.
"""

import glob
import os
import re
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    for _k, _v in st.secrets.items():
        if _k not in os.environ:
            os.environ[_k] = str(_v)
except Exception:
    pass

st.set_page_config(
    page_title="Chartbeat Analytics",
    page_icon="📊",
    layout="wide",
)

DATA_DIR = os.getenv("CHARTBEAT_DATA_DIR", "/Users/mhayes/Projects/chartbeat-data")

_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_date(filename: str):
    name = os.path.splitext(os.path.basename(filename))[0].lower()
    name = re.sub(r"[-_]?(sections?|source)$", "", name).strip("-_")

    # Numeric: M-D-YY or MM-DD-YYYY
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{2,4})$", name)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day)
        except ValueError:
            return None

    # Month name: March-23-26 or march-23-26
    m = re.match(r"^([a-z]+)-(\d{1,2})-(\d{2,4})$", name)
    if m:
        month = _MONTH_MAP.get(m.group(1)[:3])
        day, year = int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        if month:
            try:
                return datetime(year, month, day)
            except ValueError:
                return None

    return None


def _file_type(filename: str) -> str:
    name = os.path.basename(filename).lower()
    if "source" in name:
        return "source"
    if "section" in name:
        return "section"
    # Fallback: check CSV header
    try:
        header = pd.read_csv(filename, nrows=0).columns.tolist()
        if "section" in header:
            return "section"
        if "referrer_type" in header:
            return "source"
    except Exception:
        pass
    return "unknown"


@st.cache_data(show_spinner=False)
def load_data(data_dir: str):
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    sections_frames, source_frames = [], []

    for f in sorted(files):
        date = _parse_date(f)
        if date is None:
            continue
        ftype = _file_type(f)
        if ftype == "unknown":
            continue
        try:
            df = pd.read_csv(f)
            df["week"] = date
            if ftype == "section":
                sections_frames.append(df)
            else:
                source_frames.append(df)
        except Exception:
            continue

    sections = (
        pd.concat(sections_frames, ignore_index=True)
        if sections_frames
        else pd.DataFrame()
    )
    sources = (
        pd.concat(source_frames, ignore_index=True)
        if source_frames
        else pd.DataFrame()
    )
    return sections, sources


def fmt_num(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("📊 Chartbeat Weekly Analytics")
st.caption("vpm.org — drop a new CSV into your data folder and refresh to update.")

APP_PASSWORD = os.getenv("APP_PASSWORD", "")
if APP_PASSWORD:
    pwd = st.text_input("Password", type="password", key="app_password")
    if pwd != APP_PASSWORD:
        if pwd:
            st.error("Incorrect password.")
        st.stop()

if not os.path.isdir(DATA_DIR):
    st.error(f"Data folder not found: `{DATA_DIR}`. Set **CHARTBEAT_DATA_DIR** in your `.env` file.")
    st.stop()

with st.spinner("Loading data…"):
    sections, sources = load_data(DATA_DIR)

if sections.empty:
    st.warning("No section CSV files found. Add Chartbeat weekly exports to your data folder.")
    st.stop()

# ── Week selector ──────────────────────────────────────────────────────────────
all_weeks = sorted(sections["week"].unique(), reverse=True)
week_labels = {w: w.strftime("%-m/%-d/%Y") for w in all_weeks}

selected_week = st.selectbox(
    "Week",
    options=all_weeks,
    format_func=lambda w: week_labels[w],
    index=0,
)

st.divider()

# ── KPI cards ─────────────────────────────────────────────────────────────────
week_sections = sections[sections["week"] == selected_week]
week_sources = sources[sources["week"] == selected_week] if not sources.empty else pd.DataFrame()

total_uniques = int(week_sections["page_uniques"].sum())
total_views = int(week_sections["page_views"].sum())
total_quality = int(week_sections["page_views_quality"].sum())
total_loyal = int(week_sections["page_views_loyal"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Unique Visitors", fmt_num(total_uniques))
c2.metric("Page Views", fmt_num(total_views))
c3.metric("Quality Views", fmt_num(total_quality))
c4.metric("Loyal Views", fmt_num(total_loyal))

st.divider()

# ── Weekly trend ──────────────────────────────────────────────────────────────
st.subheader("Weekly Trend")

metric_options = {
    "Unique Visitors": "page_uniques",
    "Page Views": "page_views",
    "Quality Views": "page_views_quality",
    "Loyal Views": "page_views_loyal",
}
selected_metric_label = st.radio(
    "Metric",
    options=list(metric_options.keys()),
    horizontal=True,
    label_visibility="collapsed",
)
selected_metric = metric_options[selected_metric_label]

weekly_totals = (
    sections.groupby("week")[selected_metric]
    .sum()
    .reset_index()
    .sort_values("week")
    .rename(columns={"week": "Week", selected_metric: selected_metric_label})
)
weekly_totals["Week"] = weekly_totals["Week"].dt.strftime("%-m/%-d")

st.line_chart(weekly_totals, x="Week", y=selected_metric_label, height=280)

st.divider()

# ── Top sections + Traffic sources ────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Top Sections")
    top_sections = (
        week_sections[["section", "page_uniques", "page_views"]]
        .sort_values("page_uniques", ascending=False)
        .head(10)
        .rename(columns={"section": "Section", "page_uniques": "Uniques", "page_views": "Views"})
    )
    st.bar_chart(top_sections.set_index("Section")["Uniques"], height=280)
    st.dataframe(top_sections, hide_index=True, use_container_width=True)

with right:
    st.subheader("Traffic Sources")
    if not week_sources.empty:
        top_sources = (
            week_sources[["referrer_type", "page_uniques", "page_views"]]
            .sort_values("page_uniques", ascending=False)
            .rename(columns={"referrer_type": "Source", "page_uniques": "Uniques", "page_views": "Views"})
        )
        st.bar_chart(top_sources.set_index("Source")["Uniques"], height=280)
        st.dataframe(top_sources, hide_index=True, use_container_width=True)
    else:
        st.info("No source data found for this week.")

st.divider()

# ── All weeks table ────────────────────────────────────────────────────────────
with st.expander("All weeks — raw totals"):
    all_totals = (
        sections.groupby("week")
        .agg(
            Uniques=("page_uniques", "sum"),
            Views=("page_views", "sum"),
            Quality=("page_views_quality", "sum"),
            Loyal=("page_views_loyal", "sum"),
        )
        .reset_index()
        .sort_values("week", ascending=False)
        .rename(columns={"week": "Week"})
    )
    all_totals["Week"] = all_totals["Week"].dt.strftime("%-m/%-d/%Y")
    st.dataframe(all_totals, hide_index=True, use_container_width=True)

st.caption(f"Data folder: `{DATA_DIR}` · {len(all_weeks)} weeks loaded")
