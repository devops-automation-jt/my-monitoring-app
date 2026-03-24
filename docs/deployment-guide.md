# 部署文档：my-monitoring-app 全栈运维监控平台（Docker 一键部署版）

## 一、文档说明
本文档基于 Docker + Docker Compose 实现**一键容器化部署**，支持 Grafana 自动加载监控大屏与告警规则，无需手动配置，开箱即用。

## 二、环境要求
1. 操作系统：CentOS 7 / Ubuntu 20.04
2. 最低配置：CPU 2核、内存 2G、磁盘 20G
3. 网络：主节点可通外网，被监控节点开放 22 端口

## 三、前置环境安装
### 1. 安装 Docker
```bash
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
sudo systemctl start docker && sudo systemctl enable docker
```

### 2. 安装 Docker Compose
```bash
# CentOS 7
sudo yum install -y docker-compose-plugin

# Ubuntu 20.04
sudo apt install -y docker-compose-plugin
```

### 3. 配置 Ansible 免密登录
```bash
ssh-keygen -t rsa -b 2048 -N "" -f ~/.ssh/id_rsa
ssh-copy-id root@被监控节点IP
```

## 四、项目准备
1. 克隆项目到服务器
2. 将**监控大屏 JSON** 文件放入 `docker/grafana/dashboards/`
3. 将**告警规则 JSON** 文件放入 `docker/grafana/alerts/`
4. 修改 `docker/prometheus/prometheus.yml` 配置采集地址

## 五、一键启动服务
```bash
# 进入 docker 目录
cd my-monitoring-app/docker

# 一键启动所有服务
docker compose up -d

# 查看运行状态
docker ps
```

## 六、服务验证
1. **Flask 指标接口**：http://服务器IP:8080/metrics
2. **Prometheus 控制台**：http://服务器IP:9090
3. **Grafana 监控平台**：http://服务器IP:3000
   - 账号：admin
   - 密码：shell1300
   - 登录后**自动展示监控大屏 + 生效告警规则**

## 七、常用运维命令
```bash
# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 清空数据（重置）
docker compose down -v
```

## 八、常见问题
1. **端口冲突**：关闭 8080/9090/3000 占用进程
2. **无监控数据**：检查 prometheus.yml 采集配置
3. **大屏/告警未加载**：确认 JSON 文件放入正确目录