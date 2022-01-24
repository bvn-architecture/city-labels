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
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from shapely.geometry import Point

#%%
cities = pd.read_excel("worldcities.xlsx")
print(f"loaded city data, {cities.shape[0]} rows")

#%%
def getApproximateArialStringWidth(st: str) -> float:
    """Calculate rough width of a word in a variable width font.
    By https://stackoverflow.com/users/234270/speedplane

    Args:
        st (str): The string you need a width for

    Returns:
        float: The rough width in picas

    To make sure that the names will fit in the space, at the given font size etc.,
    if the space can fit 13 M chars across, then getApproximateArialStringWidth("M"*13) gives 10.53,
    so the space is 10 picas wide, and we can exclude wider names.
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
def this_city_should_be_included(
    x: pd.Series,
    label_data: list[dict],
    max_pica_width: float = 10.01,
    country_exclusion_list: list[str] = ["Korea, North"],
    verbose: bool = False,
) -> bool:
    """Based on some criteria, decide if this city should be added to the output dataset.

    Args:
        x (pd.Series): the row that describes that city
        label_data (list[dict]): running list of the cities we're keeping
        max_pica_width (float): width of the string, roughly, when rendered with a font. i.e. iiii is narrower than MMMM
        country_exclusion_list (list[str], optional): List of countries to exclude from the output. Defaults to ["Korea, North"].
        verbose (bool, optional): Explain what's going on. Note, this produces a lot of terminal output and slows things down a lot. Defaults to False.

    Returns:
        bool: [description]
    """
    if getApproximateArialStringWidth(x.country) > max_pica_width:
        if verbose:
            w = getApproximateArialStringWidth(x.country)
            print(f"too long: {x.country} ({w} picas)")
    elif getApproximateArialStringWidth(x.city) > max_pica_width:
        if verbose:
            w = getApproximateArialStringWidth(x.city)
            print(f"too long: {x.city} ({w} picas)")
    elif x.city in [d["city"] for d in label_data]:
        #  computationaly ineficient, but saves managing two arrays
        if verbose:
            print(f"Sorry {x.country}, already taken: {x.city}, {x.country}")
    elif x.country in country_exclusion_list:
        # really just a demo of how to exclude a country, sorry Mr Kim
        if verbose:
            print(f"{x.country} is on the country exclusion list")
    else:
        return True, label_data
    return False, label_data


def make_labels(cities: pd.DataFrame, number_of_labels: int = 700) -> gp.GeoDataFrame:
    by_country = cities.groupby("country")

    exhausted_countries_list = []
    label_data = []
    itteration = 0
    pica_width_cutoff = math.floor(getApproximateArialStringWidth("M" * 13))
    while len(label_data) < number_of_labels:
        for country, group in by_country:
            try:
                city_row = group.iloc[itteration]
                include, label_data = this_city_should_be_included(
                    city_row, label_data, max_pica_width=pica_width_cutoff
                )
                if include:
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
                if country in exhausted_countries_list:
                    pass
                else:
                    print(
                        f"by itteration {itteration}, "
                        f"with {len(label_data)} cities on the list, "
                        f"{country} is out of cities"
                    )
                    exhausted_countries_list.append(country)
        itteration += 1

    label_df = pd.DataFrame(label_data)
    label_gdf = gp.GeoDataFrame(label_df)
    return label_gdf


# %%
def getImage(path, zoom=1):
    return OffsetImage(plt.imread(path), zoom=zoom)


#%%
def marker_is_behind_text(ax, row, fig, text_object, draw_box=False):
    transf = ax.transData.inverted()
    bb = text_object.get_window_extent(renderer=fig.canvas.renderer)
    bbxy = bb.transformed(transf)

    if draw_box:
        from matplotlib.patches import Rectangle

        width = bbxy.x1 - bbxy.x0
        height = bbxy.y1 - bbxy.y0
        plt.gca().add_patch(
            Rectangle(
                (bbxy.x0, bbxy.y0),
                width,
                height,
                linewidth=1,
                edgecolor="r",
                facecolor="none",
            )
        )

    mx = row.geometry.x
    my = row.geometry.y
    crossing = (bbxy.x0 < mx < bb.x1) and (bbxy.y0 < my < bb.y1)
    return crossing


#%%
label_gdf = make_labels(cities)

label_gdf.sample(30)

#%% plot all cites from that run on the map
# TODO: calculate specific image sizes for the maps to fit on the sickers, and tight layout
world = gp.read_file(gp.datasets.get_path("naturalearth_lowres"))
world = world[(world.name != "Antarctica") & (world.name != "Fr. S. Antarctic Lands")]

ax = world.plot(color="silver")
ax.set_axis_off()


#%%
use_mpl_marker = False
use_img_marker = True
plot_width_mm = 62
plot_height_mm = 28
MM2IN = 25.4
colour = "magenta"
add_text = True

for i, row in label_gdf.iterrows():
    # if True:
    if i < 1 or row.country == "Tonga":
        ax = world.boundary.plot(
            color=colour,
            linewidth=0.3,
        )
        fig = matplotlib.pyplot.gcf()
        fig.set_size_inches(plot_width_mm / MM2IN, plot_height_mm / MM2IN)
        ax.set_axis_off()
        d = gp.GeoDataFrame(row)
        if use_mpl_marker:
            gp.GeoDataFrame({"geometry": row.geometry}, index=[0]).plot(
                marker="+",
                color=colour,
                linewidth=1,
                markersize=1000,  # 500000 for world spanning markers
                ax=ax,
            )
        if use_img_marker:
            ab = AnnotationBbox(
                getImage("markers/cross.png", zoom=0.11),
                (row.geometry.x, row.geometry.y),
                frameon=False,
            )
            ax.add_artist(ab)

        if add_text:
            ci = plt.text(
                0,
                0.15,
                row.city,
                fontsize=12,
                color=colour,
                transform=ax.transAxes,
            )
            co = plt.text(
                0,
                0.005,
                row.country,
                fontsize=8,
                color=colour,
                transform=ax.transAxes,
            )
            crossing_city = marker_is_behind_text(ax, row, fig, ci)
            crossing_country = marker_is_behind_text(ax, row, fig, co)

            if crossing_city or crossing_country:
                print(f"{row.country} {row.city} is behind the text")
                # TODO: drop this from the label data row if we care about crossings

        plt.savefig(row.map_file, bbox_inches="tight", dpi=300)


# %%
# TODO: export the label data to an excel file or a csv (check which)
