# 激活虚拟环境
source venv/bin/activate

# 本地

* 爬取文档
python creeper.py inputs/本地/香港地区.md

* 解析文档
python parser.py --input-folder ./outputs/香港地区/香港大埔突发大火 --output-folder ./parsers/香港地区 --template parser/local_parser


# 编程

* 爬取文档
python creeper.py inputs/编程/Calude.md

* 解析文档
python parser.py --input-folder ./outputs/claude使用文档/个人文章 --output-folder ./parsers/claude使用文档 --template parser/doc_parser