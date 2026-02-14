# 全栈式运维监控平台
## 项目介绍
my-monitoring-app 是一个全栈运维监控平台，基于 Ansible 实现多台虚拟机的自动化指标采集，通过 Prometheus 统一存储时序数据，
并利用 Grafana 提供实时可视化和 Webhook 告警能力。后端采用 Flask 构建 REST API，打通配置分发与告警接收链路。

## 核心技术栈
| 模块         | 技术选型       | 选型原因                                  |
|--------------|----------------|-------------------------------------------|
| 数据采集     | Ansible        | 支持多机并发采集，自带重试/容错，比Paramiko更高效 |
| 后端服务     | Flask          | 轻量易部署，快速暴露metrics接口给Prometheus |
| 数据存储     | Prometheus     | 专为时序监控数据设计，支持实时查询/聚合，替代CSV |
| 可视化/告警  | Grafana 12.3.2 | 原生支持大屏可视化+Webhook告警，模板化配置易复用 |
| 部署环境     | Linux虚拟机    | 适配生产环境的Linux服务器部署              |

## 核心功能
1. 多虚拟机数据采集：CPU/内存/磁盘/1分钟负载；
2. 实时可视化大屏：集群维度展示各指标，支持阈值变色；
3. 自动告警：磁盘使用率超阈值时，通过Webhook推送告警；
4. 部署便捷：基于Ansible和Shell脚本，一键完成环境配置。

## 快速开始
### 环境准备
- Linux虚拟机（CentOS 7+/Ubuntu 20.04+）；
- Python 3.9+；
- Ansible 2.14+；
- Prometheus 2.45+；
- Grafana 12.3.2。
### 快速部署
```bash
# 克隆代码
git clone https://github.com/automatedoperationdevops153/my-monitoring-app.git
cd my-monitoring-app

# 修改待监控虚拟机IP列表
vim ansible/inventory/hosts

# 一键部署（含依赖安装、服务启动）
bash scripts/deploy_all.sh

# 验证：访问Grafana（默认端口3000，账号admin/admin）
http://<服务器IP>:3000
```
### 核心分支说明
| 分支名                | 功能说明                                  |
|-----------------------|-------------------------------------------|
| feature/ansible-collection | Ansible多机数据采集脚本                  |
| feature/flask-backend     | Flask后端，暴露metrics接口                |
| feature/prometheus-integration | Prometheus采集配置、数据存储规则      |
| feature/grafana-monitoring | Grafana大屏配置、告警规则、效果截图     |
| docs/setup-guide           | 部署文档、问题排查文档                    |

## 文档入口
- 部署文档：[deploy.md](deploy.md)
- 问题排查：[possible_problems.md](possible_problems.md)