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
                 host='airbods.my-domain.com',
                 user='', # ENTER YOUR USERNAME HERE
                 password=keyring::key_get('airbods'),
                 dbname ='airbods'
                 )

# List available tables
dbListTables(con)

# Get column names for a table
print(dbListFields(con, 'reading'))

sql <- "
SELECT
   serial_number
  ,verbose_name
  ,time_europe_london
  ,area
  ,room
  ,air_quality
  ,co2
  ,humidity
  ,temperature
FROM reading
WHERE time_europe_london BETWEEN '2021-07-09' AND '2021-07-10'
  AND site LIKE '%Crucible%'
"
data = dbGetQuery(con, sql)

# Get result summary
print(names(data))
print(dim(data))
print(head(data))

# Close connection
#dbDisconnect(con) 

# Export to CSV
filename = sprintf("airbods_%s.csv", format(Sys.time(), "%Y%m%dT%H%M%S%z"))
write.csv(data, filename)
