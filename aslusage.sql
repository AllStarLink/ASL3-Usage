-- MariaDB dump 10.19  Distrib 10.11.6-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: aslusage
-- ------------------------------------------------------
-- Server version	10.11.6-MariaDB-0+deb12u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `nodes`
--

DROP TABLE IF EXISTS `nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nodes` (
  `uuid` char(36) NOT NULL,
  `astversion` varchar(50) NOT NULL,
  `aslversion` varchar(50) NOT NULL,
  `aslpkgver` varchar(50) NOT NULL,
  `node` int(11) NOT NULL,
  `uptime` int(11) NOT NULL,
  `reloadtime` int(11) NOT NULL,
  `channeltype` varchar(50) NOT NULL,
  `os` varchar(50) NOT NULL,
  `distro` varchar(50) NOT NULL,
  `relver` varchar(50) NOT NULL,
  `kernel` varchar(50) NOT NULL,
  `arch` varchar(50) NOT NULL,
  `pkglist` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`pkglist`)),
  `repdate` datetime NOT NULL DEFAULT current_timestamp(),
  `fullastver` varchar(100) NOT NULL,
  PRIMARY KEY (`node`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Ensure the Event Scheduler is enabled
SET GLOBAL event_scheduler = ON;

DROP TABLE IF EXISTS asl_usage;
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
  radio_count INT NOT NULL default 0,
  collected_time DATETIME NOT NULL
);

-- Create the daily event
CREATE EVENT daily_usage
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_DATE + INTERVAL 1 DAY
DO
  INSERT INTO asl_usage (record_count, server_count, ast_count, asl_count, node_count, dahdi_count, simpleusb_count, usbradio_count, voter_count, radio_count, collected_time)
  SELECT COUNT(*),
  COUNT(DISTINCT uuid),
  COUNT(DISTINCT astversion),
  COUNT(DISTINCT aslversion),
  COUNT(DISTINCT node),
  SUM(CASE WHEN TRIM(channeltype) = 'dahdi' THEN 1 ELSE 0 END),
  SUM(CASE WHEN TRIM(channeltype) = 'simpleusb' THEN 1 ELSE 0 END),
  SUM(CASE WHEN TRIM(channeltype) = 'usbradio' THEN 1 ELSE 0 END),
  SUM(CASE WHEN TRIM(channeltype) = 'voter' THEN 1 ELSE 0 END),
  SUM(CASE WHEN TRIM(channeltype) = 'radio' THEN 1 ELSE 0 END),
  NOW()
  FROM nodes;
