<template>
  <el-container class="app-layout">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
<span class="logo-text">销售数据分析预测系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#001529"
        text-color="#b0b9c7"
        active-text-color="#fff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>数据概览</span>
        </el-menu-item>
        <el-menu-item index="/sales">
          <el-icon><Document /></el-icon>
          <span>销售数据管理</span>
        </el-menu-item>
        <el-menu-item index="/visualization">
          <el-icon><PieChart /></el-icon>
          <span>数据可视化</span>
        </el-menu-item>
        <el-menu-item index="/prediction">
          <el-icon><TrendCharts /></el-icon>
          <span>销量预测</span>
        </el-menu-item>
        <el-menu-item index="/users" v-if="isAdmin">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <span class="page-title">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <el-tag :type="isAdmin ? 'danger' : 'primary'" size="small" class="role-tag">
            {{ isAdmin ? '管理员' : '操作员' }}
          </el-tag>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><Avatar /></el-icon>
              {{ userName }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主体内容 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'AppLayout',
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()

    const isAdmin = computed(() => store.getters.isAdmin)
    const userName = computed(() => store.getters.userName)
    const activeMenu = computed(() => route.path)
    const currentTitle = computed(() => route.meta?.title || '数据概览')

    const handleCommand = async (cmd) => {
      if (cmd === 'logout') {
        try {
          await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          })
          store.dispatch('logout')
          router.push('/login')
          ElMessage.success('已退出登录')
        } catch (_) {
          // 用户取消
        }
      }
    }

    return { isAdmin, userName, activeMenu, currentTitle, handleCommand }
  }
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
}
.sidebar {
  background-color: #001529;
  overflow-y: auto;
  overflow-x: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #0d2137;
}
.logo-text {
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 1px;
}
.el-menu {
  border-right: none;
}
.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 24px;
  height: 60px;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}
.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.role-tag {
  cursor: default;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #595959;
  font-size: 14px;
}
.user-info:hover {
  color: #409eff;
}
.main-content {
  background-color: #f0f2f5;
  overflow-y: auto;
  padding: 20px;
}
</style>
