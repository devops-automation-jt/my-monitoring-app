# 服务器集群监控大屏制作步骤
## 核心前提
- Prometheus已采集多服务器指标（指标带`hostname`标签，如`host_disk_usage{hostname="server1"}`）；
- Grafana已配置Prometheus数据源（名称：prometheus，URL：http://localhost:9090）。

## 效果展示截屏
- [grafana大屏演示效果](./dashboard-cluster-monitor.png)

## 步骤1：新建总仪表盘（整合大屏载体）
1. 登录Grafana（http://服务器IP:3000）；
2. 点击左侧菜单栏「+」（Create）→ 选择「New dashboard」；
3. 仪表盘命名：服务器集群监控大屏（可自定义，如“3台服务器资源监控大屏”）。

## 步骤2：添加磁盘使用率面板（复用该逻辑添加其他指标）
### 2.1 新建可视化面板
1. 点击「+ Add visualization」→ 选择Prometheus数据源（标有default的prometheus）；
2. 指标配置：
   - 在「Metric」输入框输入：`host_disk_usage`；
   - 「Label filters」保留`hostname`标签（不填具体值，留空，显示所有服务器）；
   - 点击「Run queries」验证数据（能看到多服务器的磁盘使用率数据）。
### 2.2 配置图表类型（仪表盘更适配使用率）
1. 右侧「Visualization」下拉框 → 选择「Gauge」（仪表盘）；
2. 基础样式配置：
   - 「Panel options」→「Title」：集群磁盘使用率(%)；
   - 「Format」→ 选择「Percent (0-100)」（显示百分比）；
   - 「Thresholds」：添加阈值（80%→黄色，90%→红色，超过阈值变色告警）。
### 2.3 保存面板
点击右上角「Apply」→ 确认保存到当前仪表盘。

## 步骤3：批量添加其他指标面板
重复步骤2，依次添加内存/CPU/负载面板，核心配置如下：

| 面板名称       | 指标名              | 图表类型       | 核心配置                |
|----------------|---------------------|----------------|-------------------------|
| 集群内存使用率 | host_memory_usage   | Gauge          | 保留hostname标签，阈值80%/90% |
| 集群CPU使用率  | host_cpu_usage      | Gauge          | 保留hostname标签，阈值85%/95% |
| 集群1分钟负载  | host_load_1min      | Time series    | 保留hostname标签，折线图看趋势 |

## 步骤4：大屏布局排版（可视化调整）
1. 回到仪表盘主页，鼠标悬停在面板右上角「?」→ 选择「Resize/move」；
2. 拖拽面板调整位置：
   - 第一行：磁盘使用率 + 内存使用率（2个仪表盘横向排列）；
   - 第二行：CPU使用率 + 1分钟负载（仪表盘+折线图横向排列）；
3. 点击右上角「Save dashboard」→ 保存整个大屏配置（可设置自动刷新间隔：5秒/10秒）。

## 步骤5：（可选）添加服务器切换变量（快速看单台/全部）
1. 点击仪表盘顶部「Settings」→「Variables」→「Add variable」；
2. 变量配置：
   - 「Name」：hostname；
   - 「Type」：Query；
   - 「Data source」：prometheus；
   - 「Query」：label_values(host_disk_usage, hostname)（自动获取所有服务器名）；
   - 「Multi-value」「Include all option」勾选（支持多选/全选）；
3. 保存变量后，面板会自动关联变量，可通过顶部下拉框切换单台/全部服务器。
## 步骤6：保存整个仪表盘：
1. 点击页面右上角的「Save dashboard」按钮（蓝色按钮）；
   - 输入仪表盘名称（比如服务器集群监控大屏_v1.0）；
   - 可选：设置「Auto refresh」（自动刷新间隔，比如 10 秒）；
   - 点击「Save」，整个大屏的配置就永久保存了。








# Grafana 服务器集群监控大屏部署文档

## 文档说明

### 适用场景
本文档适用于基于 Grafana 12.3.2 + Prometheus 构建的多服务器集群监控体系，实现磁盘、内存、CPU、负载等核心资源的实时可视化，支持多服务器切换查看与阈值告警变色，为运维决策提供直观数据支撑。

### 核心版本与目标
核心组件版本：Grafana 12.3.2、Prometheus（任意支持时序数据的稳定版本）  
监控范围：多台服务器（通过 hostname 标签区分，如 server1、service1）  
核心目标：
- 可视化：多指标面板整合，支持自动刷新与布局调整；
- 灵活性：通过变量切换单台 / 全部服务器监控数据；
- 预警性：关键指标阈值配置，超阈值自动变色提示。

