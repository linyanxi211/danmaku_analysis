import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

/**
 * 将HTML元素转换为PDF
 * @param {string} elementId - 要转换的元素的ID
 * @param {string} fileName - 下载的文件名
 */
export const generatePDF = async (elementId, fileName = 'report.pdf') => {
  const element = document.getElementById(elementId)
  if (!element) {
    throw new Error('元素不存在')
  }
  
  try {
    // 设置临时样式以确保打印质量
    const originalStyles = {
      width: element.style.width,
      maxWidth: element.style.maxWidth,
      margin: element.style.margin,
      padding: element.style.padding,
      boxShadow: element.style.boxShadow
    }
    
    element.style.width = '1200px'
    element.style.maxWidth = '1200px'
    element.style.margin = '0 auto'
    element.style.padding = '40px'
    element.style.boxShadow = 'none'
    
    // 转换为canvas
    const canvas = await html2canvas(element, {
      scale: 2,
      backgroundColor: '#ffffff',
      logging: false,
      allowTaint: true,
      useCORS: true
    })
    
    // 恢复原始样式
    Object.assign(element.style, originalStyles)
    
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'px',
      format: [canvas.width / 2, canvas.height / 2]
    })
    
    pdf.addImage(imgData, 'PNG', 0, 0, canvas.width / 2, canvas.height / 2)
    pdf.save(fileName)
    
    return true
  } catch (error) {
    console.error('PDF生成失败:', error)
    throw error
  }
}

/**
 * 打印HTML元素
 * @param {string} elementId - 要打印的元素的ID
 */
export const printElement = (elementId) => {
  const element = document.getElementById(elementId)
  if (!element) {
    throw new Error('元素不存在')
  }
  
  const printWindow = window.open('', '_blank')
  const styles = document.querySelectorAll('style, link[rel="stylesheet"]')
  let stylesHTML = ''
  
  styles.forEach(style => {
    if (style.tagName === 'STYLE') {
      stylesHTML += style.outerHTML
    } else if (style.tagName === 'LINK') {
      stylesHTML += style.outerHTML
    }
  })
  
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>情感分析报告</title>
        ${stylesHTML}
        <style>
          body { padding: 40px; background: white; }
          .report-header { display: none; }
          @media print {
            .report-header { display: none; }
          }
        </style>
      </head>
      <body>
        ${element.outerHTML}
      </body>
    </html>
  `)
  
  printWindow.document.close()
  printWindow.focus()
  setTimeout(() => {
    printWindow.print()
  }, 500)
}