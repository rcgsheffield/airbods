/* Clean data */
-- DROP TABLE IF EXISTS airbods.public.clean CASCADE;
CREATE TABLE IF NOT EXISTS airbods.public.clean
(
    device_id   uuid                     NOT NULL,
    time_       timestamp with time zone NOT NULL,
    air_quality varchar(128)             NULL,
    co2         double precision         NULL,
    humidity    double precision         NULL,
    temperature double precision         NULL,
    -- Two-column unique restriction
    -- Allow this constraint to be deferred within a multi-statement transaction
    -- so that chunks of data can be replaced easily
    -- https://dba.stackexchange.com/a/105092
    UNIQUE (device_id, time_) DEFERRABLE INITIALLY IMMEDIATE
);
