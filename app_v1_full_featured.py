import streamlit as st
import math
from statsmodels.stats.proportion import proportion_effectsize
from statsmodels.stats.power import zt_ind_solve_power

# Page title and description
st.title("Concord - Sample Size Calculator")
st.write("""
Calculate how many people need to see each version of your test before you can trust the results. 
Use this for email campaigns, web page tests, ad variations, or any experiment where you're 
comparing two versions.
""")

st.divider()

# Input: Current conversion rate
baseline_rate = st.number_input(
    "Current conversion rate (%)",
    min_value=0.1,
    max_value=99.9,
    value=5.0,
    step=0.1,
    help="Your current performance. For emails, this is your current click rate or open rate. For web pages, this is your current conversion rate. Example: if 5 out of 100 people click, enter 5."
)

# Input: Minimum detectable effect (relative improvement)
minimum_improvement = st.number_input(
    "Minimum detectable effect (%)",
    min_value=0.1,
    max_value=200.0,
    value=20.0,
    step=0.1,
    help="The minimum relative improvement you want to detect. Example: if you're at 5% and enter 20%, you're testing whether you can reach 6% (which is 20% better than 5%). Smaller improvements require much larger sample sizes."
)

# Input: Confidence level
confidence_level = st.slider(
    "Confidence level",
    min_value=80,
    max_value=99,
    value=95,
    format="%d%%",
    help="How sure you want to be that your results are real and not just random chance. 95% is the industry standard - it means you'll be wrong only 5% of the time. Use 90% if you need faster results and can tolerate more risk."
)

# Input: Statistical power
power = st.slider(
    "Statistical power (sensitivity)",
    min_value=70,
    max_value=99,
    value=80,
    format="%d%%",
    help="The probability you'll detect an improvement when it actually exists. 80% is standard - meaning if there IS a real improvement, you'll detect it 80% of the time. Higher power requires larger sample sizes but gives more reliable results."
)

# Traffic split
st.write("**Traffic split**")
col1, col2 = st.columns(2)
with col1:
    control_ratio = st.number_input(
        "Control (%)",
        min_value=10,
        max_value=90,
        value=50,
        help="What percentage of your audience sees the original version. 50/50 is most efficient. Use 90/10 if you want to minimize risk to your main experience."
    )
with col2:
    treatment_ratio = st.number_input(
        "Variation (%)",
        min_value=10,
        max_value=90,
        value=50,
        help="What percentage of your audience sees the new version. Should add up to 100% with Control."
    )

st.divider()

# Calculate button
if st.button("Calculate Sample Size", type="primary", use_container_width=True):
    
    # Convert inputs to decimals
    control_proportion = baseline_rate / 100
    sensitivity = minimum_improvement / 100
    treatment_proportion = control_proportion * (1 + sensitivity)
    
    # Validation: make sure treatment_proportion doesn't exceed 100%
    if treatment_proportion > 1.0:
        st.error(f"⚠️ Error: Your target rate ({treatment_proportion*100:.1f}%) exceeds 100%. Please reduce your baseline rate or minimum improvement.")
        st.stop()
    
    # Get statistical parameters
    alpha = (100 - confidence_level) / 100
    power_decimal = power / 100
    
    # Adjust for unequal allocation if needed
    total_ratio = control_ratio + treatment_ratio
    if total_ratio != 100:
        st.warning(f"⚠️ Your traffic split adds up to {total_ratio}%. Adjusting to Control: {control_ratio}%, Variation: {100-control_ratio}%")
        treatment_ratio = 100 - control_ratio
    
    # Calculate ratio for statsmodels
    ratio = (treatment_ratio / 100) / (control_ratio / 100)
    
    # Calculate effect size using Cohen's h
    effect_size = proportion_effectsize(treatment_proportion, control_proportion)
    
    # Calculate sample size using statsmodels
    control_sample = math.ceil(zt_ind_solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power_decimal,
        ratio=ratio,
        alternative='two-sided'
    ))
    
    treatment_sample = math.ceil(control_sample * ratio)
    total_needed = control_sample + treatment_sample
    
    # Calculate the absolute difference in percentage points
    improvement_points = (treatment_proportion - control_proportion) * 100
    
    # Display results
    st.header("Results")
    
    # Main result message
    st.info(f"**{total_needed:,} is the minimum sample size required.**")
    
    # Detailed explanation
    st.write(f"""
    For a **{minimum_improvement}%** relative improvement (from **{baseline_rate}%** to **{treatment_proportion*100:.2f}%**, 
    a difference of **{improvement_points:.2f} percentage points**), with **{power}%** power, 
    the experiment needs at least **{control_sample:,}** samples for control and **{treatment_sample:,}** for treatment.
    """)
    
    # Breakdown by group
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Control")
        st.write(f"Sample size: **{control_sample:,}**")
        expected_conversions = math.floor(control_sample * control_proportion)
        st.write(f"Expected conversions: **{expected_conversions:,}**")
        st.write(f"Conversion rate: **{baseline_rate}%**")
    
    with col2:
        st.subheader("Treatment")
        st.write(f"Sample size: **{treatment_sample:,}**")
        expected_conversions_treatment = math.floor(treatment_sample * treatment_proportion)
        st.write(f"Expected conversions: **{expected_conversions_treatment:,}**")
        st.write(f"Conversion rate: **{treatment_proportion*100:.2f}%** (+{improvement_points:.2f} points)")
    
    # Practical interpretation
    st.divider()
    st.subheader("What this means:")
    
    # Calculate time estimates for different traffic levels
    days_1k = math.ceil(total_needed / 1000)
    days_10k = math.ceil(total_needed / 10000)
    
    st.write(f"""
    - **For an email campaign:** Send your test to at least **{total_needed:,}** people total ({control_sample:,} get version A, {treatment_sample:,} get version B)
    - **For a web page test:** Run until at least **{total_needed:,}** unique visitors have seen your test ({control_sample:,} see the original, {treatment_sample:,} see the new version)
    - **Time to run:** 
        - With 1,000 visitors/day: approximately **{days_1k} days**
        - With 10,000 visitors/day: approximately **{days_10k} days**
    """)
    
    # Show code option
    with st.expander("Show code"):
        st.code(f"""
# Import the libraries
import math
from statsmodels.stats.proportion import proportion_effectsize
from statsmodels.stats.power import zt_ind_solve_power

# Define the parameters
control_proportion = {control_proportion:.4f}
sensitivity = {sensitivity:.4f}
alternative = "two-sided"
confidence = {confidence_level / 100:.2f}
power = {power_decimal:.2f}
control_ratio = {control_ratio / 100:.2f}
treatment_ratio = {treatment_ratio / 100:.2f}

# Calculate the sample size
treatment_proportion = control_proportion * (1 + sensitivity)
effect_size = proportion_effectsize(
    treatment_proportion,
    control_proportion
)
alpha = 1 - confidence
ratio = treatment_ratio / control_ratio
control_sample = math.ceil(zt_ind_solve_power(
    effect_size=effect_size,
    alpha=alpha,
    power=power,
    ratio=ratio,
    alternative=alternative
))
treatment_sample = math.ceil(control_sample * ratio)

# Show the result
print("Sample size")
print(f"Control: {{control_sample:,}}")
print(f"Treatment: {{treatment_sample:,}}")
print(f"Total: {{(control_sample + treatment_sample):,}}")
""", language="python")