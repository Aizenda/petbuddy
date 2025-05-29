const publicModel = {
  page: 0,
  getFilters() {
    return {
      place: document.getElementById("animal_place").value,
      kind: document.getElementById("animal_kind").value,
      sex: document.getElementById("animal_sex").value,
      color: document.getElementById("animal_colour").value
    };
  },
  
  async getPublic(reset = false) {
    if (reset) this.page = 0;
    const filters = this.getFilters();

    if (this.page === 0) {
      const urlParams = new URLSearchParams(window.location.search);
      for (const [key, value] of urlParams.entries()) {
        if (value && !filters[key]) {
          filters[key] = value;
        }
      }
    }

    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value) params.append(key, value);
    }
    params.append("page", this.page);

    const response = await fetch(`/api/public?${params.toString()}`);
    if (!response.ok) throw new Error("查詢失敗");

    const result = await response.json();
    this.page += 1;
    return result;
  }
};

const publicView = {
  cardContainer: document.querySelector(".public_card"),
  paginationContainer: document.querySelector(".next_page"),
  pagination: null,
  
  init() {
    if (!this.pagination) {
      this.pagination = new ModernPagination(this.paginationContainer);
      this.pagination.setPageChangeHandler((page) => {
        publicControl.gotoPage(page - 1); // 轉換為 0-based
      });
    }
  },
  
  renderCards(data, reset = false) {
  if (reset) this.cardContainer.innerHTML = "";

  data.forEach(item => {
    const card = document.createElement("div");
    card.classList.add("card");

    // 圖片
    const img = document.createElement("img");
    img.className = "card-img";
    img.src = item.album_file;
    img.alt = "animal";
    img.onerror = () => img.src = "https://img.icons8.com/plasticine/400/image.png";
    card.appendChild(img);

    // 內容容器
    const body = document.createElement("div");
    body.className = "card-body";

    // 標題：品種
    const title = document.createElement("h3");
    title.className = "card-title";
    title.textContent = item.animal_kind || "未分類";
    body.appendChild(title);

    // 其他資料欄位
    const infoList = [
      ["性別", item.animal_sex],
      ["體型", item.animal_bodytype],
      ["顏色", item.animal_colour],
      ["所在地", item.animal_place],
      ["收容所地址", item.shelter_address],
      ["聯絡電話", item.shelter_tel],
    ];

    infoList.forEach(([label, value]) => {
      const p = document.createElement("p");
      p.className = "card-info";
      p.textContent = `${label}：${value}`;
      body.appendChild(p);
    });

    // 動物編號
    const id = document.createElement("p");
    id.className = "card-id";
    id.textContent = `動物編號：${item.animal_subid}`;
    body.appendChild(id);

    card.appendChild(body);
    this.cardContainer.appendChild(card);
  });
},
  
  renderPagination(totalPages, currentPage) {
    // 確保 pagination 已初始化
    if (!this.pagination) {
      this.init();
    }
    
    this.pagination.render(totalPages, currentPage + 1);
  }
};

// 修復後的 ModernPagination 類
class ModernPagination {
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

const publicControl = {
  isLoading: false, // 添加載入狀態防止重複請求
  
  init() {
    // 初始化視圖
    publicView.init();
    this.syncSelectFromURL()
    const button = document.querySelector(".search-button");
    button.addEventListener("click", (e) => {
      e.preventDefault();
      this.searchNew();
    });

    // 頁面載入時執行搜尋
    this.searchNew();
  },

  async searchNew() {
    if (this.isLoading) return;
    this.isLoading = true;
    
    try {
      const result = await publicModel.getPublic(true);
      publicView.renderCards(result.data, true);
      publicView.renderPagination(result.pages, result.current_page);
      console.log(result.current_page);
    } catch (err) {
      alert(err.message);
    } finally {
      this.isLoading = false;
    }
  },

  async gotoPage(page) {
    if (this.isLoading) return;
    this.isLoading = true;
    
    publicModel.page = page;
    try {
      const result = await publicModel.getPublic(false);
      publicView.renderCards(result.data, true);
      publicView.renderPagination(result.pages, result.current_page);
    } catch (err) {
      alert(err.message);
    } finally {
      this.isLoading = false;
    }
  },
  syncSelectFromURL() {
  const urlParams = new URLSearchParams(window.location.search);
  const keys = {
    kind: "animal_kind",
    place: "animal_place",
    sex: "animal_sex",
    color: "animal_colour"
  };

  for (const [paramKey, selectId] of Object.entries(keys)) {
    const value = urlParams.get(paramKey);
    const select = document.getElementById(selectId);
    if (value && select) {
      select.value = value;
    }
  }
}
};

// 當 DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', () => {
  publicControl.init();
});