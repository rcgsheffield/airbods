# Airbods database

# Connect to PostgreSQL with R: A step-by-step example
# https://www.datacareer.de/blog/connect-to-postgresql-with-r-a-step-by-step-example/

# Install the latest RPostgres release from CRAN:
# https://rpostgres.r-dbi.org/
install.packages("RPostgres")

# Security tool for password storage
install.packages("keyring")

# Import database package
library(DBI)

# Store password
# keyring::key_set_with_value('airbods', password='password')

# Connect to the default PostgreSQL database
con <- dbConnect(RPostgres::Postgres(),
                 host='airbodsdev.shef.ac.uk',
                 user='airbods',
                 password=keyring::key_get('airbods'),
                 dbname ='airbods'
                 )

# List available tables
dbListTables(con)

# Get column names for a table
#print(dbListFields(con, 'device'))

sql <- "
SELECT
   device_id
  ,serial_number
  ,verbose_name
FROM device
LIMIT 10
"
data = dbGetQuery(con, sql)

# Get result summary
print(names(data))
print(dim(data))
print(head(data))

# Close connection
#dbDisconnect(con) 
