# app.py
import os
import sys
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

load_dotenv(r"C:\Project-Demografy\Neighbourhood_Livability\.env")
sys.path.insert(0, r"C:\Project-Demografy\Neighbourhood_Livability")

from db.ingestion import run_pipeline

st.set_page_config(
    page_title="Neighbourhood Livability Index",
    page_icon="🏙️",
    layout="wide"
)

# ── Metric labels & order ─────────────────────────────────────
METRICS = {
    "cafes":           "Cafes",
    "parks":           "Parks",
    "gyms":            "Gyms",
    "childcare":       "Childcare",
    "transport_stops": "Transport",
    "healthcare":      "Healthcare",
    "grocery":         "Grocery",
    "schools":         "Schools",
    "restaurants":     "Restaurants",
    "banks_atms":      "Banks & ATMs",
    "entertainment":   "Entertainment",
    "pet_friendly":    "Pet Friendly",
    "libraries":       "Libraries",
    "car_washes":      "Car Washes",
}

EMOJI = {
    "cafes":           "☕",
    "parks":           "🌳",
    "gyms":            "💪",
    "childcare":       "👶",
    "transport_stops": "🚌",
    "healthcare":      "🏥",
    "grocery":         "🛒",
    "schools":         "🏫",
    "restaurants":     "🍽️",
    "banks_atms":      "🏦",
    "entertainment":   "🎭",
    "pet_friendly":    "🐾",
    "libraries":       "📚",
    "car_washes":      "🚗",
}

def compute_score(metrics):
    """
    Computes livability score out of 10
    based on average of all 14 metrics
    normalised to max 20
    """
    keys = list(METRICS.keys())
    values = [min(metrics.get(k, 0), 20) for k in keys]
    avg = sum(values) / len(values)
    score = (avg / 20) * 10
    return round(score, 1)


def make_bar_chart(metrics_a, metrics_b, name_a, name_b):
    """Side by side bar chart for both suburbs"""
    labels  = [EMOJI[k] + " " + v for k, v in METRICS.items()]
    values_a = [metrics_a.get(k, 0) for k in METRICS.keys()]
    values_b = [metrics_b.get(k, 0) for k in METRICS.keys()]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name=name_a,
        x=labels,
        y=values_a,
        marker_color="#00C2CB",
        text=values_a,
        textposition="outside"
    ))

    fig.add_trace(go.Bar(
        name=name_b,
        x=labels,
        y=values_b,
        marker_color="#F5A623",
        text=values_b,
        textposition="outside"
    ))

    fig.update_layout(
        title="Amenity Comparison — Side by Side",
        barmode="group",
        plot_bgcolor="#0F1923",
        paper_bgcolor="#0F1923",
        font=dict(color="white"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
        margin=dict(t=80, b=20)
    )

    return fig


def make_radar_chart(metrics_a, metrics_b, name_a, name_b):
    """Radar/spider chart showing overall shape"""
    categories = [METRICS[k] for k in METRICS.keys()]
    categories.append(categories[0])  # close the loop

    values_a = [min(metrics_a.get(k, 0), 20) for k in METRICS.keys()]
    values_a.append(values_a[0])

    values_b = [min(metrics_b.get(k, 0), 20) for k in METRICS.keys()]
    values_b.append(values_b[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_a,
        theta=categories,
        fill="toself",
        name=name_a,
        line_color="#00C2CB",
        fillcolor="rgba(0,194,203,0.2)"
    ))

    fig.add_trace(go.Scatterpolar(
        r=values_b,
        theta=categories,
        fill="toself",
        name=name_b,
        line_color="#F5A623",
        fillcolor="rgba(245,166,35,0.2)"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 20],
                color="white"
            ),
            bgcolor="#0F1923"
        ),
        plot_bgcolor="#0F1923",
        paper_bgcolor="#0F1923",
        font=dict(color="white"),
        title="Livability Shape Comparison",
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1
        )
    )

    return fig


def show_score_card(name, metrics, color):
    """Shows livability score card for one suburb"""
    score = compute_score(metrics)
    stars = "★" * int(score/2) + "☆" * (5 - int(score/2))

    st.markdown(f"""
    <div style="
        background: {color}22;
        border: 2px solid {color};
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    ">
        <h2 style="color:{color}; margin:0">{name}</h2>
        <h1 style="font-size:60px; margin:10px 0; color:white">
            {score}<span style="font-size:24px">/10</span>
        </h1>
        <p style="font-size:24px; color:{color}">{stars}</p>
        <p style="color:#aaa">Livability Score</p>
    </div>
    """, unsafe_allow_html=True)

    return score


