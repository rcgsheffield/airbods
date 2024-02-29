

## Open Database Connectivity (ODBC)

To install the PostgreSQL ODBC driver for Windows:

1. Visit the [psqlODBC - PostgreSQL ODBC driver](https://odbc.postgresql.org/) page
2. Click on the [PostgreSQL downloads site](http://www.postgresql.org/ftp/odbc/versions/)
3. For Windows, select `msi`
4. Scroll down to the latest version, which is `psqlodbc_13_01_0000.zip` at the time of writing
5. Download and install this driver
6. Open the ODBC Data Source Administrator via the start menu or by running `odbcad32`
7. Create a DSN:
   1. Click "Add"
   2. Select "PostgreSQL Unicode" and click "Finish"
   3. Enter the following values:
      1. Database: `airbods`
      2. Server: `airbods.my-domain.com`
      3. Username: `<your user name>`
      4. Password: `<your password>`
