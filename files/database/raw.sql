/* Raw data */
-- DROP TABLE IF EXISTS airbods.public.raw;
CREATE TABLE IF NOT EXISTS airbods.public.raw
(
    device_id        uuid             NOT NULL,
    time_            varchar(128)     NOT NULL,
    air_quality      varchar(128)     NULL,
    co2              double precision NULL,
    humidity         double precision NULL,
    temperature      double precision NULL,
    lorawan_datarate varchar(16)      NULL,
    lorawan_rssi     double precision NULL,
    lorawan_snr      double precision NULL,
    battery          varchar(128)     NULL,
    pm1              double precision NULL,
    pm25             double precision NULL,
    pm10             double precision NULL,
    -- Two-column unique restriction
    UNIQUE (device_id, time_)
);
