"""
yunnan_backend/__init__.py
"""
# import pymysql
# pymysql.install_as_MySQLdb()
import pymysql

# 1. 让 PyMySQL 伪装成 MySQLdb
pymysql.install_as_MySQLdb()

# 2. 手动修改版本号，欺骗 Django 的版本校验机制
pymysql.version_info = (2, 2, 8, 'final', 0)