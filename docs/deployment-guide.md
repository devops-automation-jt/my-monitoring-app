# 部署文档：my-monitoring-app 全栈运维监控平台（手动部署版）
## 1. 文档说明
本文档为my-monitoring-app的纯手动部署指南，适配CentOS 7/Ubuntu 20.04 Linux虚拟机，包含从基础环境准备到监控告警验证的全手动步骤，一键部署功能将在学习Docker/K8s后补充。

## 2. 前置环境要求
### 2.1 服务器要求
- 部署主节点（运行Ansible/Prometheus/Grafana/Flask）：CPU ≥ 2核，内存 ≥ 4G，磁盘 ≥ 50G，网络可通外网
- 被监控节点（仅运行采集脚本）：基础Linux系统，网络可通主节点，开放22端口
- 操作系统：CentOS 7 64位 / Ubuntu 20.04 64位

### 2.2 软件版本要求
- Python 3.9+
- Ansible 2.14+
- Prometheus 2.45.0
- Grafana 12.3.2

## 3. 虚拟机基础配置（主节点+被监控节点）
### 3.1 配置静态IP（以CentOS 7为例）
#### 3.1.1 查看网卡名称
```bash
ip addr
# 通常网卡名称为ens33/eth0，记下来备用
```
#### 3.1.2 编辑网卡配置文件
```bash
运行
# 替换ens33为实际网卡名称
vi /etc/sysconfig/network-scripts/ifcfg-ens33
````
#### 3.1.3 修改配置内容(换为自身网段)
```plaintext
TYPE=Ethernet
BOOTPROTO=static  # 改为静态IP
ONBOOT=yes        # 开机自启网卡
NAME=ens33
DEVICE=ens33
IPADDR=192.168.1.100  # 主节点IP
NETMASK=255.255.255.0 # 子网掩码
GATEWAY=192.168.1.1   # 网关
DNS1=8.8.8.8         # DNS服务器
DNS2=114.114.114.114
3.1.4 重启网络并验证
```
```bash
运行
# CentOS 7
systemctl restart network
# Ubuntu 20.04
systemctl restart netplan
```
# 验证网络连通性
ping baidu.com
3.2 关闭防火墙 / SELinux（测试环境）
bash
运行
# CentOS 7 关闭防火墙
systemctl stop firewalld
systemctl disable firewalld

# CentOS 7 关闭SELinux
setenforce 0
sed -i 's/^SELINUX=enforcing$/SELINUX=disabled/' /etc/selinux/config

# Ubuntu 20.04 关闭防火墙
ufw disable
4. Ansible 免密登录配置（主节点操作）
4.1 生成 SSH 密钥对
bash
运行
# 无密码回车，生成rsa密钥对
ssh-keygen -t rsa -b 2048
# 生成后密钥路径：~/.ssh/id_rsa（私钥）、~/.ssh/id_rsa.pub（公钥）
4.2 分发公钥至所有被监控节点
bash
运行
# 替换为被监控节点IP，按提示输入被监控节点root密码
ssh-copy-id root@192.168.1.101
ssh-copy-id root@192.168.1.102
# 若被监控节点SSH端口非22，执行：ssh-copy-id -p 端口号 root@IP
4.3 验证免密登录
bash
运行
# 测试单节点连通性
ssh root@192.168.1.101 "hostname"

# 后续Ansible连通性测试（需先安装Ansible）
ansible all -i ansible/inventory/hosts -m ping
5. 核心依赖安装（主节点）
5.1 安装 Python 3.9
5.1.1 CentOS 7 安装 Python 3.9
bash
运行
# 安装编译依赖
yum install -y gcc openssl-devel bzip2-devel libffi-devel wget

# 下载Python 3.9源码包
wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz

# 解压并编译安装
tar xzf Python-3.9.18.tgz
cd Python-3.9.18
./configure --enable-optimizations
make altinstall  # 避免覆盖系统默认Python

# 验证安装
python3.9 --version
pip3.9 --version
5.1.2 Ubuntu 20.04 安装 Python 3.9
bash
运行
# 更新源
apt update

# 安装Python 3.9
apt install -y python3.9 python3.9-pip python3.9-dev

# 验证
python3.9 --version
5.2 安装 Ansible 2.14
bash
运行
# 用pip安装指定版本
pip3.9 install ansible==2.14.0

# 验证安装
ansible --version
# 输出包含ansible [core 2.14.x] 即为成功
6. 克隆项目代码（主节点）
bash
运行
# 安装git（若未安装）
# CentOS 7: yum install -y git
# Ubuntu 20.04: apt install -y git

# 克隆代码仓库
git clone https://github.com/automatedoperationdevops153/my-monitoring-app.git
cd my-monitoring-app

# 修改Ansible主机列表（关键步骤）
vi ansible/inventory/hosts
6.1 Ansible 主机列表配置示例
ini
# ansible/inventory/hosts 配置内容
[monitored_nodes]
192.168.1.101 ansible_ssh_user=root ansible_ssh_port=22
192.168.1.102 ansible_ssh_user=root ansible_ssh_port=22

# 可选：配置变量
[monitored_nodes:vars]
ansible_python_interpreter=/usr/bin/python3.9
7. 手动部署各核心组件
7.1 部署 Prometheus 2.45.0
7.1.1 下载并解压
bash
运行
# 下载Prometheus安装包
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz

# 解压到指定目录
tar xzf prometheus-2.45.0.linux-amd64.tar.gz
mv prometheus-2.45.0.linux-amd64 /usr/local/prometheus
7.1.2 配置 Prometheus 采集规则
bash
运行
# 编辑Prometheus配置文件
vi /usr/local/prometheus/prometheus.yml
7.1.3 配置文件内容示例
yaml
global:
  scrape_interval: 15s  # 全局采集间隔
  evaluation_interval: 15s

rule_files:
  # - "alert_rules.yml"  # 后续可添加告警规则

scrape_configs:
  # 采集Prometheus自身指标
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # 采集Flask后端暴露的metrics指标
  - job_name: "flask_backend"
    static_configs:
      - targets: ["192.168.1.100:5000"]  # 主节点IP+Flask端口

  # 采集Ansible拉取的被监控节点指标（需配合Flask后端）
  - job_name: "monitored_nodes"
    static_configs:
      - targets: ["192.168.1.100:5000"]
7.1.4 启动 Prometheus
bash
运行
# 后台启动Prometheus
nohup /usr/local/prometheus/prometheus --config.file=/usr/local/prometheus/prometheus.yml > /var/log/prometheus.log 2>&1 &

# 验证启动状态
ps -ef | grep prometheus
# 访问Prometheus UI：http://主节点IP:9090
curl http://127.0.0.1:9090/metrics
7.2 部署 Flask 后端服务
7.2.1 安装 Python 依赖
bash
运行
# 进入Flask后端目录（按项目实际结构调整）
cd flask-backend

# 安装依赖（需提前准备requirements.txt）
pip3.9 install -r requirements.txt
# 示例requirements.txt内容：
# Flask==2.3.3
# prometheus-client==0.17.1
# ansible==2.14.0
# psutil==5.9.5
7.2.2 启动 Flask 服务
bash
运行
# 后台启动Flask（用gunicorn守护，需先安装：pip3.9 install gunicorn）
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > /var/log/flask_backend.log 2>&1 &

# 验证启动状态
ps -ef | grep gunicorn
# 验证metrics接口
curl http://127.0.0.1:5000/metrics
7.3 部署 Grafana 12.3.2
7.3.1 安装 Grafana（CentOS 7）
bash
运行
# 安装依赖
yum install -y fontconfig freetype freetype-devel urw-fonts

# 下载Grafana安装包
wget https://dl.grafana.com/enterprise/release/grafana-enterprise-12.3.2-1.x86_64.rpm

# 安装
yum install -y grafana-enterprise-12.3.2-1.x86_64.rpm
7.3.2 安装 Grafana（Ubuntu 20.04）
bash
运行
# 添加Grafana源
apt install -y apt-transport-https software-properties-common wget
wget -q -O - https://apt.grafana.com/gpg.key | apt-key add -
echo "deb https://apt.grafana.com stable main" | tee -a /etc/apt/sources.list.d/grafana.list

# 更新源并安装
apt update
apt install -y grafana-enterprise=12.3.2
7.3.3 启动 Grafana 并设置开机自启
bash
运行
# 启动服务
systemctl start grafana-server
# 开机自启
systemctl enable grafana-server

# 验证状态
systemctl status grafana-server
7.3.4 Grafana 基础配置
访问 Grafana UI：http:// 主节点 IP:3000
初始账号 / 密码：admin/admin（首次登录需修改密码）
添加 Prometheus 数据源：
左侧菜单栏 → Configuration → Data sources → Add data source
选择 Prometheus
URL 填写：http://127.0.0.1:9090
点击 Save & test，提示 Success 即为成功
导入监控大屏模板：
左侧菜单栏 → Dashboards → Import
上传项目中 grafana/templates/monitor_dashboard.json 文件
选择已添加的 Prometheus 数据源，完成导入
8. Ansible 手动采集监控数据
bash
运行
# 进入Ansible脚本目录
cd ansible/playbooks

# 手动执行一次采集脚本
ansible-playbook collect_metrics.yml

# 配置定时采集（每分钟一次）
# 编辑crontab
crontab -e
# 添加以下内容
* * * * * cd /path/to/my-monitoring-app/ansible/playbooks && ansible-playbook collect_metrics.yml > /var/log/ansible_collect.log 2>&1

# 验证定时任务
crontab -l
9. 部署验证
9.1 服务状态验证
bash
运行
# 验证Prometheus
ps -ef | grep prometheus
curl http://127.0.0.1:9090/api/v1/label/job/values

# 验证Flask后端
ps -ef | grep gunicorn
curl http://127.0.0.1:5000/metrics | grep cpu_usage

# 验证Grafana
systemctl status grafana-server
9.2 可视化验证
访问 Grafana：http:// 主节点 IP:3000
进入导入的监控大屏，查看是否有 CPU / 内存 / 磁盘等指标数据
确认数据更新频率与采集间隔一致（15 秒）
9.3 告警测试（可选）
bash
运行
# 模拟被监控节点磁盘使用率超限（替换为实际被监控节点IP）
ssh root@192.168.1.101
# 创建大文件占用磁盘
dd if=/dev/zero of=/tmp/test_disk_full bs=1G count=10
在 Grafana 中查看告警面板，验证是否触发阈值告警，且 Webhook 能正常接收告警信息。
10. 常见问题排查
10.1 Ansible ping 失败
检查被监控节点 22 端口是否开放：telnet 被监控节点IP 22
检查公钥是否分发成功：ssh root@被监控节点IP "cat ~/.ssh/authorized_keys"
检查 Ansible 主机列表配置是否正确
10.2 Grafana 无数据
检查 Prometheus 数据源配置是否正确
检查 Flask metrics 接口是否有数据：curl http://127.0.0.1:5000/metrics
检查 Prometheus 采集规则是否包含 Flask 后端目标
10.3 Flask 服务启动失败
查看日志：cat /var/log/flask_backend.log
检查端口是否被占用：netstat -tulpn | grep 5000
检查 Python 依赖是否安装完整
11. 后续优化（待学习 Docker/K8s 后补充）
编写 Dockerfile，将各组件容器化
编写 docker-compose.yml 实现多容器编排
学习 K8s 后，编写 Deployment/Service 配置文件，实现集群部署
优化一键部署脚本，整合手动步骤