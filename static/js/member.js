const memberModel = {
	async getUser(){
		const token = localStorage.getItem("token");
		try{
			const req = await fetch("/api/user",{
				method:"GET",
				headers:{
					"Authorization": `Bearer ${token}`,
					"Content-Type": "application/json"
				}
			});

			const data = await req.json();

			if(!data.ok){
				throw new Error(data.message)
			}
			
			return data;

		}catch(e){
			console.log(e);
			return e;
		}
	},
	async advertise_for_adoption(){
		const token = localStorage.getItem("token");
		try{
			const req = await fetch("/api/advertise_for_adoption",{
				method:"GET",
				headers:{
					"Authorization": `Bearer ${token}`,
					"Content-Type": "application/json"
				}
			});

			const data = await req.json();

			if(!data.ok){
				throw new Error(data.message)
			}
			
			return data;

		}catch(e){
			console.log(e);
			return e;
		}
	},
	async want_to_adopt(){
		const token = localStorage.getItem("token");
		try{
			const req = await fetch("/api/want_to_adopt",{
				method:"GET",
				headers:{
					"Authorization": `Bearer ${token}`,
					"Content-Type": "application/json"
				}
			});

			const data = await req.json();

			if(!data.ok){
				throw new Error(data.message)
			}
			
			return data;

		}catch(e){
			console.log(e);
			return e;
		}
	},
	async read_form(userData){
		const token = localStorage.getItem("token");
		try{
			const req = await fetch("/api/check/form",{
				method:"POST",
				headers:{
					"Authorization": `Bearer ${token}`,
					"Content-Type": "application/json"
				},
				body: JSON.stringify(userData)
			})

			const formData = await req.json();
			
			if(!formData.ok){
				throw new Error(formData.message);
			}
			return formData;

		}catch(error){
			console.log(error);
			alert(error)
			return;
		}
	}
}

