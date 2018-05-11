# 批量自动聚类&标签推荐
对题目推荐聚类，标签并写入数据库


## 相关文档

* [大搜索专项](http://doc.shensz.local/pages/viewpage.action?pageId=16812274)
* [批量聚类标签推荐研发设计](http://doc.shensz.local/pages/viewpage.action?pageId=16829245)


# 目录结构 
推荐                                 | 描述
------------                        | ------------
lib/dal/es_query_cluster.py         | 根据题目进行聚类推荐
lib/dal/es_query_tag.py             | 根据题目进行标签推荐

数据库操作                           | 描述
------------                        | ------------
lib/dal/dao/question.py             | 包括查询，插入等操作

运行                                | 描述
------------                        | ------------
bin/label_chapter_info.py           | 标签推荐：数据库获取题目，解析推荐结果，写入数据库solution_tag
bin/label_cluster_info.py           | 聚类推荐：数据库获取题目，解析推荐结果，写入数据库solution_cluster_similar

# 运行方法    
crontab

