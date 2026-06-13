<template>
  <nav class="navbar">

    <div class="nav-section">
      <div class="menu-container" @click="toggleLeftDrawer">
        <button class="menu-btn">
          <img src="@/assets/images/菜单.png" alt="菜单" class="menu-img">
        </button>
      </div>
    </div>

    <!--左侧滑出抽屉-->
    <div class="left-drawer-overlay" v-show="showLeftDrawer" @click="showLeftDrawer = false"></div>
    <div class="left-drawer" :class="{ open: showLeftDrawer }">
      <div class="drawer-header">
        <span class="drawer-title">菜单</span>
        <button class="drawer-close-btn" @click="showLeftDrawer = false">×</button>
      </div>
      <div class="drawer-content">
        <router-link to="/status" class="drawer-item" @click="showLeftDrawer = false">商品状态</router-link>
        <router-link to="/ip" class="drawer-item" @click="showLeftDrawer = false">IP</router-link>
        <router-link to="/role" class="drawer-item" @click="showLeftDrawer = false">角色</router-link>
        <router-link to="/brand" class="drawer-item" @click="showLeftDrawer = false">品牌</router-link>
      </div>
    </div>

    <div class="logo">
      <a href="/">
        <img src="@/assets/images/次元模仓.png" alt="次元模仓" class="logo-img">
      </a>
    </div>

    <!--导航链接-->
    <div class="nav-links">
      <router-link to="/">首页</router-link>
      <router-link to="/goods">商品列表</router-link>

      <template v-if="isLoggedIn && userRole === 'merchant'">
        <router-link to="/publish" class="nav-user-text">上架商品</router-link>
      </template>
      <template v-else>
        <router-link to="/cart">购物车</router-link>
      </template>

      <!--消息通知-->
      <div 
        v-if="isLoggedIn && userRole !== 'merchant' && userRole !== 'admin'" 
        class="notification-text-wrapper"
      >
        <span class="nav-notification-text" @click="toggleNotificationPanel">消息通知</span>
        <span v-if="unreadCount > 0" class="nav-notification-badge">
          {{ unreadCount > 99 ? '99+' : unreadCount }}
        </span>
        <!--通知下拉面板-->
        <div class="nav-notification-panel" v-show="showNotificationPanel" @click.stop>
          <div class="panel-header">
            <span class="panel-title">消息通知</span>
            <span class="clear-all" @click="clearAllNotifications" v-if="notifications.length > 0">全部已读</span>
          </div>
          <div class="panel-content">
            <div v-if="notifications.length === 0" class="empty-notification">暂无新消息</div>
            <div v-else>
              <div
                v-for="notification in notifications"
                :key="notification.id"
                class="notification-item"
                :class="{ unread: notification.status === 'sent' }"
                @click="handleNotificationClick(notification)"
              >
                <img :src="notification.goods_image || DEFAULT_PLACEHOLDER" alt="商品图片" class="notification-avatar" @error="handleImgError">
                <div class="notification-content">
                  <p class="notification-text">{{ notification.content }}</p>
                  <span class="notification-time">{{ notification.sent_at }}</span>
                </div>
                <div v-if="notification.status === 'sent'" class="unread-dot"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!--用户名-->
      <template v-if="isLoggedIn">
        <span class="nav-user-text" @click="goToProfile">{{ nickname }}</span>
      </template>
      <template v-else>
        <router-link to="/login">登录</router-link>
      </template>

      <router-link to="/search" class="search-icon">
        <img src="@/assets/images/搜索.png" alt="搜索" class="search-img">
      </router-link>
    </div>

    <!--移动端汉堡按钮-->
    <button class="hamburger-btn" @click="showMobileMenu = !showMobileMenu">
      <span :class="['hamburger-line', { open: showMobileMenu }]"></span>
      <span :class="['hamburger-line', { open: showMobileMenu }]"></span>
      <span :class="['hamburger-line', { open: showMobileMenu }]"></span>
    </button>
  </nav>

  <!--移动端侧边菜单-->
  <div class="mobile-overlay" v-show="showMobileMenu" @click="showMobileMenu = false"></div>
  <div class="mobile-menu" :class="{ open: showMobileMenu }">
    <div class="mobile-menu-header">
      <span class="mobile-menu-title">菜单</span>
      <button class="mobile-close-btn" @click="showMobileMenu = false">×</button>
    </div>
    <div class="mobile-menu-body">
      <router-link to="/" class="mobile-link" @click="showMobileMenu = false">首页</router-link>
      <router-link to="/goods" class="mobile-link" @click="showMobileMenu = false">商品列表</router-link>
      <router-link to="/search" class="mobile-link" @click="showMobileMenu = false">搜索</router-link>
      <template v-if="isLoggedIn && userRole === 'merchant'">
        <router-link to="/publish" class="mobile-link" @click="showMobileMenu = false">上架商品</router-link>
      </template>
      <template v-else>
        <router-link to="/cart" class="mobile-link" @click="showMobileMenu = false">购物车</router-link>
      </template>
      <div class="mobile-divider"></div>
      <router-link to="/status" class="mobile-link" @click="showMobileMenu = false">商品状态</router-link>
      <router-link to="/ip" class="mobile-link" @click="showMobileMenu = false">IP</router-link>
      <router-link to="/role" class="mobile-link" @click="showMobileMenu = false">角色</router-link>
      <router-link to="/brand" class="mobile-link" @click="showMobileMenu = false">品牌</router-link>
      <div class="mobile-divider"></div>
      <template v-if="isLoggedIn">
        <router-link to="/profile" class="mobile-link" @click="showMobileMenu = false">{{ nickname }}</router-link>
        <a href="#" class="mobile-link mobile-link-danger" @click.prevent="handleLogout; showMobileMenu = false">退出登录</a>
      </template>
      <template v-else>
        <router-link to="/login" class="mobile-link" @click="showMobileMenu = false">登录</router-link>
      </template>
    </div>
  </div>

  <!--客服悬浮球-->
  <div
    class="customer-service-container"
    @click.stop
    v-if="isLoggedIn && userRole !== 'merchant' && userRole !== 'admin'"
  >
    <div class="floating-service-btn" @click="toggleServicePanel">
      <img :src="SERVICE_ICON" class="service-icon" alt="客服">
    </div>

    <!--聊天面板-->
    <div class="service-panel" v-show="showServicePanel">
      <div class="panel-header service-header">
        <span class="panel-title">在线客服</span>
        <button class="close-btn" @click="showServicePanel = false">×</button>
      </div>
      <div class="service-body">
        <div class="service-messages" ref="messagesContainer">
          <div class="service-message system">
            <span class="message-text">您好！欢迎来到次元模仓，请问有什么可以帮您？</span>
          </div>
          <div 
            v-for="(msg, index) in serviceMessages" 
            :key="index" 
            :class="['service-message', msg.type]"
          >
            <span class="message-text">{{ msg.content }}</span>
            <!--商品卡片-->
            <div v-if="msg.goods" class="chat-goods-card" @click="goToGoodsDetail(msg.goods.id)">
              <img :src="msg.goods.image" :alt="msg.goods.name" class="chat-goods-img" @error="handleImgError">
              <div class="chat-goods-info">
                <p class="chat-goods-name">{{ msg.goods.name }}</p>
                <p class="chat-goods-meta">
                  <span v-if="msg.goods.ip" class="chat-goods-tag">{{ msg.goods.ip }}</span>
                  <span v-if="msg.goods.charactername" class="chat-goods-tag">{{ msg.goods.charactername }}</span>
                </p>
                <p class="chat-goods-price">¥{{ (msg.goods.price || 0).toFixed(2) }}</p>
              </div>
            </div>
          </div>
          <!--打字动画-->
          <div v-if="aiLoading" class="service-message system">
            <span class="message-text typing-indicator">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </span>
          </div>
        </div>
        <div class="service-input-area">
          <input 
            v-model="serviceInput" 
            placeholder="请输入您的问题..." 
            @keyup.enter="sendServiceMessage"
            class="service-input"
            :disabled="aiLoading"
          >
          <button class="service-send-btn" @click="sendServiceMessage" :disabled="aiLoading">发送</button>
        </div>
      </div>
    </div>
  </div>

  <!--通知详情弹窗-->
  <div class="modal-overlay" v-show="showDetailModal" @click="closeDetailModal">
    <div class="detail-modal" @click.stop>
      <div class="modal-header">
        <h3>通知详情</h3>
        <button class="close-btn" @click="closeDetailModal">×</button>
      </div>
      <div class="modal-body">
        <img
          :src="currentNotification.goods_image || DEFAULT_PLACEHOLDER"
          alt="商品图片"
          class="modal-goods-img"
          @error="handleImgError"
        >
        <p class="modal-content">{{ currentNotification.content }}</p>
        <p class="modal-time">{{ currentNotification.sent_at }}</p>
      </div>
    </div>
  </div>

  <!--猜你喜欢弹窗-->
  <div class="modal-overlay" v-show="showRecommendModal" @click="closeRecommendModal">
    <div class="recommend-modal" @click.stop>
      <div class="modal-header">
        <h3> 猜你喜欢</h3>
        <button class="close-btn" @click="closeRecommendModal">×</button>
      </div>
      <div class="recommend-body">
        <div v-if="recommendLoading" class="recommend-loading">加载中...</div>
        <div v-else-if="recommendGoods.length === 0" class="recommend-empty">
          暂无推荐，快去浏览商品吧~
        </div>
        <div v-else class="recommend-grid">
          <div 
            v-for="goods in recommendGoods" 
            :key="goods.id" 
            class="recommend-card"
            @click="goToGoodsDetail(goods.id)"
          >
            <img :src="goods.image" :alt="goods.name" class="recommend-img" @error="handleImgError">
            <div class="recommend-info">
              <p class="recommend-name">{{ goods.name }}</p>
              <p class="recommend-price">¥{{ (goods.price || 0).toFixed(2) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import request from '@/api/request';
import DEFAULT_PLACEHOLDER from '@/assets/images/picture.png';
import SERVICE_ICON from '@/assets/images/客服.svg';
import { showConfirm } from '@/utils/modal';

const router = useRouter();

//下拉菜单状态
const showDropdown = ref(false);
const showMobileMenu = ref(false);
const showLeftDrawer = ref(false); // 左侧抽屉

//切换左侧抽屉
const toggleLeftDrawer = () => {
  showLeftDrawer.value = !showLeftDrawer.value;
};

//登录状态
const isLoggedIn = ref(false);
const nickname = ref('');
const userRole = ref('');

//通知详情弹窗状态
const showDetailModal = ref(false);
const currentNotification = ref({}); // 当前查看的通知

//通知相关状态
const showNotificationPanel = ref(false);
const notifications = ref([]);
const unreadCount = ref(0);
let notificationTimer = null;

//客服相关状态
const showServicePanel = ref(false);
const serviceMessages = ref([]);
const serviceInput = ref('');
const messagesContainer = ref(null);
const aiLoading = ref(false);

//客服操作
const toggleServicePanel = () => {
  showServicePanel.value = !showServicePanel.value;
};

const sendServiceMessage = async () => {
  if (!serviceInput.value.trim() || aiLoading.value) return;
  
  //添加用户消息
  serviceMessages.value.push({
    type: 'user',
    content: serviceInput.value
  });
  
  const userMsg = serviceInput.value;
  serviceInput.value = '';
  aiLoading.value = true;
  
  //滚动到底部
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  }, 50);
  
  try {
    //构建对话历史
    const history = serviceMessages.value.map(msg => ({
      role: msg.type === 'user' ? 'user' : 'assistant',
      content: msg.content
    }));
    
    //调用后端AI客服API
    const res = await request.post('/api/chat', {
      message: userMsg,
      history: history.slice(-10)
    });
    
    if (res.data.code === 200) {
      //添加AI回复，可能包含商品卡片
      const replyData = res.data.data;
      serviceMessages.value.push({
        type: 'system',
        content: replyData.reply,
        goods: replyData.goods || null
      });
    } else {
      serviceMessages.value.push({
        type: 'system',
        content: '抱歉，我暂时无法回答，请稍后再试。'
      });
    }
  } catch (err) {
    console.error('AI客服调用失败:', err);
    serviceMessages.value.push({
      type: 'system',
      content: '网络异常，请稍后再试。'
    });
  } finally {
    aiLoading.value = false;
  }
  
  //滚动到底部
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  }, 50);
};

