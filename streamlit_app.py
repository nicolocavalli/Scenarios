
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Population Projections", layout="centered")
st.title("Immigration Boost Projections for Italy")

@st.cache_data
def load_data():
    baseline = pd.read_csv("Population_Data_with_Yearly_Immigration_Columns.csv")
    boost_ready = pd.read_csv("Projections_With_Immigration_Boost_Setup.csv")
    return baseline, boost_ready

baseline_df, base_projection = load_data()

st.sidebar.header("Set Immigration Boost Parameters")
boost_start = st.sidebar.slider("Start Year", min_value=2025, max_value=2070, value=2026)
boost_end = st.sidebar.slider("End Year", min_value=2025, max_value=2075, value=2035)
boost_amount = st.sidebar.number_input("Immigrants per Year", min_value=0, value=200000, step=50000)

def run_projection(boost_start, boost_end, boost_amount, base_df):
    projections = base_df.copy()
    sex_ratio_at_birth = 0.512
    years = list(range(2025, 2076))

    for year in years[:-1]:
        next_year = year + 1

        if boost_start <= year <= boost_end:
            wm = projections["immigration_boost1w_Maschi_stranieri"]
            wf = projections["immigration_boost1w_Femmine_straniere"]  # fixed column name
            projections[f"{year}_Maschi_stranieri"] += boost_amount * wm
            projections[f"{year}_Femmine_straniere"] += boost_amount * wf

        for group in ["Maschi_stranieri", "Femmine_straniere"]:
            s_col = "Male_survival" if "Maschi" in group else "Female_survival"
            projections[f"{next_year}_{group}"] = projections[f"{year}_{group}"] * projections[s_col]

        for group in ["Maschi_stranieri", "Femmine_straniere"]:
            s_col = "Male_survival" if "Maschi" in group else "Female_survival"
            projections.loc[projections.index[1:], f"{next_year}_{group}"] = (
                projections.loc[projections.index[:-1], f"{next_year}_{group}"].values
            )
            projections.loc[projections["Età"] == 100, f"{next_year}_{group}"] = (
                projections.loc[projections["Età"] == 99, f"{year}_{group}"].values[0] * projections[s_col].iloc[99] +
                projections.loc[projections["Età"] == 100, f"{year}_{group}"].values[0] * projections[s_col].iloc[100]
            )

        fert_col = "Fertility_stranieri"
        births = (projections[f"{year}_Femmine_straniere"] * projections[fert_col]).sum() / 1000
        projections.loc[0, f"{year}_births_stranieri"] = births
        projections.loc[projections["Età"] == 0, f"{next_year}_Maschi_stranieri"] = births * sex_ratio_at_birth
        projections.loc[projections["Età"] == 0, f"{next_year}_Femmine_straniere"] = births * (1 - sex_ratio_at_birth)

        for col in [f"{next_year}_Maschi_stranieri", f"{next_year}_Femmine_straniere"]:
            projections[col] = projections[col].round().astype(int)

    return projections

proj_df = run_projection(boost_start, boost_end, boost_amount, base_projection)

st.subheader("Total Population Over Time")
years = list(range(2024, 2076))

def total_pop(df):
    return [
        (df[f"{y}_Maschi_italiani"] + df[f"{y}_Femmine_italiane"] +
         df[f"{y}_Maschi_stranieri"] + df[f"{y}_Femmine_straniere"]).sum()
        for y in years
    ]

pop_base = total_pop(baseline_df)
pop_proj = total_pop(proj_df)

fig1, ax1 = plt.subplots(figsize=(10, 4))
ax1.plot(years, pop_base, label="Baseline", linestyle="--")
ax1.plot(years, pop_proj, label="Boosted Scenario", linewidth=2)
ax1.set_xlabel("Year")
ax1.set_ylabel("Total Population")
ax1.set_title("Total Population Over Time")
ax1.grid(True)
ax1.legend()
st.pyplot(fig1)

st.subheader("Population Pyramid: Year 2075")

age = proj_df["Età"]
year = 2075
bm = (baseline_df[f"{year}_Maschi_italiani"] + baseline_df[f"{year}_Maschi_stranieri"]).values
bf = (baseline_df[f"{year}_Femmine_italiane"] + baseline_df[f"{year}_Femmine_straniere"]).values
pm = (proj_df[f"{year}_Maschi_italiani"] + proj_df[f"{year}_Maschi_stranieri"]).values
pf = (proj_df[f"{year}_Femmine_italiane"] + proj_df[f"{year}_Femmine_straniere"]).values
age_np = np.array(age)

fig2, ax2 = plt.subplots(figsize=(10, 6))
ax2.barh(age_np, -bm, label="Maschi (Baseline)", color="skyblue", alpha=0.8)
ax2.barh(age_np, bf, label="Femmine (Baseline)", color="lightcoral", alpha=0.8)
ax2.fill_betweenx(age_np, -pm, -bm, where=(-pm < -bm), facecolor='blue', alpha=0.3, label="Maschi (Boosted Area)")
ax2.fill_betweenx(age_np, pf, bf, where=(pf > bf), facecolor='red', alpha=0.3, label="Femmine (Boosted Area)")
ax2.axvline(0, color='black', linewidth=0.5)
ax2.set_xlabel("Popolazione")
ax2.set_ylabel("Età")
ax2.set_title("Piramide della popolazione (2075)")
ax2.legend(loc="upper right")
ax2.grid(True, axis='x', linestyle='--')
st.pyplot(fig2)
