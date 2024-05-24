# -IMU- 

使用Selenium爬取内蒙古大学教务系统上的学生各科目成绩，包含课程名，课程属性，学分，成绩，绩点成绩。该工具可以部署在Windows和Linux操作系统上。

## 前置要求 

- 安装相同版本的`Chrome`和`ChromeDriver`
- 配置环境变量，或者在脚本中指定`ChromeDriver`路径。
- 安装一些Python依赖库。建议使用虚拟环境来管理依赖库，以避免与其他项目的冲突。
- 安装依赖库：pip install -r requirements.txt
- 运行爬虫脚本：python scraper.py