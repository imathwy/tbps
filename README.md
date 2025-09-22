# tbps 项目

## 快速启动

1. 克隆仓库：

   ```bash
   git clone https://github.com/imathwy/tbps.git
   cd tbps
   ```

2. 确保安装了 Docker 和 docker-compose。

3. 运行启动脚本：

   ```bash
   ./start.sh
   ```

4. 数据库将在 `localhost:8923` 上运行，连接参数见脚本输出。
   - 数据库名：`mathlib_db`, `wl_encodings_db`
   - 用户名：`princhern`

5. 启动你的应用（例如 `python main.py`）。

6. 停止服务：

   ```bash
   docker-compose down
   ```

## 数据库

- 包含两个数据库转储文件：

  - `mathlib_filtered_backup0515.sql`
  - `wl_encodings_new_backup0515.sql`

- 自动导入到 PostgreSQL 数据库 `mathlib_db` 和 `wl_encodings_db`
