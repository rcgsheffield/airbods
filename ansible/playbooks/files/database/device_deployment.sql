-- Show current device deployments
-- DROP VIEW airbods.public.device_deployment;
CREATE OR REPLACE VIEW airbods.public.device_deployment AS
-- Get all device and deployment info
WITH device_deployment_ AS (
    SELECT device.device_id
         , device.serial_number
         , device.verbose_name
         , deployment.start_time
         , deployment.end_time
         , deployment.city
         , deployment.site
         , deployment.area
         , deployment.zone
         , deployment.person
         , deployment.description
         , deployment.floor
         , deployment.room
         , deployment.height
         , deployment.comments
         -- Order by deployment date
         , ROW_NUMBER() OVER (PARTITION BY device.device_id
        ORDER BY airbods.public.deployment.start_time DESC) AS latest_
    FROM airbods.public.device
             LEFT JOIN airbods.public.deployment ON device.serial_number = deployment.serial_number
)
-- Select latest deployment only
SELECT *
FROM device_deployment_
WHERE latest_ = 1;
