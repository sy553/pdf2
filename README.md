# PDF工具箱

一个功能强大的PDF处理工具，提供多种PDF处理功能。

## 功能特点

- 水印处理（添加/移除）
- PDF压缩
- 格式转换（PDF转图/图片转PDF）
- 页面管理（分割/合并/重排序）
- 安全管理（加密/解密/页码添加）

## 安装要求

- Python 3.8 或更高版本
- Windows 操作系统
- 必要的依赖库（见 requirements.txt）

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/pdf-toolbox.git
cd pdf-toolbox
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 安装项目：
```bash
pip install -e .
```

## 使用方法

1. 启动应用：
```bash
pdf-toolbox
```

2. 使用界面进行操作：
   - 选择需要的功能
   - 选择输入文件
   - 设置相关参数
   - 执行操作

## 开发指南

1. 运行测试：
```bash
pytest
```

2. 查看测试覆盖率报告：
```bash
pytest --cov=src --cov-report=html
```

## 版本历史

- v1.0.0 (2024-01)
  - 初始版本
  - 实现基本功能

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 作者

- OpenAI

## 致谢

感谢所有为本项目做出贡献的开发者。 