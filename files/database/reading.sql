/* Useful views */
DROP VIEW airbods.public.reading;
CREATE OR REPLACE VIEW airbods.public.reading AS
SELECT
     -- Dimensions
    clean.device_id
     , device.serial_number
     , device.verbose_name
     , clean.time_                                                                   AS time_utc
     , clean.time_ AT time zone 'Europe/London'                                      AS time_europe_london
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
     , clean.co2 - COALESCE(deployment.co2_baseline, 0)                              AS co2_excess
     , clean.humidity
     , clean.temperature

     -- Aggregated statistics
     -- Area daily averages
     , MIN(clean.co2) OVER (PARTITION BY deployment.area, clean.time_::DATE)         AS co2_area_min
     , MIN(clean.humidity) OVER (PARTITION BY deployment.area, clean.time_::DATE)    AS humidity_area_min
     , MIN(clean.temperature) OVER (PARTITION BY deployment.area, clean.time_::DATE) AS temperature_area_min
     , AVG(clean.co2) OVER (PARTITION BY deployment.area, clean.time_::DATE)         AS co2_area_mean
     , AVG(clean.humidity) OVER (PARTITION BY deployment.area, clean.time_::DATE)    AS humidity_area_mean
     , AVG(clean.temperature) OVER (PARTITION BY deployment.area, clean.time_::DATE) AS temperature_area_mean
     , MAX(clean.co2) OVER (PARTITION BY deployment.area, clean.time_::DATE)         AS co2_area_max
     , MAX(clean.humidity) OVER (PARTITION BY deployment.area, clean.time_::DATE)    AS humidity_area_max
     , MAX(clean.temperature) OVER (PARTITION BY deployment.area, clean.time_::DATE) AS temperature_area_max

     -- Zone daily averages
     , MIN(clean.co2) OVER (PARTITION BY deployment.zone, clean.time_::DATE)         AS co2_zone_min
     , MIN(clean.humidity) OVER (PARTITION BY deployment.zone, clean.time_::DATE)    AS humidity_zone_min
     , MIN(clean.temperature) OVER (PARTITION BY deployment.zone, clean.time_::DATE) AS temperature_zone_min
     , AVG(clean.co2) OVER (PARTITION BY deployment.zone, clean.time_::DATE)         AS co2_zone_mean
     , AVG(clean.humidity) OVER (PARTITION BY deployment.zone, clean.time_::DATE)    AS humidity_zone_mean
     , AVG(clean.temperature) OVER (PARTITION BY deployment.zone, clean.time_::DATE) AS temperature_zone_mean
     , MAX(clean.co2) OVER (PARTITION BY deployment.zone, clean.time_::DATE)         AS co2_zone_max
     , MAX(clean.humidity) OVER (PARTITION BY deployment.zone, clean.time_::DATE)    AS humidity_zone_max
     , MAX(clean.temperature) OVER (PARTITION BY deployment.zone, clean.time_::DATE) AS temperature_zone_max

     -- CO2 rolling average over last "10 minutes" per zone
     , AVG(clean.co2) OVER (PARTITION BY deployment.zone ORDER BY clean.time_
    ROWS BETWEEN 5 PRECEDING AND CURRENT ROW)                                        AS co2_mean_rolling_5_rows
     -- CO2 rolling hourly minimum and maximum per zone
    ,MIN(clean.co2) OVER (PARTITION BY deployment.zone ORDER BY clean.time_
        ROWS BETWEEN 30 PRECEDING AND CURRENT ROW)                                        AS co2_min_rolling_30_rows
    ,MAX(clean.co2) OVER (PARTITION BY deployment.zone ORDER BY clean.time_
        ROWS BETWEEN 30 PRECEDING AND CURRENT ROW)                                        AS co2_max_rolling_30_rows
FROM airbods.public.clean
         -- If no sensor is found, leave blank columns
         LEFT JOIN airbods.public.device ON clean.device_id = device.device_id
         LEFT JOIN airbods.public.deployment
                   ON device.serial_number = deployment.serial_number
                       -- Get the deployment at the time when the measurement was taken
                       AND clean.time_ BETWEEN deployment.start_time AND COALESCE(deployment.end_time, NOW())
ORDER BY clean.time_
;
