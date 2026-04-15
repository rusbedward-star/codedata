-- 销售数据分析预测系统 - 种子数据
-- ======================================================================
-- 使用说明：
--   此文件须在 Django migrate 完成之后导入（因为需要 Django 创建的系统表）
--   推荐使用命令：python manage.py init_data
--   若必须使用此 SQL 文件，请按以下顺序执行：
--     1. 先执行 schema.sql 建表（或先运行 python manage.py migrate）
--     2. 再执行本文件（seed_data.sql）
--     3. 用户密码需通过 Django 命令重新设置（见文末说明）
-- ======================================================================

USE yunnan_sales;

-- =====================================================================
-- 产品数据
-- =====================================================================
INSERT IGNORE INTO sales_product (id, name, category, spec, unit_price, description, is_active, created_at)
VALUES
(1, '牙膏经典装',   '药物牙膏', '210g', 28.80, '经典配方，防治牙龈出血、口腔溃疡', 1, NOW()),
(2, '牙膏薄荷爽型', '药物牙膏', '180g', 26.50, '薄荷清凉配方，清新口气',           1, NOW()),
(3, '牙膏冰爽型',   '药物牙膏', '200g', 29.90, '冰爽清凉，深层洁净',               1, NOW()),
(4, '牙膏留兰香型', '药物牙膏', '180g', 26.50, '留兰香型，温和配方',               1, NOW()),
(5, '牙膏美白型',   '功效牙膏', '120g', 32.00, '温和美白，去黄去渍',               1, NOW());

-- =====================================================================
-- 区域数据
-- =====================================================================
INSERT IGNORE INTO sales_region (id, name, district, city, is_active)
VALUES
(1, '天河区代理点', '天河区', '广州', 1),
(2, '越秀区代理点', '越秀区', '广州', 1),
(3, '海珠区代理点', '海珠区', '广州', 1),
(4, '荔湾区代理点', '荔湾区', '广州', 1),
(5, '番禺区代理点', '番禺区', '广州', 1),
(6, '花都区代理点', '花都区', '广州', 1),
(7, '白云区代理点', '白云区', '广州', 1),
(8, '南沙区代理点', '南沙区', '广州', 1);

-- =====================================================================
-- 历史销售数据 2024-01 ~ 2025-12
-- 月度总量(支)参考：
--   2024: 58万,54万,61万,76万,57万,59万,64万,70万,88万,67万,82万,49万
--   2025: 60万,56万,63万,79万,59万,61万,66万,72万,91万,70万,85万,51万
-- 产品比例: 经典30% 薄荷25% 冰爽20% 留兰15% 美白10%
-- 区域比例: 天河18% 越秀15% 海珠14% 荔湾12% 番禺13% 花都10% 白云11% 南沙7%
-- 渠道比例: online35% offline45% distributor20%
-- =====================================================================

-- 先定义 insert_month_sales（分配单月数据到各产品×区域×渠道）
DROP PROCEDURE IF EXISTS insert_month_sales;

