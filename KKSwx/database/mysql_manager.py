import pymysql
from sympy import N, false
from database.Base_database.manager import Manager
import datetime
class MYSQL_Manage(Manager):
    def __init__(
            self, 
            username: str, 
            passwords: str,
            database_name: str,
            port: int = 3306,
            table_name:str = 'rag',
            host:str = 'localhost'
        ):
        self.username = username
        self.passwords = passwords
        self.database_name = database_name
        self.port = port
        self.host = host
        self.table_name = table_name
        self.client = self.init_database()
        if self.init_table() == false:
            print(f"注意目前没有{self.table_name},请使用init_table,投入数据进行初始化")

    def init_table(self, data = []):
        with self.client.cursor() as cursor:
            try:
                sql = f"SELECT * from {self.table_name} limit 1"
                cursor.execute(sql)
                return True
            except pymysql.MySQLError as e:
                # user_input = input(f"表{self.table_name}不存在，是否创建？(Y/N): ").strip().upper()
                # if user_input == "Y":
                    try:
                        with self.client.cursor() as cursor:
                            dynamic_fields = []
                            for col in data:
                                dynamic_fields.append(col + ' '+self.transform_type(type(data[col])))
                            
                            
                            create_database_sql = f"""CREATE TABLE IF NOT EXISTS `{self.table_name}`(`id` INT AUTO_INCREMENT PRIMARY KEY,{', '.join(dynamic_fields)},confirmed INT)"""
                            cursor.execute(create_database_sql)
                            self.client.commit()
                            # cursor.execute(create_database_sql)
                            print(f"数据库 '{self.table_name}' 创建成功。")
                    except pymysql.MySQLError as e:
                        return false
                # elif user_input == "N":
                #     print("不创建数据库，数据库取消")
                #     return None
                # else:
                #     print("无效的输入，请输入 Y 或 N。")
                #     return None


    def init_database(self):
        try:
            connection =  pymysql.connect(
                            host=self.host,      # 数据库主机地址
                            user=self.username,  # 数据库用户名
                            password=self.passwords,  # 数据库密码
                            charset='utf8mb4',     # 字符编码
                            port = self.port,
                            cursorclass=pymysql.cursors.DictCursor  # 返回字典形式的结果
                        )
        except Exception as e:
            print(e)
        with connection.cursor() as cursor:
            # 查询数据库是否存在
            sql = f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{self.database_name}'"
            cursor.execute(sql)
            result = cursor.fetchone()
            if result:
                pass
            else:
                # print(f"数据库 '{self.database_name}' 不存在")
                # user_input = input("是否创建？(Y/N): ").strip().upper()
                # if user_input == "Y":
                    try:
                        with connection.cursor() as cursor:
                            create_database_sql = f"CREATE DATABASE IF NOT EXISTS `{self.database_name}`"
                            cursor.execute(create_database_sql)
                            print(f"数据库 '{self.database_name}' 创建成功。")
                    except pymysql.MySQLError as e:
                        print(f"数据库创建失败：{e}")
                # elif user_input == "N":
                #     print("不创建数据库，数据库取消")
                #     return None
                # else:
                #     print("无效的输入，请输入 Y 或 N。")
                #     return None
            return pymysql.connect(
                            host=self.host,      # 数据库主机地址
                            user=self.username,  # 数据库用户名
                            password=self.passwords,  # 数据库密码
                            database=self.database_name,  # 数据库名
                            charset='utf8mb4',     # 字符编码
                            port = self.port,
                            cursorclass=pymysql.cursors.DictCursor  # 返回字典形式的结果
                        )


    def Insert_database(self, data):
        tablename = self.table_name
        if self.init_table(data=data[0]) == False:
            raise ValueError('建表失败')
        try:
            with self.client.cursor() as cursor:
            #动态插入，识别队列第一个作为标准
                columns = list(data[0].keys())
                columns.append('confirmed')
                placeholders = ', '.join(['%s'] * len(columns))
                sql =f"INSERT INTO {tablename} ({', '.join(columns)}) VALUES ({placeholders})"
                values = []
                for record in data:
                    value = []
                    for k,v in record.items():
                        if isinstance(v,list):
                            value.append(str(v))
                        else:
                            value.append(v)
                    values.append(tuple(value)+(0,))
                # values = [tuple(item.values())+(0,) for item in data]

                cursor.executemany(sql, values)
                self.client.commit()
        except Exception as e:
            self.client.rollback()
            print(f"插入失败: {e}")
        finally:
            self.client.close()


    def get_unconfirmed_info(self):
        tablename = self.table_name
        try:
            with self.client.cursor() as cursor:
                # 查询多条记录
                sql = f"SELECT * FROM {tablename} WHERE confirmed = 0"
                cursor.execute(sql)
                results = cursor.fetchall()  # 获取所有记录
                
                print(f"共找到 {len(results)} 条记录:")
                for row in results:
                    print(row) 
                    
        finally:
            self.client.close()

    def transform_type(self, python_type):
        type_mapping = {
        int: "INT",
        float: "FLOAT",
        str: "TEXT",
        bool: "TINYINT(1)",
        bytes: "BLOB",
        datetime.datetime: "DATETIME",
        datetime.date: "DATE",
        datetime.time: "TIME",
        list:"TEXT"
    }
            
        mysql_type = type_mapping.get(python_type)

        if mysql_type is None:
            raise ValueError(f"No corresponding MySQL type for Python type: {python_type}")
        return mysql_type

    def delete_table(self):
            try:
                cursor = self.client.cursor()
                
                # 使用反引号包围表名，避免表名是MySQL关键字时出错
                sql = f"DROP TABLE IF EXISTS `{self.table_name}`"
                
                cursor.execute(sql)
                self.client.commit()
                print(f"表 {self.table_name} 删除成功")
                
            except Exception as e:
                print(f"删除表时出错: {e}")
                self.client.rollback()
            finally:
                cursor.close()
    

    def query_database(self, limit = 10, query = None):
        if query == None:
            query = f"SELECT * FROM {self.table_name} limit {limit}"
        try:
            cursor = self.client.cursor()
            cursor.execute(query)
            
            # 获取所有结果
            results = cursor.fetchall()
            
            # 获取列名
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
            else:
                columns = []
            
            # 将结果转换为字典列表
            result_list = []
            for row in results:
                result_list.append(row)
                
            return result_list
            
        except Exception as e:
            print(f"查询数据库时出错: {e}")
            return None
        finally:
            cursor.close()