## 一、核心前提（必验项）
确保以下条件全部满足，否则会导致大屏无数据或配置失败：

**Prometheus 指标采集就绪：**
- 已通过 Ansible/Node Exporter 等工具采集目标服务器指标，且指标包含 hostname 标签（如 host_disk_usage{hostname="service1"}、host_cpu_usage{hostname="server2"}）；
- 支持的核心指标清单（需提前在 Prometheus 验证可查询）：
  - 磁盘使用率：host_disk_usage
  - 内存使用率：host_memory_usage
  - CPU 使用率：host_cpu_usage
  - 1 分钟负载：host_load_1min

**Grafana 数据源配置完成：**
- 已在 Grafana 中添加 Prometheus 数据源，名称为 prometheus（自定义名称需在后续步骤中同步修改）；
- 数据源 URL 配置正确（如 http://localhost:9090，确保 Grafana 服务器能访问 Prometheus 端口）；
- 数据源测试连通性：进入 Grafana → 「Data sources」→ 选择 prometheus → 点击「Test」，显示「Data source is working」。

## 二、大屏部署全流程

### 步骤 1：新建总仪表盘（整合载体）
1. 登录 Grafana 控制台：访问 http://服务器IP:3000（默认账号密码 admin/admin，首次登录需修改密码）；
2. 创建空白仪表盘：
   - 点击左侧菜单栏「+」（Create）→ 选择「New dashboard」；
   - 仪表盘命名：服务器集群监控大屏_v1.0（建议包含版本号，便于后续迭代）；
   - 初始设置：默认选择「Add a new panel」，进入面板配置界面。

### 步骤 2：添加核心指标面板（以磁盘使用率为例，其他指标复用逻辑）

#### 2.1 新建可视化面板
1. 选择数据源：点击「+ Add visualization」→ 在数据源列表中选择 prometheus（标有「default」标识）；
2. 指标查询配置：
   - 在「Metric」输入框中输入指标名：host_disk_usage；
   - 标签过滤（关键）：「Label filters」中保留 hostname 标签，不填写具体值（留空即可），实现多服务器数据同时展示；
   - 数据验证：点击「Run queries」，下方图表区域应显示所有带 hostname 标签的服务器磁盘使用率数据（如 service1、server2 等），无数据需返回前提条件验证指标采集。

#### 2.2 配置图表类型与样式（适配使用率展示）
1. 选择图表类型：右侧「Visualization」下拉框 → 选择「Gauge」（仪表盘类型，直观展示使用率占比）；
2. 基础样式配置：
   - 面板标题：「Panel options」→「Title」输入 集群磁盘使用率(%)；
   - 数据格式：「Format」下拉框 → 选择「Percent (0-100)」（强制显示为百分比，如 45%）；
3. 阈值告警配置（超阈值变色）：
   - 点击「Thresholds」→ 点击「Add threshold」，添加两级阈值：
     - 第一级：80 → 颜色选择「Yellow」（使用率 80%-90% 显示黄色预警）；
     - 第二级：90 → 颜色选择「Red」（使用率 ≥90% 显示红色告警）；
   - 阈值生效逻辑：低于 80% 显示默认绿色，按区间自动切换颜色。

#### 2.3 保存面板到仪表盘
点击页面右上角「Apply」→ 确认面板添加到当前仪表盘，返回大屏主页。

### 步骤 3：批量添加其他指标面板（按表格配置高效完成）
重复步骤 2 的操作，依次添加内存、CPU、负载面板，核心配置如下表（直接复用，无需额外调整逻辑）：

| 面板名称 | 指标名 | 图表类型 | 核心配置细节 |
|----------|--------|----------|--------------|
| 集群内存使用率 | host_memory_usage | Gauge（仪表盘） | 保留 hostname 标签；Format 选「Percent (0-100)」；阈值 80%（黄）/90%（红） |
| 集群 CPU 使用率 | host_cpu_usage | Gauge（仪表盘） | 保留 hostname 标签；Format 选「Percent (0-100)」；阈值 85%（黄）/95%（红） |
| 集群 1 分钟负载 | host_load_1min | Time series（折线图） | 保留 hostname 标签；Format 选「Number」；Y 轴范围设置「0-10」（按需调整） |