const memberView = {
	element:{
		name:document.getElementById("name"),
		time:document.getElementById("time"),
		adoption:document.getElementById("adoption"),
		tboday:document.querySelector("#tbody-1"),
		tboday2:document.querySelector("#tbody-2")

	},
	showBar(){
		const navLinks = document.querySelectorAll('.nav-link');
		const sections = document.querySelectorAll('.section');

		navLinks.forEach(link => {
			link.addEventListener('click', (e) => {
				e.preventDefault();
				
				navLinks.forEach(nav => nav.classList.remove('active'));
				sections.forEach(section => section.classList.remove('active'));

				link.classList.add('active');
				const targetSection = document.getElementById(link.dataset.section);
				targetSection.classList.add('active');
			});
		});
	},
	renderUser(user){
		this.element.name.textContent = user.data.name;
		const time = user.data.created_at.split("T")[0];
		this.element.time.textContent = `成為會員時間:${time}`;
	},
	renderAdvertiseCards(data, formData) {
			const tbody = this.element.tboday;
			
			// 創建卡片式表格行
			const tr = document.createElement("tr");
			tr.classList.add("modern-card-row", "advertise-row");
			
			// 添加懸停效果事件
			this.addHoverEffects(tr);
			
			// 寵物圖片列
			const td0 = document.createElement("td");
			td0.classList.add("image-cell");
			
			const imageContainer = this.createImageContainer(data, 'images');
			td0.appendChild(imageContainer);
			tr.appendChild(td0);
			
			// 編號列
			const td1 = document.createElement("td");
			td1.classList.add("id-cell");
			
			const idBadge = document.createElement("span");
			idBadge.classList.add("id-badge");
			idBadge.textContent = `#${data.id}`;
			
			td1.appendChild(idBadge);
			tr.appendChild(td1);
			
			// 寵物名稱列
			const td2 = document.createElement("td");
			td2.classList.add("name-cell");
			
			const nameContainer = this.createNameContainer(data.pet_name, data.species, data.age);
			td2.appendChild(nameContainer);
			tr.appendChild(td2);
			
			// 領養狀態列
			const td3 = document.createElement("td");
			td3.classList.add("status-cell");
			
			const statusContainer = this.createAdoptionStatusContainer(data.user_name);
			td3.appendChild(statusContainer);
			tr.appendChild(td3);
			
			// 表單狀態列
			const td4 = document.createElement("td");
			td4.classList.add("form-cell");
			
			const formElement = this.createFormStatusElement(formData);
			if (formElement) {
					td4.appendChild(formElement);
			}
			tr.appendChild(td4);
			
			// 操作列
			const td5 = document.createElement("td");
			td5.classList.add("action-cell");
			
			const actionContainer = this.createAdvertiseActionContainer();
			td5.appendChild(actionContainer);
			tr.appendChild(td5);
			
			tbody.appendChild(tr);
	},

	renderAdoptCards(data, formData) {
			const tbody = this.element.tboday2;
			
			// 創建卡片式表格行
			const tr = document.createElement("tr");
			tr.classList.add("modern-card-row", "adopt-row");
			
			// 添加懸停效果事件
			this.addHoverEffects(tr);
			
			// 寵物圖片列
			const td0 = document.createElement("td");
			td0.classList.add("image-cell");
			
			const imageContainer = this.createImageContainer(data, 'images');
			td0.appendChild(imageContainer);
			tr.appendChild(td0);
			
			// 寵物編號列
			const td1 = document.createElement("td");
			td1.classList.add("id-cell");
			
			const idBadge = document.createElement("span");
			idBadge.classList.add("id-badge");
			idBadge.textContent = `#${data.id}`;
			
			td1.appendChild(idBadge);
			tr.appendChild(td1);
			
			// 寵物名稱列
			const td2 = document.createElement("td");
			td2.classList.add("name-cell");
			
			const nameContainer = this.createNameContainer(data.pet_name, null, null, "申請中的寵物");
			td2.appendChild(nameContainer);
			tr.appendChild(td2);
			
			// 送養人列
			const td3 = document.createElement("td");
			td3.classList.add("owner-cell");
			
			const ownerContainer = this.createOwnerContainer(data.sender_name);
			td3.appendChild(ownerContainer);
			tr.appendChild(td3);
			
			// 填寫狀態列 - 修复这里，传递正确的参数
			const td4 = document.createElement("td");
			td4.classList.add("fill-status-cell");
			
			const fillStatusElement = this.createFormStatusElementAsAdopt(formData);
			if (fillStatusElement) {
				td4.appendChild(fillStatusElement);
			}
			tr.appendChild(td4);
			
			// 操作列
			const td5 = document.createElement("td");
			td5.classList.add("action-cell");
			
			const actionContainer = this.createAdoptActionContainer();
			td5.appendChild(actionContainer);
			tr.appendChild(td5);
			
			tbody.appendChild(tr);
	},
	
	addHoverEffects(element) {
			element.addEventListener('mouseenter', () => {
					element.classList.add('hovered');
			});
			
			element.addEventListener('mouseleave', () => {
					element.classList.remove('hovered');
			});
	},

	// 創建圖片容器
	createImageContainer(data, imageField) {
			const imageContainer = document.createElement("div");
			imageContainer.classList.add("image-container");
			
			const img = document.createElement("img");
			// 根據不同的圖片欄位處理
			if (imageField === 'images') {
					if (data.images) {
							try {
									const images = typeof data.images === 'string' ? JSON.parse(data.images) : data.images;
									img.src = Array.isArray(images) ? images[0] : images.split(",")[0];
							} catch (e) {
									img.src = data.images.split(",")[0];
							}
					}
			}
			
			img.classList.add("pet-image");
			img.alt = `${data.pet_name || '寵物'}的照片`;
			
			// 圖片載入錯誤處理
			img.addEventListener('error', () => {
					img.src = '';
					img.alt = '圖片載入失敗';
			});
			
			// 添加圖片疊加效果
			const imageDetails = document.createElement("a");
			imageDetails.classList.add("image-overlay");
			imageDetails.href = `/details/${data.id}`
		
			imageContainer.appendChild(img);
			imageContainer.appendChild(imageDetails);
			
			return imageContainer;
	},

	// 創建名稱容器
	createNameContainer(petName, species, age, customInfo) {
			const nameContainer = document.createElement("div");
			nameContainer.classList.add("name-container");
			
			const petNameElement = document.createElement("h4");
			petNameElement.classList.add("pet-name");
			petNameElement.textContent = petName;
			
			const petInfo = document.createElement("small");
			petInfo.classList.add("pet-info");
			petInfo.textContent = customInfo;			
			nameContainer.appendChild(petNameElement);
			
			return nameContainer;
	},

	// 創建領養狀態容器
	createAdoptionStatusContainer(userName) {
			const statusContainer = document.createElement("div");
			statusContainer.classList.add("status-container");
			
			const statusBadge = document.createElement("span");
			statusBadge.classList.add("status-badge");
			
			const isAdopted = userName && userName !== "正在尋找家";
			
			if (isAdopted) {
					const adopterName = document.createElement("div");
					adopterName.classList.add("adopter-name");
					adopterName.textContent = userName;
					
					statusContainer.appendChild(adopterName);
			} else {
					statusBadge.classList.add("status-available");
					
					const icon = document.createElement("i");
					icon.classList.add("icon");
					icon.textContent = "🔍";
					
					const text = document.createElement("span");
					text.textContent = "尋找家庭";
					
					statusBadge.appendChild(icon);
					statusBadge.appendChild(text);
					statusContainer.appendChild(statusBadge);
			}
			
			return statusContainer;
	},

	// 創建表單狀態元素 (送養人視角)
	createFormStatusElement(formData) {
			if (formData.formExists && formData.adopterFilled) {
					const btn = document.createElement("button");
					btn.classList.add("modern-btn", "btn-primary");
					
					const icon = document.createElement("img");
					icon.classList.add("icon");
					icon.src = "/static/img/file.png";
					
					const text = document.createElement("span");
					text.textContent = "查看表單";
					
					btn.appendChild(icon);
					btn.appendChild(text);
					btn.addEventListener("click", () => {
							localStorage.setItem("postId",formData.postId)
							localStorage.setItem("user_id",formData.adoptId)
							window.location.href = "/read";
					});
					
					return btn;
					
			} else if (!formData.formExists) {
					const btn = document.createElement("button");
					btn.classList.add("modern-btn", "btn-success");
					
					const icon = document.createElement("img");
					icon.classList.add("icon");
					icon.src = "/static/img/add-document.png";
					
					const text = document.createElement("span");
					text.textContent = "建立表單";
					
					btn.appendChild(icon);
					btn.appendChild(text);
					
					btn.addEventListener("click", () => {
							window.location.href = `/question/${formData.postId}`;
					});
					
					return btn;
					
			} else if (!formData.adopterFilled && !formData.adoptId) {
					const waitingBadge = document.createElement("div");
					waitingBadge.classList.add("waiting-badge");
					
					const icon = document.createElement("img");
					icon.classList.add("icon");
					icon.src = "/static/img/sand-clock.png";
					
					const text = document.createElement("span");
					text.textContent = "等待領養";
					
					waitingBadge.appendChild(icon);
					waitingBadge.appendChild(text);
					
					return waitingBadge;
			}else if(!formData.adopterFilled){
					const waitinUser = document.createElement("div");
					waitinUser.classList.add("waiting-badge");
					
					const icon = document.createElement("img");
					icon.classList.add("icon");
					icon.src = "/static/img/sand-clock.png";
					
					const text = document.createElement("span");
					text.textContent = "等待填寫";
					
					waitinUser.appendChild(icon);
					waitinUser.appendChild(text);
					
					return waitinUser;
			}
			
			return null;
	},
	
	createFormStatusElementAsAdopt(formData) {
		
		if (!formData) {
			// 如果沒有表單數據，顯示等待狀態
			const waitingBadge = document.createElement("div");
			waitingBadge.classList.add("waiting-badge");
			
			const icon = document.createElement("img");
			icon.classList.add("icon");
			icon.src = "/static/img/sand-clock.png";
			
			const text = document.createElement("span");
			text.textContent = "等待送養人建立表單";
			
			waitingBadge.appendChild(icon);
			waitingBadge.appendChild(text);
			
			return waitingBadge;
		}
		
		if (formData.formExists && formData.adopterFilled) {
			// 表單存在且已填寫 - 可以修改
			const btn = document.createElement("button");
			btn.classList.add("modern-btn", "btn-primary");
			
			const icon = document.createElement("img");
			icon.classList.add("icon");
			icon.src = "/static/img/file.png";
			
			const text = document.createElement("span");
			text.textContent = "修改表單";
			
			btn.appendChild(icon);
			btn.appendChild(text);
			console.log(formData)
			btn.addEventListener("click", () => {
				localStorage.setItem("postId",formData.postId)
				localStorage.setItem("user_id",formData.adoptId)
				window.location.href = "/revise"
				;
			});
			
			return btn;
			
		} else if (formData.formExists && !formData.adopterFilled) {
			// 表單存在但未填寫 - 需要填寫
			const btn = document.createElement("button");
			btn.classList.add("modern-btn", "btn-warning");
			
			const icon = document.createElement("img");
			icon.classList.add("icon");
			icon.src = "/static/img/written-paper.png";
			
			const text = document.createElement("span");
			text.textContent = "填寫表單";
			
			btn.appendChild(icon);
			btn.appendChild(text);
			
			btn.addEventListener("click", () => {
				window.location.href = `/ans/${formData.postId}`;
			});
			
			return btn;
			
		} else if (!formData.formExists) {
			// 表單不存在 - 等待送養人建立
			const waitingBadge = document.createElement("div");
			waitingBadge.classList.add("waiting-badge");
			
			const icon = document.createElement("img");
			icon.classList.add("icon");
			icon.src = "/static/img/sand-clock.png";
			
			const text = document.createElement("span");
			text.textContent = "等待送養人建立表單";
			
			waitingBadge.appendChild(icon);
			waitingBadge.appendChild(text);
			
			return waitingBadge;
		}
		
		return null;
	},

	// 創建送養人容器
	createOwnerContainer(senderName) {
			const ownerContainer = document.createElement("div");
			ownerContainer.classList.add("owner-container");
			
			const ownerName = document.createElement("span");
			ownerName.classList.add("owner-name");
			ownerName.textContent = senderName;
			
			ownerContainer.appendChild(ownerName);
			
			return ownerContainer;
	},

	// 創建刊登送養操作容器
	createAdvertiseActionContainer() {
			const actionContainer = document.createElement("div");
			actionContainer.classList.add("action-container");
			
			const completeBtn = document.createElement("button");
			completeBtn.classList.add("modern-btn", "btn-success", "btn-small");
			
			const completeIcon = document.createElement("img");
			completeIcon.classList.add("icon");
			completeIcon.src = "/static/img/check.png";
			
			const completeText = document.createElement("span");
			completeText.textContent = "完成送養";
			
			completeBtn.appendChild(completeIcon);
			completeBtn.appendChild(completeText);
			
			const cancelBtn = document.createElement("button");
			cancelBtn.classList.add("modern-btn", "btn-danger", "btn-small");
			
			const cancelIcon = document.createElement("img");
			cancelIcon.classList.add("icon");
			cancelIcon.src = "/static/img/square.png";
			
			const cancelText = document.createElement("span");
			cancelText.textContent = "取消刊登";
			
			cancelBtn.appendChild(cancelIcon);
			cancelBtn.appendChild(cancelText);
			
			actionContainer.appendChild(completeBtn);
			actionContainer.appendChild(cancelBtn);
			
			return actionContainer;
	},

	// 創建領養申請操作容器
	createAdoptActionContainer() {
			const actionContainer = document.createElement("div");
			actionContainer.classList.add("action-container");
			
			const cancelBtn = document.createElement("button");
			cancelBtn.classList.add("modern-btn", "btn-warning", "btn-small");
			
			const icon = document.createElement("img");
			icon.classList.add("icon");
			icon.src = "/static/img/cancelled.png";
			
			const text = document.createElement("span");
			text.textContent = "取消領養";
			
			cancelBtn.appendChild(icon);
			cancelBtn.appendChild(text);
			actionContainer.appendChild(cancelBtn);
			
			return actionContainer;
	}
}

