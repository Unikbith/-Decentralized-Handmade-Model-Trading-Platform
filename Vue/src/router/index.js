import { createRouter, createWebHistory } from 'vue-router'

//路由组件 - 路由懒加载
const HomeView = () => import('@/views/homeView.vue')
const GoodsView = () => import('@/views/goodsView.vue')
const LoginView = () => import('@/views/loginView.vue')
const RegisterView = () => import('@/views/registerView.vue')
const ResetPasswordView = () => import('@/views/resetPasswordView.vue')
const GoodsCartView = () => import('@/views/goodsCartView.vue')
const GoodsDetailView = () => import('@/views/goodsDetailView.vue')
const SearchView = () => import('@/views/searchView.vue')
const ProfileView = () => import('@/views/profileView.vue')
const PublishView = () => import('@/views/publishView.vue')
const StatusView = () => import('@/views/base/statusView.vue')
const AdminLoginView = () => import('@/views/admin/adminLoginView.vue')
const AdminView = () => import('@/views/admin/adminView.vue')
const MonitorView = () => import('@/views/admin/monitorView.vue')
const IpView = () => import('@/views/base/ipView.vue')
const RoleView = () => import('@/views/base/roleView.vue')
const BrandView = () => import('@/views/base/brandView.vue')
const ConfirmPayView = () => import('@/views/confirmPayView.vue')
const OrderSettlementView = () => import('@/views/orderSettlementView.vue')


//公共工具方法
const getUserToken = () => sessionStorage.getItem('token')
const getUserRole = () => sessionStorage.getItem('userRole')
const getAdminToken = () => sessionStorage.getItem('adminToken')

//路由白名单：无需登录直接访问
const whiteList = ['/login', '/register', '/reset-password', '/admin/login', '/']


//商家权限守卫：仅商家可访问
const merchantGuard = (to, from, next) => {
  const token = getUserToken()
  const role = getUserRole()
  if (token && role === 'merchant') {
    next()
  } else if (!token) {
    next('/login')
  } else {
    next('/')
  }
}

//管理员权限守卫：仅管理员可访问
const adminGuard = (to, from, next) => {
  if (getAdminToken()) {
    next()
  } else {
    next('/admin/login')
  }
}

//普通登录守卫：必须登录才能访问
const loginGuard = (to, from, next) => {
  if (getUserToken()) {
    next()
  } else {
    next('/login')
  }
}

//路由配置
const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/goods', name: 'Goods', component: GoodsView },
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/register', name: 'Register', component: RegisterView },
  { path: '/reset-password', name: 'ResetPassword', component: ResetPasswordView },
  { path: '/cart', name: 'Cart', component: GoodsCartView, beforeEnter: loginGuard },
  { path: '/goods/detail/:id', name: 'goodsDetail', component: GoodsDetailView },
  { path: '/search', name: 'Search', component: SearchView },
  { path: '/profile', name: 'Profile', component: ProfileView, beforeEnter: loginGuard },
  { path: '/publish', name: 'Publish', component: PublishView, beforeEnter: merchantGuard },
  { path: '/status', name: 'Status', component: StatusView, beforeEnter: loginGuard },
  { path: '/ip', name: 'Ip', component: IpView, beforeEnter: loginGuard },
  { path: '/brand', name: 'Brand', component: BrandView, beforeEnter: loginGuard },
  { path: '/role', name: 'Role', component: RoleView, beforeEnter: loginGuard },
  { path: '/confirmPay', name: 'ConfirmPay', component: ConfirmPayView, meta: { noGlobalLayout: true } },
  { path: '/orderSettlement', name: 'OrderSettlement', component: OrderSettlementView, beforeEnter: loginGuard },

  {
    path: '/admin',
    redirect: '/admin/login',
    children: [
      { path: 'login', name: 'AdminLogin', component: AdminLoginView, meta: { noGlobalLayout: true } },
      { path: 'dashboard', name: 'AdminDashboard', component: AdminView, beforeEnter: adminGuard, meta: { noGlobalLayout: true } },
      { path: 'monitor', name: 'AdminMonitor', component: MonitorView, beforeEnter: adminGuard, meta: { noGlobalLayout: true } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

//创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  // 切换路由滚动到顶部
  scrollBehavior() {
    return { top: 0, left: 0 }
  }
})

//全局前置守卫
router.beforeEach((to, from, next) => {
  // 白名单直接放行
  if (whiteList.includes(to.path)) {
    next()
    return
  }
  next()
})

export default router