//刷新登录状态
const refreshLoginState = () => {
  const token = sessionStorage.getItem('token');
  const storedNickname = sessionStorage.getItem('nickname');
  const storedRole = sessionStorage.getItem('userRole');

  if (token && storedNickname) {
    isLoggedIn.value = true;
    nickname.value = storedNickname;
    userRole.value = storedRole || '';
    if (userRole.value !== 'merchant' && userRole.value !== 'admin') {
      fetchNotifications();
      fetchUnreadCount();
      startNotificationPolling();
    }
  } else {
    isLoggedIn.value = false;
    nickname.value = '';
    userRole.value = '';
    stopNotificationPolling();
    notifications.value = [];
    unreadCount.value = 0;
  }
};

// 获取通知列表
const fetchNotifications = async () => {
  try {
    const res = await request.get('/api/user/notifications');
    if (res.data.code === 200) {
      notifications.value = res.data.data;
    }
  } catch (err) {
    console.error('获取通知列表失败:', err);
  }
};

// 获取未读通知数量
const fetchUnreadCount = async () => {
  try {
    const res = await request.get('/api/user/notifications/unread-count');
    if (res.data.code === 200) {
      unreadCount.value = res.data.data.count;
    }
  } catch (err) {
    console.error('获取未读数量失败:', err);
  }
};

           // 通知轮询
