// 模态框实例引用
let modalInstance = null

// 设置模态框实例
export function setModalInstance(instance) {
  modalInstance = instance
}

// 显示Alert弹窗
export function showAlert(msg, title = '提示', type = 'info') {
  if (!modalInstance) return Promise.reject('modal not ready')
  return modalInstance.showAlert(msg, title, type)
}

// 显示Confirm弹窗
export function showConfirm(msg, title = '确认操作') {
  if (!modalInstance) return Promise.reject('modal not ready')
  return modalInstance.showConfirm(msg, title)
}
