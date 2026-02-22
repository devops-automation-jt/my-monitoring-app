# 监控大屏&告警使用手册
## 核心操作入口（具体步骤见对应文档）
1. 监控大屏配置
   - 操作文档：`grafana/grafana12.3.2_dashboards.md`
   - 核心步骤：导入grafana/grafana12.3.2_dashboards.md内的`dashboard.json` → 绑定Prometheus数据源 → 调整大屏展示指标
2. 告警规则配置
   - 操作文档：`grafana/grafana12.3.2_dashboards.md`
   - 核心步骤：设置磁盘/CPU使用率阈值 → 配置告警通知通道（如钉钉/邮件） → 测试告警触发
3. 新增被监控节点
   - 操作文档：`ansible/inventory/hosts`
   - 核心步骤：修改`ansible/inventory/hosts`添加节点IP → 执行Ansible采集脚本
4. 查看监控指标
   - 核心入口：Grafana访问地址（http://部署IP:3000） → 进入“集群监控”仪表盘