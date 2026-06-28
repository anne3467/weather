Open-Meteo local tile adapter for the modified Bing Weather 4.53 package

1. Run Install-BingWeather453LocalTile.ps1 from the package root.
2. The installer trusts the local test certificate, installs the app,
   enables loopback, and registers the adapter to start at logon.
3. If needed, run Start-Adapter.ps1 manually before opening Weather.

The adapter listens on http://127.0.0.1:8765 and converts Open-Meteo
forecast/geocoding responses into the old MSN Weather response shape.
It also serves the 4.46-style live tile icons and backgrounds locally.
