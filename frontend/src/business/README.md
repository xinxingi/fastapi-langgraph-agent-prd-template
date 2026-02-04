# Business 业务层目录

此目录用于存放具体的业务功能模块。

## 目录组织原则

- **core/** - 框架层核心功能（认证、API 客户端、配置等）
- **business/** - 业务层特定功能（此目录）

## 重要说明

**登录、注册、Token 管理是框架核心功能**，位于 `core/auth` 目录，而不在这里。

`business/` 目录用于存放具体业务模块，例如：
- 聊天机器人 (`business/chatbot`)
- HR 入职流程 (`business/hr_onboarding`)
- 订单管理 (`business/orders`)
- 等等...

## 创建新业务模块示例

假设要创建一个聊天机器人模块：

```
business/chatbot/
├── views/              # 页面组件
│   └── ChatView.vue
├── components/         # 业务组件
│   ├── ChatMessage.vue
│   └── ChatInput.vue
├── composables/        # 业务逻辑
│   └── useChat.ts
├── types.ts           # 模块类型定义
└── service.ts         # 业务服务
```

### 示例代码结构

```typescript
// business/chatbot/service.ts
import axios from '@/core/api/client'

export class ChatService {
  async sendMessage(message: string) {
    const response = await axios.post('/api/v1/chat', { message })
    return response.data
  }
}

export const chatService = new ChatService()
```

```typescript
// business/chatbot/composables/useChat.ts
import { ref } from 'vue'
import { chatService } from '../service'

export function useChat() {
  const messages = ref([])
  const loading = ref(false)

  const sendMessage = async (text: string) => {
    loading.value = true
    try {
      const response = await chatService.sendMessage(text)
      messages.value.push(response)
    } finally {
      loading.value = false
    }
  }

  return { messages, loading, sendMessage }
}
```

## 与 core 的关系

- 业务模块可以自由使用 `core/` 中的功能
- 业务模块之间应保持独立，避免相互依赖
- 复用 `core/auth` 中的认证功能
- 复用 `core/api/client` 进行 HTTP 请求

## 路由配置

在 `src/router/index.ts` 中添加业务模块路由：

```typescript
import ChatView from '@/business/chatbot/views/ChatView.vue'

const router = createRouter({
  routes: [
    // ... 现有路由
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
      meta: { requiresAuth: true },
    },
  ],
})
```

## 参考后端结构

前端 `business/` 目录对应后端的 `app/business/` 目录：

```
后端: app/business/chatbot/
前端: src/business/chatbot/

后端: app/business/hr_onboarding_verification/
前端: src/business/hr_onboarding/
```

保持前后端业务模块的一致性。
