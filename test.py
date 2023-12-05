import unittest
from watchlist import app, db
from watchlist.models import User, Movie
from watchlist.commands import initdb, forge


class TestCase(unittest.TestCase):
    # 测试方法执行前被调用
    def setUp(self):
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'    # SQLite 内存型数据库，不会干扰开发时使用的数据库文件
        )
        with app.app_context():
            db.create_all()
            user = User(name='Test', username='test')
            user.set_password('123')
            movie = Movie(title='Test Movie Title', year='2019')
            db.session.add_all([user, movie])
            db.session.commit()

        self.client = app.test_client()     # 创建测试客户端
        self.runner = app.test_cli_runner() # 创建测试命令运行器

    # 测试方法执行后被调用
    def tearDown(self):
        with app.app_context():
            db.session.remove() # 清除数据库会话
            db.drop_all()       # 删除数据库表

    # 测试程序实例是否存在
    def test_app_exist(self):
        self.assertIsNotNone(app)

    # 测试程序是否处于测试模式
    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    # 测试 404 页面
    def test_404_page(self):
        response = self.client.get('/nothing')
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('Go Back', data)
        self.assertEqual(response.status_code, 404)

    # 测试主页
    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test\'s Watchlist', data)
        self.assertIn('Test Movie Title', data)
        self.assertEqual(response.status_code, 200)

    # 登录
    def login(self):
        self.client.post('/login', data=dict(username='test', password='123'), follow_redirects=True)

    # 测试创建
    def test_create(self):
        self.login()

        response = self.client.post('/', data=dict(title='New Movie', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item created.', data)
        self.assertIn('New Movie', data)

        response = self.client.post('/', data=dict(title='', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)

        response = self.client.post('/', data=dict(title='New Movie', year=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)

    # 测试更新
    def test_update(self):
        self.login()

        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('Edit item', data)
        self.assertIn('Test Movie Title', data)
        self.assertIn('2019', data)

        response = self.client.post('/movie/edit/1', data=dict(title='New Movie Edited', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item updated.', data)
        self.assertIn('New Movie Edited', data)

        response = self.client.post('/movie/edit/1', data=dict(title='', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertIn('Invalid input.', data)

        response = self.client.post('/movie/edit/1', data=dict(title='New Movie Edited', year=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertIn('Invalid input.', data)

    # 测试删除
    def test_delete(self):
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item deleted.', data)
        self.assertNotIn('Test Movie Title', data)

    # 测试登录保护
    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('<form method="post">', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)

    # 测试登录
    def test_login(self):
        response = self.client.post('/login', data=dict(username='test', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)
        self.assertIn('Logout', data)
        self.assertIn('Settings', data)
        self.assertIn('Delete', data)
        self.assertIn('Edit', data)
        self.assertIn('<form method="post">', data)

        # 密码错误
        response = self.client.post('/login', data=dict(username='test', password='456'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 用户名错误
        response = self.client.post('/login', data=dict(username='wrong', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 空用户
        response = self.client.post('/login', data=dict(username='', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

        # 空密码
        response = self.client.post('/login', data=dict(username='test', password=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

    # 测试登出
    def test_logout(self):
        self.login()

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Goodbye.', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('<form method="post">', data)

    # 测试设置
    def test_settings(self):
        self.login()

        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('Settings', data)
        self.assertIn('Your Name', data)

        response = self.client.post('/settings', data=dict(name='Grey Li'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Settings updated.', data)
        self.assertIn('Grey Li', data)

        response = self.client.post('/settings', data=dict(name=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Settings updated.', data)
        self.assertIn('Invalid input.', data)

    # 测试虚拟数据
    def test_forge(self):
        with app.app_context():
            result = self.runner.invoke(forge)
            self.assertIn('Done.', result.output)
            self.assertNotEqual(Movie.query.count(), 0)

    # 测试初始化数据库
    def test_initdb(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    # 测试生成管理员账户
    def test_admin(self):
        with app.app_context():
            db.drop_all()
            db.create_all()
            result = self.runner.invoke(args=['admin', '--username', 'grey', '--password', '123'])
            self.assertIn('Creating user', result.output)
            self.assertIn('Done.', result.output)
            self.assertEqual(User.query.count(), 1)
            self.assertEqual(User.query.first().username, 'grey')
            self.assertTrue(User.query.first().check_password('123'))

    # 测试更新管理员账户
    def test_admin_update(self):
        with app.app_context():
            result = self.runner.invoke(args=['admin', '--username', 'peter', '--password', '456'])
            self.assertIn('Updating user', result.output)
            self.assertIn('Done.', result.output)
            self.assertEqual(User.query.count(), 1)
            self.assertEqual(User.query.first().username, 'peter')
            self.assertTrue(User.query.first().check_password('456'))


if __name__ == '__main__':
    unittest.main()
