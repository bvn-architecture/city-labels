"""
https://simplemaps.com/data/world-cities

https://stackoverflow.com/questions/16007743/roughly-approximate-the-width-of-a-string-of-text-in-python/16008023#16008023
"""
#%%
import math
import os
import string

import fiona
import geopandas as gp
import matplotlib
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import Point


def getApproximateArialStringWidth(st: str) -> int:
    """Calculate rough width of a word in a variable width font.
    By https://stackoverflow.com/users/234270/speedplane

    Args:
        st (str): The string you need a width for

    Returns:
        int: The rough width in picas
    """
    size = 0  # in milinches
    for s in st:
        if s in "lij|' ":
            size += 37
        elif s in "![]fI.,:;/\\t":
            size += 50
        elif s in '`-(){}r"':
            size += 60
        elif s in "*^zcsJkvxy":
            size += 85
        elif s in "aebdhnopqug#$L+<>=?_~FZT" + string.digits:
            size += 95
        elif s in "BSPEAKVXY&UwNRCHD":
            size += 112
        elif s in "QGOMm%W@":
            size += 135
        else:
            size += 50
    return size * 6 / 1000.0  # Convert to picas


#%%
cities = pd.read_excel("worldcities.xlsx")
cities.shape
# %%
cities.columns
#%%
by_country = cities.groupby("country")
#%%
def check_this_city_for_inclusion(
    x, label_data, country_exclusion_list=["Korea, North"]
):
    if getApproximateArialStringWidth(x.country) < 10:
        print(f"too long: {x.country}")
        return False
    elif getApproximateArialStringWidth(x.city) < 10:
        print(f"too long: {x.city}")
        return False
    elif x.city not in [d["city"] for d in label_data]:
        #  computationaly ineficient, but saves managing two arrays
        print(f"already taken: {x.city}, {x.country}")
        return False
    elif x.country in country_exclusion_list:
        # really just a demo of how to exclude a country, sorry Mr Kim
        print(f"{x.country} is on the country exclusion list")
        return False
    else:
        return True


#%%

"""
To make sure that the names will fit in the space, at the given font size etc.,
if the space can fit 13 M chars across, then getApproximateArialStringWidth("M"*13) gives 10.53,
so the space is 10 picas wide, and we can exclude wider names
"""
world = gp.read_file(gp.datasets.get_path("naturalearth_lowres"))
world = world[(world.name != "Antarctica") & (world.name != "Fr. S. Antarctic Lands")]

label_data = []
itteration = 0
pica_width_cutoff = math.floor(getApproximateArialStringWidth("M" * 13))
while len(label_data) < 700:
    for country, group in by_country:
        try:
            city_row = group.iloc[itteration]
            if check_this_city_for_inclusion(city_row, label_data):
                label_data.append(
                    {
                        "country": city_row.country,
                        "city": city_row.city,
                        "lat": city_row.lat,
                        "lon": city_row.lng,
                        "geometry": Point(city_row.lng, city_row.lat),
                        "map_file": f"city_maps/{city_row.country}_{city_row.city}.png",
                    }
                )
        except IndexError as e:
            print(f"by {itteration}, {country} is out of cities")
    itteration += 1

label_df = pd.DataFrame(label_data)
label_gdf = gp.GeoDataFrame(label_df)
label_gdf.sample(30)

#%% plot all cites from that run on the map
world = gp.read_file(gp.datasets.get_path("naturalearth_lowres"))
world = world[(world.name != "Antarctica") & (world.name != "Fr. S. Antarctic Lands")]
ax = world.plot(color="silver")
ax.set_axis_off()

label_gdf.plot(marker="+", color="k", markersize=50, ax=ax)
plt.savefig("world.png")

# %%
for i, row in label_gdf.iterrows():
    if True:  # i < 5:
        ax = world.plot(color="silver")
        ax.set_axis_off()
        d = gp.GeoDataFrame(row)
        # d.plot(marker="+", color="k", markersize=50, ax=ax)
        gp.GeoDataFrame({"geometry": row.geometry}, index=[0]).plot(
            marker="+", color="k", markersize=50, ax=ax
        )
        # plt.title(f"{row.country}, {row.city}")
        plt.savefig(row.map_file)

# %%