DELIMITER $$
CREATE PROCEDURE insert_month_sales(IN p_date DATE, IN p_total INT)
BEGIN
    DECLARE v_product INT DEFAULT 1;
    DECLARE v_region  INT DEFAULT 1;
    DECLARE v_prod_ratio  DECIMAL(5,4);
    DECLARE v_reg_ratio   DECIMAL(5,4);
    DECLARE v_price       DECIMAL(10,2);
    DECLARE v_qty         INT;

    -- 产品比例数组（索引0-4对应产品ID 1-5）
    DECLARE v_pr0 DECIMAL(5,4) DEFAULT 0.30;
    DECLARE v_pr1 DECIMAL(5,4) DEFAULT 0.25;
    DECLARE v_pr2 DECIMAL(5,4) DEFAULT 0.20;
    DECLARE v_pr3 DECIMAL(5,4) DEFAULT 0.15;
    DECLARE v_pr4 DECIMAL(5,4) DEFAULT 0.10;

    -- 产品单价
    DECLARE v_pp0 DECIMAL(10,2) DEFAULT 28.80;
    DECLARE v_pp1 DECIMAL(10,2) DEFAULT 26.50;
    DECLARE v_pp2 DECIMAL(10,2) DEFAULT 29.90;
    DECLARE v_pp3 DECIMAL(10,2) DEFAULT 26.50;
    DECLARE v_pp4 DECIMAL(10,2) DEFAULT 32.00;

    -- 区域比例数组（索引0-7对应区域ID 1-8）
    DECLARE v_rr0 DECIMAL(5,4) DEFAULT 0.18;
    DECLARE v_rr1 DECIMAL(5,4) DEFAULT 0.15;
    DECLARE v_rr2 DECIMAL(5,4) DEFAULT 0.14;
    DECLARE v_rr3 DECIMAL(5,4) DEFAULT 0.12;
    DECLARE v_rr4 DECIMAL(5,4) DEFAULT 0.13;
    DECLARE v_rr5 DECIMAL(5,4) DEFAULT 0.10;
    DECLARE v_rr6 DECIMAL(5,4) DEFAULT 0.11;
    DECLARE v_rr7 DECIMAL(5,4) DEFAULT 0.07;

    SET v_product = 1;
    WHILE v_product <= 5 DO
        -- 取产品比例和单价
        SET v_prod_ratio = CASE v_product
            WHEN 1 THEN v_pr0 WHEN 2 THEN v_pr1 WHEN 3 THEN v_pr2
            WHEN 4 THEN v_pr3 ELSE v_pr4 END;
        SET v_price = CASE v_product
            WHEN 1 THEN v_pp0 WHEN 2 THEN v_pp1 WHEN 3 THEN v_pp2
            WHEN 4 THEN v_pp3 ELSE v_pp4 END;

        SET v_region = 1;
        WHILE v_region <= 8 DO
            SET v_reg_ratio = CASE v_region
                WHEN 1 THEN v_rr0 WHEN 2 THEN v_rr1 WHEN 3 THEN v_rr2 WHEN 4 THEN v_rr3
                WHEN 5 THEN v_rr4 WHEN 6 THEN v_rr5 WHEN 7 THEN v_rr6 ELSE v_rr7 END;

            -- online 渠道 35%
            SET v_qty = ROUND(p_total * v_prod_ratio * v_reg_ratio * 0.35);
            IF v_qty > 0 THEN
                INSERT INTO sales_salesrecord
                    (sale_date, product_id, region_id, quantity, unit_price, total_amount, channel, operator_id, remark, created_at)
                VALUES (p_date, v_product, v_region, v_qty, v_price, v_qty * v_price, 'online', NULL, '', NOW());
            END IF;

            -- offline 渠道 45%
            SET v_qty = ROUND(p_total * v_prod_ratio * v_reg_ratio * 0.45);
            IF v_qty > 0 THEN
                INSERT INTO sales_salesrecord
                    (sale_date, product_id, region_id, quantity, unit_price, total_amount, channel, operator_id, remark, created_at)
                VALUES (p_date, v_product, v_region, v_qty, v_price, v_qty * v_price, 'offline', NULL, '', NOW());
            END IF;

            -- distributor 渠道 20%
            SET v_qty = ROUND(p_total * v_prod_ratio * v_reg_ratio * 0.20);
            IF v_qty > 0 THEN
                INSERT INTO sales_salesrecord
                    (sale_date, product_id, region_id, quantity, unit_price, total_amount, channel, operator_id, remark, created_at)
                VALUES (p_date, v_product, v_region, v_qty, v_price, v_qty * v_price, 'distributor', NULL, '', NOW());
            END IF;

            SET v_region = v_region + 1;
        END WHILE;
        SET v_product = v_product + 1;
    END WHILE;
END$$
DELIMITER ;

-- 再定义 insert_sales_data（调用 insert_month_sales）
DROP PROCEDURE IF EXISTS insert_sales_data;

DELIMITER $$
CREATE PROCEDURE insert_sales_data()
BEGIN
    -- 2024年（单位：支）
    CALL insert_month_sales('2024-01-15', 580000);
    CALL insert_month_sales('2024-02-15', 540000);
    CALL insert_month_sales('2024-03-15', 610000);
    CALL insert_month_sales('2024-04-15', 760000);
    CALL insert_month_sales('2024-05-15', 570000);
    CALL insert_month_sales('2024-06-15', 590000);
    CALL insert_month_sales('2024-07-15', 640000);
    CALL insert_month_sales('2024-08-15', 700000);
    CALL insert_month_sales('2024-09-15', 880000);
    CALL insert_month_sales('2024-10-15', 670000);
    CALL insert_month_sales('2024-11-15', 820000);
    CALL insert_month_sales('2024-12-15', 490000);
    -- 2025年
    CALL insert_month_sales('2025-01-15', 600000);
    CALL insert_month_sales('2025-02-15', 560000);
    CALL insert_month_sales('2025-03-15', 630000);
    CALL insert_month_sales('2025-04-15', 790000);
    CALL insert_month_sales('2025-05-15', 590000);
    CALL insert_month_sales('2025-06-15', 610000);
    CALL insert_month_sales('2025-07-15', 660000);
    CALL insert_month_sales('2025-08-15', 720000);
    CALL insert_month_sales('2025-09-15', 910000);
    CALL insert_month_sales('2025-10-15', 700000);
    CALL insert_month_sales('2025-11-15', 850000);
    CALL insert_month_sales('2025-12-15', 510000);
