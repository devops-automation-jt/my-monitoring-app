## 一、Ansible 采集相关问题
### 问题 1：Ansible ping 不通被监控机 / 连接超时
#### 现象
执行 ansible all -i ansible/inventory/hosts.ini -m ping 出现 UNREACHABLE / Timeout。
#### 可能原因
- 目标主机防火墙未放通 22 端口
- hosts.ini 中 IP、端口、用户名写错
- 目标机器未安装 Python（Ansible 依赖）
#### 解决方案
1. 先用 ssh 用户名@IP -p 端口 手动测试连通性
2. 检查并修正 ansible/inventory/hosts.ini
3. 用 raw 模块预安装 Python：
```bash
#运行
ansible all -i hosts.ini -m raw -a "yum install -y python3"
```
#### 经验总结 / 复盘
Ansible 排错优先遵循「网络 → 配置 → 依赖」的顺序。先保证底层 SSH 通，再看配置，最后看环境依赖。很多时候采集失败不是脚本问题，而是基础连通性没解决。

### 问题 2：Ansible 执行成功，但采集不到指标 / 指标为空
#### 现象
playbook 执行绿色成功，但 Flask / Prometheus 没有对应监控数据。
#### 可能原因
- 目标机未安装 psutil
- 脚本输出格式不符合 Prometheus 规范
- 采集脚本权限不足
#### 解决方案
1. 用 Ansible 批量安装依赖：
```bash
#运行
ansible all -i hosts.ini -m pip -a "name=psutil state=present"
```
2. 确保输出是 指标名 数值 格式
3. 确保脚本有执行权限
#### 经验总结 / 复盘
跨机器运维一定要考虑环境一致性：本地开发有的库，远端机器不一定有。把依赖安装写到剧本或文档里，能避免 80% 的 “明明本地好使” 类问题。

## 二、Flask 后端接口问题
### 问题 1：curl /metrics 返回 404 / 本机通、外网不通
#### 现象
- Flask 启动成功
- 本机访问正常
- 其他机器（Prometheus）访问 404 或拒绝连接
#### 可能原因
- Flask 绑定 127.0.0.1，只允许本机访问
- 端口被防火墙拦截
- 路由写错（例如 /metric 少写 s）
#### 解决方案
启动时改为：
```python
#运行 app.run(host='0.0.0.0', port=5000)
```
#### 经验总结 / 复盘
凡是给别的服务调用的接口，一定要绑定 0.0.0.0，这是后端服务最经典的坑之一。排查 404 / 无法访问优先看「绑定地址 + 防火墙 + 路由」。

### 问题 2：/metrics 返回 200，但 Prometheus 提示格式错误
#### 现象
接口能访问，但 Prometheus 提示 invalid metric format。
#### 可能原因
- 输出混了 print 日志、中文、调试信息
- 指标名不符合规范
- 值不是数字
#### 解决方案
1. 删掉调试 print
2. 严格按照 metric_name{label="value"} value 格式输出
#### 经验总结 / 复盘
监控数据是给机器读的，不是给人看的。输出必须干净、标准、无杂质。格式规范是整个监控链路能否跑通的关键。

## 三、Prometheus 相关问题
### 问题 1：Prometheus 显示 Target DOWN
#### 现象
Prometheus 控制台 target 状态为 DOWN，无法采集 Flask。
#### 可能原因
- Prometheus.yml 中 targets 地址写错
- Flask 未监听 0.0.0.0
- 网络不通 / 端口不通
#### 解决方案
1. 检查 prometheus.yml 的 targets 配置
2. 确保 Flask 可以被 Prometheus 所在机器访问
#### 经验总结 / 复盘
Prometheus 采集失败，90% 是「地址写错」或「网络不通」。先 curl 手动测接口，再看配置，不要一上来怀疑 Prometheus 本身。

## 四、Grafana 大屏 & 告警问题
### 问题 1：Grafana 仪表盘加载成功，但无数据（No Data）
#### 现象
面板正常，就是不显示曲线 / 数值。
#### 可能原因
- 数据源地址错误
- PromQL 指标名写错
- Prometheus 根本没抓到数据
#### 解决方案
1. 去 Grafana → 数据源 → 测试连通性
2. 去 Prometheus 页面先查指标是否存在
3. 再复制到 Grafana
#### 经验总结 / 复盘
排查链路遵循：
Ansible → Flask → Prometheus → Grafana
从源头一步步查，不要一上来就调面板。数据没到 Prometheus，面板怎么改都没用。

### 问题 2：Grafana 告警配置了，但不触发
#### 现象
指标明明超过阈值，告警却不发送。
#### 可能原因
- 告警通道（邮件 / 钉钉 /webhook）配置错误
- 阈值设置不合理
- 告警状态为 Pending，还没到 Firing
- 时间范围设置太短
#### 解决方案
1. 先在 Contact Points 点 Test 测试通道
2. 检查 PromQL 与阈值
3. 等待一个完整评估周期
#### 经验总结 / 复盘
告警不触发优先排查「通道是否可达」，再排查规则。很多时候是通知渠道问题，而不是查询语句问题。

## 五、项目工程化 / Git 问题
### 问题：分支合并时出现文件路径冲突（如 hosts 文件多份）
#### 现象
合并 feature/ansible-collection 到 main 时出现路径冲突。
#### 可能原因
开发时文件目录不统一，同一文件出现在多个位置。
#### 解决方案
1. 统一规范：Ansible 相关只放 ansible/ 目录下
2. 废弃根目录冗余文件，只保留一份规范路径
3. 一次提交完成结构整理，保持提交原子性