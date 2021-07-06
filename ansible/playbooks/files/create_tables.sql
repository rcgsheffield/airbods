/* Sensor devices */
-- DROP TABLE IF EXISTS airbods.public.device CASCADE;
CREATE TABLE IF NOT EXISTS airbods.public.device
(
    device_id     uuid        NOT NULL PRIMARY KEY,
    serial_number varchar(128) NOT NULL UNIQUE,
    verbose_name  varchar(128) NOT NULL UNIQUE,
    object        json        NOT NULL
);

/* Deployments (sensor position during time period) */
-- DROP TABLE IF EXISTS airbods.public.deployment CASCADE ;
CREATE TABLE IF NOT EXISTS airbods.public.deployment
(
    serial_number varchar(128)               NOT NULL,
    start_time    timestamp with time zone  NOT NULL,
    -- end_time = NULL means that the deployment remains active
    end_time      timestamp with time zone  NULL,
    verbose_name  varchar(128)               NULL,
    city          varchar(128)               NULL,
    site          varchar(128)               NULL,
    area          varchar(128)               NULL,
    floor         varchar(128)               NULL,
    room          varchar(128)               NULL,
    zone          varchar(128)               NULL,
    description   varchar(256)              NULL,
    height        numeric(4, 2)             NULL,
    comments      text                      NULL,
    person        varchar(128)              NULL,
    UNIQUE (serial_number, start_time)
);

/* Raw data */
-- DROP TABLE IF EXISTS airbods.public.raw;
CREATE TABLE IF NOT EXISTS airbods.public.raw
(
    device_id        uuid               NOT NULL,
    time_            varchar(128)        NOT NULL,
    air_quality      varchar(128)        NULL,
    co2              double precision   NULL,
    humidity         double precision   NULL,
    temperature      double precision   NULL,
    lorawan_datarate varchar(16)        NULL,
    lorawan_rssi     double precision   NULL,
    lorawan_snr      double precision   NULL,
    battery          varchar(128)        NULL,
    pm1              double precision   NULL,
    pm25             double precision   NULL,
    pm10             double precision   NULL,
    -- Two-column unique restriction
    UNIQUE (device_id, time_)
);

/* Clean data */
-- DROP TABLE IF EXISTS airbods.public.clean CASCADE;
CREATE TABLE IF NOT EXISTS airbods.public.clean
(
    device_id   uuid                        NOT NULL,
    time_       timestamp with time zone    NOT NULL,
    air_quality varchar(128)                 NULL,
    co2         double precision            NULL,
    humidity    double precision            NULL,
    temperature double precision            NULL,
    -- Two-column unique restriction
    -- Allow this constraint to be deferred within a multi-statement transaction
    -- so that chunks of data can be replaced easily
    -- https://dba.stackexchange.com/a/105092
    UNIQUE (device_id, time_) DEFERRABLE INITIALLY IMMEDIATE
);

/* Useful view */
CREATE OR REPLACE VIEW airbods.public.clean_device AS
SELECT clean.device_id
     , device.serial_number AS serial_number
     , device.verbose_name  AS sensor_name
     , clean.time_ AS time_utc
     , clean.time_ AT time zone 'Europe/London' AS time_europe_london
     , deployment.city
     , deployment.site
     , deployment.floor
     , deployment.room
     , deployment.zone
     , deployment.area
     , deployment.height
     , deployment.description
     , deployment.comments
     , deployment.person
     -- Metrics
     , clean.air_quality
     , clean.co2
     , clean.humidity
     , clean.temperature
    -- Room averages
    , AVG(clean.co2) OVER (PARTITION BY deployment.room) AS co2_room
    , AVG(clean.humidity) OVER (PARTITION BY deployment.room) AS humidity_room
    , AVG(clean.temperature) OVER (PARTITION BY deployment.room) AS temperature_room
FROM airbods.public.clean
    INNER JOIN airbods.public.device ON clean.device_id = device.device_id
    LEFT JOIN airbods.public.deployment
        ON device.serial_number = deployment.serial_number
        AND clean.time_ BETWEEN deployment.start_time AND COALESCE(deployment.end_time, NOW());
