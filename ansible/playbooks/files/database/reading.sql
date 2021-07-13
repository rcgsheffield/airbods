/* Useful views */
-- DROP VIEW airbods.public.reading;
CREATE OR REPLACE VIEW airbods.public.reading AS
SELECT clean.device_id
     , device.serial_number                                       AS serial_number
     , device.verbose_name                                        AS sensor_name
     , clean.time_                                                AS time_utc
     , clean.time_ AT time zone 'Europe/London'                   AS time_europe_london
     , deployment.city
     , deployment.site
     , deployment.area
     , deployment.room
     , deployment.floor
     , deployment.zone
     , deployment.height
     , deployment.description
     , deployment.comments
     , deployment.person
     -- Metrics
     , clean.air_quality
     , clean.co2
     , clean.co2 - COALESCE(deployment.co2_baseline, 0)           AS co2_excess
     , clean.humidity
     , clean.temperature
     -- Room averages
     , MIN(clean.co2) OVER (PARTITION BY deployment.room)         AS co2_room_min
     , MIN(clean.humidity) OVER (PARTITION BY deployment.room)    AS humidity_room_min
     , MIN(clean.temperature) OVER (PARTITION BY deployment.room) AS temperature_room_min
     , AVG(clean.co2) OVER (PARTITION BY deployment.room)         AS co2_room_mean
     , AVG(clean.humidity) OVER (PARTITION BY deployment.room)    AS humidity_room_mean
     , AVG(clean.temperature) OVER (PARTITION BY deployment.room) AS temperature_room_mean
     , MAX(clean.co2) OVER (PARTITION BY deployment.room)         AS co2_room_max
     , MAX(clean.humidity) OVER (PARTITION BY deployment.room)    AS humidity_room_max
     , MAX(clean.temperature) OVER (PARTITION BY deployment.room) AS temperature_room_max
     -- Area averages
     , MIN(clean.co2) OVER (PARTITION BY deployment.area)         AS co2_area_min
     , MIN(clean.humidity) OVER (PARTITION BY deployment.area)    AS humidity_area_min
     , MIN(clean.temperature) OVER (PARTITION BY deployment.area) AS temperature_area_min
     , AVG(clean.co2) OVER (PARTITION BY deployment.area)         AS co2_area_mean
     , AVG(clean.humidity) OVER (PARTITION BY deployment.area)    AS humidity_area_mean
     , AVG(clean.temperature) OVER (PARTITION BY deployment.area) AS temperature_area_mean
     , MAX(clean.co2) OVER (PARTITION BY deployment.area)         AS co2_area_max
     , MAX(clean.humidity) OVER (PARTITION BY deployment.area)    AS humidity_area_max
     , MAX(clean.temperature) OVER (PARTITION BY deployment.area) AS temperature_area_max
FROM airbods.public.clean
         INNER JOIN airbods.public.device ON clean.device_id = device.device_id
         LEFT JOIN airbods.public.deployment
                   ON device.serial_number = deployment.serial_number
                       AND clean.time_ BETWEEN deployment.start_time AND COALESCE(deployment.end_time, NOW());
