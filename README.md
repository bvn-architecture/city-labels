# City Labels

| | |
|---|---|  
|![A world map with a marker that points to Oran in Algeria](city_maps/Algeria_Oran.png)|![A world map with a marker that points to Antwerp in Belgium](city_maps/Belgium_Antwerp.png)|


A way to generate a lot of unique, but memorable labels. The cities are unique, the countries are just for context.

**Warning:** this is super sketchy code. If you think it's useful, let me know and I'll add more features and tidy it up.

You can either use a `png` marker or a MatPlotLib marker. 

I've tested it up to 7000 labels, it seems pretty quick.

You'll still need to do a merge in something like InDesign to make sheets ready to print.

These are coloured in magenta because that's what the printer takes as white when they print white onto a clear sticker. You can change that colour in the code. 

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
