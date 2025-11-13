## 说明
- 基于代码实际使用的环境变量，整理出“最小可运行”与“扩展完整”两套 `.env` 示例，路径建议：`/www/wwwroot/wwwroot/timao-douyin-live-manager/server/.env`。
- 最小版满足启动、鉴权、数据库与单一AI提供商；扩展版覆盖多提供商与功能级默认模型。

## 最小可运行示例（推荐）
```
SECRET_KEY=replace_with_random_32bytes
ENCRYPTION_KEY=replace_with_random_32bytes
DEBUG=false
BACKEND_PORT=11111
DIS