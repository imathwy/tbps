# 使用官方 PostgreSQL 15 镜像
FROM postgres:17

# 安装 xz-utils 以解压 .xz 文件
RUN apt-get update && apt-get install -y xz-utils

# 复制数据库备份文件到初始化目录
COPY data/*.sql.xz /docker-entrypoint-initdb.d/

# 解压 .xz 文件
RUN for file in /docker-entrypoint-initdb.d/*.sql.xz; do xz -d "$file"; done

# 复制初始化脚本
COPY init-databases.sh /docker-entrypoint-initdb.d/10-init-databases.sh