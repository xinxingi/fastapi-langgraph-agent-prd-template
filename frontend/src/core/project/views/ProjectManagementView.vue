<template>
  <main-layout>
    <div class="project-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>项目管理</span>
          <el-button type="primary" @click="handleCreate">创建项目</el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filter-section">
        <el-radio-group v-model="activeFilter" @change="handleFilterChange">
          <el-radio-button :label="undefined">全部</el-radio-button>
          <el-radio-button :label="true">激活</el-radio-button>
          <el-radio-button :label="false">未激活</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 项目列表 -->
      <el-table :data="projectStore.projects" v-loading="projectStore.loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目名称" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '激活' : '未激活' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="info" @click="handleManageApiKeys(row)">
              API Key 权限
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-section">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="projectStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑项目对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑项目' : '创建项目'"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item v-if="isEditing" label="状态" prop="is_active">
          <el-switch v-model="formData.is_active" active-text="激活" inactive-text="未激活" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="projectStore.loading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- API Key 权限管理对话框 -->
    <api-key-projects-dialog
      v-model="apiKeyDialogVisible"
      :project="selectedProject"
      @updated="handleProjectsUpdated"
    />
  </div>
  </main-layout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useProjectStore } from '@/core/project/store'
import type { ProjectResponse, ProjectCreate, ProjectUpdate } from '@/core/types/project'
import { format } from 'date-fns'
import ApiKeyProjectsDialog from '../components/ApiKeyProjectsDialog.vue'
import MainLayout from '@/layouts/MainLayout.vue'

const projectStore = useProjectStore()

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const activeFilter = ref<boolean | undefined>(undefined)

// 对话框
const dialogVisible = ref(false)
const isEditing = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive<ProjectCreate & ProjectUpdate & { id?: number }>({
  name: '',
  description: '',
  is_active: true,
})

// API Key 权限对话框
const apiKeyDialogVisible = ref(false)
const selectedProject = ref<ProjectResponse | null>(null)

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度在 1 到 100 个字符', trigger: 'blur' },
  ],
  description: [{ max: 500, message: '描述长度不能超过 500 个字符', trigger: 'blur' }],
}

// 生命周期
onMounted(() => {
  loadProjects()
})

// 加载项目列表
async function loadProjects() {
  await projectStore.loadProjects({
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value,
    is_active: activeFilter.value,
  })
}

// 格式化日期
function formatDate(dateString: string) {
  return format(new Date(dateString), 'yyyy-MM-dd HH:mm:ss')
}

// 筛选变更
function handleFilterChange() {
  currentPage.value = 1
  loadProjects()
}

// 分页变更
function handlePageChange() {
  loadProjects()
}

function handlePageSizeChange() {
  currentPage.value = 1
  loadProjects()
}

// 创建项目
function handleCreate() {
  isEditing.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑项目
function handleEdit(project: ProjectResponse) {
  isEditing.value = true
  formData.id = project.id
  formData.name = project.name
  formData.description = project.description || ''
  formData.is_active = project.is_active
  dialogVisible.value = true
}

// 删除项目
async function handleDelete(project: ProjectResponse) {
  try {
    await ElMessageBox.confirm(`确定要删除项目 "${project.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await projectStore.deleteProject(project.id)
  } catch (error) {
    // 用户取消操作
  }
}

// 管理 API Key 权限
function handleManageApiKeys(project: ProjectResponse) {
  selectedProject.value = project
  apiKeyDialogVisible.value = true
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      if (isEditing.value && formData.id) {
        await projectStore.updateProject(formData.id, {
          name: formData.name,
          description: formData.description || null,
          is_active: formData.is_active,
        })
      } else {
        await projectStore.createProject({
          name: formData.name,
          description: formData.description || undefined,
        })
      }
      dialogVisible.value = false
      loadProjects()
    } catch (error) {
      // 错误已在 store 中处理
    }
  })
}

// 关闭对话框
function handleDialogClose() {
  resetForm()
}

// 重置表单
function resetForm() {
  formData.id = undefined
  formData.name = ''
  formData.description = ''
  formData.is_active = true
  formRef.value?.clearValidate()
}

// 项目更新回调
function handleProjectsUpdated() {
  loadProjects()
}
</script>

<style scoped>
.project-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-section {
  margin-bottom: 20px;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