// 开始轮询
const startNotificationPolling = () => {
  stopNotificationPolling();
  notificationTimer = setInterval(() => {
    fetchUnreadCount();
  }, 30000);
};

// 停止轮询
const stopNotificationPolling = () => {
  if (notificationTimer) {
    clearInterval(notificationTimer);
    notificationTimer = null;
  }
};

// 切换通知面板
const toggleNotificationPanel = () => {
  showNotificationPanel.value = !showNotificationPanel.value;
  if (showNotificationPanel.value) {
    fetchNotifications();
  }
};

// 标记已读 + 打开详情弹窗
const handleNotificationClick = async (notification) => {
  // 标记为已读
  if (notification.status === 'sent') {
    try {
      await request.post(`/api/user/notifications/read/${notification.id}`);
      notification.status = 'read';
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    } catch (err) {
      console.error('标记已读失败:', err);
    }
  }

  // 赋值当前通知 + 打开弹窗
  currentNotification.value = notification;
  showDetailModal.value = true;
  // 关闭通知面板
  showNotificationPanel.value = false;
};

// 关闭详情弹窗
const closeDetailModal = () => {
  showDetailModal.value = false;
};

// 猜你喜欢相关
const showRecommendModal = ref(false);
const recommendGoods = ref([]);
const recommendLoading = ref(false);

