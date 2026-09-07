import { ElMessageBox } from 'element-plus'

// 显示Alert弹窗：改用 Element Plus ElMessageBox，保持阻塞确认行为
export function showAlert(msg, title = '提示', type = 'info') {
  const boxType = type === 'confirm' ? 'warning' : type
  return ElMessageBox.alert(msg, title, {
    type: boxType,
    confirmButtonText: '确定',
    closeOnClickModal: false,
  })
}

// 显示Confirm弹窗：确定=true，取消/关闭=false
export function showConfirm(msg, title = '确认操作') {
  return ElMessageBox.confirm(msg, title, {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => true).catch(() => false)
}