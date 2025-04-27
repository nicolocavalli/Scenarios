import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- UI Sidebar ---
st.sidebar.title("Immigration Boost Policy")
boost_start = st.sidebar.number_input("Boost Start Year", min_value=2026, max_value=2070, value=2026, step=1)
boost_end = st.sidebar.number_input("Boost End Year", min_value=2026, max_value=2075, value=2035, step=1)
boost_amount = st.sidebar.number_input("Annual Immigration Boost", min_value=0, value=200000, step=10000)

# --- Load Data ---
@st.cache_data
def load_data():
    boost_df = pd.read_csv("Youth_Boost_Weights_Applied.csv")
    no_imm_df = pd.read_csv("Population_Data_with_Yearly_Immigration_Columns.csv")
    return boost_df, no_imm_df

boost_df, no_immigration_df = load_data()

# --- Projection Engine ---
def simulate_boost_population(boost_start, boost_end, boost_amount, base_df):
    projections = base_df.copy()
    years = list(range(2025, 2076))
    sex_ratio_at_birth = 0.512

    for year in years:
        for group in ["Maschi_stranieri", "Femmine_straniere"]:
            projections[f"{year}_{group}"] = 0

    for year in years[:-1]:
        next_year = year + 1

        if boost_start <= year <= boost_end:
            wm = projections["immigration_boost1w_Maschi_stranieri"]
            wf = projections["immigration_boost1w_Femmine_stranieri"]
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

# --- Totals Calculation ---
def total_population(df):
    years = list(range(2025, 2076))
    return [
        (df[f"{y}_Maschi_italiani"] + df[f"{y}_Femmine_italiane"] +
         df[f"{y}_Maschi_stranieri"] + df[f"{y}_Femmine_straniere"]).sum()
        for y in years
    ]

def total_foreign_population(df):
    years = list(range(2025, 2076))
    return [
        (df[f"{y}_Maschi_stranieri"] + df[f"{y}_Femmine_straniere"]).sum()
        for y in years
    ]

# --- Run Projection ---
years = list(range(2025, 2076))
pop_baseline = total_population(boost_df)
pop_no_immigration = total_population(no_immigration_df)

boost_projection = simulate_boost_population(boost_start, boost_end, boost_amount, boost_df)
pop_boost = total_foreign_population(boost_projection)
pop_boosted = [b + p for b, p in zip(pop_baseline, pop_boost)]


# --- Plot: Total Births Over Time ---
st.subheader("Total Births Per Year: Baseline vs Boosted Scenario")

birth_years = list(range(2026, 2075))

# Corrected births: combine existing births from baseline and additional from boost_projection
births_baseline = [
    boost_df[f"{y}_births_italiani"].sum() + boost_df[f"{y}_births_stranieri"].sum()
    for y in birth_years
]

births_boosted = [
    boost_df[f"{y}_births_italiani"].sum() + 
    boost_df[f"{y}_births_stranieri"].sum() + 
    boost_projection.get(f"{y}_births_stranieri", pd.Series([0])).sum()
    for y in birth_years
]

# Plot
fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.plot(birth_years, births_baseline, label="Baseline", linestyle="--", color="black")
ax3.plot(birth_years, births_boosted, label="With Immigration Boost", color="blue", linewidth=2)
ax3.axvspan(boost_start, boost_end, color="blue", alpha=0.1, label="Boost Period")
ax3.set_xlabel("Year")
ax3.set_ylabel("Total Births")
ax3.set_title("Total Annual Births: Baseline vs Boosted Scenario")
ax3.legend()
ax3.grid(True)
st.pyplot(fig3)


# --- Plot: Total Population Over Time ---
st.subheader("Total Population Over Time")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(years, pop_no_immigration, label="No Immigration", linestyle="--", color="gray")
ax.plot(years, pop_baseline, label="Baseline (Current Forecast)", linestyle="--", color="black")
ax.plot(years, pop_boosted, label="With Immigration Boost", color="blue", linewidth=2)
ax.axvspan(boost_start, boost_end, color="blue", alpha=0.1, label="Boost Period")
ax.set_xlabel("Year")
ax.set_ylabel("Total Population")
ax.set_title("Total Population: No Immigration vs Baseline vs Boost")
ax.legend()
ax.grid(True)
st.pyplot(fig)


# --- Plot: Population Pyramid in Final Year (e.g. 2075) ---
st.subheader(f"Population Pyramid: {years[-1]} (Baseline vs Boosted Total)")

final_year = years[-1]
età = boost_df["Età"]

# Baseline population (males + females)
baseline_m = boost_df[f"{final_year}_Maschi_italiani"] + boost_df[f"{final_year}_Maschi_stranieri"]
baseline_f = boost_df[f"{final_year}_Femmine_italiane"] + boost_df[f"{final_year}_Femmine_straniere"]

# Boosted foreign population
boost_m = boost_projection[f"{final_year}_Maschi_stranieri"]
boost_f = boost_projection[f"{final_year}_Femmine_straniere"]

# Total with boost
total_boosted_m = baseline_m + boost_m
total_boosted_f = baseline_f + boost_f

# Plot
fig2, ax2 = plt.subplots(figsize=(8, 6))
ax2.barh(età, -baseline_m, color="lightgray", label="Baseline M")
ax2.barh(età, baseline_f, color="gray", label="Baseline F")
ax2.barh(età, -total_boosted_m, color="blue", alpha=0.4, label="Boosted M")
ax2.barh(età, total_boosted_f, color="red", alpha=0.4, label="Boosted F")

ax2.set_xlabel("Population")
ax2.set_ylabel("Age")
ax2.set_title(f"Population Pyramid in {final_year}: Baseline vs Boosted")
ax2.legend(loc="lower right")
ax2.grid(True)

st.pyplot(fig2)