// 打开猜你喜欢弹窗
const openRecommendModal = async () => {
  showDropdown.value = false;
  showRecommendModal.value = true;
  recommendLoading.value = true;
  
  try {
    const res = await request.get('/api/recommend/personal');
    if (res.data.code === 200) {
      recommendGoods.value = res.data.data || [];
    }
  } catch (err) {
    console.error('获取推荐失败:', err);
  } finally {
    recommendLoading.value = false;
  }
};

// 关闭猜你喜欢弹窗
const closeRecommendModal = () => {
  showRecommendModal.value = false;
};

// 跳转商品详情
const goToGoodsDetail = (goodsId) => {
  showRecommendModal.value = false;
  showServicePanel.value = false;
  router.push(`/goods/detail/${goodsId}`);
};

// 全部标记为已读
const clearAllNotifications = async () => {
  try {
    const unreadNotifications = notifications.value.filter(n => n.status === 'sent');
    for (const notification of unreadNotifications) {
      await request.post(`/api/user/notifications/read/${notification.id}`);
      notification.status = 'read';
    }
    unreadCount.value = 0;
  } catch (err) {
    console.error('全部已读失败:', err);
  }
};

// 图片错误处理 
const handleImgError = (e) => {
  e.target.src = DEFAULT_PLACEHOLDER;
};

