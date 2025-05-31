export class ModernPagination {
  constructor(container) {
    this.container = container;
    this.currentPage = 1;
    this.totalPages = 1;
    this.displayRange = 0;
    this.onPageChange = null;
    this.addStyles();
  }
  
  addStyles() {
    if (document.getElementById('modern-pagination-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'modern-pagination-styles';
    style.textContent = `
      .next_page {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        margin: 40px 0;
      }

      .page-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border: 1px solid #e0e0e0;
        background: white;
        color: #666;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        border-radius: 8px;
        transition: all 0.2s ease;
        text-decoration: none;
        user-select: none;
        font-family: inherit;
      }

      .page-btn:hover:not(:disabled):not(.active) {
        border-color: #ff7a7a;
        color: #ff7a7a;
        background-color: #fff5f5;
        transform: translateY(-1px);
      }

      .page-btn.active {
        background: linear-gradient(135deg, #ff7a7a, #ff6b6b);
        border-color: #ff7a7a;
        color: white;
        box-shadow: 0 2px 8px rgba(255, 122, 122, 0.3);
      }

      .page-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
        background: #f5f5f5;
        color: #ccc;
      }

      .page-btn.nav-btn {
        font-size: 16px;
        font-weight: 600;
      }

      .pagination-dots {
        color: #999;
        font-size: 14px;
        padding: 0 4px;
        display: flex;
        align-items: center;
        height: 44px;
      }
    `;
    document.head.appendChild(style);
  }

  render(totalPages, currentPage ) {
  this.totalPages = totalPages;
  this.currentPage = currentPage;

  const container = this.container;
  container.innerHTML = '';

  if (totalPages <= 1) return;

  // 上一頁按鈕
  const prevBtn = this.createButton('❮', currentPage - 1, currentPage === 1, false, 'nav-btn');
  container.appendChild(prevBtn);

  const maxVisiblePages = 7;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
  let endPage = startPage + maxVisiblePages - 1;

  if (endPage > totalPages) {
    endPage = totalPages;
    startPage = Math.max(1, endPage - maxVisiblePages + 1);
  }

  // 第一頁與省略號
  if (startPage > 1) {
    container.appendChild(this.createButton('1', 1));
    if (startPage > 2) {
      container.appendChild(this.createDots());
    }
  }

  // 中間頁碼
  for (let i = startPage; i <= endPage; i++) {
    container.appendChild(
      this.createButton(i.toString(), i, false, i === currentPage)
    );
  }

  // 最後一頁與省略號
  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      container.appendChild(this.createDots());
    }
    container.appendChild(this.createButton(totalPages.toString(), totalPages));
  }

  // 下一頁按鈕
  const nextBtn = this.createButton('❯', currentPage + 1, currentPage === totalPages, false, 'nav-btn');
  container.appendChild(nextBtn);
}

  createButton(text, page, disabled = false, active = false, extraClass = '') {
    const btn = document.createElement('button');
    btn.className = `page-btn ${extraClass}`;
    btn.textContent = text;
    
    if (active) btn.classList.add('active');
    if (disabled) btn.disabled = true;
    
    if (!disabled) {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation(); // 防止事件冒泡
        if (this.onPageChange && !btn.disabled) {
          this.onPageChange(page);
        }
      });
    }
    
    return btn;
  }

  createDots() {
    const dots = document.createElement('span');
    dots.className = 'pagination-dots';
    dots.textContent = '...';
    return dots;
  }

  setPageChangeHandler(handler) {
    this.onPageChange = handler;
  }
}