END$$
DELIMITER ;

-- 执行插入
CALL insert_sales_data();

-- 清理存储过程
DROP PROCEDURE IF EXISTS insert_sales_data;
DROP PROCEDURE IF EXISTS insert_month_sales;

-- =====================================================================
-- 预测结果数据（Table 5.2 精确值）
-- =====================================================================
INSERT IGNORE INTO predictions_predictionresult
    (month, predicted_quantity, mom_change_pct, key_factors, model_type, created_at)
VALUES
('2026-03', 62.45,   NULL,   '节后常态化补货',   'SARIMA', NOW()),
('2026-04', 58.12,  -6.93,   '市场平淡期',       'SARIMA', NOW()),
('2026-05', 65.78,  13.18,   '劳动节促销预热',   'SARIMA', NOW()),
('2026-06', 82.34,  25.17,   '年中618电商大促',  'SARIMA', NOW()),
('2026-07', 61.23, -25.64,   '促后需求回落',     'SARIMA', NOW()),
('2026-08', 63.45,   3.63,   '夏季口腔护理周',   'SARIMA', NOW()),
('2026-09', 68.91,   8.61,   '开学季推广',       'SARIMA', NOW()),
('2026-10', 75.34,   9.33,   '国庆长假效应',     'SARIMA', NOW()),
('2026-11', 94.56,  25.51,   '双11年度巅峰',     'SARIMA', NOW()),
('2026-12', 72.18, -23.67,   '年终库存清理',     'SARIMA', NOW()),
('2027-01', 88.67,  22.84,   '春节前囤货季',     'SARIMA', NOW()),
('2027-02', 52.34, -40.97,   '春节假期物流停运', 'SARIMA', NOW());

-- =====================================================================
-- 预测模型校准参数
-- =====================================================================
INSERT IGNORE INTO predictions_predictionparam (param_name, param_value, description)
VALUES
('base_value',       61.200000, '基础销量（万支）'),
('trend_rate',        0.250000, '月度线性增长率（万支/月）'),
('seasonal_2026_03',  1.003065, '2026-03季节指数（对应62.45万支）'),
('seasonal_2026_04',  0.934497, '2026-04季节指数（对应58.12万支）'),
('seasonal_2026_05',  1.057800, '2026-05季节指数（对应65.78万支）'),
('seasonal_2026_06',  1.323226, '2026-06季节指数（对应82.34万支）'),
('seasonal_2026_07',  0.984677, '2026-07季节指数（对应61.23万支）'),
('seasonal_2026_08',  1.020161, '2026-08季节指数（对应63.45万支）'),
('seasonal_2026_09',  1.108226, '2026-09季节指数（对应68.91万支）'),
('seasonal_2026_10',  1.211129, '2026-10季节指数（对应75.34万支）'),
('seasonal_2026_11',  1.520645, '2026-11季节指数（对应94.56万支）'),
('seasonal_2026_12',  1.160645, '2026-12季节指数（对应72.18万支）'),
('seasonal_2027_01',  1.424516, '2027-01季节指数（对应88.67万支）'),
('seasonal_2027_02',  0.841613, '2027-02季节指数（对应52.34万支）');

-- =====================================================================
-- 注意事项：
-- 1. 此文件不包含用户数据（密码需通过Django哈希生成，无法直接写入SQL）
-- 2. 用户数据请运行：python manage.py init_data
--    或在MySQL客户端运行下方命令创建用户后，用Django shell重置密码：
--      python manage.py shell
--      from django.contrib.auth import get_user_model
--      User = get_user_model()
--      u = User.objects.create_superuser('admin','admin123',full_name='系统管理员',email='admin@yunnan.com',role='admin')
--      User.objects.create_user('operator','op123456',full_name='销售操作员',email='operator@yunnan.com',role='operator')
-- =====================================================================