// 点击外部关闭面板
const handleClickOutside = (e) => {
  if (showNotificationPanel.value && !e.target.closest('.notification-text-wrapper')) {
    showNotificationPanel.value = false;
  }
};

// 生命周期钩子
onMounted(() => {
  refreshLoginState();
  document.addEventListener('click', handleClickOutside);
});

// 路由变化监听
watch(() => router.currentRoute.value.path, () => {
  refreshLoginState();
});

onUnmounted(() => {
  stopNotificationPolling();
  document.removeEventListener('click', handleClickOutside);
});

// 退出登录
const handleLogout = async () => {
  const isConfirm = await showConfirm('确定要退出登录吗？');
  if (isConfirm) {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('userRole');
    sessionStorage.removeItem('username');
    sessionStorage.removeItem('nickname');
    isLoggedIn.value = false;
    nickname.value = '';
    userRole.value = '';
    router.push('/');
  }
};

// 跳转到个人中心
const goToProfile = () => {
  router.push('/profile');
};
</script>

<style scoped>
/* ===== 导航栏主体 ===== */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  background: #80acee;
  color: white;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* ===== 左侧菜单区域 ===== */
.menu-container {
  position: relative;
  display: flex;
  align-items: center;
  height: 100%;
}

.nav-section {
  display: flex;
  align-items: center;
  flex: 1;
}

/* ===== 右侧导航链接 ===== */
.nav-links {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: flex-end;
  height: 100%;
}

.nav-links a,
.nav-links .nav-user-text {
  color: white;
  margin-left: 25px;
  text-decoration: none;
  transition: opacity 0.3s;
  font-size: 14px;
  line-height: 60px;
  cursor: pointer;
  display: inline-block;
  flex-shrink: 0;
}

.nav-links a:hover,
.nav-links .nav-user-text:hover {
  opacity: 0.8;
}

/* ===== 下拉菜单 ===== */
.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  min-width: 180px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 8px 0;
  margin-top: 0;
  animation: dropdownFade 0.2s ease;
  z-index: 1001;
}

.dropdown-menu::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 20px;
  width: 12px;
  height: 12px;
  background: white;
  transform: rotate(45deg);
  border-top-left-radius: 2px;
}

.dropdown-item {
  display: block;
  padding: 12px 20px;
  color: #333;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s ease;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  box-sizing: border-box;
  white-space: nowrap;
}

.dropdown-item:hover {
  background-color: #f5f5f5;
  color: #80acee;
}

@keyframes dropdownFade {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== Logo样式 ===== */
.logo {
  display: flex;
  align-items: center;
  height: 100%;
}
.logo-img {
  height: 40px;
  width: auto;
  object-fit: contain;
  max-width: 150px;
}

/* ===== 搜索图标 ===== */
.search-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  transition: background-color 0.3s;
  margin-left: 10px;
}

.search-icon:hover {
  background-color: rgba(31, 31, 38, 0.1);
}

