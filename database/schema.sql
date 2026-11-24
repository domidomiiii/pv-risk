-- PV-Risk SQLite 数据库结构
-- 存储企业风险评估历史记录。不实现用户注册、权限、多人协作与云端管理。

CREATE TABLE IF NOT EXISTS assessments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name    TEXT    NOT NULL,               -- 企业名称
    stock_code      TEXT,                           -- 股票代码
    fiscal_year     INTEGER NOT NULL,               -- 财务数据所属年度
    created_at      TEXT    NOT NULL,               -- 记录创建时间 ISO8601

    -- 原始报表输入（JSON 字符串，键见 indicator_definitions.raw_input_fields）
    raw_inputs      TEXT,

    -- 八项指标原始值 / 缩尾值 / 标准化 z 值 / 贡献（JSON 字符串）
    indicators      TEXT,
    winsorized      TEXT,
    z_scores        TEXT,
    contributions   TEXT,

    -- 评分结果
    logit           REAL,
    score           REAL,
    risk_level      TEXT,                           -- A / B / C / D
    level_meaning   TEXT,
    top_risk_sources TEXT,                          -- 正向贡献最大三项（JSON）

    -- 校验提示（JSON 字符串，errors + warnings）
    validation_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_assessments_company ON assessments (company_name);
CREATE INDEX IF NOT EXISTS idx_assessments_year ON assessments (fiscal_year);
