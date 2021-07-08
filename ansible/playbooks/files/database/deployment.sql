/* Deployments (sensor position during time period) */
-- DROP TABLE IF EXISTS airbods.public.deployment CASCADE ;
CREATE TABLE IF NOT EXISTS airbods.public.deployment
(
    serial_number varchar(128)             NOT NULL,
    start_time    timestamp with time zone NOT NULL,
    -- end_time = NULL means that the deployment remains active
    end_time      timestamp with time zone NULL,
    verbose_name  varchar(128)             NULL,
    city          varchar(128)             NULL,
    site          varchar(128)             NULL,
    area          varchar(128)             NULL,
    floor         varchar(128)             NULL,
    room          varchar(128)             NULL,
    zone          varchar(128)             NULL,
    description   varchar(256)             NULL,
    height        numeric(4, 2)            NULL,
    comments      text                     NULL,
    person        varchar(128)             NULL,
    co2_baseline  numeric(9, 4)            NULL DEFAULT 0,
    UNIQUE (serial_number, start_time)
);