.search-img {
  height: 30px;
  width: 20px;
  object-fit: contain;
  filter: brightness(100%);
  transition: transform 0.3s;
  padding-left: 8px;
}

.search-icon:hover .search-img {
  transform: scale(1.1);
}

/* ===== 菜单按钮 - 优化平滑过渡 ===== */
.menu-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.menu-btn:hover {
  background-color: rgba(255, 255, 255, 0.18);
  transform: scale(1.05);
}
.menu-img {
  height: 24px;
  width: 24px;
  object-fit: contain;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  filter: brightness(0) invert(1);
}
.menu-btn:hover .menu-img {
  transform: scale(1.15) rotate(90deg);
}


/* === 客服悬浮按钮样式 === */
.customer-service-container {
  position: fixed;
  bottom: 120px;
  right: 30px;
  z-index: 9999;
}

.floating-service-btn {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #80acee, #6a9bdb);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(128, 172, 238, 0.4);
  transition: all 0.3s ease;
  user-select: none;
}

.floating-service-btn:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 20px rgba(128, 172, 238, 0.5);
  background: linear-gradient(135deg, #6a9bdb, #5a8fd8);
}

.service-icon {
  width: 28px;
  height: 28px;
  filter: brightness(0) invert(1);
}

/* ===== 客服聊天面板 ===== */
.service-panel {
  position: absolute;
  bottom: 100%;
  right: 0;
  width: 360px;
  height: 450px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  margin-bottom: 16px;
  z-index: 10001;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: panelFadeIn 0.2s ease;
}

.service-header {
  background: linear-gradient(135deg, #80acee, #6a9bdb);
  color: white;
}

.service-header .panel-title {
  color: white;
}

.service-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.service-messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background: #f9f9f9;
}

