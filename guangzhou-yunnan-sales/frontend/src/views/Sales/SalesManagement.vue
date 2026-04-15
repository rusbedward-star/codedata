<template>
  <div class="sales-page">
    <!-- 搜索筛选 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="filter" class="filter-form">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item label="产品">
          <el-select v-model="filter.product_id" placeholder="全部产品" clearable style="width:160px">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="区域">
          <el-select v-model="filter.region_id" placeholder="全部区域" clearable style="width:160px">
            <el-option v-for="r in regions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="渠道">
          <el-select v-model="filter.channel" placeholder="全部渠道" clearable style="width:130px">
            <el-option label="线上电商" value="online" />
            <el-option label="线下门店" value="offline" />
            <el-option label="经销商" value="distributor" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="loadData">查询</el-button>
          <el-button icon="Refresh" @click="resetFilter">重置</el-button>
          <el-button type="success" icon="Download" @click="handleExport">导出CSV</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span>销售记录列表</span>
          <el-button v-if="isAdmin" type="primary" size="small" icon="Plus" @click="openAddDialog">新增记录</el-button>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" stripe border style="width:100%">
        <el-table-column prop="sale_date" label="销售日期" width="110" />
        <el-table-column prop="product_name" label="产品名称" min-width="160" />
        <el-table-column prop="region_name" label="区域" width="130" />
        <el-table-column prop="channel_display" label="渠道" width="100">
          <template #default="{ row }">
            <el-tag :type="channelTagType(row.channel)" size="small">{{ row.channel_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量(支)" width="100" align="right" />
        <el-table-column prop="unit_price" label="单价(元)" width="90" align="right" />
        <el-table-column prop="total_amount" label="金额(元)" width="120" align="right">
          <template #default="{ row }">{{ Number(row.total_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作员" width="90" />
        <el-table-column label="操作" width="120" v-if="isAdmin" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" text @click="openEditDialog(row)">编辑</el-button>
            <el-button type="danger" size="small" text @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        class="pagination"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadData"
        @size-change="loadData"
      />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editMode ? '编辑销售记录' : '新增销售记录'" width="560px">
      <el-form ref="dialogFormRef" :model="dialogForm" :rules="dialogRules" label-width="90px">
        <el-form-item label="销售日期" prop="sale_date">
          <el-date-picker v-model="dialogForm.sale_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="产品" prop="product">
          <el-select v-model="dialogForm.product" style="width:100%">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="区域" prop="region">
          <el-select v-model="dialogForm.region" style="width:100%">
            <el-option v-for="r in regions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="渠道" prop="channel">
          <el-select v-model="dialogForm.channel" style="width:100%">
            <el-option label="线上电商" value="online" />
            <el-option label="线下门店" value="offline" />
            <el-option label="经销商" value="distributor" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量(支)" prop="quantity">
          <el-input-number v-model="dialogForm.quantity" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="单价(元)" prop="unit_price">
          <el-input-number v-model="dialogForm.unit_price" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="dialogForm.remark" type="textarea" :rows="2" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSales, createSale, updateSale, deleteSale, exportSales, getProducts, getRegions } from '@/api/sales'

export default {
  name: 'SalesManagement',
  setup() {
    const store = useStore()
    const isAdmin = computed(() => store.getters.isAdmin)
    const loading = ref(false)
    const tableData = ref([])
    const total = ref(0)
    const page = ref(1)
    const pageSize = ref(20)
    const products = ref([])
    const regions = ref([])
    const dateRange = ref(null)

    const filter = reactive({ product_id: '', region_id: '', channel: '' })

    const dialogVisible = ref(false)
    const editMode = ref(false)
    const editId = ref(null)
    const dialogFormRef = ref(null)
    const submitLoading = ref(false)

    const dialogForm = reactive({
      sale_date: '', product: '', region: '', channel: 'offline',
      quantity: 100, unit_price: 28.80, remark: ''
    })
    const dialogRules = {
      sale_date: [{ required: true, message: '请选择日期' }],
      product: [{ required: true, message: '请选择产品' }],
      region: [{ required: true, message: '请选择区域' }],
      channel: [{ required: true, message: '请选择渠道' }],
      quantity: [{ required: true, message: '请输入数量' }],
      unit_price: [{ required: true, message: '请输入单价' }],
    }

    const channelTagType = (ch) => ({ online: 'primary', offline: '', distributor: 'warning' }[ch] || '')

    const loadData = async () => {
      loading.value = true
      const params = {
        page: page.value,
        page_size: pageSize.value,
        ...filter,
      }
      if (dateRange.value) {
        params.date_start = dateRange.value[0]
        params.date_end = dateRange.value[1]
      }
      try {
        const res = await getSales(params)
        tableData.value = res.data.results || res.data
        total.value = res.data.count || (res.data.results ? res.data.count : res.data.length)
      } finally {
        loading.value = false
      }
    }

    const resetFilter = () => {
      filter.product_id = ''
      filter.region_id = ''
      filter.channel = ''
      dateRange.value = null
      page.value = 1
      loadData()
    }

    const handleExport = async () => {
      const params = { ...filter }
      if (dateRange.value) {
        params.date_start = dateRange.value[0]
        params.date_end = dateRange.value[1]
      }
      const res = await exportSales(params)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'sales_data.csv'
      a.click()
      URL.revokeObjectURL(url)
    }

    const openAddDialog = () => {
      editMode.value = false
      editId.value = null
      Object.assign(dialogForm, { sale_date: '', product: '', region: '', channel: 'offline', quantity: 100, unit_price: 28.80, remark: '' })
      dialogVisible.value = true
    }

    const openEditDialog = (row) => {
      editMode.value = true
      editId.value = row.id
      Object.assign(dialogForm, {
        sale_date: row.sale_date, product: row.product, region: row.region,
        channel: row.channel, quantity: row.quantity,
        unit_price: parseFloat(row.unit_price), remark: row.remark
      })
      dialogVisible.value = true
    }

    const handleSubmit = async () => {
      await dialogFormRef.value.validate()
      submitLoading.value = true
      try {
        if (editMode.value) {
          await updateSale(editId.value, dialogForm)
          ElMessage.success('更新成功')
        } else {
          await createSale(dialogForm)
          ElMessage.success('新增成功')
        }
        dialogVisible.value = false
        loadData()
      } catch (e) {
        const detail = e.response?.data?.detail
        const errors = e.response?.data
        ElMessage.error(
          detail ||
          (typeof errors === 'object' ? JSON.stringify(errors) : '提交失败')
        )
      } finally {
        submitLoading.value = false
      }
    }

    const handleDelete = async (row) => {
      await ElMessageBox.confirm(`确定删除 ${row.product_name} 的销售记录吗？`, '警告', { type: 'warning' })
      await deleteSale(row.id)
      ElMessage.success('删除成功')
      loadData()
    }

    onMounted(async () => {
      const [pRes, rRes] = await Promise.all([getProducts(), getRegions()])
      products.value = pRes.data
      regions.value = rRes.data
      loadData()
    })

    return {
      isAdmin, loading, tableData, total, page, pageSize, products, regions, dateRange, filter,
      dialogVisible, editMode, dialogFormRef, submitLoading, dialogForm, dialogRules,
      channelTagType, loadData, resetFilter, handleExport,
      openAddDialog, openEditDialog, handleSubmit, handleDelete
    }
  }
}
</script>

<style scoped>
.filter-card { margin-bottom: 16px; }
.filter-form { display: flex; flex-wrap: wrap; gap: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.table-card { }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
