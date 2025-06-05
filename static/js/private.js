import { ModernPagination } from "./next_page.js";

const privateModel = {
  async privateData(filters) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== null && value !== "") {
        params.append(key, value);
      }
    }
    const res = await fetch(`/api/private?${params.toString()}`, {
      method: "GET"
    });
    const json = await res.json();
    if (res.status !== 200) {
      throw new Error(json.error || "API 回傳錯誤");
    }
    return json;  
  }
};

const privateView = {
  createCardElement(item) {
    console.log(item)
    const card = document.createElement("div");
    card.classList.add("card");

    const img = document.createElement("img");
    img.classList.add("card-img");
    const imgArray = JSON.parse(item.images); 
    img.src = imgArray[0];
    card.appendChild(img);

    const body = document.createElement("div");
    body.classList.add("card-body");
    card.appendChild(body);

    const title = document.createElement("h3");
    title.classList.add("card-title");
    title.textContent = item.pet_name;
    body.appendChild(title);

    const kind = document.createElement("p");
    kind.classList.add("card-info");
    kind.textContent = `類別：${item.pet_kind}`;
    body.appendChild(kind);

    const region = document.createElement("p");
    region.classList.add("card-info");
    region.textContent = `地點：${item.pet_place}`;
    body.appendChild(region);

    const type = document.createElement("p");
    type.classList.add("card-info");
    type.textContent = `品種：${item.pet_breed}`;
    body.appendChild(type);

    const sex = document.createElement("p");
    sex.classList.add("card-info");
    sex.textContent = `性別：${item.pet_sex}`;
    body.appendChild(sex);

    const color = document.createElement("p");
    color.classList.add("card-info");
    color.textContent = `毛色：${item.pet_colour}`;
    body.appendChild(color);

    const link = document.createElement("a");
    link.classList.add("category-link");
    link.textContent = "查看更多";
    link.href = `/details/${item.id}`;
    body.appendChild(link);

    link.addEventListener("click", (e) => {
      const token = localStorage.getItem("token");
      
      if (!token) {
        e.preventDefault();
        alert("請先登入才能查看完整資訊");
        window.location.href = "/login";
        return;
      }
    });

    document.querySelector(".public_card").appendChild(card);
  }
};

const privateControl = {
  
  currentFilters: {
    place: "", kind: "", sex: "", color: "", page: 0
  },
  pagination: null,

  async renderPage(page = 0) {
    page = Number(page);
    if (Number.isNaN(page) || page < 0) page = 0;
    this.currentFilters.page = page;

    this.currentFilters.place  = document.querySelector("#animal_place").value;
    this.currentFilters.kind   = document.querySelector("#animal_kind").value;
    this.currentFilters.sex    = document.querySelector("#animal_sex").value;
    this.currentFilters.color  = document.querySelector("#animal_colour").value;

    const filtersToSend = {};
    for (const key of ["place", "kind", "sex", "color", "page"]) {
      const val = this.currentFilters[key];
      if (val !== undefined && val !== null && val !== "") {
        filtersToSend[key] = String(val);
      }
    }

    let response;
    try {
      response = await privateModel.privateData(filtersToSend);
    } catch (err) {
      return;
    }

    const cardContainer = document.querySelector(".public_card");
    cardContainer.innerHTML = "";
    response.data.forEach(item => {
      privateView.createCardElement(item);
    });

    if (!this.pagination) {
      const pagerContainer = document.querySelector(".next_page");

      this.pagination = new ModernPagination(pagerContainer);
      this.pagination.setPageChangeHandler((oneBasedPage) => {
        this.renderPage(oneBasedPage - 1);
      });
    }

    this.pagination.render(response.total_pages, response.current_page + 1);
  },

  init() {

    this.renderPage(0);

    const searchForm = document.querySelector("#searchForm");
    searchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      this.renderPage(0);
    });
    
  },

};

document.addEventListener("DOMContentLoaded", () => {
  privateControl.init();
});
