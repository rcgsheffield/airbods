# Excel

To use Excel to connect to the database, you need an ODBC connection or DSN. You need the ODBC driver for PostgreSQL installed to do this.

1. Open the "Data" tab
2. Click "New Query"
3. Click "From Other Sources"
4. Click "From ODBC"
5. Under "Data source name (DSN)" select "PostreSQL35W" and click "OK"
6. Open the folders: `airbods` then `public` 
7. Select `reading` (or another item) and click "Edit" to customise the query (to avoid downloading the entire database)
8. Click "Refresh Preview" to see what the data look like
9. Use the Power Query Editor to filter and transform data as required then click "Close & Load"