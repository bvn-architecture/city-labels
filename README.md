# City Labels

A way to generate a lot of unique, but memorable labels. The cities are unique, the countries are just for context.

:warning: **Warning:** this is super sketchy code. If you think it's useful, let me know and I'll add more features and tidy it up.

|Vancouver, Canada |Lagos, Nigeria |
|---|---|  
|![A world map with a marker that points to Vancouver in Canada](Canada_Vancouver.svg)|![A world map with a marker that points to Lagos in Nigeria](Nigeria_Lagos.svg)|


You can either use a `png` marker or a MatPlotLib marker. 

I've tested it up to 7000 labels, it seems pretty quick.

You'll still need to do a merge in something like InDesign to make sheets ready to print.

These are coloured in magenta because that's what the printer takes as white when they print white onto a clear sticker. You can change that colour in the code. 

## Installing

If you're on windows, you'll need to do the following to install geopandas:

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
The requirements.txt is pointing to packages on my laptop, which sucks
