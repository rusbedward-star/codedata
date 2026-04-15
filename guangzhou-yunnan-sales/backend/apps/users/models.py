from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('用户名不能为空')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('operator', '操作员'),
    ]

    username = models.CharField('用户名', max_length=150, unique=True)
    full_name = models.CharField('姓名', max_length=50, blank=True, default='')
    email = models.EmailField('邮箱', blank=True, default='')
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='operator')
    is_active = models.BooleanField('启用', default=True)
    is_staff = models.BooleanField('后台权限', default=False)
    date_joined = models.DateTimeField('注册时间', default=timezone.now)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users_customuser'
        verbose_name = '用户'
        verbose_name_plural = '用户管理'

    def __str__(self):
        return f'{self.username}({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == 'admin'
