<template>
  <div class="users-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" icon="Plus" @click="openAddDialog">新增用户</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="filter" class="filter-form">
        <el-form-item>
          <el-input v-model="filter.keyword" placeholder="用户名/姓名" clearable prefix-icon="Search" style="width:180px" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item>
          <el-select v-model="filter.role" placeholder="角色" clearable style="width:120px">
            <el-option label="管理员" value="admin" />
            <el-option label="操作员" value="operator" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="loadData">查询</el-button>
          <el-button icon="Refresh" @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 用户表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="130" />
        <el-table-column prop="full_name" label="姓名" width="110" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
              {{ row.role_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" text @click="openEditDialog(row)">编辑</el-button>
            <el-button
              :type="row.is_active ? 'warning' : 'success'"
              size="small" text
              @click="handleToggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editMode ? '编辑用户' : '新增用户'" width="480px">
      <el-form ref="dialogFormRef" :model="dialogForm" :rules="dialogRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="dialogForm.username" :disabled="editMode" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="dialogForm.full_name" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="dialogForm.email" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="dialogForm.role" style="width:100%">
            <el-option label="管理员" value="admin" />
            <el-option label="操作员" value="operator" />
          </el-select>
        </el-form-item>
        <el-form-item :label="editMode ? '新密码' : '密码'" :prop="editMode ? '' : 'password'">
          <el-input v-model="dialogForm.password" type="password" show-password :placeholder="editMode ? '不修改留空' : '至少6位'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, createUser, updateUser } from '@/api/users'

export default {
  name: 'UserManagement',
  setup() {
    const loading = ref(false)
    const tableData = ref([])
    const filter = reactive({ keyword: '', role: '' })
    const dialogVisible = ref(false)
    const editMode = ref(false)
    const editId = ref(null)
    const dialogFormRef = ref(null)
    const submitLoading = ref(false)
    const dialogForm = reactive({ username: '', full_name: '', email: '', role: 'operator', password: '' })

    const dialogRules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      full_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
      role: [{ required: true, message: '请选择角色', trigger: 'change' }],
      password: [{ required: true, message: '请输入密码', min: 6, trigger: 'blur' }],
    }

    const loadData = async () => {
      loading.value = true
      try {
        const res = await getUsers(filter)
        tableData.value = res.data.results || res.data
      } finally {
        loading.value = false
      }
    }

    const resetFilter = () => {
      filter.keyword = ''
      filter.role = ''
      loadData()
    }

    const openAddDialog = () => {
      editMode.value = false
      editId.value = null
      Object.assign(dialogForm, { username: '', full_name: '', email: '', role: 'operator', password: '' })
      dialogVisible.value = true
    }

    const openEditDialog = (row) => {
      editMode.value = true
      editId.value = row.id
      Object.assign(dialogForm, { username: row.username, full_name: row.full_name, email: row.email, role: row.role, password: '' })
      dialogVisible.value = true
    }

    const handleSubmit = async () => {
      await dialogFormRef.value.validate()
      submitLoading.value = true
      const data = { ...dialogForm }
      if (editMode.value && !data.password) delete data.password
      try {
        if (editMode.value) {
          await updateUser(editId.value, data)
          ElMessage.success('用户更新成功')
        } else {
          await createUser(data)
          ElMessage.success('用户创建成功')
        }
        dialogVisible.value = false
        loadData()
      } finally {
        submitLoading.value = false
      }
    }

    const handleToggleActive = async (row) => {
      const action = row.is_active ? '禁用' : '启用'
      await ElMessageBox.confirm(`确定${action}用户 ${row.username} 吗？`, '确认', { type: 'warning' })
      await updateUser(row.id, { is_active: !row.is_active })
      ElMessage.success(`${action}成功`)
      loadData()
    }

    onMounted(loadData)

    return {
      loading, tableData, filter, dialogVisible, editMode, dialogFormRef,
      submitLoading, dialogForm, dialogRules,
      loadData, resetFilter, openAddDialog, openEditDialog, handleSubmit, handleToggleActive
    }
  }
}
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-form { margin-bottom: 12px; }
</style>