.service-message {
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.service-message.user {
  align-items: flex-end;
}

.service-message.system {
  align-items: flex-start;
}

.service-message .message-text {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.service-message.user .message-text {
  background: linear-gradient(135deg, #80acee, #6a9bdb);
  color: white;
  border-bottom-right-radius: 4px;
}

.service-message.system .message-text {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.service-input-area {
  padding: 12px;
  background: white;
  border-top: 1px solid #eee;
  display: flex;
  gap: 8px;
}

.service-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.service-input:focus {
  border-color: #80acee;
}

.service-send-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #80acee, #6a9bdb);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: transform 0.2s;
}

.service-send-btn:hover {
  transform: scale(1.05);
}

/* ===== 聊天商品卡片样式 ===== */
.chat-goods-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: white;
  border-radius: 8px;
  border: 1px solid #eee;
  cursor: pointer;
  max-width: 250px;
  transition: all 0.2s;
}

.chat-goods-card:hover {
  border-color: #80acee;
  box-shadow: 0 2px 8px rgba(128, 172, 238, 0.2);
}

.chat-goods-img {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
}

.chat-goods-info {
  flex: 1;
  min-width: 0;
}

.chat-goods-name {
  font-size: 13px;
  color: #333;
  margin: 0 0 4px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-goods-meta {
  margin: 0 0 4px 0;
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.chat-goods-tag {
  font-size: 11px;
  color: #80acee;
  background: #f0f5ff;
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
}

.chat-goods-price {
  font-size: 15px;
  color: #fb7299;
  font-weight: bold;
  margin: 0;
}

/* ===== 打字动画 ===== */
.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 10px 16px !important;
}

.typing-dot {
  width: 6px;
  height: 6px;
  background: #999;
  border-radius: 50%;
  animation: typingBounce 1.2s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* === 导航栏通知文字样式 === */
.notification-text-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  margin-left: 25px;
  cursor: pointer;
}

.nav-notification-text {
  color: white;
  font-size: 14px;
  line-height: 60px;
  transition: opacity 0.3s;
}

.nav-notification-text:hover {
  opacity: 0.8;
}

.nav-notification-badge {
  position: absolute;
  top: 8px;
  right: -12px;
  min-width: 16px;
  height: 16px;
  background: #ff4400;
  color: white;
  font-size: 10px;
  font-weight: bold;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  border: 2px solid #80acee;
}

.nav-notification-panel {
  position: absolute;
  top: 100%;
  right: 0;
  width: 360px;
  max-height: 480px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  margin-top: 8px;
  z-index: 10001;
  overflow: hidden;
  animation: dropdownFade 0.2s ease;
}

/* === 用户下拉菜单样式 === */
.user-dropdown-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  margin-left: 20px;
  cursor: pointer;
}

.user-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  min-width: 150px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 8px 0;
  margin-top: 0;
  animation: dropdownFade 0.2s ease;
  z-index: 1001;
}

.user-dropdown-menu::before {
  content: '';
  position: absolute;
  top: -6px;
  right: 20px;
  width: 12px;
  height: 12px;
  background: white;
  transform: rotate(45deg);
  border-top-left-radius: 2px;
}

.dropdown-item-danger {
  color: #ff4d4f !important;
}

.dropdown-item-danger:hover {
  color: #ff7875 !important;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  background: #fafafa;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.clear-all {
  font-size: 13px;
  color: #80acee;
  cursor: pointer;
  transition: color 0.2s;
}

.clear-all:hover {
  color: #5a8fd8;
}

.panel-content {
  max-height: 400px;
  overflow-y: auto;
}

.empty-notification {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  font-size: 14px;
}

/* ===== 通知列表项 ===== */
.notification-item {
  display: flex;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.notification-item:hover {
  background-color: #f9f9f9;
}

.notification-item.unread {
  background-color: #f0f7ff;
}

.notification-avatar {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  object-fit: cover;
  background: #f5f5f5;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.notification-text {
  font-size: 14px;
  color: #333;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.unread-dot {
  width: 8px;
  height: 8px;
  background: #ff4400;
  border-radius: 50%;
  position: absolute;
  top: 18px;
  right: 16px;
}

@keyframes panelFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== 面板滚动条 ===== */
.panel-content::-webkit-scrollbar {
  width: 6px;
}
.panel-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.panel-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}
.panel-content::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

/* ===== 通知详情弹窗 ===== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
}

.detail-modal {
  background: white;
  width: 90%;
  max-width: 500px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  background: #fafafa;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0 8px;
}

.modal-body {
  padding: 24px;
  text-align: center;
}

.modal-goods-img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid #eee;
}

.modal-content {
  font-size: 16px;
  color: #333;
  line-height: 1.6;
  margin: 0 0 12px;
  white-space: pre-line;
}

.modal-time {
  font-size: 12px;
  color: #999;
  margin: 0;
}


/* ==== 移动端适配 ==== */
.hamburger-btn {
  display: none;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 5px;
  width: 40px;
  height: 40px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
}

.hamburger-line {
  display: block;
  width: 22px;
  height: 2px;
  background: white;
  border-radius: 1px;
  transition: all 0.3s ease;
}

.hamburger-line.open:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}
.hamburger-line.open:nth-child(2) {
  opacity: 0;
}
.hamburger-line.open:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

/* ===== 移动端侧边菜单 ===== */
.mobile-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
}

.mobile-menu {
  display: none;
  position: fixed;
  top: 0;
  right: -280px;
  width: 280px;
  height: 100%;
  background: white;
  z-index: 9999;
  transition: right 0.3s ease;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.1);
}

.mobile-menu.open {
  right: 0;
}

.mobile-menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #80acee;
  color: white;
}

.mobile-menu-title {
  font-size: 18px;
  font-weight: 600;
}

.mobile-close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 28px;
  cursor: pointer;
  line-height: 1;
}

.mobile-menu-body {
  padding: 8px 0;
  overflow-y: auto;
  max-height: calc(100vh - 56px);
}

.mobile-link {
  display: block;
  padding: 14px 24px;
  color: #333;
  text-decoration: none;
  font-size: 15px;
  transition: background 0.2s;
}

