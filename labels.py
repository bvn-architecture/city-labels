"""
https://simplemaps.com/data/world-cities

https://stackoverflow.com/questions/16007743/roughly-approximate-the-width-of-a-string-of-text-in-python/16008023#16008023
"""
#%%
from itertools import count
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

#%% There's something strange happening inside geopandas, this silences the warning
import warnings
from shapely.errors import ShapelyDeprecationWarning

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

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
                            "map_file": f"city_maps/{city_row.country}_{city_row.city}.svg",
                        }
                    )
            except IndexError as e:
                if country in exhausted_countries_list:
                    pass
                else:
                    print(
                        f"by itteration {itteration+1}, "
                        f"with {len(label_data)} cities on the list, "
                        f"{country} is out of cities"
                    )
                    exhausted_countries_list.append(country)
        itteration += 1

    label_data.append(
        make_specific_place(
            # For Lulu
            lat=45.81477,
            lon=9.07528,
            country="Italy",
            city="Como",
        )
    )
    label_data.append(
        make_specific_place(
            # for Ben
            lat=51.12547,
            lon=1.08836,
            country="United Kingdom",
            city="Lyminge",
        )
    )
    label_df = pd.DataFrame(label_data)
    label_gdf = gp.GeoDataFrame(label_df)
    return label_gdf


def make_specific_place(lat=6.9, lon=6.9, country="Nigeria", city="Afa"):
    """Make a data dict to add to the list of places for labels to be made for.

    There is no option to add an ascii name for teh filename, so let me know if
    you need one. See above for what I mean.

    Args:
        lat (float, optional): Latitude . Defaults to 6.9.
        lon (float, optional): Longitude. Defaults to 6.9.
        country (str, optional): Name of country. Defaults to "Nigeria".
        city (str, optional): Name of place. Defaults to "Afa".

    Returns:
        dict: a dictionary ready to put into the dataframe
    """
    return {
        "country": country,
        "city": city,
        "lat": lat,
        "lon": lon,
        "geometry": Point(lon, lat),
        "map_file": f"city_maps/{country}_{city}.svg",
    }


# %%
def getImage(path, zoom=1):
    return OffsetImage(plt.imread(path), zoom=zoom)


#%%
def marker_is_behind_text(ax, row, fig, text_object, draw_box=False):
    transf = ax.transData.inverted()
    bb = text_object.get_window_extent(renderer=fig.canvas.renderer)
    bbxy = bb.transformed(transf)

    mx = row.geometry.x
    my = row.geometry.y
    crossing = (bbxy.x0 < mx < bbxy.x1) and (bbxy.y0 < my < bbxy.y1)

    if draw_box:
        from matplotlib.patches import Rectangle

        if crossing:
            colour = "red"
        else:
            colour = "green"

        width = bbxy.x1 - bbxy.x0
        height = bbxy.y1 - bbxy.y0
        plt.gca().add_patch(
            Rectangle(
                (bbxy.x0, bbxy.y0),
                width,
                height,
                linewidth=1,
                edgecolor=colour,
                facecolor="none",
            )
        )

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
def place_anti_bounce_markers(ax, dist=0.2):
    # set some markers far out of the print area so that INDD doesn't bounce when it's placing the image file
    plt.text(-dist, -dist * 1.5, "|", fontsize=2, transform=ax.transAxes)
    plt.text(-dist, 1 + dist, "|", fontsize=2, transform=ax.transAxes)
    plt.text(1 + dist, 1 + dist, "|", fontsize=2, transform=ax.transAxes)
    plt.text(1 + dist, -dist * 1.5, "|", fontsize=2, transform=ax.transAxes)


def draw_text(ax, ink_colour, row, alpha):
    ci = plt.text(
        0.02,
        0.04,
        row.city,
        fontsize=10,
        color=ink_colour,
        alpha=alpha,
        transform=ax.transAxes,
    )
    if row.city == row.country:
        country = ""
    else:
        country = row.country
    co = plt.text(
        0.02,
        -0.11,
        country,
        fontsize=7,
        color=ink_colour,
        alpha=alpha,
        transform=ax.transAxes,
    )

    return ci, co


#%%
use_mpl_marker = False
use_img_marker = True
plot_width_mm = 62
plot_height_mm = 28
MM2IN = 25.4
ink_colour = "black"
paper_colour = "magenta"
add_text = False
data_about_labels_made = []
skipped_cities = []

for i, row in label_gdf.iterrows():
    if True:
        # if (
        #     i < 1
        #     # or row.country == "Tonga"
        #     or row.country == "Brazil"
        #     # or row.country == "Australia"
        #     # or row.country == "Bahamas"
        # ):
        try:
            ax = world.boundary.plot(
                color=ink_colour,
                linewidth=0.3,
            )
            fig = matplotlib.pyplot.gcf()
            # fig.set_dpi(600)
            fig.set_size_inches(plot_width_mm / MM2IN, plot_height_mm / MM2IN)
            ax.set_axis_off()
            # Don't set the background colour here as it converts to \
            # RGB, therefore won't match process magenta
            # fig.patch.set_facecolor(paper_colour)
            d = gp.GeoDataFrame(row)
            if use_mpl_marker:
                gp.GeoDataFrame({"geometry": row.geometry}, index=[0]).plot(
                    marker="+",
                    color=ink_colour,
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

            place_anti_bounce_markers(ax)

            if add_text:
                alpha = 1
            else:
                alpha = 0
            ci, co = draw_text(ax, ink_colour, row, alpha)
            crossing_city = marker_is_behind_text(ax, row, fig, ci)  # , draw_box=True)
            crossing_country = marker_is_behind_text(
                ax, row, fig, co
            )  # , draw_box=True)

            if crossing_city or crossing_country:
                print(f"{row.country} {row.city} is behind the text")
                skipped_cities.append(row)
                ## Uncomment this to see the cities that didn't make the cut
                # ci, co = draw_text(ax, ink_colour, row, 1)
                # marker_is_behind_text(ax, row, fig, ci, draw_box=True)
                # marker_is_behind_text(ax, row, fig, co, draw_box=True)
                # plt.savefig(
                #     row.map_file.replace("city_maps", "crossing_maps"),
                #     bbox_inches="tight",
                #     dpi=1200,
                #     transparent=True,
                # )
            else:
                plt.savefig(
                    row.map_file, bbox_inches="tight", dpi=1200, transparent=True
                )
                img_path = f"C:/Users/bdoherty/OneDrive - BVN/General/labeling/city-labels/{row.map_file}".replace(
                    "/", "\\"
                )
                data_about_labels_made.append(
                    {
                        "country": row.country,
                        "city": row.city,
                        "@platform_path": img_path,
                        "platform_path_check": img_path,
                    }
                )
            plt.close(fig)
        except FileNotFoundError as fe:
            print(fe)
            # maybe a name with a slash in it, e.g. https://en.wikipedia.org/wiki/Biel/Bienne

print("saving the CSV")
pd.DataFrame(data_about_labels_made).to_csv(
    "label_data.csv", index=False
)  # , encoding="utf-16")
print("saved the CSV, remember to resave it with Western (Windows 1252) encoding")
# %%
# TODO: export the label data to an excel file or a csv (check which)