### 步骤 4：大屏布局排版（优化可视化体验）
1. 进入布局模式：回到仪表盘主页，鼠标悬停在任意面板右上角的「?」图标 → 选择「Resize/move」（所有面板进入可拖拽状态）；
2. 推荐布局方案（适配 16:9 屏幕）：
   - 第一行（横向排列）：磁盘使用率面板 + 内存使用率面板（各占 50% 宽度）；
   - 第二行（横向排列）：CPU 使用率面板 + 1 分钟负载面板（各占 50% 宽度）；
3. 调整细节：
   - 拖拽面板边缘可修改宽高（建议所有仪表盘类型面板大小一致，折线图面板高度略高于仪表盘）；
   - 点击面板标题可上下移动面板，调整排列顺序；
4. 保存布局：点击页面右上角「Save dashboard」→ 无需修改名称，直接点击「Save」。

### 步骤 5：添加服务器切换变量（支持单台 / 全部快速筛选）

#### 5.1 创建变量（自动获取所有服务器名）
1. 进入变量配置页：点击仪表盘顶部「Settings」（齿轮图标）→ 选择「Variables」→ 点击「Add variable」；
2. 变量核心配置：
   - 变量名称：hostname（后续面板自动关联，不可随意修改）；
   - 变量类型：「Type」下拉框 → 选择「Query」（基于 Prometheus 查询动态获取值）；
   - 数据源：选择 prometheus；
   - 查询语句：label_values(host_disk_usage, hostname)（通过 host_disk_usage 指标的 hostname 标签，自动获取所有服务器名称）；
3. 高级配置：
   - 勾选「Multi-value」（支持同时选择多台服务器）；
   - 勾选「Include all option」（添加「All」选项，一键查看所有服务器）；
   - 「All value」输入 $__all（Grafana 内置变量，代表选中所有值）；
4. 保存变量：点击页面底部「Save changes」，返回仪表盘主页。

#### 5.2 验证变量功能
1. 仪表盘顶部会新增 hostname 下拉框，包含所有服务器名称和「All」选项；
2. 切换测试：选择某台服务器（如 service1），所有面板应自动刷新为该服务器的指标数据；选择「All」，恢复所有服务器数据展示。

### 步骤 6：配置自动刷新与权限（可选，提升实用性）
1. 自动刷新配置：
   - 点击仪表盘顶部「Refresh」下拉框 → 选择刷新间隔（推荐「10s」或「30s」，根据监控实时性需求调整）；
   - 支持手动刷新：点击「Refresh」按钮可立即刷新所有面板数据。
2. 权限配置（多人协作场景）：
   - 点击仪表盘顶部「Share」→ 选择「Permissions」；
   - 添加用户权限：输入用户名 / 邮箱，选择权限级别（如「Viewer」仅查看，「Editor」可编辑）；
   - 生成公开链接（可选）：点击「Share dashboard」→ 勾选「Public access」，生成公开链接（需谨慎开启，避免敏感数据泄露）。

## 三、大屏配置导出与导入（复用 / 迁移必备）

### 3.1 导出配置（备份 / 提交 GitHub）
1. 进入仪表盘主页 → 点击顶部「Settings」→ 选择「JSON Model」；
2. 复制 JSON 配置：点击「Copy to clipboard」，将配置复制到本地文件，命名为 cluster-monitor-dashboard.json；
3. 提交建议：将该 JSON 文件与本文档放在同一目录下（如 grafana/dashboard/），一起提交到 GitHub，便于后续迁移或他人复用。

### 3.2 导入配置（快速部署）
1. 进入 Grafana → 左侧「Dashboards」→ 选择「Import」；
2. 上传配置：点击「Upload JSON file」，选择导出的 cluster-monitor-dashboard.json 文件；
3. 确认导入：选择数据源（需与导出时的数据源名称一致，如 prometheus）→ 点击「Import」，即可快速生成相同的大屏。

