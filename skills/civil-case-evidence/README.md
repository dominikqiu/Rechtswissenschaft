# Civil Case Evidence 1.0.0

中国民法案例分析 skill，基于游初的 gutachten-civil-case 独立改造。原作者版权、学术致谢及非背书声明完整保留于 [LICENSE](LICENSE)，来源及修改记录见 [NOTICE.md](NOTICE.md)。

将本目录整体复制至宿主支持的 skills 目录，读取 [SKILL.md](SKILL.md)。不要单独安装 references/upstream；该目录是完整原版存档，不是第二套活动指令。无需安装 Python 依赖；结构检查需要 Python 3.10+。法律检索、文档解析、Word 导出由宿主已有工具提供。

新版入口：SKILL.md → workflow.md → reasoning.md / knowledge.md → artifacts.md → report-template.md。默认自主执行，涉及结论的未知事实用条件分支或精确提问处理。

```sh
python3 scripts/validate_case.py /path/to/private-case/case.json
python3 scripts/validate_case.py /path/to/private-case/case.json --require-reviewed
python3 -m unittest discover -s tests -v
```

`examples/case-template.json` 是未填写模板；校验应失败。填入实际材料、检索及分析后再校验。测试仅验证记录完整性与状态约束，不验证法律正确性。不得把测试数据当作法律资料。

本版尚未用真实案件和外部法律数据库做端到端评测。建议由法律专业人员选取历史法律适用、事实缺失、竞合、相反判例四类案件，分别评估依据准确性、要件覆盖、涵摄质量与不确定性表达；记录误判后再修改规则。没有真实资料时不报告虚构准确率。
