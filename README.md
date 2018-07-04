# 批量自动聚类&标签推荐
对题目推荐聚类，标签并写入数据库

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
app.py                              | 批量自动聚类&标签推荐
test.py          | 测试新模型，统计准确率、召回率

# 运行方法    
crontab

```bash
30 00 * * * source ~/.bash_profile; cd /data/app/yqss/shensz/tag_cluster_recommend/ && python app.py 2>&1 > /dev/null
```