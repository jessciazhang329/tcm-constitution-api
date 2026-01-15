# 中医体质判定 API 服务

基于规则系统的中医体质分类与判定服务，参考《中医体质分类与判定》标准，支持九种体质的倾向性分析。

## ⚠️ 重要声明

**本服务仅供参考，不构成医疗诊断。**
- 不提供疾病诊断、用药建议或处方
- 不输出“你得了某病”等诊断性内容
- 仅提供体质倾向性分析和生活方式建议
- 如有健康问题，请咨询专业医生或中医师

## 功能特性

- 基于规则系统的体质判定（无需外部大模型）
- 支持九种体质：平和质、气虚质、阳虚质、阴虚质、痰湿质、湿热质、血瘀质、气郁质、特禀质
- API Key 鉴权 + 内存限流（按 API Key 每分钟限制）
- trace_id 贯穿请求，日志可观测
- 限制请求体大小与超时控制
- 支持可配置 CORS

## 运行方式

### 本地运行（推荐）

```bash
# 1) 创建并激活虚拟环境（仅首次需要）
python3 -m venv venv
source venv/bin/activate

# 2) 安装依赖
pip install -r requirements.txt

# 3) 设置必要环境变量（至少配置 API_KEYS）
export API_KEYS="demo_key_123"

# 4) 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 使用启动脚本（自动安装依赖）

```bash
export API_KEYS="demo_key_123"
./start.sh
```

### Docker 运行

```bash
docker build -t constitution-api .
docker run -p 8000:8000 \
  -e API_KEYS="demo_key_123" \
  -e RATE_LIMIT_PER_MINUTE=60 \
  -e REQUEST_TIMEOUT_SECONDS=5 \
  -e MAX_BODY_SIZE=32768 \
  constitution-api
```

### Docker Compose

```bash
docker compose up --build
```

## 环境变量

- `API_KEYS`：必填，多个 key 用逗号分隔
- `RATE_LIMIT_PER_MIN`：每个 API Key 每分钟最多请求数，默认 60
- `RATE_LIMIT_PER_MINUTE`：兼容旧变量名（可不填）
- `REQUEST_TIMEOUT_SECONDS`：请求超时秒数，默认 5
- `MAX_BODY_SIZE`：请求体最大字节数，默认 32768 (32KB)
- `ALLOWED_ORIGINS`：CORS 允许的来源，逗号分隔，默认关闭
- `RELOAD`：本地开发热重载（true/false）

## API 端点

所有接口需要 Header：`Authorization: Bearer <API_KEY>`

- `GET /health`
- `GET /version`
- `POST /v1/constitution/estimate`

### POST /v1/constitution/estimate

**请求体：**
```json
{
  "text": "用户症状描述（中文）",
  "meta": {
    "age": 28,
    "sex": "F",
    "region": "CN",
    "notes": "可选"
  }
}
```

**响应字段：**
- `primary_type`: 主要体质类型
- `secondary_types`: 次要体质类型列表
- `confidence`: 置信度 (0.0-1.0)
- `evidence`: 判定证据（关键词匹配详情）
- `recommendations`: 生活建议（lifestyle、diet、when_to_seek_help）
- `questions_to_clarify`: 需要澄清的问题列表
- `disclaimer`: 免责声明

## curl 示例（3 个）

### 1) 正常请求
```bash
curl -X POST "http://localhost:8000/v1/constitution/estimate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo_key_123" \
  -d '{
    "text": "我最近总是感觉很累，容易疲劳，说话声音也比较低，稍微动一下就出汗，还经常感冒。",
    "meta": { "age": 35, "sex": "M" }
  }'
```

### 2) 未授权请求（401）
```bash
curl -X POST "http://localhost:8000/v1/constitution/estimate" \
  -H "Content-Type: application/json" \
  -d '{ "text": "我怕冷，手脚冰凉" }'
```

### 3) 信息不足（或可用于测试超限）
```bash
curl -X POST "http://localhost:8000/v1/constitution/estimate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo_key_123" \
  -d '{ "text": "有点不舒服" }'
```

> 测试 429：把 `RATE_LIMIT_PER_MINUTE` 设置为 1，然后用同一个 API Key 连续请求两次即可触发。

## 项目结构

```
.
├── main.py              # FastAPI 应用主文件
├── rules.py             # 体质规则定义和评分逻辑
├── security.py          # 鉴权/限流/错误模型
├── requirements.txt     # Python 依赖
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 技术说明

### 规则系统

- 每种体质包含关键词库（含权重）和反证词库
- 文本匹配采用简单的包含匹配（可扩展为更复杂的分词）
- 评分 = 关键词匹配得分 - 反证扣分
- 置信度使用 `score / (score + K)` 方法归一化

### 判定逻辑

1. 计算所有体质的得分
2. 如果最高分低于阈值（默认 3.0），返回"信息不足"
3. 主要体质为最高分
4. 次要体质为分差在阈值内（默认 5.0）的前2个
5. 置信度低于 0.5 时，返回补充问题列表

### 扩展性

- 规则库在 `rules.py` 中定义，易于添加新关键词
- 可扩展为正则匹配或更复杂的中文分词
- 可添加更多体质类型或细化规则

## 注意事项

1. **非医疗诊断**：本服务仅提供体质倾向性分析，不构成医疗建议
2. **信息准确性**：输入信息越详细，判定结果越准确
3. **规则限制**：基于关键词匹配，可能无法覆盖所有情况
4. **专业咨询**：如有健康问题，请咨询专业医生或中医师

## 许可证

本项目仅供学习和研究使用。
# tcm-constitution-api
