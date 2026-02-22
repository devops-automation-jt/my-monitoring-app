# Grafana 磁盘使用率告警配置部署文档
## 文档说明
### 适用场景
本文档适用于基于 Grafana 12.3.2 + Prometheus 构建的运维监控体系，实现 service1 服务器磁盘使用率异常时的自动告警，并通过 Webhook 渠道推送告警通知。

### 核心版本
- Grafana：12.3.2
- 监控指标：host_disk_usage{hostname="service1"}（磁盘使用率）
- 通知渠道：Webhook（以 webhook.site 为例）

### 效果展示截屏
- [grafana告警演示效果](alert-disk.png)

## 一、前提准备
告警配置生效的核心前提，需先完成以下步骤：
1. 数据源对接：Grafana 已成功连接 Prometheus，且 Prometheus 能正常采集 host_disk_usage 指标。
2. 指标验证：
   - 进入 Grafana → 左侧「Explore」；
   - 输入查询语句 host_disk_usage{hostname="service1"}，能查到具体数值（如 45），确认指标有效。
3. 监控大屏制作：基于 host_disk_usage 指标制作可视化面板，验证指标展示正常（为告警规则提供基础）。

## 二、告警配置全流程
### 步骤 1：新增 Webhook 通知渠道（Contact Point）
用于接收告警的外部渠道，配置后可测试基础连通性：
- 路径：Grafana 左侧菜单栏 → Alerting → Contact points → New contact point；
- 核心配置：
  - 名称：Webhook-Test（自定义，便于识别）；
  - 类型：选择「Webhook」；
  - URL：填写 webhook.site 生成的专属 URL（示例：https://webhook.site/467d8e2f-fa55-468b-a569-8baf94c5c869）；
  - 状态：确保勾选「Enabled」（启用）；
- 保存后，可通过 webhook.site 发送测试消息，验证渠道能正常接收数据。

### 步骤 2：配置通知策略（Notification Policies）
关键遗漏项：确保告警规则能路由到上述 Webhook 渠道：
- 路径：Grafana 左侧 → Alerting → Notification policies；
- 配置方式（二选一）：
  - 方式 1（全局）：在「默认策略」中，「Contact point」选择 Webhook-Test；
  - 方式 2（精准路由）：新增子策略，添加匹配规则 alertname=磁盘预警，指定「Contact point」为 Webhook-Test；
- 保存策略，确保路由规则生效。

### 步骤 3：新增 Alert Rules（告警规则）
核心告警逻辑配置，贴合磁盘使用率监控场景：
- 路径：Grafana 左侧 → Alerting → Alert rules → New alert rule；
- 分模块配置：
  1. 基础信息：
     - 名称：磁盘预警；
     - 文件夹：ServerAlert（自定义，便于归类）；
  2. 告警条件（Alert condition）：
     - 数据源：选择已对接的 Prometheus；
     - 指标查询：host_disk_usage{hostname="service1"}；
     - 阈值设置：如「>40」（使用率超 40% 触发告警）；
     - 评估间隔：默认 30s（Grafana 周期性检查指标）；
     - 持续时间（For）：1m（指标满足条件持续 1 分钟触发，避免偶发波动）；
  3. 标注 / 注释（Annotations and labels）：
     - Labels（可选）：添加 hostname=service1、instance=139.199.178.185:8080 等标签，便于筛选告警；
     - Annotations（模板写此处，12.x 版本核心）：
       ```plaintext
       # Summary
       service1磁盘使用率异常（当前值：{{ $value }}）
       # Description
       服务器：{{ $labels.instance }}
       磁盘使用率数值：{{ $value }}
       触发时间：{{ now.Format "2006-01-02 15:04:05" }}
       ```
  4. 通知配置（Configure notifications）：
     - 选择通知渠道：Webhook-Test；
     - 消息模板：引用 Annotations 内容（避免直接写变量导致渲染失败）：
       - Summary：{{ .Annotations.summary }}
       - Description：{{ .Annotations.description }}；
- 保存规则，确保状态为「Active」（未暂停）。

## 三、告警规则 JSON 配置（可直接导入）
以下为「磁盘预警」规则的导出 JSON（替换 <你的配置> 为实际值即可直接导入 Grafana）：
```json
{
    "apiVersion": 1,
    "groups": [
        {
            "orgId": 1,
            "name": "AlertGroup",
            "folder": "ServerAlert",
            "interval": "30s",
            "rules": [
                {
                    "uid": "<磁盘预警规则UID（可自定义）>",
                    "title": "磁盘预警",
                    "condition": "C",
                    "data": [
                        {
                            "refId": "A",
                            "relativeTimeRange": {
                                "from": 300,
                                "to": 0
                            },
                            "datasourceUid": "<你的Prometheus数据源UID>",
                            "model": {
                                "editorMode": "code",
                                "expr": "host_disk_usage{hostname=\"service1\"}  ",
                                "instant": true,
                                "intervalMs": 1000,
                                "legendFormat": "__auto",
                                "maxDataPoints": 43200,
                                "range": false,
                                "refId": "A"
                            }
                        },
                        {
                            "refId": "C",
                            "relativeTimeRange": {
                                "from": 0,
                                "to": 0
                            },
                            "datasourceUid": "__expr__",
                            "model": {
                                "conditions": [
                                    {
                                        "evaluator": {
                                            "params": [
                                                81
                                            ],
                                            "type": "gt"
                                        },
                                        "operator": {
                                            "type": "and"
                                        },
                                        "query": {
                                            "params": [
                                                "C"
                                            ]
                                        },
                                        "reducer": {
                                            "params": [],
                                            "type": "last"
                                        },
                                        "type": "query"
                                    }
                                ],
                                "datasource": {
                                    "type": "__expr__",
                                    "uid": "__expr__"
                                },
                                "expression": "A",
                                "intervalMs": 1000,
                                "maxDataPoints": 43200,
                                "refId": "C",
                                "type": "threshold"
                            }
                        }
                    ],
                    "noDataState": "NoData",
                    "execErrState": "Error",
                    "for": "1m",
                    "keepFiringFor": "1m",
                    "annotations": {
                        "description": "服务器:{{$labels.instance }}\n磁盘使用率数值:{{$value }}\n触发时间:{{now.Format \"2006-01-02 15:04:05\"}}",
                        "summary": "service1磁盘使用率异常(当前值:{{ $value }})"
                    },
                    "labels": {},
                    "isPaused": false,
                    "notification_settings": {
                        "receiver": "Webhook-Test"
                    }
                }
            ]
        }
    ]
}
 ```