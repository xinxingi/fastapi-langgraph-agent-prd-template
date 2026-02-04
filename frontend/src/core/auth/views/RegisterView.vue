<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="card-header">
          <h2>用户注册</h2>
        </div>
      </template>

      <!-- 错误提示 -->
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        :closable="true"
        @close="errorMessage = ''"
        style="margin-bottom: 20px"
        show-icon
      />

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        @submit.prevent
      >
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="form.email"
            type="email"
            placeholder="请输入邮箱"
            :disabled="loading"
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :disabled="loading"
            show-password
            @keyup.enter="handleRegister"
          />
          <div class="password-tips">
            <p>密码要求：</p>
            <ul>
              <li>至少8个字符</li>
              <li>至少包含一个大写字母</li>
              <li>至少包含一个小写字母</li>
              <li>至少包含一个数字</li>
              <li>至少包含一个特殊字符</li>
            </ul>
          </div>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            :disabled="loading"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click.prevent="handleRegister"
            style="width: 100%"
          >
            注册
          </el-button>
        </el-form-item>

        <el-form-item>
          <el-button
            text
            @click="goToLogin"
            style="width: 100%"
          >
            已有账号？去登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/core/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMessage = ref('')

const form = reactive({
  email: '',
  password: '',
  confirmPassword: '',
})

const validatePassword = (rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请输入密码'))
    return
  }
  
  if (value.length < 8) {
    callback(new Error('密码长度至少为8个字符'))
    return
  }
  
  if (!/[A-Z]/.test(value)) {
    callback(new Error('密码必须包含至少一个大写字母'))
    return
  }
  
  if (!/[a-z]/.test(value)) {
    callback(new Error('密码必须包含至少一个小写字母'))
    return
  }
  
  if (!/[0-9]/.test(value)) {
    callback(new Error('密码必须包含至少一个数字'))
    return
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
    callback(new Error('密码必须包含至少一个特殊字符'))
    return
  }
  
  callback()
}

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
    return
  }
  
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  
  callback()
}

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, validator: validatePassword, trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  if (!formRef.value) return

  // 清除之前的错误消息
  errorMessage.value = ''

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await authStore.register({
        email: form.email,
        password: form.password,
      })
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } catch (error: any) {
      console.error('Registration failed:', error)
      // 显示持久错误提示
      errorMessage.value = error.response?.data?.detail || error.message || '注册失败，请稍后重试'
    } finally {
      loading.value = false
    }
  })
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 100%;
  max-width: 500px;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  color: #303133;
}

.password-tips {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.password-tips p {
  margin: 0 0 4px 0;
}

.password-tips ul {
  margin: 0;
  padding-left: 20px;
}

.password-tips li {
  margin: 2px 0;
}
</style>
