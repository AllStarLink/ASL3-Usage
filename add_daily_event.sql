-- daily_usage_setup.sql

-- Ensure the Event Scheduler is enabled
SET GLOBAL event_scheduler = ON;

-- DROP TABLE IF EXISTS asl_usage;
DROP EVENT IF EXISTS daily_usage;

-- Create the asl_usage table if it doesn't exist
CREATE TABLE IF NOT EXISTS asl_usage (
  id INT AUTO_INCREMENT PRIMARY KEY,
  record_count INT NOT NULL,
  server_count INT NOT NULL,
  ast_count INT NOT NULL,
  asl_count INT NOT NULL,
  node_count INT NOT NULL,
  dahdi_count INT NOT NULL default 0,
  simpleusb_count INT NOT NULL default 0,
  usbradio_count INT NOT NULL default 0,
  voter_count INT NOT NULL default 0,
  collected_time DATETIME NOT NULL
);

-- Create the daily event
CREATE EVENT daily_usage
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_DATE + INTERVAL 1 DAY
DO
  INSERT INTO asl_usage (record_count, server_count, ast_count, asl_count, node_count, dahdi_count, simpleusb_count, usbradio_count, voter_count, collected_time)
  SELECT COUNT(*),
  COUNT(DISTINCT uuid),
  COUNT(DISTINCT astversion),
  COUNT(DISTINCT aslversion),
  COUNT(DISTINCT node),
  SUM(CASE WHEN TRIM(channeltype) = 'dahdi' THEN 1 ELSE 0 END),
  SUM(CASE WHEN TRIM(channeltype) = 'simpleusb' THEN 1 ELSE 0 END),
  SUM(CASE WHEN TRIM(channeltype) = 'radio' THEN 1 ELSE 0 END),
  SUM(CASE WHEN TRIM(channeltype) = 'voter' THEN 1 ELSE 0 END),
  NOW()
  FROM nodes;