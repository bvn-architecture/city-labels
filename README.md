# City Labels
  
![A world map with a marker that points to Oran in Algeria](city_maps/Algeria_Oran.png)
![A world map with a marker that points to Antwerp in Belgium](city_maps\Belgium_Antwerp.png)


A way to generate a lot of unique, but memorable labels. The cities are unique, the countries are just for context.

You can either use a `png` marker or a matplotlib marker. 

I've tested it up to 7000 labels, it seems pretty quick.

You'll still need to do a merge in something like indesign to make sheets ready to print.

## Installing

If you're on windows, you'll need to do:

```
pip install wheel
pip install pipwin
pipwin install numpy
pipwin install pandas
pipwin install shapely
pipwin install gdal
pipwin install fiona
pipwin install pyproj
pipwin install six
pipwin install rtree
pipwin install descartes
pipwin install geopandas
```
The requirements.txt is pointing to things on my laptop, which sucks
