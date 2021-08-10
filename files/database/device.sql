/* Sensor devices */
-- DROP TABLE IF EXISTS airbods.public.device CASCADE;
CREATE TABLE IF NOT EXISTS airbods.public.device
(
    device_id     uuid         NOT NULL PRIMARY KEY,
    serial_number varchar(128) NOT NULL UNIQUE,
    verbose_name  varchar(128) NOT NULL UNIQUE,
    object        json         NOT NULL
);
