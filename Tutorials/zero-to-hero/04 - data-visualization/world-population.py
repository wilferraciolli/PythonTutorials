import matplotlib.pyplot as plt

years = [
    1, 500, 1000, 1200, 1400, 1500, 1600, 1700, 1750,
    1800, 1850, 1900, 1920, 1950, 1970, 1980, 1990,
    2000, 2010, 2020, 2024, 2050, 2100
]

pops = [
    200, 190, 300, 400, 350, 450, 550, 610, 790,
    1000, 1260, 1650, 1860, 2520, 3700, 4440, 5330,
    6140, 6960, 7840, 8100, 9700, 10300
]

# Keep deaths in millions by dividing the thousands list by 1000
annual_deaths_mil = [d / 1000 for d in [
    8000, 7600, 11000, 15000, 15000, 16000, 19000, 21000, 26000,
    32000, 38000, 48000, 55000, 50000, 47000, 47500, 50000,
    52000, 56000, 63000, 63000, 74000, 90000
]]

fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Population on the left axis
ax1.set_xlabel('Year')
ax1.set_ylabel('World Population (Millions)', color='#FF6464')
line1 = ax1.plot(years, pops, '--', color='#FF6464', label='Population')
ax1.tick_params(axis='y', labelcolor='#FF6464')

# Create a second Y-axis for Annual Deaths on the right
ax2 = ax1.twinx()
ax2.set_ylabel('Annual Deaths (Millions)', color='#3333CC')
line2 = ax2.plot(years, annual_deaths_mil, color='#3333CC', label='Annual Deaths')
ax2.tick_params(axis='y', labelcolor='#3333CC')

plt.title('World Population vs. Annual Deaths (Dual Axis)')
fig.tight_layout()
plt.show()