# ── Page layout ───────────────────────────────────────────────
st.title("🏙️ Neighbourhood Livability Index")
st.caption("Compare suburbs by amenity density — powered by Google Places")
st.divider()

# Radius selector
st.write("#### Search Radius")
radius_km = st.select_slider(
    "Select how far from suburb centre to search:",
    options=[1, 2, 3, 5],
    value=2,
    format_func=lambda x: f"{x} km"
)
st.divider()

# Suburb inputs
col1, col2 = st.columns(2)
with col1:
    suburb_a = st.text_input("📍 Suburb A", placeholder="e.g. Geelong")
with col2:
    suburb_b = st.text_input("📍 Suburb B", placeholder="e.g. Werribee")

compare_btn = st.button(
    "🔍 Compare Suburbs",
    type="primary",
    use_container_width=True
)

# ── Main logic ────────────────────────────────────────────────
if compare_btn:
    if not suburb_a or not suburb_b:
        st.warning("Please enter BOTH suburbs to compare!")
    else:
        # Run pipeline for both suburbs
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"### Loading {suburb_a.title()}...")
            bar_a    = st.progress(0)
            text_a   = st.empty()
            def prog_a(p, m):
                bar_a.progress(p)
                text_a.write(m)

        with col2:
            st.write(f"### Loading {suburb_b.title()}...")
            bar_b    = st.progress(0)
            text_b   = st.empty()
            def prog_b(p, m):
                bar_b.progress(p)
                text_b.write(m)

        # Fetch data
        metrics_a = None
        metrics_b = None

        try:
            metrics_a = run_pipeline(suburb_a, prog_a, radius_km)
            bar_a.empty()
            text_a.empty()
        except Exception as e:
            bar_a.empty()
            text_a.empty()
            st.error(f"Error loading {suburb_a}: {e}")

        try:
            metrics_b = run_pipeline(suburb_b, prog_b, radius_km)
            bar_b.empty()
            text_b.empty()
        except Exception as e:
            bar_b.empty()
            text_b.empty()
            st.error(f"Error loading {suburb_b}: {e}")

        # Show charts if both loaded
        if metrics_a and metrics_b:
            name_a = suburb_a.strip().title()
            name_b = suburb_b.strip().title()

            st.divider()

            # ── Score cards ───────────────────────────────
            st.subheader("🏆 Livability Scores")
            sc1, sc2 = st.columns(2)

            with sc1:
                score_a = show_score_card(
                    name_a, metrics_a, "#00C2CB"
                )
            with sc2:
                score_b = show_score_card(
                    name_b, metrics_b, "#F5A623"
                )

            # Winner banner
            st.divider()
            if score_a > score_b:
                st.success(f"🏆 {name_a} wins with a livability score of {score_a}/10!")
            elif score_b > score_a:
                st.success(f"🏆 {name_b} wins with a livability score of {score_b}/10!")
            else:
                st.info("🤝 It's a tie!")

            st.divider()

            # ── Bar chart ─────────────────────────────────
            st.subheader("📊 Side by Side Comparison")
            bar_fig = make_bar_chart(
                metrics_a, metrics_b, name_a, name_b
            )
            st.plotly_chart(bar_fig, use_container_width=True)

            st.divider()

            # ── Radar chart ───────────────────────────────
            st.subheader("🕸️ Livability Shape")
            radar_fig = make_radar_chart(
                metrics_a, metrics_b, name_a, name_b
            )
            st.plotly_chart(radar_fig, use_container_width=True)

            st.divider()

            # ── Detailed table ────────────────────────────
            st.subheader("📋 Full Breakdown")
            rows = []
            for key, label in METRICS.items():
                val_a = metrics_a.get(key, 0)
                val_b = metrics_b.get(key, 0)
                if val_a > val_b:
                    winner = f"✅ {name_a}"
                elif val_b > val_a:
                    winner = f"✅ {name_b}"
                else:
                    winner = "🤝 Tie"
                rows.append({
                    "Category":   EMOJI[key] + " " + label,
                    name_a:       val_a,
                    name_b:       val_b,
                    "Winner":     winner
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.caption("demografy.com.au | Phase 3 of 5")
