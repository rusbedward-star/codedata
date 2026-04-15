<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>销售数据分析预测系统</h1>
        <h2>数据驱动，智能预测</h2>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="login-btn"
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>
      <div class="login-tip">
        <el-text type="info" size="small">管理员：admin / admin123 &nbsp;|&nbsp; 操作员：operator / op123456</el-text>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'

export default {
  name: 'LoginView',
  setup() {
    const store = useStore()
    const router = useRouter()
    const formRef = ref(null)
    const loading = ref(false)

    const form = reactive({ username: '', password: '' })
    const rules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
    }

    const handleLogin = async () => {
      if (!formRef.value) return
      try {
        await formRef.value.validate()
        loading.value = true
        const res = await login({ username: form.username, password: form.password })
        store.dispatch('login', { token: res.data.access, user: res.data.user })
        ElMessage.success(`欢迎回来，${res.data.user.full_name || res.data.user.username}！`)
        router.push('/dashboard')
      } catch (err) {
        if (err?.response?.data?.detail) {
          ElMessage.error(err.response.data.detail)
        } else if (typeof err !== 'object' || !err.fields) {
          // 表单验证错误不弹toast
        }
      } finally {
        loading.value = false
      }
    }

    return { formRef, form, rules, loading, handleLogin }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #001529 0%, #003a66 50%, #006ab5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-container {
  background: #fff;
  border-radius: 12px;
  padding: 48px 40px;
  width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.login-header {
  text-align: center;
  margin-bottom: 36px;
}
.login-header h1 {
  font-size: 22px;
  color: #1a1a1a;
  font-weight: 700;
  margin-bottom: 6px;
}
.login-header h2 {
  font-size: 15px;
  color: #555;
  font-weight: 500;
  margin-bottom: 8px;
}
.subtitle {
  font-size: 13px;
  color: #999;
}
.login-form {
  margin-bottom: 12px;
}
.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}
.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  letter-spacing: 2px;
}
.login-tip {
  text-align: center;
  margin-top: 16px;
}
</style>
