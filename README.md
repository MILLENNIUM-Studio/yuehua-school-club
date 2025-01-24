# Yuehua School Club

这是一个基于 Flask 的社团管理系统，允许用户注册、登录、加入社团、退出社团以及转让社团名额。管理员可以添加和删除用户以及管理社团。
WARNING：此不可用于生产环境，仅为比赛可用

## 功能

- 用户注册和登录
- 加入和退出社团
- 转让社团名额
- 管理员功能：添加和删除用户，管理社团
- 文件上传功能

## 安装

1. 克隆项目到本地：

   ```bash
   git clone https://gitee.com/millennium_x/yuehua-club_system.git
   cd yuehua-club_system
   ```

2. 创建并激活虚拟环境：

   ```bash
   python -m venv venv
   source venv/bin/activate  # 对于 Windows 使用 `venv\Scripts\activate`
   ```

3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

4. 设置数据库：

   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. 运行应用：

   ```bash
   flask run
   ```

## 使用说明

- 访问 `http://localhost:5000` 以使用应用。
- 注册新用户并登录。
- 加入或退出社团。
- 管理员可以通过 `/add_user` 和 `/delete_user` 路由管理用户。

## 配置

- 在 `app.py` 中配置数据库 URI 和其他应用设置。
- 确保在生产环境中使用强随机的 `SECRET_KEY`。

## 常见问题

### 如何更改数据库？

在 `app.py` 中修改 `SQLALCHEMY_DATABASE_URI` 为你所需的数据库 URI。

### 如何启用 HTTPS？

将 `SESSION_COOKIE_SECURE` 设置为 `True` 并在生产环境中使用 HTTPS。

### 如何限制社团成员数量？

每个社团的成员数量限制为 20 人，代码中已实现此功能。

## 贡献

欢迎贡献代码！请 fork 本项目并提交 pull request。

## 许可证
本项目采用 GPL 3.0 许可证。详情请参阅 LICENSE 文件。

Powered By MILLENNIUM Studio 
