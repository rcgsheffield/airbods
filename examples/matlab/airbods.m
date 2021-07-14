% Get Airbods data from the PostgreSQL database

% You'll need to install MATLAB Database Toolbox
% https://uk.mathworks.com/products/database.html

% Configure PostgreSQL Native Interface Data Source
% https://uk.mathworks.com/help/database/ug/configure-postgresql-native-interface-data-source.html

% Import Data from PostgreSQL Database Table
% https://uk.mathworks.com/help/database/ug/import-data-from-postgresql-database-table.html

% Connect to the database
datasource = "Airbods Dev";
username = "airbods";
conn = postgresql(datasource, username, 'PASSWORD');

% Explore the schema
tablename = "device";
data = sqlread(conn, tablename);
disp(data)
