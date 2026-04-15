-- 销售数据分析预测系统 - 数据库结构
-- MySQL 8.0+
-- ======================================================================
-- 使用说明（二选一）：
--
-- 【方式一 - 推荐】使用 Django 自动建表（含 Django 系统表）：
--   mysql -u root -p -e "CREATE DATABASE yunnan_sales DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
--   cd backend
--   python manage.py makemigrations users sales predictions
--   python manage.py migrate
--   python manage.py init_data
--
-- 【方式二】手动导入 SQL（仅建业务表，Django 系统表需单独 migrate）：
--   1. 先在 MySQL 中执行本文件（schema.sql）建表
--   2. 再执行 seed_data.sql 导入数据（不含用户，用户需 Django 命令创建）
--   3. 再运行 python manage.py migrate --run-syncdb 同步 Django 系统表
--   4. 再运行 python manage.py init_data 创建用户
-- ======================================================================

CREATE DATABASE IF NOT EXISTS yunnan_sales
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE yunnan_sales;

-- =====================================================================
-- Django 所需最小系统表（migrate 会自动创建，此处备用）
-- =====================================================================

-- 内容类型表（权限系统依赖）
CREATE TABLE IF NOT EXISTS django_content_type (
    id       INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model    VARCHAR(100) NOT NULL,
    UNIQUE KEY django_content_type_app_label_model (app_label, model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 权限表
CREATE TABLE IF NOT EXISTS auth_permission (
    id              INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    content_type_id INT NOT NULL,
    codename        VARCHAR(100) NOT NULL,
    UNIQUE KEY auth_permission_content_type_id_codename (content_type_id, codename),
    CONSTRAINT auth_permission_content_type_id_fk
        FOREIGN KEY (content_type_id) REFERENCES django_content_type (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户组表
CREATE TABLE IF NOT EXISTS auth_group (
    id   INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 组权限关联表
CREATE TABLE IF NOT EXISTS auth_group_permissions (
    id            BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    group_id      INT NOT NULL,
    permission_id INT NOT NULL,
    UNIQUE KEY auth_group_permissions_group_id_permission_id (group_id, permission_id),
    CONSTRAINT auth_group_permissions_group_id_fk
        FOREIGN KEY (group_id) REFERENCES auth_group (id),
    CONSTRAINT auth_group_permissions_permission_id_fk
        FOREIGN KEY (permission_id) REFERENCES auth_permission (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Django 迁移记录表
CREATE TABLE IF NOT EXISTS django_migrations (
    id      BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    app     VARCHAR(255) NOT NULL,
    name    VARCHAR(255) NOT NULL,
    applied DATETIME(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Django session 表
CREATE TABLE IF NOT EXISTS django_session (
    session_key  VARCHAR(40)  NOT NULL PRIMARY KEY,
    session_data LONGTEXT     NOT NULL,
    expire_date  DATETIME(6)  NOT NULL,
    INDEX django_session_expire_date (expire_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Django admin 日志表
CREATE TABLE IF NOT EXISTS django_admin_log (
    id              INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    action_time     DATETIME(6) NOT NULL,
    object_id       LONGTEXT,
    object_repr     VARCHAR(200) NOT NULL,
    action_flag     SMALLINT UNSIGNED NOT NULL,
    change_message  LONGTEXT NOT NULL,
    content_type_id INT,
    user_id         BIGINT NOT NULL,
    CONSTRAINT django_admin_log_content_type_id_fk
        FOREIGN KEY (content_type_id) REFERENCES django_content_type (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 用户表（CustomUser，继承 AbstractBaseUser + PermissionsMixin）
-- =====================================================================
CREATE TABLE IF NOT EXISTS users_customuser (
    id           BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    password     VARCHAR(128) NOT NULL,
    last_login   DATETIME(6)  NULL,
    username     VARCHAR(150) NOT NULL UNIQUE,
    full_name    VARCHAR(50)  NOT NULL DEFAULT '',
    email        VARCHAR(254) NOT NULL DEFAULT '',
    role         VARCHAR(20)  NOT NULL DEFAULT 'operator' COMMENT 'admin/operator',
    is_active    TINYINT(1)   NOT NULL DEFAULT 1,
    is_staff     TINYINT(1)   NOT NULL DEFAULT 0,
    is_superuser TINYINT(1)   NOT NULL DEFAULT 0,
    date_joined  DATETIME(6)  NOT NULL,
    created_at   DATETIME(6)  NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户-组关联表
CREATE TABLE IF NOT EXISTS users_customuser_groups (
    id             BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    customuser_id  BIGINT NOT NULL,
    group_id       INT    NOT NULL,
    UNIQUE KEY users_customuser_groups_customuser_id_group_id (customuser_id, group_id),
    CONSTRAINT users_customuser_groups_customuser_id_fk
        FOREIGN KEY (customuser_id) REFERENCES users_customuser (id),
    CONSTRAINT users_customuser_groups_group_id_fk
        FOREIGN KEY (group_id) REFERENCES auth_group (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户-权限关联表
CREATE TABLE IF NOT EXISTS users_customuser_user_permissions (
    id             BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    customuser_id  BIGINT NOT NULL,
    permission_id  INT    NOT NULL,
    UNIQUE KEY users_customuser_user_permissions_customuser_id_permission_id (customuser_id, permission_id),
    CONSTRAINT users_customuser_user_permissions_customuser_id_fk
        FOREIGN KEY (customuser_id) REFERENCES users_customuser (id),
    CONSTRAINT users_customuser_user_permissions_permission_id_fk
        FOREIGN KEY (permission_id) REFERENCES auth_permission (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Django admin 日志表补充外键（users_customuser 创建后才能添加）
ALTER TABLE django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_fk
    FOREIGN KEY (user_id) REFERENCES users_customuser (id);

-- =====================================================================
-- 产品表
-- =====================================================================
CREATE TABLE IF NOT EXISTS sales_product (
    id          BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(50)  NOT NULL DEFAULT '',
    spec        VARCHAR(50)  NOT NULL DEFAULT '' COMMENT '规格',
    unit_price  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    description TEXT         NOT NULL DEFAULT '',
    is_active   TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME(6)  NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 区域表
-- =====================================================================
CREATE TABLE IF NOT EXISTS sales_region (
    id        BIGINT      NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(50) NOT NULL,
    district  VARCHAR(50) NOT NULL DEFAULT '',
    city      VARCHAR(50) NOT NULL DEFAULT '广州',
    is_active TINYINT(1)  NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 销售记录表
-- =====================================================================
CREATE TABLE IF NOT EXISTS sales_salesrecord (
    id           BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    sale_date    DATE         NOT NULL,
    product_id   BIGINT       NOT NULL,
    region_id    BIGINT       NOT NULL,
    quantity     INT          NOT NULL DEFAULT 0    COMMENT '销售数量（支）',
    unit_price   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    channel      VARCHAR(20)  NOT NULL DEFAULT 'offline' COMMENT 'online/offline/distributor',
    operator_id  BIGINT       NULL,
    remark       VARCHAR(200) NOT NULL DEFAULT '',
    created_at   DATETIME(6)  NOT NULL,
    CONSTRAINT sales_salesrecord_product_id_fk
        FOREIGN KEY (product_id) REFERENCES sales_product (id),
    CONSTRAINT sales_salesrecord_region_id_fk
        FOREIGN KEY (region_id) REFERENCES sales_region (id),
    CONSTRAINT sales_salesrecord_operator_id_fk
        FOREIGN KEY (operator_id) REFERENCES users_customuser (id)
            ON DELETE SET NULL,
    INDEX idx_sale_date (sale_date),
    INDEX idx_product   (product_id),
    INDEX idx_region    (region_id),
    INDEX idx_channel   (channel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 预测结果表
-- =====================================================================
CREATE TABLE IF NOT EXISTS predictions_predictionresult (
    id                 BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    month              VARCHAR(7)   NOT NULL COMMENT 'YYYY-MM格式',
    predicted_quantity DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '预测销量（万支）',
    mom_change_pct     DECIMAL(8,2)  NULL               COMMENT '环比变化百分比',
    key_factors        VARCHAR(200) NOT NULL DEFAULT '' COMMENT '预测关键因素',
    model_type         VARCHAR(50)  NOT NULL DEFAULT 'SARIMA',
    created_at         DATETIME(6)  NOT NULL,
    UNIQUE KEY unique_month (month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 预测参数表
-- =====================================================================
CREATE TABLE IF NOT EXISTS predictions_predictionparam (
    id          BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    param_name  VARCHAR(50)   NOT NULL UNIQUE,
    param_value DECIMAL(15,6) NOT NULL,
    description VARCHAR(200)  NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
