-- 表exchange_info的创建sql
CREATE TABLE `exchange_info` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `exchange_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '交易所的名字',
  `exchange_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '交易所网站url',
  `state` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否有效，0:失效、1:有效',
  `insert_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_exchange_name` (`exchange_name`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC COMMENT='交易所信息';

-- 表exchange_info所需要的数据
INSERT INTO `exchange_info` (`exchange_name`, `exchange_url`)
VALUES
	('Binance', 'https://www.binance.com'),
	('Huobi Global', 'https://www.huobi.com'),
	('OKX', 'https://www.okx.com');


-- 表exchange_symbol_info的创建sql
CREATE TABLE `exchange_symbol_info` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `exchange_id` int NOT NULL COMMENT '交易所ID',
  `symbol_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '交易对名字',
  `symbol_type` int NOT NULL COMMENT '交易对类型，1: 现货、2: U本位、3:币本位',
  `price_change_24h` decimal(35,18) DEFAULT NULL COMMENT '24H的价格变化',
  `base_volume_24h` decimal(35,18) DEFAULT NULL COMMENT '24H的成交量',
  `state` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否有效',
  `insert_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `version` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '数据版本',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_key` (`exchange_id`,`symbol_name`,`symbol_type`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC COMMENT='交易对信息';


-- 表binance_symbol_kline_1day的创建sql
CREATE TABLE `binance_symbol_kline_1day` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `exchange_id` int NOT NULL COMMENT '交易所ID',
  `symbol_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '交易对名字',
  `symbol_type` int NOT NULL COMMENT '交易对类型，1: 现货、2: U本位、3:币本位',
  `open_timestamp` bigint NOT NULL DEFAULT '1' COMMENT 'K线开始时间',
  `close_timestamp` bigint NOT NULL COMMENT 'K线截止时间',
  `open` decimal(35,18) NOT NULL COMMENT '开盘价格',
  `high` decimal(35,18) NOT NULL COMMENT '最高价格',
  `low` decimal(35,18) NOT NULL COMMENT '最低价格',
  `close` decimal(35,18) DEFAULT NULL COMMENT '收盘价格',
  `base_volume` decimal(35,18) DEFAULT NULL COMMENT '成交量',
  `quote_volume` decimal(35,18) DEFAULT NULL COMMENT '成交额',
  `insert_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `version` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '数据版本',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_key` (`exchange_id`,`symbol_name`,`symbol_type`,`open_timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC COMMENT='BinanceK线数据';