const memberControl = {
	async init(){
		this.checkToken();
		memberView.showBar();
		const user = await memberModel.getUser();
		
		// 處理送養資料
		const advertiseForAdoption = await memberModel.advertise_for_adoption();
		const userData = [];
		for (let i = 0; i < advertiseForAdoption.data.length; i++) {
			userData.push({
				postId: advertiseForAdoption.data[i].id,
				adopterId: advertiseForAdoption.data[i].user_id
			});
		}
		const formData = await memberModel.read_form(userData);
		for (let i = 0; i < advertiseForAdoption.data.length; i++) {
			memberView.renderAdvertiseCards(advertiseForAdoption.data[i], formData.data[i]);
		}

		const wantToAdopt = await memberModel.want_to_adopt();
		const wantToAdoptUserData = [];
		for (let i = 0; i < wantToAdopt.data.length; i++) {
			wantToAdoptUserData.push({
				postId: wantToAdopt.data[i].id,
				adopterId: wantToAdopt.data[i].adopter_id
			});
		};

		const wantToAdoptFormData = await memberModel.read_form(wantToAdoptUserData);
		for (let i = 0; i < wantToAdopt.data.length; i++) {
			console.log(wantToAdoptFormData.data[i])
			memberView.renderAdoptCards(wantToAdopt.data[i], wantToAdoptFormData.data[i]);
		};
		
		memberView.renderUser(user);
		this.logout();	
	},
	logout(){
		const btn = document.querySelector("#memberButton");
		btn.addEventListener("click",(e)=>{
			e.preventDefault();
			alert("登出成功");
			localStorage.removeItem("token");
			window.location.href = "/"
			return;
		})
	},
	checkToken(){
		const token = localStorage.getItem("token");
		if(token === null || token === undefined){
			alert("請登入");
			window.location.href = "/"
			return;
		}
	}
}

memberControl.init()