.mobile-link:hover,
.mobile-link:active {
  background: #f0f5ff;
  color: #80acee;
}

.mobile-link-danger {
  color: #ff4d4f;
}

.mobile-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 8px 0;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .navbar {
    padding: 0 12px;
    height: 50px;
  }

  .nav-links {
    display: none !important;
  }

  .menu-container {
    display: flex !important;
  }

  .hamburger-btn {
    display: flex;
  }

  .mobile-overlay {
    display: block;
  }

  .mobile-menu {
    display: block;
  }

  .logo-img {
    height: 32px;
    max-width: 120px;
  }

  .customer-service-container {
    bottom: 100px;
    right: 20px;
  }

  .floating-service-btn {
    width: 48px;
    height: 48px;
  }

  .service-panel {
    width: calc(100vw - 32px);
    right: -8px;
    height: 60vh;
  }

  .nav-notification-panel {
    width: calc(100vw - 32px);
    right: -20px;
  }

  .detail-modal {
    width: 95%;
    margin: 0 auto;
  }
}

/* ===== 猜你喜欢弹窗样式 ===== */
.recommend-modal {
  width: 90%;
  max-width: 600px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.recommend-body {
  padding: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.recommend-loading,
.recommend-empty {
  text-align: center;
  padding: 40px;
  color: #999;
}

.recommend-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.recommend-card {
  background: #f8f8f8;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.recommend-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.recommend-img {
  width: 100%;
  height: 100px;
  object-fit: cover;
}

.recommend-info {
  padding: 8px;
}

.recommend-name {
  font-size: 12px;
  color: #333;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recommend-price {
  font-size: 14px;
  color: #fb7299;
  font-weight: 600;
  margin: 4px 0 0;
}

.dropdown-divider {
  height: 1px;
  background: #eee;
  margin: 8px 12px;
}

.recommend-item {
  color: #fb7299 !important;
  font-weight: 500;
}

@media (max-width: 768px) {
  .recommend-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* ===== 修复用户下拉菜单文字看不见的问题 ===== */
.nav-links .user-dropdown-menu .dropdown-item {
  color: #333 !important;
  line-height: 1.5 !important;
  margin-left: 0 !important;
}

.nav-links .user-dropdown-menu .dropdown-item-danger {
  color: #ff4d4f !important;
}

/* ===== 左侧抽屉样式 - 优化平滑过渡 */
.left-drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  z-index: 9998;
  animation: overlayFadeIn 0.25s ease-out;
}

.left-drawer {
  position: fixed;
  top: 0;
  left: -300px;
  width: 300px;
  height: 100vh;
  background: white;
  z-index: 9999;
  transition: left 0.35s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
}

.left-drawer.open {
  left: 0;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  background: linear-gradient(135deg, #80acee, #6a9bdb);
  color: white;
  box-shadow: 0 2px 8px rgba(106, 155, 219, 0.2);
}

.drawer-title {
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.drawer-close-btn {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: white;
  font-size: 26px;
  cursor: pointer;
  line-height: 1;
  padding: 4px 10px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.drawer-close-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: rotate(90deg);
}

.drawer-content {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}

.drawer-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 28px;
  color: #444;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border-bottom: 1px solid #f8f8f8;
  position: relative;
  overflow: hidden;
}

.drawer-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(to bottom, #80acee, #6a9bdb);
  transform: scaleY(0);
  transition: transform 0.25s ease;
}

.drawer-item:hover {
  background: linear-gradient(135deg, #f5faff, #f0f7ff);
  color: #6a9bdb;
  padding-left: 32px;
}

.drawer-item:hover::before {
  transform: scaleY(1);
}

@keyframes overlayFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ===== 响应式抽屉适配 ===== */
@media (max-width: 768px) {
  .left-drawer {
    width: 75vw;
    left: -75vw;
  }
}
</style>