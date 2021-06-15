/* Sensor devices */
DROP TABLE IF EXISTS airbods.public.device;
CREATE TABLE IF NOT EXISTS airbods.public.device (
    device_id       uuid NOT NULL PRIMARY KEY,
    serial_number   varchar(32) NOT NULL UNIQUE,
    verbose_name    varchar(64) NOT NULL UNIQUE,
    object          json NOT NULL
);

/* Deployments (sensor position during time period) */
DROP TABLE IF EXISTS airbods.public.deployment;
CREATE TABLE IF NOT EXISTS airbods.public.deployment (
    device_id       uuid NOT NULL PRIMARY KEY REFERENCES device(device_id),
    start_time      timestamp with time zone NOT NULL,
    end_time        timestamp with time zone NOT NULL,
    sensor_number   int NULL,
    city            varchar(32) NULL,
    site            varchar(32) NULL,
    area            varchar(32) NULL,
    floor           varchar(32) NULL,
    room            varchar(32) NULL,
    zone            varchar(32) NULL,
    position        varchar(32) NULL,
    description     varchar(32) NULL,
    height          numeric(4, 2) NULL,
    comments        text NOT NULL DEFAULT '',
    coordinates     point NULL,
    extra           json NOT NULL DEFAULT '{}'::json,
    UNIQUE (device_id, start_time, end_time)
);

/* Raw data */
DROP TABLE IF EXISTS airbods.public.raw;
CREATE TABLE IF NOT EXISTS airbods.public.raw (
    device_id         uuid NOT NULL,
    time_             varchar(32) NOT NULL,
    air_quality       varchar(32) NULL,
    co2               numeric(5, 1) NULL,
    humidity          numeric(5, 1) NULL,
    temperature       numeric(5, 1) NULL,
    lorawan_datarate  varchar(16) NULL,
    lorawan_rssi      numeric(5, 1) NULL,
    lorawan_snr       numeric(5, 1) NULL,
    battery           varchar(32) NULL,
    pm1               numeric(5, 1) NULL,
    pm25              numeric(5, 1) NULL,
    pm10              numeric(5, 1) NULL,
    -- Two-column unique restriction
    UNIQUE (device_id, time_)
);

/* Clean data */
DROP TABLE IF EXISTS airbods.public.clean;
CREATE TABLE IF NOT EXISTS airbods.public.clean (
    device_id       uuid NOT NULL,
    time_           timestamp with time zone NOT NULL,
    air_quality     varchar(32) NULL,
    co2             numeric(5, 1) NULL,
    humidity        numeric(5, 1) NULL,
    temperature     numeric(5, 1) NULL,
    -- Two-column unique restriction
    UNIQUE (device_id, time_)
);

/* Useful view */
DROP VIEW IF EXISTS airbods.public.clean_device;
CREATE OR REPLACE VIEW airbods.public.clean_device AS
    SELECT
         clean.device_id
        ,device.verbosename AS sensor_name
        ,device.serialnumber AS serial_number
        ,clean.time_
        ,clean.air_quality
        ,clean.co2
        ,clean.humidity
        ,clean.temperature
    FROM airbods.public.clean
    INNER JOIN airbods.public.device ON clean.device_id = device.device_id
    LEFT JOIN airbods.public.deployment
        ON device.device_id = deployment.device_id
        AND clean.time_ BETWEEN deployment.start_time AND deployment.end_time;
