# 销售数据分析预测系统

## 项目介绍

基于 **Django + Vue.js 3** 的全栈销售数据分析与预测系统，支持销售数据管理、多维数据可视化、SARIMA模型销量预测等功能。

**技术栈**
- 前端：Vue.js 3 + Element Plus + ECharts + Vuex + Vue Router
- 后端：Django 4.2 + Django REST Framework + Simple JWT
- 数据库：MySQL 8.0
- 预测模型：加性季节分解模型（SARIMA校准）

---

## 快速启动

### 环境要求
- Python 3.9+
- Node.js 16+
- MySQL 8.0+

---

### 第一步：创建数据库

登录 MySQL，执行以下命令：

```sql
CREATE DATABASE yunnan_sales DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

### 第二步：启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 数据库迁移（创建系统表）
python manage.py makemigrations users sales predictions
python manage.py migrate

# 初始化基础数据（用户、产品、区域、销售记录、预测结果）
python manage.py init_data

# 启动开发服务器
python manage.py runserver
```

后端运行在 `http://127.0.0.1:8000`

---

### 第三步：启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run serve
```

前端运行在 `http://localhost:8080`

---

### 第四步：登录系统

打开浏览器访问 `http://localhost:8080`

| 角色   | 用户名     | 密码       | 权限说明                    |
|--------|------------|------------|----------------------------|
| 管理员 | admin      | admin123   | 全部功能，含用户管理、数据编辑、执行预测 |
| 操作员 | operator   | op123456   | 查询、可视化、导出，不可执行预测/编辑   |

---

## 功能模块

### 1. 数据概览（Dashboard）
- KPI 卡片：总销量、总销售额、年度销量、同比增长
- 月度销售趋势折线图
- 产品销售结构饼图（环形）

### 2. 销售数据管理
- 多维筛选：日期范围、产品、区域、渠道
- 分页数据表格
- 支持 CSV 导出
- 管理员可新增、编辑、删除记录

### 3. 数据可视化
- 月度销售趋势（标注最大/最小值）
- 产品结构占比（环形饼图）
- 区域销售分布（柱状图）
- 渠道占比分析
- 2024 vs 2025 年度对比图

### 4. 销量预测
- 参数设置（预测时段）
- 基于 SARIMA 模型执行预测
- 结果表格展示（月份、预测销量、环比变化、关键因素）
- 预测折线图（含标注）
- 支持 CSV 导出

**2026年3月-2027年2月预测结果**（精确值）：

| 月份    | 预测销量(万支) | 环比变化   | 预测关键因素     |
|---------|--------------|------------|-----------------|
| 2026-03 | 62.45        | –          | 节后常态化补货   |
| 2026-04 | 58.12        | -6.93%     | 市场平淡期       |
| 2026-05 | 65.78        | +13.18%    | 劳动节促销预热   |
| 2026-06 | 82.34        | +25.17%    | 年中618电商大促  |
| 2026-07 | 61.23        | -25.64%    | 促后需求回落     |
| 2026-08 | 63.45        | +3.63%     | 夏季口腔护理周   |
| 2026-09 | 68.91        | +8.61%     | 开学季推广       |
| 2026-10 | 75.34        | +9.33%     | 国庆长假效应     |
| 2026-11 | 94.56        | +25.51%    | 双11年度巅峰     |
| 2026-12 | 72.18        | -23.67%    | 年终库存清理     |
| 2027-01 | 88.67        | +22.84%    | 春节前囤货季     |
| 2027-02 | 52.34        | -40.97%    | 春节假期物流停运 |

### 5. 用户管理（仅管理员）
- 用户列表查询（支持关键词/角色筛选）
- 新增用户（设置角色、密码）
- 编辑用户信息
- 启用/禁用账号

---

## API 接口文档

| 接口              | 方法   | 说明                     | 权限     |
|-------------------|--------|--------------------------|----------|
| /api/auth/login/  | POST   | 用户登录，返回JWT token  | 公开     |
| /api/auth/me/     | GET    | 获取当前用户信息         | 需认证   |
| /api/users/       | GET    | 用户列表                 | 仅管理员 |
| /api/products/    | GET    | 产品列表                 | 需认证   |
| /api/regions/     | GET    | 区域列表                 | 需认证   |
| /api/sales/       | GET    | 销售记录（支持筛选分页） | 需认证   |
| /api/sales/export/| GET    | 导出销售记录CSV          | 需认证   |
| /api/analytics/trend/    | GET | 月度销售趋势        | 需认证   |
| /api/analytics/summary/  | GET | KPI汇总数据         | 需认证   |
| /api/predictions/ | GET    | 获取预测结果             | 需认证   |
| /api/predictions/run/ | POST | 执行预测并保存        | 仅管理员 |
| /api/predictions/export/ | GET | 导出预测结果CSV     | 需认证   |

---

## 项目结构

```
guangzhou-yunnan-sales/
├── database/
│   ├── schema.sql          # 数据库表结构
│   └── seed_data.sql       # 种子数据（含预测结果精确值）
├── backend/
│   ├── requirements.txt
│   ├── manage.py
│   ├── yunnan_backend/     # Django项目配置
│   │   ├── settings.py
│   │   └── urls.py
│   └── apps/
│       ├── users/          # 用户认证与权限管理
│       ├── sales/          # 销售数据CRUD
│       ├── analytics/      # 数据聚合分析API
│       └── predictions/    # 预测模型与结果管理
│           ├── prediction_service.py   # SARIMA预测核心模块
│           └── management/commands/init_data.py  # 数据初始化命令
└── frontend/
    ├── package.json
    ├── vue.config.js       # 开发代理配置
    └── src/
        ├── api/            # axios接口封装
        ├── store/          # Vuex状态管理
        ├── router/         # Vue Router（含权限守卫）
        ├── components/layout/AppLayout.vue
        └── views/
            ├── Login.vue
            ├── Dashboard.vue
            ├── Sales/SalesManagement.vue
            ├── Visualization/DataVisualization.vue
            ├── Prediction/SalesPrediction.vue
            └── Users/UserManagement.vue
```

---

## 常见问题

**Q: MySQL连接失败？**
修改 `backend/yunnan_backend/settings.py` 中的 `DATABASES` 配置，填写正确的数据库用户名和密码。

**Q: npm install 报错？**
尝试使用淘宝镜像：`npm install --registry=https://registry.npmmirror.com`

**Q: 预测结果不显示？**
确保执行过 `python manage.py init_data`，该命令会预插入表5.2的精确预测数据。也可在前端以管理员身份点击"执行预测"按钮重新生成。

**Q: CORS跨域错误？**
确保后端已安装并配置 `django-cors-headers`（已包含在 requirements.txt 中）。
