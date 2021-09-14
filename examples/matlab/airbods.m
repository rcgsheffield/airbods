%{
Get Airbods data from the PostgreSQL database

You'll need to install MATLAB Database Toolbox
https://uk.mathworks.com/products/database.html

Configure PostgreSQL Native Interface Data Source
https://uk.mathworks.com/help/database/ug/configure-postgresql-native-interface-data-source.html

Import Data from PostgreSQL Database Table
https://uk.mathworks.com/help/database/ug/import-data-from-postgresql-database-table.html
%}

% Connect to the database
datasource = "Airbods";
username = ""; % ENTER YOUR USERNAME HERE
password = input("Enter password: ", "s");
conn = postgresql(datasource, username, password);

% Explore the schema

% Get details of each device
devices = sqlread(conn, "device");
%disp(devices);

% Download data
% Define SQL statement as multiline string
% https://uk.mathworks.com/matlabcentral/answers/21308-dealing-with-multiline-text#answer_28088
sql = sprintf('%s\n', [
"SELECT",
"   serial_number",
"  ,verbose_name",
"  ,time_europe_london",
"  ,area",
"  ,room",
"  ,air_quality",
"  ,co2",
"  ,humidity",
"  ,temperature",
"FROM reading",
"WHERE time_europe_london BETWEEN '2021-07-09' AND '2021-07-10'",
"  AND site LIKE '%Crucible%'"
]);
readings = fetch(conn, sql);
%disp(readings);

% Write to CSV
filename = sprintf('airbods_%s.csv', datestr(now, 'yyyyddmmTHHMMSS.FFFZ'));
writetable(readings, filename)