### 3.3 大屏制作JSON配置（可直接导入）
以下为「服务器集群监控大屏_v1.0」的导出 JSON（替换 <你的配置> 为实际值即可直接导入 Grafana）：
```json
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": 0,
  "links": [],
  "panels": [
    {
      "datasource": {
        "type": "prometheus",
        "uid": "<你的Prometheus数据源UID>"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              },
              {
                "color": "blue",
                "value": 40
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 2,
      "options": {
        "minVizHeight": 75,
        "minVizWidth": 75,
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "sizing": "auto"
      },
      "pluginVersion": "12.3.2",
      "targets": [
        {
          "editorMode": "builder",
          "expr": "host_memory_usage",
          "legendFormat": "{{hostname}}",
          "range": true,
          "refId": "A"
        }
      ],
      "title": "集群内存使用率",
      "type": "gauge"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "<你的Prometheus数据源UID>"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "barWidthFactor": 0.6,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "auto",
            "showValues": false,
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              },
              {
                "color": "blue",
                "value": 0.04
              },
              {
                "color": "red",
                "value": 0.1
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 4,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "hideZeros": false,
          "mode": "single",
          "sort": "none"
        }
      },
      "pluginVersion": "12.3.2",
      "targets": [
        {
          "editorMode": "builder",
          "expr": "host_load_1min",
          "legendFormat": "{{hostname}}",
          "range": true,
          "refId": "A"
        }
      ],
      "title": "集群1分钟负载",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "<你的Prometheus数据源UID>"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              },
              {
                "color": "blue",
                "value": 40
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 8
      },
      "id": 1,
      "options": {
        "minVizHeight": 75,
        "minVizWidth": 75,
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "sizing": "auto"
      },
      "pluginVersion": "12.3.2",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "<你的Prometheus数据源UID>"
          },
          "editorMode": "builder",
          "expr": "host_disk_usage",
          "legendFormat": "{{hostname}}",
          "range": true,
          "refId": "A"
        }
      ],
      "title": "集群磁盘使用率",
      "type": "gauge"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "<你的Prometheus数据源UID>"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              },
              {
                "color": "blue",
                "value": 0.5
              },
              {
                "color": "red",
                "value": 1.5
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 8
      },
      "id": 3,
      "options": {
        "minVizHeight": 75,
        "minVizWidth": 75,
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "sizing": "auto"
      },
      "pluginVersion": "12.3.2",
      "targets": [
        {
          "editorMode": "builder",
          "expr": "host_cpu_usage",
          "legendFormat": "{{hostname}}",
          "range": true,
          "refId": "A"
        }
      ],
      "title": "集群CPU使用率",
      "type": "gauge"
    }
  ],
  "preload": false,
  "refresh": "",
  "schemaVersion": 42,
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-5m",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "browser",
  "title": "服务器集群监控大屏_v1.0",
  "uid": "<集群监控大屏UID（导入时自动生成）>",
  "version": 2
}
```

## 四、功能验证

**验证项 1：数据展示完整性**
- 切换 hostname 下拉框的「All」选项，所有面板应显示多台服务器的指标数据（无数据缺失）；
- 检查指标格式：百分比面板显示正确（如 45%），折线图趋势平滑（无异常波动）。

**验证项 2：阈值告警变色**
- 模拟超阈值场景（或修改阈值为当前指标值以下）：如将磁盘使用率阈值改为「40%」，当前使用率 45% 的服务器应显示黄色；
- 确认颜色切换实时生效（无需手动刷新）。

**验证项 3：自动刷新功能**
- 查看仪表盘顶部刷新间隔（如 10s），等待周期后，数据应自动更新（可通过 Prometheus 手动修改指标值验证）。

**验证项 4：成果截图（推荐提交 GitHub）**
（注：将大屏完整效果截图保存至该路径，直观展示部署成果，提升项目文档可读性）

## 五、日常运维操作

### 1. 大屏管理

| 操作 | 步骤 |
|------|------|
| 编辑面板 | 进入大屏 → 点击面板右上角「...」→ 选择「Edit」，修改指标 / 样式 / 阈值 |
| 复制大屏 | 进入大屏 → 点击顶部「Settings」→ 选择「Duplicate」，生成新大屏副本 |
| 删除大屏 | 进入大屏 → 点击顶部「Settings」→ 选择「Delete」→ 确认删除（谨慎操作） |
| 导出更新 | 大屏配置修改后，重新导出 JSON 文件，覆盖原有备份（提交 GitHub 时同步更新） |

### 2. Grafana 服务管理（与告警模块通用）

```bash
# 启动 Grafana 服务
sudo systemctl start grafana-server

# 停止 Grafana 服务（优雅关闭）
sudo systemctl stop grafana-server

# 重启服务（配置修改后生效）
sudo systemctl restart grafana-server

# 查看服务状态（验证是否运行）
sudo systemctl status grafana-server

# 设置开机自启
sudo systemctl enable grafana-server
```